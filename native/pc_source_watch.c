#include "pc_source_watch.h"
#include <string.h>

static const uint16_t pcs[YS_PC_WATCH_EVENTS]={
    0x476Cu,0x4773u,0x47C2u,0x486Cu,0x48DFu
};
bool ys_pc_source_watch_sample(YsPcSourceWatch *out,
                               const YsSmsRuntime *rt) {
    if(!out || !rt || !rt->cpu || !rt->cpu->bus) return false;
    const YsZ80 *cpu=rt->cpu;
    const YsSmsBus *bus=cpu->bus;
    if(bus->mapped_bank[1]!=1u) return true;
    for(unsigned i=0;i<YS_PC_WATCH_EVENTS;++i) {
        if(cpu->pc!=pcs[i]) continue;
        if(out->counts[i]!=UINT32_MAX) ++out->counts[i];
        if(i>=2u && out->observed_collision_calls!=UINT32_MAX)
            ++out->observed_collision_calls;
        if(out->seen[i]) return true;
        YsPcSourceWatchEvent ev={0};
        ev.pc=cpu->pc;ev.ix=cpu->ix;
        ev.slot1=bus->mapped_bank[1];ev.slot2=bus->mapped_bank[2];
        ev.bank_select2=bus->bank_select[2];
        ev.mapper_control=bus->mapper_control;
        ev.c100=ys_sms_bus_read(bus,0xC100u);
        ev.c119=ys_sms_bus_read(bus,0xC119u);
        ev.c181=ys_sms_bus_read(bus,0xC181u);
        ev.c20d=ys_sms_bus_read(bus,0xC20Du);
        ev.c20e=ys_sms_bus_read(bus,0xC20Eu);
        ev.c210=ys_sms_bus_read(bus,0xC210u);
        ev.c211=ys_sms_bus_read(bus,0xC211u);
        /* These are observed relative IX slot bytes; no assertion
           that IX points to a valid object when at the entry site. */
        ev.ix13=ys_sms_bus_read(bus,(uint16_t)(cpu->ix+13u));
        ev.ix14=ys_sms_bus_read(bus,(uint16_t)(cpu->ix+14u));
        ev.ix16=ys_sms_bus_read(bus,(uint16_t)(cpu->ix+16u));
        ev.ix17=ys_sms_bus_read(bus,(uint16_t)(cpu->ix+17u));
        ev.steps=cpu->steps;ev.irqs=rt->recognized_irqs;
        ev.vblanks=rt->clock.vblank_events;
        out->seen[i]=true;out->events[i]=ev;
        return true;
    }
    return true;
}
bool ys_pc_source_watch_write(FILE *file,const YsPcSourceWatch *watch,
                               const YsSmsRuntime *rt,
                               const char *reason,unsigned long executed) {
    if(!file || !watch || !rt || !rt->cpu || !rt->cpu->bus ||
       !reason || (strcmp(reason,"budget")!=0 &&
                   strcmp(reason,"unsupported")!=0 &&
                   strcmp(reason,"halted")!=0 &&
                   strcmp(reason,"vblank_limit")!=0)) return false;
    const YsZ80 *cpu=rt->cpu;
    if(fprintf(file,
       "{\n  \"schema\": \"ys-pc12-source-watch-v1\",\n"
       "  \"start_pc\": \"0C92\",\n"
       "  \"stop_reason\": \"%s\",\n"
       "  \"continued_steps\": %lu,\n"
       "  \"stop_pc\": \"%04X\",\n"
       "  \"stop_cpu_status\": %u,\n"
       "  \"stop_slot1\": %u,\n"
       "  \"stop_slot2\": %u,\n"
       "  \"stop_irq\": %llu,\n"
       "  \"stop_vblank\": %llu,\n"
       "  \"observed_collision_calls\": %u,\n"
       "  \"events\": [\n",
       reason,executed,cpu->pc,(unsigned)cpu->status,
       (unsigned)cpu->bus->mapped_bank[1],
       (unsigned)cpu->bus->mapped_bank[2],
       (unsigned long long)rt->recognized_irqs,
       (unsigned long long)rt->clock.vblank_events,
       watch->observed_collision_calls)<0) return false;
    for(unsigned i=0;i<YS_PC_WATCH_EVENTS;++i) {
        const YsPcSourceWatchEvent *e=&watch->events[i];
        if(fprintf(file,
          "    {\"pc\":\"%04X\",\"seen\":%s,\"count\":%u,"
          "\"mapper_slot1\":%u,\"mapper_slot2\":%u,"
          "\"raw_bank_select2\":%u,\"mapper_control\":%u,"
          "\"ix\":%u,\"c100\":%u,\"c119\":%u,\"c181\":%u,"
          "\"c20d\":%u,\"c20e\":%u,\"c210\":%u,\"c211\":%u,"
          "\"ix13\":%u,\"ix14\":%u,\"ix16\":%u,\"ix17\":%u,"
          "\"steps\":%llu,\"irq\":%llu,\"vblank\":%llu}%s\n",
          pcs[i],watch->seen[i]?"true":"false",watch->counts[i],
          e->slot1,e->slot2,e->bank_select2,e->mapper_control,
          e->ix,e->c100,e->c119,e->c181,e->c20d,e->c20e,
          e->c210,e->c211,e->ix13,e->ix14,e->ix16,e->ix17,
          (unsigned long long)e->steps,
          (unsigned long long)e->irqs,
          (unsigned long long)e->vblanks,
          i+1u<YS_PC_WATCH_EVENTS?",":"")<0) return false;
    }
    return fputs("  ]\n}\n",file)>=0 && ferror(file)==0;
}
