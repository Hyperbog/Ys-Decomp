#ifndef YS_Z80_H
#define YS_Z80_H
#include "sms_bus.h"
#include "sms_vdp.h"
#include "sms_sound.h"
#include "sms_input.h"
#include <stdint.h>
#include <stdbool.h>

enum { Z80_F_C = 0x01, Z80_F_N = 0x02, Z80_F_PV = 0x04,
       Z80_F_3 = 0x08, Z80_F_H = 0x10, Z80_F_5 = 0x20,
       Z80_F_Z = 0x40, Z80_F_S = 0x80 };
typedef enum {
    Z80_RUNNING, Z80_HALTED, Z80_UNSUPPORTED, Z80_BAD_WRITE,
    Z80_UNSUPPORTED_PORT, Z80_STEP_LIMIT
} Z80Status;
typedef struct {
    YsSmsBus *bus;
    YsSmsVdp *vdp; /* Optional $80-$BF VDP device; ports fail closed if detached. */
    YsSmsSound *sound; /* Optional observable PSG/FM write sink. */
    YsSmsInput *input; /* Optional active-low controller read snapshots. */
    uint16_t pc, sp, fault_pc, ix, iy;
    uint8_t a, f, b, c, d, e, h, l, interrupt_mode;
    uint8_t a_alt, f_alt, b_alt, c_alt, d_alt, e_alt, h_alt, l_alt;
    uint8_t ei_delay; /* Interrupt recognition blocked until after following instruction. */
    bool iff1, iff2;
    uint64_t steps, total_tstates;
    uint8_t last_tstates; /* 0 means unavailable, including failed steps. */
    Z80Status status;
} YsZ80;
void ys_z80_reset(YsZ80 *cpu, YsSmsBus *bus);
void ys_z80_attach_vdp(YsZ80 *cpu, YsSmsVdp *vdp);
void ys_z80_attach_sound(YsZ80 *cpu, YsSmsSound *sound);
void ys_z80_attach_input(YsZ80 *cpu, YsSmsInput *input);
/* Successful steps record documented instruction T-states (no bus waits). */
Z80Status ys_z80_step(YsZ80 *cpu);
/* External caller provides the VBlank/IRQ event; no timing is synthesized. */
bool ys_z80_irq(YsZ80 *cpu);
/* Stops after reaching stop_pc (before executing it); reports budget exhaustion. */
Z80Status ys_z80_run_until(YsZ80 *cpu, uint16_t stop_pc, uint64_t budget);
const char *ys_z80_status_name(Z80Status status);
#endif
