#include "pc_sat_strobes.h"
#include <limits.h>
#include <string.h>

bool ys_pc_sat_strobes_set_phase(YsPcSatStrobeAudit *a,unsigned phase) {
    if(!a || !a->cpu || a->overflow || phase>=YS_PC39_PHASES ||
       phase<a->phase) return false;
    a->phase=phase;
    return true;
}

void ys_pc_sat_strobes_hook(void *context,uint16_t logical,
                            uint16_t physical,uint8_t before,uint8_t after) {
    YsPcSatStrobeAudit *a=context;
    if(!a || a->overflow || physical<0x1D00u ||
       physical>=0x1DC0u) return;
    if(!a->cpu || a->phase>=YS_PC39_PHASES ||
       logical<0xC000u || ((unsigned)logical&0x1FFFu)!=physical) {
        a->overflow=true;
        return;
    }
    const unsigned phase=a->phase;
    const unsigned index=physical-0x1D00u;
    const bool same=before==after;
    const bool irq=a->cpu->irq_write_active;
    const uint16_t pc=irq?0x0038u:a->cpu->instruction_pc;
    const uint8_t bank=irq?0u:a->cpu->instruction_bank;
    const uint64_t step=a->cpu->steps;
    if((bank>15u && bank!=254u && bank!=255u) ||
       a->count[phase]==UINT64_MAX ||
       (same && a->same[phase]==UINT64_MAX) ||
       (!same && a->changed[phase]==UINT64_MAX)) {
        a->overflow=true;
        return;
    }
    unsigned site=0u;
    while(site<a->site_count) {
        const YsPcSatStrobeSite *s=&a->sites[site];
        if(s->phase==phase && s->pc==pc && s->bank==bank &&
           s->irq==(unsigned)irq) break;
        ++site;
    }
    if(site==a->site_count) {
        if(site==YS_PC39_MAX_SITES) {a->overflow=true;return;}
        a->sites[site]=(YsPcSatStrobeSite){0};
        a->sites[site].pc=pc;a->sites[site].bank=bank;
        a->sites[site].phase=(uint8_t)phase;
        a->sites[site].irq=(uint8_t)irq;
        a->sites[site].first_step=step;
        ++a->site_count;
    }
    YsPcSatStrobeSite *s=&a->sites[site];
    if(s->count==UINT64_MAX || (same && s->same==UINT64_MAX) ||
       step<s->last_step || (logical>=0xE000u &&
                             a->alias[phase]==UINT64_MAX) ||
       (irq && a->irq[phase]==UINT64_MAX) ||
       (index<64u && a->y[phase]==UINT64_MAX) ||
       (index>=64u && a->xt[phase]==UINT64_MAX)) {
        a->overflow=true;
        return;
    }
    ++s->count;
    if(same) ++s->same;
    s->last_step=step;
    ++a->count[phase];
    if(same) ++a->same[phase];
    else ++a->changed[phase];
    if(index<64u) ++a->y[phase];
    else ++a->xt[phase];
    if(logical>=0xE000u) ++a->alias[phase];
    if(irq) ++a->irq[phase];
    if(!a->touched[phase][index]) {
        a->touched[phase][index]=1u;
        ++a->unique[phase];
    }
}

bool ys_pc_sat_strobes_write(FILE *file,const YsPcSatStrobeAudit *a,
                              const YsSmsRuntime *rt,
                              const char *reason,unsigned long steps) {
    if(!file || !a || !rt || !rt->cpu || !rt->cpu->bus ||
       a->cpu!=rt->cpu || a->overflow || a->phase!=1u ||
       !reason || strcmp(reason,"budget")!=0 ||
       a->site_count>YS_PC39_MAX_SITES) return false;
    for(unsigned p=0;p<2u;++p) {
        if(a->count[p]!=a->same[p]+a->changed[p] ||
           a->count[p]!=a->y[p]+a->xt[p] ||
           a->unique[p]>YS_PC39_BYTES ||
           a->alias[p]>a->count[p] ||
           a->irq[p]>a->count[p]) return false;
        uint64_t found=0u;
        for(unsigned i=0;i<a->site_count;++i) {
            const YsPcSatStrobeSite *s=&a->sites[i];
            if(s->phase!=p) continue;
            if(s->same>s->count || s->last_step<s->first_step ||
               found>UINT64_MAX-s->count) return false;
            found+=s->count;
        }
        if(found!=a->count[p]) return false;
    }
    if(fprintf(file,
       "{\n\"schema\":\"ys-pc39-original-sat-wram-strobes-v1\","
       "\"source\":\"pc34-same-run\",\"continued_steps\":%lu,"
       "\"stop_reason\":\"%s\",\"stop_pc\":\"%04X\","
       "\"stop_irq\":%llu,\"stop_vblank\":%llu,"
       "\"site_count\":%u,\n\"phases\":[\n",
       steps,reason,rt->cpu->pc,
       (unsigned long long)rt->recognized_irqs,
       (unsigned long long)rt->clock.vblank_events,a->site_count)<0)
        return false;
    for(unsigned p=0;p<2u;++p) {
        if(fprintf(file,
          "{\"name\":\"%s\",\"count\":%llu,\"same\":%llu,"
          "\"changed\":%llu,\"y\":%llu,\"xt\":%llu,"
          "\"alias\":%llu,\"irq\":%llu,\"unique\":%u}%s\n",
          p==0u?"pre-m45":"post-m45",
          (unsigned long long)a->count[p],
          (unsigned long long)a->same[p],
          (unsigned long long)a->changed[p],
          (unsigned long long)a->y[p],
          (unsigned long long)a->xt[p],
          (unsigned long long)a->alias[p],
          (unsigned long long)a->irq[p],a->unique[p],
          p==0u?",":"")<0) return false;
    }
    if(fputs("],\"sites\":[\n",file)<0) return false;
    for(unsigned i=0;i<a->site_count;++i) {
        const YsPcSatStrobeSite *s=&a->sites[i];
        if(fprintf(file,
           "{\"phase\":%u,\"pc\":\"%04X\",\"bank\":%u,"
           "\"irq\":%s,\"count\":%llu,\"same\":%llu,"
           "\"first_step\":%llu,\"last_step\":%llu}%s\n",
           (unsigned)s->phase,s->pc,(unsigned)s->bank,
           s->irq?"true":"false",
           (unsigned long long)s->count,
           (unsigned long long)s->same,
           (unsigned long long)s->first_step,
           (unsigned long long)s->last_step,
           i+1u<a->site_count?",":"")<0) return false;
    }
    return fputs("]}\n",file)>=0 && ferror(file)==0;
}
