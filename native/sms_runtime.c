#include "sms_runtime.h"
#include <string.h>

bool ys_sms_runtime_bind(YsSmsRuntime *rt, YsZ80 *cpu, YsSmsRegion region) {
    if(!rt || !cpu || !cpu->vdp || !cpu->bus) return false;
    memset(rt,0,sizeof(*rt));
    if(!ys_sms_clock_reset(&rt->clock,region)) return false;
    rt->cpu=cpu;
    return true;
}
bool ys_sms_runtime_advance(YsSmsRuntime *rt, uint32_t tstates,
                            bool *irq_delivered) {
    if(irq_delivered) *irq_delivered=false;
    if(!rt || !rt->cpu || !rt->cpu->vdp ||
       !ys_sms_clock_advance(&rt->clock,rt->cpu->vdp,tstates))
        return false;
    if(ys_sms_clock_vblank_irq(&rt->clock,rt->cpu->vdp) &&
       ys_z80_irq(rt->cpu)) {
        /* IM 1 maskable interrupt acknowledgment consumes 13 T-states.
           The stack push/vector happens in ys_z80_irq. */
        if(!ys_sms_clock_advance(&rt->clock,rt->cpu->vdp,13u))
            return false;
        rt->cpu->total_tstates+=13u;
        ++rt->recognized_irqs;
        if(irq_delivered) *irq_delivered=true;
    }
    return true;
}
Z80Status ys_sms_runtime_step(YsSmsRuntime *rt, uint32_t instruction_tstates) {
    if(!rt || !rt->cpu || instruction_tstates==0)
        return Z80_UNSUPPORTED;
    Z80Status status=ys_z80_step(rt->cpu);
    if(status!=Z80_RUNNING) return status;
    if(!ys_sms_runtime_advance(rt,instruction_tstates,NULL))
        return Z80_UNSUPPORTED;
    return rt->cpu->status;
}

Z80Status ys_sms_runtime_step_auto(YsSmsRuntime *rt) {
    if(!rt || !rt->cpu || !rt->cpu->bus || !rt->cpu->vdp)
        return Z80_UNSUPPORTED;
    YsZ80 *cpu=rt->cpu;
    if(cpu->status==Z80_HALTED) {
        /* HALT refresh cycles proceed until a maskable interrupt is accepted.
           The PC already points one byte beyond HALT. */
        /* HALT M1 happens BEFORE the clock advance may accept an IM1
           interrupt. Counting afterward would lose the refresh if
           the IRQ changes status from HALTED to RUNNING. */
        ys_z80_refresh_halt(cpu);
        if(!ys_sms_runtime_advance(rt,4u,NULL)) return Z80_UNSUPPORTED;
        cpu->total_tstates+=4u;
        cpu->last_tstates=4u;
        return cpu->status;
    }
    if(cpu->status!=Z80_RUNNING) return cpu->status;
    Z80Status result=ys_z80_step(cpu);
    if(result!=Z80_RUNNING && result!=Z80_HALTED) return result;
    if(cpu->last_tstates==0u) {
        cpu->status=Z80_UNSUPPORTED;
        cpu->fault_pc=(uint16_t)(cpu->pc-1u);
        return cpu->status;
    }
    if(!ys_sms_runtime_advance(rt,cpu->last_tstates,NULL))
        return Z80_UNSUPPORTED;
    return cpu->status;
}
