#include "pc_sat_provenance.h"
#include <limits.h>
#include <string.h>

static uint8_t source_bank(const YsZ80 *cpu) {
    const YsSmsBus *bus=cpu->bus;
    if(cpu->pc>=0xC000u) return 255u;
    if(cpu->pc>=0x8000u && (bus->mapper_control&8u)) return 254u;
    return cpu->pc<0x0400u?0u:bus->mapped_bank[cpu->pc>>14u];
}
static void read_sat(const YsSmsBus *bus,uint8_t out[YS_PC38_BYTES]) {
    for(unsigned i=0;i<YS_PC38_BYTES;++i)
        out[i]=ys_sms_bus_read(bus,(uint16_t)(0xDD00u+i));
}
bool ys_pc_sat_provenance_sample(YsPcSatProvenance *a,
                                 const YsSmsRuntime *rt) {
    if(!a || !rt || !rt->cpu || !rt->cpu->bus) return false;
    const YsZ80 *cpu=rt->cpu;
    uint8_t current[YS_PC38_BYTES];
    read_sat(cpu->bus,current);
    if(a->initialized) {
        if(cpu->steps==a->previous_steps)
            return cpu->pc==a->previous_pc &&
                   source_bank(cpu)==a->previous_bank;
        if(cpu->steps<a->previous_steps) return false;
        /* Attribution is to the previous sampled CPU/IRQ step boundary.
           A change is not proof that the preceding opcode alone wrote it. */
        for(unsigned i=0;i<YS_PC38_BYTES;++i) {
            if(current[i]==a->previous[i]) continue;
            unsigned site=0u;
            for(;site<a->site_count;++site)
                if(a->sites[site].pc==a->previous_pc &&
                   a->sites[site].physical_bank==a->previous_bank) break;
            if(site==a->site_count) {
                if(a->site_count==YS_PC38_MAX_SITES) return false;
                a->sites[site].pc=a->previous_pc;
                a->sites[site].physical_bank=a->previous_bank;
                a->sites[site].changed_bytes=0u;
                ++a->site_count;
            }
            if(a->sites[site].changed_bytes==UINT64_MAX ||
               a->changed==UINT64_MAX) return false;
            ++a->sites[site].changed_bytes;
            ++a->changed;
            if(i<YS_PC38_Y) ++a->changed_y;
            else ++a->changed_xt;
            if(!a->unique[i]) {a->unique[i]=1u;++a->unique_bytes;}
        }
    } else a->initialized=true;
    if(a->samples==UINT64_MAX) return false;
    ++a->samples;
    memcpy(a->previous,current,sizeof(current));
    a->previous_steps=cpu->steps;
    a->previous_pc=cpu->pc;
    a->previous_bank=source_bank(cpu);
    return true;
}
bool ys_pc_sat_provenance_upload(YsPcSatProvenance *a,
                                 const YsSmsRuntime *rt) {
    if(!a || !a->initialized || !rt || !rt->cpu ||
       !rt->cpu->bus || rt->cpu->pc!=0x0427u ||
       rt->cpu->steps!=a->previous_steps ||
       a->upload_count==UINT_MAX) return false;
    uint8_t current[YS_PC38_BYTES];
    read_sat(rt->cpu->bus,current);
    if(a->have_upload) {
        unsigned different=0u;
        for(unsigned i=0;i<YS_PC38_BYTES;++i)
            different+=(unsigned)(current[i]!=a->uploaded[i]);
        if(a->upload_diff_bytes>UINT64_MAX-different) return false;
        a->upload_diff_bytes+=different;
        if(different) ++a->changed_uploads;
        else ++a->equal_uploads;
    }
    memcpy(a->uploaded,current,sizeof(current));
    a->have_upload=true;
    ++a->upload_count;
    return true;
}
bool ys_pc_sat_provenance_write(FILE *f,const YsPcSatProvenance *a,
                                const YsSmsRuntime *rt,
                                const char *reason,unsigned long steps) {
    if(!f || !a || !a->initialized || !rt || !rt->cpu ||
       !rt->cpu->bus || !reason || strcmp(reason,"budget")!=0 ||
       a->upload_count!=a->changed_uploads+a->equal_uploads+1u ||
       a->changed!=a->changed_y+a->changed_xt ||
       a->unique_bytes>YS_PC38_BYTES ||
       a->site_count>YS_PC38_MAX_SITES) return false;
    uint64_t total=0u;
    for(unsigned i=0;i<a->site_count;++i) total+=a->sites[i].changed_bytes;
    if(total!=a->changed) return false;
    if(fprintf(f,
       "{\n\"schema\":\"ys-pc38-sat-wram-boundary-v1\","
       "\"source\":\"pc34-same-run\","
       "\"continued_steps\":%lu,\"stop_reason\":\"%s\","
       "\"stop_pc\":\"%04X\",\"stop_irq\":%llu,"
       "\"stop_vblank\":%llu,"
       "\"sampled_boundaries\":%llu,"
       "\"changed_bytes\":%llu,\"changed_y\":%llu,"
       "\"changed_xt\":%llu,\"unique_bytes\":%u,"
       "\"upload_count\":%u,\"changed_uploads\":%u,"
       "\"equal_uploads\":%u,\"upload_diff_bytes\":%llu,"
       "\"site_count\":%u,\"sites\":[\n",
       steps,reason,rt->cpu->pc,
       (unsigned long long)rt->recognized_irqs,
       (unsigned long long)rt->clock.vblank_events,
       (unsigned long long)a->samples,
       (unsigned long long)a->changed,
       (unsigned long long)a->changed_y,
       (unsigned long long)a->changed_xt,a->unique_bytes,
       a->upload_count,a->changed_uploads,a->equal_uploads,
       (unsigned long long)a->upload_diff_bytes,a->site_count)<0) return false;
    for(unsigned i=0;i<a->site_count;++i) {
        const YsPcSatChangeSite *s=&a->sites[i];
        if(fprintf(f,
           "{\"pc\":\"%04X\",\"physical_bank\":%u,"
           "\"changed_bytes\":%llu}%s\n",s->pc,
           (unsigned)s->physical_bank,
           (unsigned long long)s->changed_bytes,
           i+1u<a->site_count?",":"")<0) return false;
    }
    return fputs("]}\n",f)>=0 && ferror(f)==0;
}
