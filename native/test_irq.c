#include "z80.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static uint8_t rom[YS_ROM_BYTES];
static YsSmsBus bus;
static YsZ80 cpu;
static YsSmsVdp vdp;
static void setup(void) {
    memset(rom,0,sizeof(rom));
    assert(ys_sms_bus_init(&bus,rom,sizeof(rom)));
    ys_z80_reset(&cpu,&bus);
    ys_sms_vdp_reset(&vdp);
    ys_z80_attach_vdp(&cpu,&vdp);
    cpu.sp=0xDFF0;
}
static void place(uint16_t address, const uint8_t *program, size_t size) {
    assert(address<0x4000u && size<=0x4000u-address);
    memcpy(rom+address,program,size);
}
#define CODE(address,...) do { const uint8_t data[]={__VA_ARGS__};place(address,data,sizeof(data)); } while(0)
static void until(uint16_t pc, uint64_t budget) {
    assert(ys_z80_run_until(&cpu,pc,budget)==Z80_RUNNING);
    assert(cpu.pc==pc);
}
static void shadow_and_index_registers(void) {
    setup();
    cpu.a=0x12;cpu.f=0x41;cpu.b=0x23;cpu.c=0x34;
    cpu.d=0x45;cpu.e=0x56;cpu.h=0x67;cpu.l=0x78;
    cpu.a_alt=0x9A;cpu.f_alt=0x81;cpu.b_alt=0xAB;cpu.c_alt=0xBC;
    cpu.d_alt=0xCD;cpu.e_alt=0xDE;cpu.h_alt=0xEF;cpu.l_alt=0xF0;
    cpu.ix=0x1234;cpu.iy=0x5678;
    CODE(0x0000,0x08,0xD9,0xDD,0xE5,0xFD,0xE5, /* exchange, IX/IY push */
         0x21,0x00,0x00,0xDD,0xE1,0xFD,0xE1,0xD9,0x08);
    until(0x0006,4);
    assert(cpu.a==0x9A && cpu.f==0x81);
    assert(cpu.b==0xAB && cpu.c==0xBC);
    assert(cpu.h==0xEF && cpu.l==0xF0);
    assert(cpu.a_alt==0x12 && cpu.b_alt==0x23);
    assert(cpu.sp==0xDFEC);
    assert(ys_sms_bus_read(&bus,0xDFEC)==0x78 &&
           ys_sms_bus_read(&bus,0xDFED)==0x56);
    until(0x000F,5);
    assert(cpu.sp==0xDFF0);
    assert(cpu.a==0x12 && cpu.f==0x41);
    assert(cpu.b==0x23 && cpu.c==0x34);
    assert(cpu.h==0x67 && cpu.l==0x78);
    assert(cpu.ix==0x5678 && cpu.iy==0x1234);
}
static void conditional_jp_sign(void) {
    setup();
    CODE(0x0000,0xF2,0x20,0x00,0xFA,0x10,0x00);
    cpu.f=Z80_F_S;
    until(0x0010,2);
    setup();
    CODE(0x0000,0xF2,0x20,0x00,0xFA,0x10,0x00);
    cpu.f=0;
    until(0x0020,2);
}
static void ei_delay_and_im1_irq(void) {
    setup();
    cpu.interrupt_mode=1;
    CODE(0x0000,0xF3,0xFB,0x00,0x00);
    CODE(0x0038,0xFB,0x00,0xED,0x4D); /* EI; NOP; RETI */
    assert(!ys_z80_irq(&cpu));
    until(0x0002,2);
    assert(cpu.iff1 && cpu.ei_delay==1 && !ys_z80_irq(&cpu));
    until(0x0003,1);
    assert(cpu.ei_delay==0 && ys_z80_irq(&cpu));
    assert(cpu.pc==0x0038 && cpu.sp==0xDFEE &&
           ys_sms_bus_read(&bus,0xDFEE)==0x03);
    assert(!cpu.iff1 && cpu.iff2);
    until(0x003B,2);
    assert(cpu.iff1 && cpu.ei_delay==0);
    until(0x0003,1);
    assert(cpu.sp==0xDFF0);
}
static void ys_real_source_vblank_wait_and_interrupt_entry(void) {
    setup();
    /* Exact bank-0 opcode path of $0BC5-$0BD9 and $0042-$004C,
       reconstructed from phase16/bank00_symbolic.asm. */
    CODE(0x0BC5,0xF5,0xC5,0xD5,0xE5,0x08,0xD9,0xF5,0xC5,0xD5,0xE5,
         0xDD,0xE5,0xFD,0xE5,0x3A,0xFF,0xFF,0xF5,0x3E,0x01,
         0xCD,0x42,0x00);
    CODE(0x0042,0x32,0x21,0xC0,0xFB,0x3A,0x21,0xC0,0xB7,
         0x20,0xFA,0xC9);
    CODE(0x0038,0xF5,0xDB,0xBF,0xB7,0xF2,0x40,0x05,
         0xC3,0x02,0x01);
    assert(ys_sms_bus_write(&bus,0xFFFF,2));
    cpu.pc=0x0BC5;
    cpu.interrupt_mode=1;
    cpu.a=0x77;cpu.f=Z80_F_S;cpu.b=0x32;
    cpu.a_alt=0x44;cpu.f_alt=Z80_F_Z;cpu.b_alt=0x12;
    cpu.ix=0xAABB;cpu.iy=0xCCDD;
    until(0x0046,32);
    assert(cpu.sp==0xDFD8 && cpu.ei_delay==1);
    assert(ys_sms_bus_read(&bus,0xC021)==1);
    assert(!ys_z80_irq(&cpu)); /* EI recognition is delayed. */
    until(0x0049,1);          /* LD A,($C021) retires. */
    assert(ys_z80_irq(&cpu));
    assert(cpu.pc==0x0038 && cpu.sp==0xDFD6);
    assert(ys_sms_bus_read(&bus,0xDFD6)==0x49);
    vdp.status=0x80;          /* Explicit event; no video clock yet. */
    until(0x0102,5);
    assert(cpu.sp==0xDFD4 && cpu.a==0x80 && vdp.status==0);
    assert(!cpu.iff1);
}
static void unknown_index_opcode_still_fails(void) {
    setup();
    CODE(0,0xDD,0x00);
    assert(ys_z80_step(&cpu)==Z80_UNSUPPORTED);
    assert(cpu.pc==0 && cpu.fault_pc==0 && cpu.steps==0);
    setup();
    assert(!ys_z80_irq(&cpu));
}
int main(void) {
    shadow_and_index_registers();
    conditional_jp_sign();
    ei_delay_and_im1_irq();
    ys_real_source_vblank_wait_and_interrupt_entry();
    unknown_index_opcode_still_fails();
    puts("PASS: alternate registers, IX/IY stack, EI delay, IM1 and Ys VBlank entry");
}
