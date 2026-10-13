#ifndef YS_SMS_INPUT_H
#define YS_SMS_INPUT_H
#include <stdbool.h>
#include <stdint.h>

/* Two Sega Master System controller I/O port snapshots, active-low.
   No input-event polling or console I/O control-port emulation yet. */
typedef struct {
    uint8_t dc;
    uint8_t dd;
    uint64_t reads_dc, reads_dd;
} YsSmsInput;

void ys_sms_input_reset(YsSmsInput *input);
bool ys_sms_input_read(YsSmsInput *input, uint8_t port, uint8_t *value);
#endif
