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
    until(0x003A,2); /* RETI starts at $003A, after EI and NOP. */
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
static void ys_source_vblank_vdp_commands_and_rst08(void) {
    setup();
    /* Source-backed bank-0 $0108-$0124 and RST $08 helper opcodes. */
    CODE(0x0108,0x21,0x1A,0xC0,0x01,0xBF,0x8B,
         0xED,0xAB,0xED,0x41,0xED,0xAB,0xED,0x41,
         0xED,0xAB,0xED,0x41,0x21,0xFF,0x85,
         0xED,0x69,0xED,0x61,0x21,0xAA,0x01,0xCF);
    CODE(0x0008,0x87,0x85,0x6F,0x30,0x01,0x24,
         0x7E,0x23,0x66,0x6F,0xE9);
    CODE(0x01AA,0xFB,0xC9,0xB4,0x01,0xBA,0x01,0xD7,0x01,0xB8,0x03);
    assert(ys_sms_bus_write(&bus,0xC01A,0x45));
    assert(ys_sms_bus_write(&bus,0xC019,0x23));
    assert(ys_sms_bus_write(&bus,0xC018,0x11));
    cpu.pc=0x0108;
    cpu.a=1; /* First VBlank dispatch selector is one-based. */
    until(0x01B4,40);
    assert(vdp.control_writes==8 && vdp.register_writes==4);
    assert(vdp.registers[10]==0x45 && vdp.registers[9]==0x23);
    assert(vdp.registers[8]==0x11 && vdp.registers[5]==0xFF);
    assert(cpu.b==0x88 && cpu.c==0xBF);
    assert(cpu.a==0xB4 && cpu.h==0x01 && cpu.l==0xB4);
    assert(cpu.sp==0xDFEE &&
           ys_sms_bus_read(&bus,0xDFEE)==0x25 &&
           ys_sms_bus_read(&bus,0xDFEF)==0x01);
}
static void test_add_a_8bit_flags(void) {
    setup();
    CODE(0x0000,0x3E,0x7F,0x87,0x06,0x01,0x80);
    until(0x0003,2); /* ADD A,A => $FE, signed overflow. */
    assert(cpu.a==0xFE && (cpu.f&Z80_F_PV) &&
           (cpu.f&Z80_F_H) && (cpu.f&Z80_F_S));
    until(0x0006,2); /* ADD A,B => $FF, no carry. */
    assert(cpu.a==0xFF && !(cpu.f&Z80_F_C));
    setup();
    CODE(0,0x3E,0x80,0x87);
    until(3,2);
    assert(cpu.a==0 && (cpu.f&Z80_F_C) &&
           (cpu.f&Z80_F_Z) && (cpu.f&Z80_F_PV));
}
static void test_ys_sprite_table_transfer_and_return(void) {
    setup();
    /* $01B4 -> $0427: 64 Y bytes and 128 X/tile bytes into SAT VRAM.
       Opcode bytes and $04BF/$053F RET boundaries follow phase16 bank 0. */
    CODE(0x01B4,0xCD,0x27,0x04,0xC3,0xE8,0x03);
    CODE(0x0427,0xAF,0xD3,0xBF,0x3E,0x7F,0xD3,0xBF,
         0x0E,0xBE,0x21,0x00,0xDD,0xCD,0xBF,0x04,
         0x3C,0xD3,0xBF,0x3D,0xD3,0xBF,0x21,0x40,0xDD);
    for (unsigned i=0;i<128;++i) {
        unsigned offset=0x043Fu+i*2u;
        rom[offset]=0xED; rom[offset+1u]=0xA3;
    }
    rom[0x053F]=0xC9;
    CODE(0x03E8,0x3A,0x2C,0xC0,0xB7,0xC8);
    assert(ys_sms_bus_write(&bus,0xDFF0,0x25));
    assert(ys_sms_bus_write(&bus,0xDFF1,0x01));
    for (unsigned i=0;i<192;++i)
        assert(ys_sms_bus_write(&bus,(uint16_t)(0xDD00u+i),
                                (uint8_t)(i*3u+7u)));
    cpu.pc=0x01B4;
    until(0x0125,240);
    assert(cpu.sp==0xDFF2 && cpu.a==0);
    assert(vdp.control_writes==4 && vdp.register_writes==0);
    assert(vdp.vram_writes==192 && vdp.address==0 && vdp.code==1);
    for (unsigned i=0;i<64;++i)
        assert(vdp.vram[0x3F00u+i]==(uint8_t)(i*3u+7u));
    for (unsigned i=0;i<128;++i)
        assert(vdp.vram[0x3F80u+i]==(uint8_t)((i+64u)*3u+7u));
}
static void test_ys_controller_sample(void) {
    setup();
    YsSmsInput input;
    ys_sms_input_reset(&input);
    ys_z80_attach_input(&cpu,&input);
    CODE(0x0773,0xDB,0xDC,0x21,0x1B,0xC0,0xF6,0xC0,
         0x2F,0x47,0xAE,0x70,0x23,0xA0,0x77,0xC9);
    assert(ys_sms_bus_write(&bus,0xC01B,0x03));
    assert(ys_sms_bus_write(&bus,0xDFF0,0x30));
    assert(ys_sms_bus_write(&bus,0xDFF1,0x01));
    cpu.pc=0x0773;
    input.dc=0xEF; /* active-low button nibble */
    until(0x0130,15);
    assert(input.reads_dc==1 && input.reads_dd==0);
    assert(ys_sms_bus_read(&bus,0xC01B)==0x10);
    assert(ys_sms_bus_read(&bus,0xC01C)==0x10);
    assert(cpu.a==0x10 && cpu.b==0x10 && cpu.sp==0xDFF2);
    setup();
    ys_sms_input_reset(&input);
    ys_z80_attach_input(&cpu,&input);
    cpu.pc=0x0773;
    CODE(0x0773,0xDB,0xDC,0x21,0x1B,0xC0,0xF6,0xC0,
         0x2F,0x47,0xAE,0x70,0x23,0xA0,0x77,0xC9);
    assert(ys_sms_bus_write(&bus,0xDFF0,0x30));
    assert(ys_sms_bus_write(&bus,0xDFF1,0x01));
    until(0x0130,15);
    assert(input.reads_dc==1 && cpu.a==0 && cpu.b==0);
    assert(ys_sms_bus_read(&bus,0xC01B)==0);
    assert(ys_sms_bus_read(&bus,0xC01C)==0);
}
static void test_conditional_return(void) {
    setup();
    CODE(0,0xC8,0x00);
    assert(ys_sms_bus_write(&bus,0xDFF0,0x34));
    assert(ys_sms_bus_write(&bus,0xDFF1,0x12));
    cpu.f=0;
    until(1,1);
    assert(cpu.sp==0xDFF0);
    cpu.pc=0; cpu.f=Z80_F_Z;
    until(0x1234,1);
    assert(cpu.sp==0xDFF2);
}
static void test_source_bank2_idle_sound_channel_scan(void) {
    setup();
    /* Exact bank-2 $8042-$8066 path, from phase11_roundtrip/bank02.asm.
       Initializer has left six FM channels inactive (bit 7 clear). */
    const uint8_t idle[]={0xDD,0x21,0xAF,0xDE,0x06,0x06,
        0xC5,0x3E,0x03,0xB8,0x28,0x10,
        0xDD,0xCB,0x00,0x7E,0xC4,0x47,0x89,
        0x11,0x20,0x00,0xDD,0x19,0xC1,0x10,0xEB,0xC9,
        0xDD,0xCB,0x00,0x7E,0xC4,0x89,0x88,0x18,0xEE};
    assert(sizeof(idle)==0x25u);
    memcpy(rom+0x8042,idle,sizeof(idle));
    assert(ys_sms_bus_write(&bus,0xFFFF,2));
    assert(ys_sms_bus_write(&bus,0xDFF0,0x38));
    assert(ys_sms_bus_write(&bus,0xDFF1,0x01));
    cpu.pc=0x8042;
    until(0x0138,90);
    assert(cpu.ix==0xDF6F && cpu.b==0 && cpu.sp==0xDFF2);
    assert(cpu.a==3 && (cpu.f&Z80_F_Z));
}
static void test_index_bit_and_conditional_call_flags(void) {
    setup();
    CODE(0,0xDD,0x21,0x00,0xC0,  /* LD IX,$C000 */
           0x11,0x20,0x00,        /* LD DE,$0020 */
           0xDD,0x19,             /* ADD IX,DE */
           0xDD,0xCB,0xFE,0x7E,   /* BIT 7,(IX-2) */
           0xC4,0x20,0x00,        /* CALL NZ,$0020 (not taken) */
           0x3E,0x80,0xCB,0x7F); /* BIT 7,A (set) */
    assert(ys_sms_bus_write(&bus,0xC01E,0));
    until(0x0009,3); /* IX arithmetic itself updates carry. */
    assert(cpu.ix==0xC020);
    cpu.f=Z80_F_C;
    until(0x000D,1); /* Indexed BIT must preserve carry. */
    assert(cpu.ix==0xC020 && (cpu.f&Z80_F_Z) &&
           (cpu.f&Z80_F_PV) && (cpu.f&Z80_F_C) &&
           (cpu.f&Z80_F_H) && !(cpu.f&Z80_F_S));
    until(0x0014,3);
    assert(cpu.a==0x80 && !(cpu.f&Z80_F_Z) &&
           !(cpu.f&Z80_F_PV) && (cpu.f&Z80_F_S));
    setup();
    CODE(0,0xDD,0xCB,0x00,0x46); /* BIT 0,(IX+0), address $C000 */
    cpu.ix=0xC000;
    assert(ys_sms_bus_write(&bus,0xC000,1));
    until(4,1);
    assert(!(cpu.f&Z80_F_Z) && (cpu.f&Z80_F_H));
    setup();
    CODE(0,0xDD,0xCB,0x00,0x06); /* unsupported indexed rotate */
    assert(ys_z80_step(&cpu)==Z80_UNSUPPORTED);
    assert(cpu.pc==0 && cpu.fault_pc==0);
}
int main(void) {
    test_source_bank2_idle_sound_channel_scan();
    test_index_bit_and_conditional_call_flags();
    test_ys_sprite_table_transfer_and_return();
    test_ys_controller_sample();
    test_conditional_return();
    ys_source_vblank_vdp_commands_and_rst08();
    test_add_a_8bit_flags();
    shadow_and_index_registers();
    conditional_jp_sign();
    ei_delay_and_im1_irq();
    ys_real_source_vblank_wait_and_interrupt_entry();
    unknown_index_opcode_still_fails();
    puts("PASS: alternate registers, IX/IY stack, EI delay, IM1 and Ys VBlank entry");
}
