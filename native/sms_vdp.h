#ifndef YS_SMS_VDP_H
#define YS_SMS_VDP_H
#include <stdbool.h>
#include <stdint.h>

enum { YS_VRAM_BYTES = 0x4000, YS_CRAM_BYTES = 32, YS_VDP_REGISTERS = 16 };
typedef struct {
    uint8_t vram[YS_VRAM_BYTES], cram[YS_CRAM_BYTES], registers[YS_VDP_REGISTERS];
    uint8_t status, read_buffer, code, control_first;
    uint16_t address;
    bool control_pending;
    uint64_t register_writes, vram_writes, cram_writes, control_writes;
} YsSmsVdp;

/* No clock, renderer, sprite evaluation or frame/line interrupt generator yet. */
void ys_sms_vdp_reset(YsSmsVdp *vdp);
/* Only mirrored VDP I/O range $80-$BF is accepted. */
bool ys_sms_vdp_write(YsSmsVdp *vdp, uint8_t port, uint8_t value);
bool ys_sms_vdp_read(YsSmsVdp *vdp, uint8_t port, uint8_t *value);
#endif
