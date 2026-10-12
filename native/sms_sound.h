#ifndef YS_SMS_SOUND_H
#define YS_SMS_SOUND_H
#include <stdbool.h>
#include <stdint.h>

enum { YS_SMS_PSG_TRACE_CAP = 32, YS_SMS_FM_REGISTERS = 64 };
typedef struct {
    uint64_t psg_write_count, fm_address_count, fm_data_count;
    uint8_t psg_prefix[YS_SMS_PSG_TRACE_CAP];
    uint8_t fm_selected;
    uint8_t fm_registers[YS_SMS_FM_REGISTERS];
    bool fm_touched[YS_SMS_FM_REGISTERS];
} YsSmsSound;

/* Observable audio I/O write ledger only: no tone rendering, delays or playback. */
void ys_sms_sound_reset(YsSmsSound *sound);
/* PSG data $7F and YM2413 register/data $F0/$F1; unsupported ports fail. */
bool ys_sms_sound_write(YsSmsSound *sound, uint8_t port, uint8_t value);
#endif
