#include "pc40_route.h"
#include <limits.h>
#include <string.h>

/* Fixed bank-0 selector/callsite path, mapped bank-6 producers and
   mapped bank-1 collision route. Event meanings are SOURCE PCs only. */
static const uint16_t pcs[YS_PC40_EVENTS]={
    0x26B6u,0x26DAu,0x26F3u,0x26F5u,0x2704u,0x2BF2u,
    0x9932u,0x9966u,0x4773u,0x47C2u,0x486Cu,0x48DFu
};
static const uint8_t banks[YS_PC40_EVENTS]={
    0u,0u,0u,0u,0u,0u,6u,6u,1u,1u,1u,1u
};
static uint8_t bank_at(const YsZ80 *cpu) {
    const YsSmsBus *b=cpu->bus;
    if(cpu->pc<0x0400u) return 0u;
    if(cpu->pc>=0xC000u) return 255u;
    if(cpu->pc>=0x8000u && (b->mapper_control&8u)) return 254u;
    return b->mapped_bank[cpu->pc>>14u];
}
bool ys_pc40_route_sample(YsPc40Route *w,const YsSmsRuntime *rt,
                           unsigned long iteration) {
    if(!w || !rt || !rt->cpu || !rt->cpu->bus ||
       iteration!=w->seen_iterations || iteration>=600000ul)
        return false;
    unsigned phase=iteration>=300000ul?1u:0u;
    if(phase && !w->prefix_seen) return false;
    uint8_t bank=bank_at(rt->cpu);
    uint8_t selector=ys_sms_bus_read(rt->cpu->bus,0xC01Fu);
    for(unsigned i=0;i<YS_PC40_EVENTS;++i) {
        if(rt->cpu->pc!=pcs[i] || bank!=banks[i]) continue;
        YsPc40Event *e=&w->events[phase][i];
        if(e->hits==UINT32_MAX) return false;
        if(e->hits==0u) {
            e->first_step=rt->cpu->steps;
            e->first_selector=selector;
            e->first_slot2=rt->cpu->bus->mapped_bank[2];
        }
        ++e->hits;
        e->last_step=rt->cpu->steps;
        break;
    }
    ++w->seen_iterations;
    return true;
}
bool ys_pc40_route_mark_prefix(YsPc40Route *w,const YsSmsRuntime *rt,
                                unsigned long iteration,
                                const uint32_t sprite_counts[5],
                                uint32_t collisions) {
    if(!w || !rt || !rt->cpu || !rt->cpu->bus ||
       !sprite_counts || iteration!=300000ul ||
       w->seen_iterations!=iteration || w->prefix_seen) return false;
    w->prefix_seen=true;
    w->prefix_pc=rt->cpu->pc;
    w->prefix_slot1=rt->cpu->bus->mapped_bank[1];
    w->prefix_slot2=rt->cpu->bus->mapped_bank[2];
    w->prefix_selector=ys_sms_bus_read(rt->cpu->bus,0xC01Fu);
    w->prefix_irq=rt->recognized_irqs;
    w->prefix_vblank=rt->clock.vblank_events;
    for(unsigned i=0;i<5u;++i) w->prefix_sprite[i]=sprite_counts[i];
    w->prefix_collisions=collisions;
    return true;
}
bool ys_pc40_route_write(FILE *file,const YsPc40Route *w,
                          const YsSmsRuntime *rt,const char *reason,
                          unsigned long steps) {
    if(!file || !w || !rt || !rt->cpu || !rt->cpu->bus ||
       !reason || !w->prefix_seen ||
       /* A stop inside the iteration occurs AFTER the read-only
          sample but BEFORE for-loop ++steps. A budget stop does not. */
       (strcmp(reason,"budget")==0 ?
        steps!=w->seen_iterations :
        !(w->seen_iterations==steps ||
          (steps<600000ul && w->seen_iterations==steps+1ul))) ||
       steps<300000ul || steps>600000ul ||
       (strcmp(reason,"budget")!=0 &&
        strcmp(reason,"unsupported")!=0 &&
        strcmp(reason,"vblank_limit")!=0 &&
        strcmp(reason,"collision_observed")!=0)) return false;
    if(fprintf(file,
      "{\n\"schema\":\"ys-pc40-source-route-600k-v1\","
      "\"source\":\"pc34-controller-prefix\","
      "\"continued_steps\":%lu,\"stop_reason\":\"%s\","
      "\"stop_pc\":\"%04X\",\"stop_irq\":%llu,"
      "\"stop_vblank\":%llu,"
      "\"stop_slot1\":%u,\"stop_slot2\":%u,"
      "\"stop_selector\":%u,\n"
      "\"prefix_steps\":300000,\"prefix_pc\":\"%04X\","
      "\"prefix_slot1\":%u,\"prefix_slot2\":%u,"
      "\"prefix_selector\":%u,"
      "\"prefix_irq\":%llu,\"prefix_vblank\":%llu,"
      "\"prefix_collisions\":%u,"
      "\"prefix_sprite\":[%u,%u,%u,%u,%u],\n"
      "\"events\":[\n",
      steps,reason,rt->cpu->pc,
      (unsigned long long)rt->recognized_irqs,
      (unsigned long long)rt->clock.vblank_events,
      (unsigned)rt->cpu->bus->mapped_bank[1],
      (unsigned)rt->cpu->bus->mapped_bank[2],
      (unsigned)ys_sms_bus_read(rt->cpu->bus,0xC01Fu),
      w->prefix_pc,(unsigned)w->prefix_slot1,
      (unsigned)w->prefix_slot2,(unsigned)w->prefix_selector,
      (unsigned long long)w->prefix_irq,
      (unsigned long long)w->prefix_vblank,w->prefix_collisions,
      w->prefix_sprite[0],w->prefix_sprite[1],w->prefix_sprite[2],
      w->prefix_sprite[3],w->prefix_sprite[4])<0) return false;
    for(unsigned phase=0;phase<YS_PC40_PHASES;++phase)
        for(unsigned i=0;i<YS_PC40_EVENTS;++i) {
            const YsPc40Event *e=&w->events[phase][i];
            if(e->hits && e->last_step<e->first_step) return false;
            if(fprintf(file,
              "{\"phase\":%u,\"pc\":\"%04X\",\"bank\":%u,"
              "\"hits\":%u,\"first_step\":%llu,"
              "\"last_step\":%llu,\"first_selector\":%u,"
              "\"first_slot2\":%u}%s\n",
              phase,pcs[i],banks[i],e->hits,
              (unsigned long long)e->first_step,
              (unsigned long long)e->last_step,
              (unsigned)e->first_selector,(unsigned)e->first_slot2,
              phase==YS_PC40_PHASES-1u && i==YS_PC40_EVENTS-1u?"":",")<0)
                return false;
        }
    return fputs("]}\n",file)>=0 && ferror(file)==0;
}
