#ifndef YS_SMS_CLOCK_H
#define YS_SMS_CLOCK_H
#include "sms_vdp.h"
#include <stdbool.h>
#include <stdint.h>

enum {
    YS_SMS_TSTATES_PER_LINE = 228,
    YS_SMS_VISIBLE_LINES = 192,
    YS_SMS_NTSC_LINES = 262,
    YS_SMS_PAL_LINES = 313
};
typedef enum { YS_SMS_NTSC = 0, YS_SMS_PAL = 1 } YsSmsRegion;

typedef struct {
    YsSmsRegion region;
    uint16_t line, tstates;
    uint64_t frames, vblank_events;
} YsSmsClock;

/* Standalone VDP scanline clock. The caller must supply CPU T-states:
   z80.c does not yet account T-states automatically. */
bool ys_sms_clock_reset(YsSmsClock *clock, YsSmsRegion region);
bool ys_sms_clock_advance(YsSmsClock *clock, YsSmsVdp *vdp, uint32_t tstates);

/* VBlank status remains asserted until the game reads the status port.
   Enabled frame IRQs can be serviced via ys_z80_irq once EI is recognized. */
bool ys_sms_clock_vblank_irq(const YsSmsClock *clock, const YsSmsVdp *vdp);
uint32_t ys_sms_clock_tstates_per_frame(const YsSmsClock *clock);
#endif
