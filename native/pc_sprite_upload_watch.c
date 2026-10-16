#include "pc_sprite_upload_watch.h"
#include <limits.h>
#include <string.h>

static uint32_t crc32(const uint8_t *p,unsigned length) {
    uint32_t crc=0xFFFFFFFFu;
    for(unsigned i=0;i<length;++i) {
        crc^=p[i];
        for(unsigned k=0;k<8u;++k)
            crc=(crc>>1u)^(0xEDB88320u&(0u-(crc&1u)));
    }
    return ~crc;
}
bool ys_pc_sprite_upload_watch_sample(YsPcSpriteUploadWatch *w,
                                      const YsSmsRuntime *rt) {
    if(!w || !rt || !rt->cpu || !rt->cpu->bus || !rt->cpu->vdp)
        return false;
    const YsZ80 *cpu=rt->cpu;
    const YsSmsBus *bus=cpu->bus;
    const YsSmsVdp *vdp=cpu->vdp;
    if(w->sampled && w->last_pc==cpu->pc && w->last_step==cpu->steps)
        return true;
    w->sampled=true;w->last_pc=cpu->pc;w->last_step=cpu->steps;
    if(cpu->pc==0x0427u) {
        if(w->entries==UINT_MAX) return false;
        if(w->active) {
            if(w->abandoned==UINT_MAX) return false;
            ++w->abandoned;
        }
        for(unsigned i=0;i<YS_PC_UPLOAD_Y;++i)
            w->snapshot[i]=ys_sms_bus_read(bus,(uint16_t)(0xDD00u+i));
        for(unsigned i=0;i<YS_PC_UPLOAD_XT;++i)
            w->snapshot[YS_PC_UPLOAD_Y+i]=
                ys_sms_bus_read(bus,(uint16_t)(0xDD40u+i));
        w->entry_step=cpu->steps;
        w->entry_writes=vdp->vram_writes;
        w->active=true;w->return_phase=0u;
        ++w->entries;
    } else if(cpu->pc==0x053Fu && w->active &&
              cpu->steps>w->entry_step) {
        if(w->return_phase==0u) {
            if(w->halfway==UINT_MAX) return false;
            ++w->halfway;w->return_phase=1u;
            return true; /* This first RET resumes at $0436. */
        }
        if(w->return_phase!=1u || w->completed==UINT_MAX ||
           w->bytes_compared>UINT64_MAX-YS_PC_UPLOAD_TOTAL ||
           vdp->vram_writes<w->entry_writes) return false;
        uint8_t dest[YS_PC_UPLOAD_TOTAL];
        memcpy(dest,vdp->vram+0x3F00u,YS_PC_UPLOAD_Y);
        memcpy(dest+YS_PC_UPLOAD_Y,vdp->vram+0x3F80u,YS_PC_UPLOAD_XT);
        unsigned different=0u;
        for(unsigned i=0;i<YS_PC_UPLOAD_TOTAL;++i) {
            if(dest[i]==w->snapshot[i]) continue;
            ++different;
            if(w->first_mismatch_1based==0u) {
                w->first_mismatch_1based=i+1u;
                w->first_expected=w->snapshot[i];
                w->first_actual=dest[i];
            }
        }
        if(w->bytes_different>UINT64_MAX-different) return false;
        w->bytes_different+=different;
        w->bytes_compared+=YS_PC_UPLOAD_TOTAL;
        if(different) {
            if(w->mismatched==UINT_MAX) return false;
            ++w->mismatched;
        } else {
            if(w->matched==UINT_MAX) return false;
            ++w->matched;
        }
        uint32_t source_crc=crc32(w->snapshot,YS_PC_UPLOAD_TOTAL);
        uint32_t vram_crc=crc32(dest,YS_PC_UPLOAD_TOTAL);
        if(w->completed==0u) {
            w->first_completion=cpu->steps;
            w->first_source_crc=source_crc;
            w->first_vram_crc=vram_crc;
        }
        ++w->completed;
        w->last_completion=cpu->steps;
        w->last_write_delta=vdp->vram_writes-w->entry_writes;
        w->last_source_crc=source_crc;
        w->last_vram_crc=vram_crc;
        w->active=false;w->return_phase=0u;
    }
    return true;
}
bool ys_pc_sprite_upload_watch_write(FILE *out,
                                     const YsPcSpriteUploadWatch *w,
                                     const YsSmsRuntime *rt,
                                     const char *reason,unsigned long steps) {
    if(!out || !w || !rt || !rt->cpu ||
       !rt->cpu->bus || !rt->cpu->vdp || !reason ||
       (strcmp(reason,"budget")!=0 &&
        strcmp(reason,"vblank_limit")!=0 &&
        strcmp(reason,"unsupported")!=0 &&
        strcmp(reason,"collision_observed")!=0) ||
       (uint64_t)w->completed+w->abandoned+(w->active?1u:0u)!=w->entries ||
       (uint64_t)w->matched+w->mismatched!=w->completed ||
       w->bytes_compared!=(uint64_t)YS_PC_UPLOAD_TOTAL*w->completed ||
       w->halfway<w->completed) return false;
    const YsZ80 *cpu=rt->cpu;
    return fprintf(out,
       "{\n"
       " \"schema\":\"ys-pc36-sat-source-upload-v1\",\n"
       " \"source\":\"pc34-same-run\",\n"
       " \"continued_steps\":%lu,\"stop_reason\":\"%s\",\n"
       " \"stop_pc\":\"%04X\",\"stop_irq\":%llu,"
       "\"stop_vblank\":%llu,\"stop_slot2\":%u,\n"
       " \"entry_pc\":\"0427\",\"return_pc\":\"053F\",\n"
       " \"source_y\":\"DD00\",\"source_xt\":\"DD40\","
       "\"vram_y\":\"3F00\",\"vram_xt\":\"3F80\",\n"
       " \"bytes_per_upload\":%u,\"entries\":%u,\"halfway\":%u,\n"
       " \"completed\":%u,\"matched\":%u,\"mismatched\":%u,"
       "\"abandoned\":%u,\"pending\":%s,\n"
       " \"bytes_compared\":%llu,\"bytes_different\":%llu,\n"
       " \"first_mismatch_1based\":%u,\"first_expected\":%u,"
       "\"first_actual\":%u,\n"
       " \"first_completion\":%llu,\"last_completion\":%llu,"
       "\"last_write_delta\":%llu,\n"
       " \"first_source_crc32\":%u,\"first_vram_crc32\":%u,"
       "\"last_source_crc32\":%u,\"last_vram_crc32\":%u\n}\n",
       steps,reason,cpu->pc,
       (unsigned long long)rt->recognized_irqs,
       (unsigned long long)rt->clock.vblank_events,
       (unsigned)cpu->bus->mapped_bank[2],
       (unsigned)YS_PC_UPLOAD_TOTAL,w->entries,w->halfway,
       w->completed,w->matched,w->mismatched,w->abandoned,
       w->active?"true":"false",
       (unsigned long long)w->bytes_compared,
       (unsigned long long)w->bytes_different,
       w->first_mismatch_1based,w->first_expected,w->first_actual,
       (unsigned long long)w->first_completion,
       (unsigned long long)w->last_completion,
       (unsigned long long)w->last_write_delta,
       w->first_source_crc,w->first_vram_crc,
       w->last_source_crc,w->last_vram_crc)>0 &&
       ferror(out)==0;
}
