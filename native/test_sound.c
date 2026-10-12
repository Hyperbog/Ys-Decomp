#include "sms_sound.h"
#include <assert.h>
#include <stdio.h>

int main(void) {
    YsSmsSound sound;
    ys_sms_sound_reset(&sound);
    assert(!ys_sms_sound_write(&sound,0xBE,0x23));
    assert(!ys_sms_sound_write(&sound,0xF1,0xCC) || sound.fm_data_count==1);
    ys_sms_sound_reset(&sound);
    for (unsigned i=0;i<40;++i)
        assert(ys_sms_sound_write(&sound,0x7F,(uint8_t)i));
    assert(sound.psg_write_count==40 && sound.psg_prefix[0]==0 &&
           sound.psg_prefix[31]==31);
    assert(ys_sms_sound_write(&sound,0xF0,0x20));
    assert(ys_sms_sound_write(&sound,0xF1,0xA5));
    assert(ys_sms_sound_write(&sound,0xF0,0x25));
    assert(ys_sms_sound_write(&sound,0xF1,0x00));
    assert(sound.fm_address_count==2 && sound.fm_data_count==2);
    assert(sound.fm_touched[0x20] && sound.fm_registers[0x20]==0xA5);
    assert(sound.fm_touched[0x25] && sound.fm_registers[0x25]==0);
    assert(ys_sms_sound_write(&sound,0xF0,0xFF));
    assert(!ys_sms_sound_write(&sound,0xF1,0));
    assert(sound.fm_data_count==2);
    puts("PASS: bounded PSG writes, FM register writes and unknown-port rejection");
    return 0;
}
