#include "z80.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static uint8_t rom[YS_ROM_BYTES];
static YsSmsBus bus;
static YsZ80 cpu;
static void setup(void) {
    memset(rom,0,sizeof(rom));
    assert(ys_sms_bus_init(&bus,rom,sizeof(rom)));
    ys_z80_reset(&cpu,&bus);
}
static void program(uint16_t address, const uint8_t *bytes, size_t count) {
    assert(address < 0x4000 && count <= 0x4000u - address);
    memcpy(rom+address,bytes,count);
}
#define LOAD(at, ...) do { const uint8_t x[]={__VA_ARGS__};program(at,x,sizeof(x)); } while(0)
static void run(uint16_t pc, uint64_t budget) {
    assert(ys_z80_run_until(&cpu,pc,budget)==Z80_RUNNING);
    assert(cpu.pc==pc);
}
static void boot_prefix_source_fixture(void) {
    setup();
    /* Exact opcode ranges from Ys/src/bank00_boot.lst, not arbitrary stand-ins. */
    LOAD(0,0xF3,0xED,0x56,0xC3,0x89,0x00);
    LOAD(0x89,
         0x31,0xF0,0xDF,0x21,0xFC,0xFF,0x36,0x80,0x23,
         0x36,0x00,0x23,0x36,0x01,0x23,0x36,0x02,0xAF,
         0x32,0x60,0xDE,0x3D,0x32,0x01,0xC0,0xCD,0x9A,0x07);
    run(0x079A, 64);
    assert(cpu.steps==17);
    assert(cpu.interrupt_mode==1 && !cpu.iff1 && !cpu.iff2);
    assert(cpu.a==0xFF && cpu.sp==0xDFEE);
    assert(cpu.h==0xFF && cpu.l==0xFF);
    assert(bus.mapper_control==0x80);
    assert(bus.mapped_bank[0]==0 && bus.mapped_bank[1]==1 && bus.mapped_bank[2]==2);
    assert(ys_sms_bus_read(&bus,0xC001)==0xFF);
    assert(ys_sms_bus_read(&bus,0xDE60)==0);
    assert(ys_sms_bus_read(&bus,cpu.sp)==0xA5 && ys_sms_bus_read(&bus,cpu.sp+1)==0);
}
static void test_control_and_stack(void) {
    setup();
    LOAD(0,0x31,0x00,0xD0,   /* LD SP,D000 */
           0xCD,0x10,0x00,   /* CALL 0010 */
           0x76);           /* HALT */
    LOAD(0x10,0x3E,0x05,0xF5,0x3E,0x00,0xF1,0xC9); /* save AF */
    run(0x0006, 16);
    assert(cpu.a==5 && cpu.sp==0xD000);
    assert(ys_sms_bus_read(&bus,0xCFFE)==6);
    assert(ys_z80_step(&cpu)==Z80_HALTED);
    assert(ys_z80_step(&cpu)==Z80_HALTED);
}
static void test_flags_and_relative_jumps(void) {
    setup();
    LOAD(0,0x3E,0x7F,0x3C,     /* INC A = 80, overflow */
           0x3D,               /* DEC A = 7F, overflow */
           0xFE,0x7F,          /* CP 7F, Z */
           0x28,0x02,          /* JR Z,+2 */
           0x3E,0xEE,          /* skipped */
           0xAF,               /* XOR A */
           0x20,0x02,          /* JR NZ,+2 (not taken) */
           0x3E,0x03,          /* LD A,03 */
           0x18,0xFE);         /* JR -2 forever */
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    ys_z80_step(&cpu); assert(cpu.a==0x80 && (cpu.f & Z80_F_PV));
    ys_z80_step(&cpu); assert(cpu.a==0x7F && (cpu.f & Z80_F_PV));
    run(0x000A,2);
    assert(cpu.a==0x7F && (cpu.f & Z80_F_Z));
    run(0x000F,3);
    assert(cpu.a==3 && (cpu.f & Z80_F_Z));
    assert(ys_z80_run_until(&cpu,0x1111,8)==Z80_STEP_LIMIT);
    assert(cpu.pc==0x000F);
}
static void test_ldir_and_mapper(void) {
    setup();
    LOAD(0,0x21,0x00,0xC0,     /* HL=C000 */
           0x11,0x10,0xC0,     /* DE=C010 */
           0x01,0x03,0x00,     /* BC=3 */
           0xED,0xB0,          /* LDIR: three iterations */
           0x3E,0x07,0x32,0xFF,0xFF); /* map bank 7 to slot 2 */
    assert(ys_sms_bus_write(&bus,0xC000,0x11));
    assert(ys_sms_bus_write(&bus,0xC001,0x22));
    assert(ys_sms_bus_write(&bus,0xC002,0x33));
    run(0x0010, 20);
    for(unsigned i=0;i<3;++i)
        assert(ys_sms_bus_read(&bus,(uint16_t)(0xC010+i))==(i==0?0x11:i==1?0x22:0x33));
    assert(bus.mapped_bank[2]==7);
    assert(cpu.b==0 && cpu.c==0);
    assert(cpu.steps==8);
}
static void test_fail_closed(void) {
    setup(); LOAD(0,0xCB,0x00); /* CB prefix not supported in this bounded core. */
    assert(ys_z80_step(&cpu)==Z80_UNSUPPORTED);
    assert(cpu.pc==0 && cpu.fault_pc==0 && cpu.steps==0);
    setup(); LOAD(0,0x21,0x00,0x80,0x36,0x77);
    run(3,1);
    assert(ys_z80_step(&cpu)==Z80_BAD_WRITE && cpu.fault_pc==3);
    setup(); LOAD(0,0xD3,0xBE);
    assert(ys_z80_step(&cpu)==Z80_UNSUPPORTED_PORT && cpu.pc==0);
    setup(); LOAD(0,0xED,0x00);
    assert(ys_z80_step(&cpu)==Z80_UNSUPPORTED && cpu.pc==0);
}
static void test_extended_startup_instructions(void) {
    setup();
    LOAD(0,0x06,0x03,        /* LD B,03 */
           0x10,0xFE,        /* DJNZ $0002 (three passes) */
           0x3E,0x10,        /* LD A,10 */
           0xF6,0x07,        /* OR 07 */
           0xE6,0x0F,        /* AND 0F */
           0x21,0x00,0xC0,   /* LD HL,C000 */
           0xBE,             /* CP (HL) */
           0x20,0x02,        /* JR NZ, HALT */
           0x3E,0xAA,        /* skipped */
           0x76);
    assert(ys_sms_bus_write(&bus,0xC000,6));
    run(18,24);
    assert(cpu.b==0 && cpu.a==7 && !(cpu.f & Z80_F_Z));
    assert(ys_z80_step(&cpu)==Z80_HALTED);
}
static void test_vdp_cpu_ports_and_rst(void) {
    setup();
    YsSmsVdp vdp;
    ys_sms_vdp_reset(&vdp);
    ys_z80_attach_vdp(&cpu,&vdp);
    vdp.status=0x80;
    LOAD(0,0x3E,0x56,0xD3,0xBF, /* reg 1 value 56 */
           0x3E,0x81,0xD3,0xBF,
           0x3E,0x10,0xD3,0xBF, /* CRAM address 10 */
           0x3E,0xC0,0xD3,0xBF,
           0xAF,0xD3,0xBE,      /* zero palette entry */
           0xDB,0xBF);          /* read/reset status */
    run(21,11);
    assert(cpu.a==0x80 && vdp.status==0);
    assert(vdp.registers[1]==0x56 && vdp.register_writes==1);
    assert(vdp.cram[0x10]==0 && vdp.cram_writes==1);
    assert(vdp.control_writes==4);
    setup();
    ys_sms_vdp_reset(&vdp);
    ys_z80_attach_vdp(&cpu,&vdp);
    cpu.sp=0xDFF0;
    cpu.e=0x10;cpu.d=0xC0;
    LOAD(0,0xEF); /* RST $28 */
    LOAD(0x28,0xF3,0x7B,0xD3,0xBF,0x7A,0xD3,0xBF,0xFB,0xC9);
    run(1,12);
    assert(cpu.sp==0xDFF0 && cpu.iff1);
    assert(vdp.code==3 && vdp.address==0x10);
}
static void test_bank2_audio_io_and_block_transfer(void) {
    setup();
    YsSmsSound sound;
    ys_sms_sound_reset(&sound);
    ys_z80_attach_sound(&cpu,&sound);
    LOAD(0,0x31,0xF0,0xDF,0x3E,0x02,0x32,0xFF,0xFF,
           0xCD,0x03,0x88,0x76);
    /* Representative bank-2 instruction sequence at $8803, using synthetic
       program bytes; the actual cartridge is traced in trace_boot.c. */
    const uint8_t program2[]={
        0x21,0x00,0xC0,0x11,0x10,0xC0,0x01,0x02,0x00,
        0xED,0xA0,0xED,0xA0, /* two LDI instructions */
        0x21,0x20,0x80,0x0E,0x7F,0xED,0xA3,0xED,0xA3, /* OUTI */
        0x06,0x03,0x21,0x00,0xC0,0x11,0x18,0x00,0x19, /* ADD HL,DE */
        0x16,0x20,0x0E,0xF0,0xED,0x51, /* OUT (C),D */
        0x3E,0x55,0xD3,0xF1,0xC9
    };
    memcpy(rom+0x8803,program2,sizeof(program2));
    rom[0x8020]=0x9A;rom[0x8021]=0xAC;
    assert(ys_sms_bus_write(&bus,0xC000,0x43));
    assert(ys_sms_bus_write(&bus,0xC001,0x44));
    run(0x000B,100);
    assert(cpu.sp==0xDFF0 && cpu.h==0xC0 && cpu.l==0x18);
    assert(ys_sms_bus_read(&bus,0xC010)==0x43);
    assert(ys_sms_bus_read(&bus,0xC011)==0x44);
    assert(sound.psg_write_count==2 && sound.psg_prefix[0]==0x9A &&
           sound.psg_prefix[1]==0xAC);
    assert(sound.fm_address_count==1 && sound.fm_data_count==1 &&
           sound.fm_touched[0x20] && sound.fm_registers[0x20]==0x55);
}
static void test_first_boot_dispatch_and_palette_copy(void) {
    setup();
    /* Actual bank-0 startup dispatcher $00C4, RST $08 at $0008,
       state table $00D4, handlers $00FC/$0C4A and $0A5B/$0A80/$0AE8.
       Source-encoded $0B10 copies 32 bytes before calling $0B22. */
    LOAD(0x0008,0x87,0x85,0x6F,0x30,0x01,0x24,
         0x7E,0x23,0x66,0x6F,0xE9);
    LOAD(0x00C4,0x3A,0x18,0xC0,0x32,0x31,0xC0,0x3A,0x1F,0xC0,
         0x21,0xD4,0x00,0xCF,0xC3,0xC4,0x00);
    LOAD(0x00D4,0xFC,0x00,0x4A,0x0C);
    LOAD(0x00FC,0x3E,0x01,0x32,0x1F,0xC0,0xC9);
    LOAD(0x0C4A,0xCD,0x5B,0x0A);
    LOAD(0x0A5B,0xCD,0x80,0x0A);
    LOAD(0x0A80,0xCD,0xE8,0x0A);
    LOAD(0x0AE8,0xCD,0x10,0x0B,0xAF,0xCD,0x22,0x0B);
    LOAD(0x0B10,0x21,0x60,0xC1,0x11,0x30,0xC5,0x01,0x20,0x00,
         0xF5,0xED,0xA0,0x78,0xB1,0x20,0xFA,0xF1,0xC9);
    cpu.pc=0x00C4;
    cpu.sp=0xDFF0;
    assert(ys_sms_bus_write(&bus,0xC018,0x49));
    for(unsigned i=0;i<32;i++)
        assert(ys_sms_bus_write(&bus,(uint16_t)(0xC160u+i),
                                (uint8_t)(0x90u+i)));
    run(0x0B22,300);
    assert(ys_sms_bus_read(&bus,0xC031)==0x49);
    assert(ys_sms_bus_read(&bus,0xC01F)==1);
    for(unsigned i=0;i<32;i++)
        assert(ys_sms_bus_read(&bus,(uint16_t)(0xC530u+i))==(uint8_t)(0x90u+i));
    assert(cpu.a==0 && cpu.b==0 && cpu.c==0);
    assert(cpu.h==0xC1 && cpu.l==0x80 && cpu.d==0xC5 && cpu.e==0x50);
    assert(cpu.sp==0xDFE6);
    assert(ys_sms_bus_read(&bus,0xDFE6)==0xEF);
    assert(ys_sms_bus_read(&bus,0xDFE7)==0x0A);
    assert(ys_sms_bus_read(&bus,0xDFEE)==0xD1);
    assert(ys_sms_bus_read(&bus,0xDFEF)==0);
}
static void test_rld_nibble_rotation_and_rom_guard(void) {
    setup();
    /* SCF is not part of this bounded interpreter; set carry explicitly. */
    LOAD(0,0x21,0x00,0xC0,0x3E,0xA3,0xED,0x6F);
    assert(ys_sms_bus_write(&bus,0xC000,0x6C));
    run(5,2);
    cpu.f=Z80_F_C;
    run(7,1);
    assert(cpu.a==0xA6 && ys_sms_bus_read(&bus,0xC000)==0xC3);
    assert((cpu.f&Z80_F_C) && (cpu.f&Z80_F_S) &&
           !(cpu.f&Z80_F_H) && !(cpu.f&Z80_F_N) &&
           (cpu.f&Z80_F_PV));
    setup();
    LOAD(0,0x21,0x00,0x00,0x3E,0xA3,0xED,0x6F);
    run(5,2);
    assert(ys_z80_step(&cpu)==Z80_BAD_WRITE);
    assert(cpu.fault_pc==5 && cpu.pc==5);
}
static void test_pc12_source_set_bits(void) {
    setup();
    /* Original source bank0 $0AAD CB EB (SET 5,E) and
       $0AB5 CB F3 (SET 6,E), verified in Ys/phase6/code.lst.
       CB FE is a separate memory SET instruction with 15T. */
    LOAD(0,0x1E,0x00,0xCB,0xEB,0xCB,0xF3,
         0x21,0x00,0xC0,0xCB,0xFE);
    assert(ys_sms_bus_write(&bus,0xC000u,0x05u));
    run(2,1);
    cpu.f=Z80_F_C|Z80_F_Z|Z80_F_N;
    const uint8_t unchanged=cpu.f;
    run(4,1);
    assert(cpu.e==0x20u && cpu.f==unchanged &&
           cpu.last_tstates==8u);
    run(6,1);
    assert(cpu.e==0x60u && cpu.f==unchanged &&
           cpu.last_tstates==8u);
    run(9,1);
    run(11,1);
    assert(ys_sms_bus_read(&bus,0xC000u)==0x85u &&
           cpu.f==unchanged && cpu.last_tstates==15u);
    setup();
    LOAD(0,0x21,0x00,0x00,0xCB,0xFE);
    run(3,1);
    assert(ys_z80_step(&cpu)==Z80_BAD_WRITE);
    assert(cpu.fault_pc==3u && cpu.pc==3u);
}
/* PC-15: original bank2 $8204 D6 81; $8206 F8 (RET M).
   Test signed return boundary, half borrow and overflow/carry,
   preserving genuine source opcode bytes and 7/5/11 T-state costs. */
static void test_pc15_sound_sub_immediate(void) {
    setup();
    LOAD(0,0x3E,0x80,0xD6,0x81,0xF8,0x76);
    run(2,1);
    assert(cpu.a==0x80u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0xFFu && cpu.pc==4u &&
           (cpu.f&Z80_F_S) && (cpu.f&Z80_F_N) &&
           (cpu.f&Z80_F_H) && (cpu.f&Z80_F_C) &&
           !(cpu.f&Z80_F_Z) && !(cpu.f&Z80_F_PV) &&
           cpu.last_tstates==7u);
    cpu.sp=0xC100u;
    assert(ys_sms_bus_write(&bus,0xC100u,0x25u));
    assert(ys_sms_bus_write(&bus,0xC101u,0x00u));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.pc==0x0025u && cpu.sp==0xC102u &&
           cpu.last_tstates==11u);

    setup();
    LOAD(0,0x3E,0x81,0xD6,0x81,0xF8,0x76);
    run(2,1);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0 && (cpu.f&Z80_F_Z) && (cpu.f&Z80_F_N) &&
           !(cpu.f&Z80_F_S) && !(cpu.f&Z80_F_C) &&
           cpu.last_tstates==7u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.pc==5u && cpu.last_tstates==5u);

    setup();
    /* +127 - (-1) => signed overflow, wrapped $80 and borrow. */
    LOAD(0,0x3E,0x7F,0xD6,0xFF);
    run(2,1);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0x80u && (cpu.f&Z80_F_PV) &&
           (cpu.f&Z80_F_C) && (cpu.f&Z80_F_N) &&
           (cpu.f&Z80_F_S));
}
static void test_pc15_sound_rra_nibble(void) {
    setup();
    /* Original bank2 $818F AND $F0, $8191-$8194 RRA x4.
       Z80 RRA is THROUGH carry, unlike RRCA. */
    LOAD(0,0x3E,0xA7,0xE6,0xF0,
         0x1F,0x1F,0x1F,0x1F,0x76);
    run(4,2);
    assert(cpu.a==0xA0u && !(cpu.f&Z80_F_C));
    for(unsigned i=0;i<4u;++i) {
        assert(ys_z80_step(&cpu)==Z80_RUNNING);
        assert(cpu.last_tstates==4u);
    }
    assert(cpu.a==0x0Au && cpu.pc==8u &&
           !(cpu.f&Z80_F_C) && !(cpu.f&Z80_F_H) &&
           !(cpu.f&Z80_F_N) && (cpu.f&Z80_F_PV));
    setup();
    LOAD(0,0x1F,0x1F);
    cpu.a=0x01u;
    cpu.f=Z80_F_C|Z80_F_Z|Z80_F_PV;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0x80u && (cpu.f&Z80_F_C) &&
           (cpu.f&Z80_F_Z) && (cpu.f&Z80_F_PV) &&
           !(cpu.f&Z80_F_S)); /* old S, not new bit7 */
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0xC0u && !(cpu.f&Z80_F_C) &&
           (cpu.f&Z80_F_Z) && (cpu.f&Z80_F_PV));
}
int main(void) {
    test_first_boot_dispatch_and_palette_copy();
    test_rld_nibble_rotation_and_rom_guard();
    test_pc12_source_set_bits();
    test_pc15_sound_sub_immediate();
    test_pc15_sound_rra_nibble();
    test_bank2_audio_io_and_block_transfer();
    test_extended_startup_instructions();
    test_vdp_cpu_ports_and_rst();
    boot_prefix_source_fixture();
    test_control_and_stack();
    test_flags_and_relative_jumps();
    test_ldir_and_mapper();
    test_fail_closed();
    puts("PASS: Z80 startup, flags, calls, stack, LDIR, mapper and fail-closed errors");
}
