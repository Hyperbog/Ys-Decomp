#ifndef YS_SMS_RUNTIME_H
#define YS_SMS_RUNTIME_H
#include "sms_clock.h"
#include "z80.h"

typedef struct {
    YsSmsClock clock;
    YsZ80 *cpu; /* Borrowed, caller-owned CPU with attached VDP. */
    uint64_t recognized_irqs;
} YsSmsRuntime;

/* Does not reset CPU or VDP. Caller supplies already-reset devices. */
bool ys_sms_runtime_bind(YsSmsRuntime *rt, YsZ80 *cpu, YsSmsRegion region);

/* Advance externally supplied CPU T-states and automatically deliver any
   enabled VBlank IM1 interrupt recognized at this instruction boundary.
   A pending VBlank remains latched if IFF1/EI delay blocks recognition. */
bool ys_sms_runtime_advance(YsSmsRuntime *rt, uint32_t tstates,
                            bool *irq_delivered);

/* Execute one bounded CPU instruction, then advance its caller-supplied
   T-state duration. This is NOT an instruction-timing decoder. */
Z80Status ys_sms_runtime_step(YsSmsRuntime *rt, uint32_t instruction_tstates);
#endif
