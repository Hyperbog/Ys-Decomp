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
