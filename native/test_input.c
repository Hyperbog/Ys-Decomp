#include "sms_input.h"
#include <assert.h>
#include <stdio.h>

int main(void) {
    YsSmsInput input;
    uint8_t value=0;
    ys_sms_input_reset(&input);
    assert(ys_sms_input_read(&input,0xDC,&value) && value==0xFF);
    assert(ys_sms_input_read(&input,0xDD,&value) && value==0xFF);
    assert(input.reads_dc==1 && input.reads_dd==1);
    input.dc=0xEF; input.dd=0xDF;
    assert(ys_sms_input_read(&input,0xDC,&value) && value==0xEF);
    assert(ys_sms_input_read(&input,0xDD,&value) && value==0xDF);
    assert(!ys_sms_input_read(&input,0xBF,&value));
    assert(!ys_sms_input_read(NULL,0xDC,&value));
    assert(!ys_sms_input_read(&input,0xDC,NULL));
    assert(input.reads_dc==2 && input.reads_dd==2);
    puts("PASS: idle-high DC/DD controller snapshots and bounded reads");
    return 0;
}
