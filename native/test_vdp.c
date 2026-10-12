#include "sms_vdp.h"
#include <assert.h>
#include <stdio.h>

static YsSmsVdp v;
static void command(uint8_t lo, uint8_t hi) {
    assert(ys_sms_vdp_write(&v,0xBF,lo));
    assert(ys_sms_vdp_write(&v,0xBF,hi));
}
static void test_vram_and_prefetch(void) {
    ys_sms_vdp_reset(&v);
    command(0xFF,0x7F);
    assert(v.code==1 && v.address==0x3FFF);
    assert(ys_sms_vdp_write(&v,0xBE,0x77));
    assert(ys_sms_vdp_write(&v,0xBE,0x88));
    assert(v.vram[0x3FFF]==0x77 && v.vram[0]==0x88);
    assert(v.address==1 && v.vram_writes==2);
    command(0,0); /* VRAM read command prefetches address 0. */
    assert(v.address==1 && v.read_buffer==0x88);
    uint8_t value=0;
    assert(ys_sms_vdp_read(&v,0xBE,&value) && value==0x88);
    assert(v.address==2);
    assert(v.read_buffer==0);
}
static void test_registers_and_palette(void) {
    ys_sms_vdp_reset(&v);
    command(0x97,0x8A);
    assert(v.registers[10]==0x97 && v.register_writes==1);
    assert(v.vram_writes==0);
    command(0x1F,0xC0);
    assert(v.code==3 && v.address==31);
    assert(ys_sms_vdp_write(&v,0xBE,0x3F));
    assert(ys_sms_vdp_write(&v,0xBE,0x15));
    assert(v.cram[31]==0x3F && v.cram[0]==0x15);
    assert(v.cram_writes==2 && v.address==33);
}
static void test_latch_and_status(void) {
    ys_sms_vdp_reset(&v);
    assert(!ys_sms_vdp_write(&v,0x7F,0xAA));
    assert(ys_sms_vdp_write(&v,0x80,0x44)); /* Mirrored data port. */
    assert(v.vram[0]==0x44);
    assert(ys_sms_vdp_write(&v,0x81,0x12)); /* Mirrored control port. */
    assert(v.control_pending);
    v.status=0xA0;
    uint8_t value=0;
    assert(ys_sms_vdp_read(&v,0xBF,&value));
    assert(value==0xA0 && v.status==0 && !v.control_pending);
    assert(ys_sms_vdp_write(&v,0xBF,0x99));
    assert(ys_sms_vdp_write(&v,0xBE,0x22)); /* Data write cancels command. */
    assert(!v.control_pending);
    assert(ys_sms_vdp_write(&v,0xBF,0x66));
    assert(v.control_pending); /* New first byte, not second. */
    assert(!ys_sms_vdp_read(&v,0x7F,&value));
}
int main(void) {
    test_vram_and_prefetch();
    test_registers_and_palette();
    test_latch_and_status();
    puts("PASS: SMS VDP command latch, registers, VRAM, CRAM, read buffer and status");
    return 0;
}
