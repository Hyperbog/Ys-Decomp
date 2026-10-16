#ifndef YS_PC_SAT_STROBES_H
#define YS_PC_SAT_STROBES_H
#include "sms_runtime.h"
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

/* PC-39 only observes *successful* CPU bus write strobes to physical
   console WRAM $1D00-$1DBF (visible at $DD00/$FD00).
   This includes same-value stores absent from PC-38's diff audit. */
enum { YS_PC39_BYTES=192,YS_PC39_MAX_SITES=512,YS_PC39_PHASES=2 };
typedef struct {
    uint16_t pc;
    uint8_t bank,phase,irq;
    uint64_t count,same,first_step,last_step;
} YsPcSatStrobeSite;
typedef struct {
    YsZ80 *cpu; /* Borrowed; the callback never modifies CPU or bus. */
    unsigned phase,site_count,unique[YS_PC39_PHASES];
    uint8_t touched[YS_PC39_PHASES][YS_PC39_BYTES];
    uint64_t count[YS_PC39_PHASES],same[YS_PC39_PHASES],
             changed[YS_PC39_PHASES],alias[YS_PC39_PHASES],
             irq[YS_PC39_PHASES],y[YS_PC39_PHASES],
             xt[YS_PC39_PHASES];
    YsPcSatStrobeSite sites[YS_PC39_MAX_SITES];
    bool overflow;
} YsPcSatStrobeAudit;

/* Safe to install on an initialized bus via ys_sms_bus_set_wram_hook.
   Only writer site/counters change; CPU execution is not intercepted. */
void ys_pc_sat_strobes_hook(void *context,uint16_t logical,
                             uint16_t physical,uint8_t before,uint8_t after);
bool ys_pc_sat_strobes_set_phase(YsPcSatStrobeAudit *audit,unsigned phase);
bool ys_pc_sat_strobes_write(FILE *file,const YsPcSatStrobeAudit *audit,
                              const YsSmsRuntime *runtime,
                              const char *reason,unsigned long continued_steps);
#endif
