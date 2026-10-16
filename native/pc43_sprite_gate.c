#include "pc43_sprite_gate.h"
#include <limits.h>
#include <string.h>

/* Physical bank 6 source code maps into SMS slot 2 $8000-$BFFF.
   SRAM-enable makes even a matching numeric bank non-ROM. */
static bool mapped_bank6(const YsZ80 *cpu) {
    return cpu && cpu->bus && cpu->pc>=0x8000u &&
           cpu->pc<0xC000u &&
           (cpu->bus->mapper_control&0x08u)==0u &&
           cpu->bus->mapped_bank[2]==6u;
}
bool ys_pc43_gate_pre(YsPc43SpriteGate *w,const YsSmsRuntime *rt,
                      unsigned long iteration) {
    if(!w || !rt || !rt->cpu || !rt->cpu->bus ||
       w->jump_pending || iteration!=w->observed_iterations ||
       iteration>=600000ul) return false;
    const YsZ80 *cpu=rt->cpu;
    const YsSmsBus *bus=cpu->bus;
    if(mapped_bank6(cpu)) {
        if(cpu->pc==0x9966u) {
            if(w->count>=YS_PC43_MAX_ENTRIES) return false;
            YsPc43GateEvent *e=&w->entries[w->count++];
            memset(e,0,sizeof(*e));
            e->entry_iteration=iteration;
            e->entry_cpu_step=cpu->steps;
            e->slot2=bus->mapped_bank[2];
            e->selector=ys_sms_bus_read(bus,0xC01Fu);
            e->c198_entry=ys_sms_bus_read(bus,0xC198u);
            e->c199_entry=ys_sms_bus_read(bus,0xC199u);
            e->c1b9_entry=ys_sms_bus_read(bus,0xC1B9u);
        } else if(cpu->pc==0x9969u) {
            if(w->or_hits==UINT_MAX) return false;
            ++w->or_hits;
            if(w->count && !w->entries[w->count-1u].or_seen)
                w->entries[w->count-1u].or_seen=true;
        } else if(cpu->pc==0x996Au) {
            if(w->gate_hits==UINT_MAX) return false;
            ++w->gate_hits;
            if(!w->count || w->entries[w->count-1u].gate_seen) {
                if(w->orphan_gates==UINT_MAX) return false;
                ++w->orphan_gates;
            } else {
                unsigned idx=w->count-1u;
                YsPc43GateEvent *e=&w->entries[idx];
                e->gate_seen=true;
                e->gate_iteration=iteration;
                e->gate_cpu_step=cpu->steps;
                e->a_gate=cpu->a;
                e->f_gate=cpu->f;
                e->c198_gate=ys_sms_bus_read(bus,0xC198u);
                e->iff2_gate=(uint8_t)cpu->iff2;
                e->irq_before=rt->recognized_irqs;
                w->jump_pending=true;
                w->pending_entry=idx;
            }
        } else if(cpu->pc==0x996Cu) {
            if(w->call_sites==UINT_MAX) return false;
            ++w->call_sites;
        } else if(cpu->pc==0x9932u) {
            if(w->producer_entries==UINT_MAX) return false;
            ++w->producer_entries;
        } else if(cpu->pc==0x99C6u) {
            if(w->skip_targets==UINT_MAX) return false;
            ++w->skip_targets;
        }
    }
    ++w->observed_iterations;
    return true;
}
bool ys_pc43_gate_post(YsPc43SpriteGate *w,const YsSmsRuntime *rt,
                       unsigned long iteration) {
    if(!w || !rt || !rt->cpu || !rt->cpu->bus ||
       w->observed_iterations!=iteration+1ul) return false;
    if(!w->jump_pending) return true;
    if(w->pending_entry>=w->count) return false;
    YsPc43GateEvent *e=&w->entries[w->pending_entry];
    if(!e->gate_seen || e->successor_seen ||
       e->gate_iteration!=iteration) return false;
    e->successor_seen=true;
    e->successor_pc=rt->cpu->pc;
    e->irq_after=rt->recognized_irqs;
    e->irq_during_gate=e->irq_after!=e->irq_before;
    bool zero=(e->f_gate&Z80_F_Z)!=0u;
    if(zero) ++w->branch_zero;
    else ++w->branch_nonzero;
    if(e->irq_during_gate) ++w->irq_gate;
    else if(e->successor_pc!=(zero?0x99C6u:0x996Cu))
        ++w->branch_mismatch;
    w->jump_pending=false;
    return true;
}
bool ys_pc43_gate_write(FILE *f,const YsPc43SpriteGate *w,
                        const YsSmsRuntime *rt,const char *reason,
                        unsigned long steps) {
    if(!f || !w || !rt || !rt->cpu || !reason ||
       strcmp(reason,"budget")!=0 || steps!=600000ul ||
       w->observed_iterations!=steps || w->jump_pending ||
       w->count>YS_PC43_MAX_ENTRIES) return false;
    if(fprintf(f,
       "{\"schema\":\"ys-pc43-original-bank6-c198-gate-v1\","
       "\"source\":\"pc42-600k-original-controller\","
       "\"continued_steps\":%lu,\"stop_reason\":\"%s\","
       "\"stop_pc\":\"%04X\","
       "\"entries\":%u,\"or_hits\":%u,\"gate_hits\":%u,"
       "\"call_sites\":%u,\"producer_entries\":%u,"
       "\"skip_targets\":%u,\"orphan_gates\":%u,"
       "\"branch_zero\":%u,\"branch_nonzero\":%u,"
       "\"branch_mismatch\":%u,\"irq_gate\":%u,"
       "\"events\":[\n",
       steps,reason,rt->cpu->pc,w->count,w->or_hits,
       w->gate_hits,w->call_sites,w->producer_entries,
       w->skip_targets,w->orphan_gates,w->branch_zero,
       w->branch_nonzero,w->branch_mismatch,w->irq_gate)<0)
        return false;
    for(unsigned i=0;i<w->count;++i) {
        const YsPc43GateEvent *e=&w->entries[i];
        if(fprintf(f,
           "{\"entry_iteration\":%lu,\"gate_iteration\":%lu,"
           "\"entry_cpu_step\":%llu,\"gate_cpu_step\":%llu,"
           "\"slot2\":%u,\"selector\":%u,"
           "\"c198_entry\":%u,\"c199_entry\":%u,"
           "\"c1b9_entry\":%u,\"c198_gate\":%u,"
           "\"a_gate\":%u,\"f_gate\":%u,\"iff2_gate\":%u,"
           "\"or_seen\":%s,\"gate_seen\":%s,"
           "\"successor_seen\":%s,\"irq_during_gate\":%s,"
           "\"successor_pc\":\"%04X\","
           "\"irq_before\":%llu,\"irq_after\":%llu}%s\n",
           e->entry_iteration,e->gate_iteration,
           (unsigned long long)e->entry_cpu_step,
           (unsigned long long)e->gate_cpu_step,
           (unsigned)e->slot2,(unsigned)e->selector,
           (unsigned)e->c198_entry,(unsigned)e->c199_entry,
           (unsigned)e->c1b9_entry,(unsigned)e->c198_gate,
           (unsigned)e->a_gate,(unsigned)e->f_gate,
           (unsigned)e->iff2_gate,
           e->or_seen?"true":"false",
           e->gate_seen?"true":"false",
           e->successor_seen?"true":"false",
           e->irq_during_gate?"true":"false",
           e->successor_pc,
           (unsigned long long)e->irq_before,
           (unsigned long long)e->irq_after,
           i+1u==w->count?"":",")<0)
            return false;
    }
    return fputs("]}\n",f)>=0 && ferror(f)==0;
}
