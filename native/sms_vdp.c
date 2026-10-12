#include "sms_vdp.h"
#include <string.h>

void ys_sms_vdp_reset(YsSmsVdp *vdp) {
    if (vdp) memset(vdp, 0, sizeof(*vdp));
}
bool ys_sms_vdp_write(YsSmsVdp *vdp, uint8_t port, uint8_t value) {
    if (!vdp || port < 0x80u || port > 0xBFu) return false;
    if (port & 1u) {
        ++vdp->control_writes;
        if (!vdp->control_pending) {
            vdp->control_first = value;
            vdp->control_pending = true;
            return true;
        }
        vdp->control_pending = false;
        vdp->address = (uint16_t)(((uint16_t)(value & 0x3Fu) << 8) |
                                  vdp->control_first);
        vdp->code = (uint8_t)(value >> 6);
        if (vdp->code == 0u) { /* VRAM prefetch on read command. */
            vdp->read_buffer = vdp->vram[vdp->address];
            vdp->address = (uint16_t)((vdp->address + 1u) & 0x3FFFu);
        } else if (vdp->code == 2u) {
            vdp->registers[value & 0x0Fu] = vdp->control_first;
            ++vdp->register_writes;
        }
        return true;
    }
    /* Any data access cancels an incomplete two-byte control command. */
    vdp->control_pending = false;
    if (vdp->code == 3u) {
        vdp->cram[vdp->address & 0x1Fu] = value;
        ++vdp->cram_writes;
    } else {
        vdp->vram[vdp->address & 0x3FFFu] = value;
        ++vdp->vram_writes;
    }
    vdp->read_buffer = value;
    vdp->address = (uint16_t)((vdp->address + 1u) & 0x3FFFu);
    return true;
}
bool ys_sms_vdp_read(YsSmsVdp *vdp, uint8_t port, uint8_t *value) {
    if (!vdp || !value || port < 0x80u || port > 0xBFu) return false;
    vdp->control_pending = false;
    if (port & 1u) {
        *value = vdp->status;
        vdp->status = 0; /* Read-to-clear frame/sprite status; timing deferred. */
    } else {
        *value = vdp->read_buffer;
        vdp->read_buffer = vdp->vram[vdp->address & 0x3FFFu];
        vdp->address = (uint16_t)((vdp->address + 1u) & 0x3FFFu);
    }
    return true;
}
