#include "sms_clock.h"
#include <string.h>

static uint16_t total_lines(YsSmsRegion region) {
    return region == YS_SMS_PAL ? YS_SMS_PAL_LINES : YS_SMS_NTSC_LINES;
}
bool ys_sms_clock_reset(YsSmsClock *clock, YsSmsRegion region) {
    if (!clock || (region != YS_SMS_NTSC && region != YS_SMS_PAL))
        return false;
    memset(clock, 0, sizeof(*clock));
    clock->region = region;
    return true;
}
bool ys_sms_clock_advance(YsSmsClock *clock, YsSmsVdp *vdp, uint32_t tstates) {
    if (!clock || !vdp || clock->region > YS_SMS_PAL ||
        clock->line >= total_lines(clock->region) ||
        clock->tstates >= YS_SMS_TSTATES_PER_LINE)
        return false;
    while (tstates) {
        unsigned remaining = YS_SMS_TSTATES_PER_LINE - clock->tstates;
        unsigned slice = tstates < remaining ? tstates : remaining;
        clock->tstates = (uint16_t)(clock->tstates + slice);
        tstates -= slice;
        if (clock->tstates == YS_SMS_TSTATES_PER_LINE) {
            clock->tstates = 0;
            ++clock->line;
            if (clock->line == YS_SMS_VISIBLE_LINES) {
                vdp->status |= 0x80u; /* Latched until status port read. */
                ++clock->vblank_events;
            }
            if (clock->line == total_lines(clock->region)) {
                clock->line = 0;
                ++clock->frames;
            }
        }
    }
    return true;
}
bool ys_sms_clock_vblank_irq(const YsSmsClock *clock, const YsSmsVdp *vdp) {
    return clock && vdp && clock->region <= YS_SMS_PAL &&
        (vdp->status & 0x80u) != 0 && (vdp->registers[1] & 0x20u) != 0;
}
uint32_t ys_sms_clock_tstates_per_frame(const YsSmsClock *clock) {
    if (!clock || clock->region > YS_SMS_PAL) return 0;
    return (uint32_t)total_lines(clock->region) * YS_SMS_TSTATES_PER_LINE;
}
