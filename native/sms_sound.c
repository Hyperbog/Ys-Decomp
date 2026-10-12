#include "sms_sound.h"
#include <string.h>

void ys_sms_sound_reset(YsSmsSound *sound) {
    if (sound) memset(sound,0,sizeof(*sound));
}
bool ys_sms_sound_write(YsSmsSound *sound, uint8_t port, uint8_t value) {
    if (!sound) return false;
    switch (port) {
    case 0x7F:
        if (sound->psg_write_count < YS_SMS_PSG_TRACE_CAP)
            sound->psg_prefix[sound->psg_write_count] = value;
        ++sound->psg_write_count;
        return true;
    case 0xF0:
        sound->fm_selected=value;
        ++sound->fm_address_count;
        return true;
    case 0xF1:
        if (sound->fm_selected >= YS_SMS_FM_REGISTERS) return false;
        sound->fm_registers[sound->fm_selected]=value;
        sound->fm_touched[sound->fm_selected]=true;
        ++sound->fm_data_count;
        return true;
    default: return false;
    }
}
