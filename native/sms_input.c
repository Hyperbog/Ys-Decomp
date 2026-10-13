#include "sms_input.h"
#include <string.h>

void ys_sms_input_reset(YsSmsInput *input) {
    if (!input) return;
    memset(input,0,sizeof(*input));
    input->dc=0xFFu; /* Unpressed controller buttons are active-low high. */
    input->dd=0xFFu;
}
bool ys_sms_input_read(YsSmsInput *input, uint8_t port, uint8_t *value) {
    if (!input || !value) return false;
    if (port==0xDCu) {
        *value=input->dc;
        ++input->reads_dc;
        return true;
    }
    if (port==0xDDu) {
        *value=input->dd;
        ++input->reads_dd;
        return true;
    }
    return false;
}
