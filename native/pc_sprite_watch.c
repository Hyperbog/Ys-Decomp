#include "pc_sprite_watch.h"
#include <string.h>

static const uint16_t pcs[YS_PC_SPRITE_WATCH_EVENTS]={
    0x26F3u,0x26F5u,0x2704u,0x9932u,0x0427u
};
static uint16_t ram_word(const YsSmsBus *bus,uint16_t lo) {
    unsigned a=ys_sms_bus_read(bus,lo);
    unsigned b=ys_sms_bus_read(bus,(uint16_t)(lo+1u));
    return (uint16_t)(a|(b<<8u));
}
bool ys_pc_sprite_watch_sample(YsPcSpriteWatch *watch,
                               const YsSmsRuntime *runtime) {
    if(!watch || !runtime || !runtime->cpu || !runtime->cpu->bus)
        return false;
    const YsZ80 *cpu=runtime->cpu;
    const YsSmsBus *bus=cpu->bus;
    for(unsigned i=0;i<YS_PC_SPRITE_WATCH_EVENTS;++i) {
        if(cpu->pc!=pcs[i]) continue;
        if(i==3u && bus->mapped_bank[2]!=6u) continue;
        if(watch->counts[i]!=UINT32_MAX) ++watch->counts[i];
        if(watch->seen[i]) return true;
        YsPcSpriteWatchEvent e={0};
        e.pc=cpu->pc;e.ix=cpu->ix;
        e.slot1=bus->mapped_bank[1];e.slot2=bus->mapped_bank[2];
        e.mapper_control=bus->mapper_control;
        e.bank_select2=bus->bank_select[2];
        e.selector_c199=ys_sms_bus_read(bus,0xC199u);
        e.origin_c210=ys_sms_bus_read(bus,0xC210u);
        e.origin_c211=ys_sms_bus_read(bus,0xC211u);
        e.c100=ys_sms_bus_read(bus,0xC100u);
        e.dd00=ram_word(bus,0xC028u);
        e.dd40=ram_word(bus,0xC02Au);
        if(cpu->vdp) {
            const uint8_t *reg=cpu->vdp->registers;
            e.vdp_reg0=reg[0];e.vdp_reg1=reg[1];
            e.vdp_reg5=reg[5];e.vdp_reg6=reg[6];
            e.display_enabled=(reg[0]&4u)!=0u && (reg[1]&0x40u)!=0u;
            e.vram_writes=cpu->vdp->vram_writes;
            e.cram_writes=cpu->vdp->cram_writes;
        }
        e.steps=cpu->steps;e.irqs=runtime->recognized_irqs;
        e.vblanks=runtime->clock.vblank_events;
        watch->events[i]=e;watch->seen[i]=true;
        return true;
    }
    return true;
}
bool ys_pc_sprite_watch_write(FILE *out,const YsPcSpriteWatch *watch,
                              const YsSmsRuntime *runtime,
                              const char *why,unsigned long steps) {
    if(!out || !watch || !runtime || !runtime->cpu ||
       !runtime->cpu->bus || !why ||
       (strcmp(why,"budget")!=0 &&
        strcmp(why,"vblank_limit")!=0 &&
        strcmp(why,"unsupported")!=0 &&
        strcmp(why,"observed")!=0)) return false;
    const YsZ80 *cpu=runtime->cpu;
    if(fprintf(out,
       "{\n  \"schema\": \"ys-pc15-original-sprite-watch-v1\",\n"
       "  \"start_pc\": \"0C92\",\n"
       "  \"stop_reason\": \"%s\",\n"
       "  \"continued_steps\": %lu,\n"
       "  \"stop_pc\": \"%04X\",\n"
       "  \"stop_slot2\": %u,\n"
       "  \"stop_irqs\": %llu,\n"
       "  \"stop_vblanks\": %llu,\n"
       "  \"events\": [\n",
       why,steps,cpu->pc,(unsigned)cpu->bus->mapped_bank[2],
       (unsigned long long)runtime->recognized_irqs,
       (unsigned long long)runtime->clock.vblank_events)<0) return false;
    for(unsigned i=0;i<YS_PC_SPRITE_WATCH_EVENTS;++i) {
        const YsPcSpriteWatchEvent *e=&watch->events[i];
        if(fprintf(out,
          "    {\"pc\":\"%04X\",\"seen\":%s,\"count\":%u,"
          "\"slot1\":%u,\"slot2\":%u,\"bank_select2\":%u,"
          "\"mapper_control\":%u,\"c199\":%u,\"c210\":%u,"
          "\"c211\":%u,\"c100\":%u,\"dd00\":%u,\"dd40\":%u,"
          "\"ix\":%u,\"reg0\":%u,\"reg1\":%u,"
          "\"reg5\":%u,\"reg6\":%u,\"display_enabled\":%s,"
          "\"vram_writes\":%llu,\"cram_writes\":%llu,"
          "\"steps\":%llu,\"irqs\":%llu,\"vblanks\":%llu}%s\n",
          pcs[i],watch->seen[i]?"true":"false",watch->counts[i],
          e->slot1,e->slot2,e->bank_select2,e->mapper_control,
          e->selector_c199,e->origin_c210,e->origin_c211,e->c100,
          e->dd00,e->dd40,e->ix,e->vdp_reg0,e->vdp_reg1,
          e->vdp_reg5,e->vdp_reg6,
          e->display_enabled?"true":"false",
          (unsigned long long)e->vram_writes,
          (unsigned long long)e->cram_writes,
          (unsigned long long)e->steps,
          (unsigned long long)e->irqs,
          (unsigned long long)e->vblanks,
          i+1u<YS_PC_SPRITE_WATCH_EVENTS?",":"")<0) return false;
    }
    return fputs("  ]\n}\n",out)>=0 && ferror(out)==0;
}
