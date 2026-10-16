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

/* PC-16: original physical bank-2 $8307: EB (EX DE,HL).
   Both pairs exchange atomically, with no flags/memory/mapper effects. */
static void test_pc16_sound_ex_de_hl(void) {
    setup();
    LOAD(0,0xEB,0xEB,0x76);
    cpu.a=0x9Cu; cpu.f=0xFFu;
    cpu.b=0x36u; cpu.c=0x47u;
    cpu.d=0xA5u; cpu.e=0x5Au; /* DE=A55A */
    cpu.h=0x12u; cpu.l=0x34u; /* HL=1234 */
    cpu.d_alt=0x01u; cpu.e_alt=0x02u;
    cpu.h_alt=0x03u; cpu.l_alt=0x04u;
    cpu.sp=0xC800u; cpu.ix=0xBEEFu; cpu.iy=0x00F1u;
    cpu.iff1=true; cpu.iff2=false;
    assert(ys_sms_bus_write(&bus,0xC200u,0x75u));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.d==0x12u && cpu.e==0x34u);
    assert(cpu.h==0xA5u && cpu.l==0x5Au);
    assert(cpu.pc==1u && cpu.steps==1u &&
           cpu.last_tstates==4u && cpu.total_tstates==4u);
    assert(cpu.a==0x9Cu && cpu.f==0xFFu &&
           cpu.b==0x36u && cpu.c==0x47u);
    assert(cpu.d_alt==1u && cpu.e_alt==2u &&
           cpu.h_alt==3u && cpu.l_alt==4u);
    assert(cpu.sp==0xC800u && cpu.ix==0xBEEFu &&
           cpu.iy==0x00F1u && cpu.iff1 && !cpu.iff2);
    assert(ys_sms_bus_read(&bus,0xC200u)==0x75u);
    assert(bus.mapped_bank[1]==1u && bus.mapped_bank[2]==2u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.d==0xA5u && cpu.e==0x5Au &&
           cpu.h==0x12u && cpu.l==0x34u);
    assert(cpu.pc==2u && cpu.steps==2u &&
           cpu.last_tstates==4u && cpu.total_tstates==8u &&
           cpu.f==0xFFu);
    setup();
    LOAD(0,0xEB);
    cpu.d=0xFFu; cpu.e=0xFFu;
    cpu.h=0u; cpu.l=0u;
    cpu.f=Z80_F_C|Z80_F_Z;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.d==0u && cpu.e==0u &&
           cpu.h==0xFFu && cpu.l==0xFFu &&
           cpu.f==(Z80_F_C|Z80_F_Z) &&
           cpu.last_tstates==4u);
}


/* PC-17: exact source opcodes at original bank2 $8A4B-$8A57.
   PSG emission uses a controlled RAM fixture; it is NOT a real game frame. */
static void test_pc17_original_psg_instruction_path(void) {
    setup();
    YsSmsSound sound;
    ys_sms_sound_reset(&sound);
    ys_z80_attach_sound(&cpu,&sound);
    LOAD(0,0xDD,0x7E,0x08, /* LD A,(IX+8) */
           0xE6,0x0F,      /* AND $0F */
           0xDD,0xB6,0x01, /* OR (IX+1) */
           0xC6,0x10,      /* ADD A,$10 */
           0xD3,0x7F,      /* OUT ($7F),A */
           0xC9);          /* RET */
    cpu.ix=0xC100u;
    cpu.sp=0xC300u;
    cpu.f=0xFFu;
    assert(ys_sms_bus_write(&bus,0xC108u,0xA7u));
    assert(ys_sms_bus_write(&bus,0xC101u,0x20u));
    assert(ys_sms_bus_write(&bus,0xC300u,0x00u));
    assert(ys_sms_bus_write(&bus,0xC301u,0x20u));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0xA7u && cpu.f==0xFFu &&
           cpu.pc==3u && cpu.last_tstates==19u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0x07u && cpu.pc==5u &&
           cpu.last_tstates==7u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0x27u && cpu.pc==8u &&
           cpu.last_tstates==19u &&
           cpu.f==(Z80_F_5|Z80_F_PV));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0x37u && cpu.pc==10u &&
           cpu.last_tstates==7u && cpu.f==Z80_F_5);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(sound.psg_write_count==1u &&
           sound.psg_prefix[0]==0x37u &&
           cpu.last_tstates==11u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.pc==0x2000u && cpu.sp==0xC302u &&
           cpu.ix==0xC100u && cpu.steps==6u &&
           cpu.last_tstates==10u && cpu.total_tstates==73u);
    assert(ys_sms_bus_read(&bus,0xC108u)==0xA7u);
    assert(ys_sms_bus_read(&bus,0xC101u)==0x20u);
}

/* Indexed reads respect signed displacement, slot mapping and 16-bit wrap.
   On LD A,(IX/IY+d), flags are never recomputed from loaded data. */
static void test_pc17_indexed_displacements(void) {
    setup();
    LOAD(0,0xFD,0x7E,0xFE, /* LD A,(IY-2) */
           0xDD,0x7E,0xFF);/* LD A,(IX-1) */
    cpu.iy=0xC110u;
    cpu.ix=0x8000u;
    cpu.f=Z80_F_S|Z80_F_C|Z80_F_N;
    assert(ys_sms_bus_write(&bus,0xC10Eu,0x4Cu));
    rom[0x7FFFu]=0xA3u; /* physical bank1 $7FFF */
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0x4Cu && cpu.pc==3u &&
           cpu.last_tstates==19u && cpu.iy==0xC110u &&
           cpu.f==(Z80_F_S|Z80_F_C|Z80_F_N));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0xA3u && cpu.pc==6u &&
           cpu.last_tstates==19u && cpu.total_tstates==38u &&
           cpu.ix==0x8000u && cpu.f==(Z80_F_S|Z80_F_C|Z80_F_N));
    setup();
    LOAD(0,0xDD,0x7E,0x01);
    cpu.ix=0xFFFFu; /* $FFFF+1 wraps to CPU $0000. */
    cpu.f=Z80_F_Z;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0xDDu && cpu.pc==3u &&
           cpu.last_tstates==19u && cpu.f==Z80_F_Z);
}

static void test_pc17_add_immediate_flags(void) {
    static const struct {
        uint8_t prior, result, flags;
    } cases[]={
        {0x0Fu,0x10u,Z80_F_H},
        {0x7Fu,0x80u,Z80_F_S|Z80_F_H|Z80_F_PV},
        {0xFFu,0x00u,Z80_F_Z|Z80_F_H|Z80_F_C}
    };
    for(size_t i=0;i<sizeof(cases)/sizeof(cases[0]);++i) {
        setup();
        LOAD(0,0xC6,0x01);
        cpu.a=cases[i].prior;
        cpu.f=0xFFu;
        assert(ys_z80_step(&cpu)==Z80_RUNNING);
        assert(cpu.a==cases[i].result && cpu.f==cases[i].flags &&
               cpu.pc==2u && cpu.steps==1u &&
               cpu.last_tstates==7u && cpu.total_tstates==7u);
    }
}


/* PC-18 exact original bank2 $8947-$8952 instruction bytes.
   Bounded synthetic RAM fixture; no claim of original Ys scene/audio. */
static void test_pc18_indexed_sound_counter_prefix(void) {
    setup();
    LOAD(0,0xDD,0x34,0x0B,  /* $8947 INC (IX+11) */
           0xDD,0x7E,0x0A,  /* $894A LD A,(IX+10) */
           0xDD,0x96,0x0B,  /* $894D SUB (IX+11) */
           0xCC,0xF1,0x84); /* $8950 CALL Z,$84F1 */
    cpu.ix=0xC100u;
    cpu.sp=0xC300u;
    cpu.a=0x55u;
    cpu.f=Z80_F_C|Z80_F_N;
    assert(ys_sms_bus_write(&bus,0xC10Bu,0x7Fu));
    assert(ys_sms_bus_write(&bus,0xC10Au,0x90u));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(ys_sms_bus_read(&bus,0xC10Bu)==0x80u);
    assert(cpu.a==0x55u && cpu.ix==0xC100u &&
           cpu.f==(Z80_F_S|Z80_F_H|Z80_F_PV|Z80_F_C) &&
           cpu.pc==3u && cpu.last_tstates==23u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0x90u && cpu.pc==6u && cpu.last_tstates==19u &&
           cpu.f==(Z80_F_S|Z80_F_H|Z80_F_PV|Z80_F_C));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0x10u && cpu.pc==9u && cpu.last_tstates==19u &&
           cpu.f==Z80_F_N && ys_sms_bus_read(&bus,0xC10Bu)==0x80u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.pc==12u && cpu.sp==0xC300u &&
           cpu.last_tstates==10u && cpu.total_tstates==71u &&
           cpu.steps==4u);
    /* Source CALL Z is taken only for a genuine zero result. */
    setup();
    LOAD(0,0xDD,0x34,0x0B,0xDD,0x7E,0x0A,
           0xDD,0x96,0x0B,0xCC,0xF1,0x84);
    cpu.ix=0xC100u;
    cpu.sp=0xC300u;
    assert(ys_sms_bus_write(&bus,0xC10Bu,0xFFu));
    assert(ys_sms_bus_write(&bus,0xC10Au,0x00u));
    run(9u,3u);
    assert(cpu.a==0 && cpu.f==(Z80_F_Z|Z80_F_N) &&
           ys_sms_bus_read(&bus,0xC10Bu)==0 &&
           cpu.total_tstates==61u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.pc==0x84F1u && cpu.sp==0xC2FEu &&
           cpu.last_tstates==17u && cpu.total_tstates==78u &&
           ys_sms_bus_read(&bus,0xC2FEu)==0x0Cu &&
           ys_sms_bus_read(&bus,0xC2FFu)==0x00u);
}

/* Independent boundary expectations for indexed INC flags and timing. */
static void test_pc18_indexed_inc_flags(void) {
    static const struct {
        uint8_t old, next, flags;
    } cases[]={
        {0x00u,0x01u,0u},
        {0x07u,0x08u,Z80_F_3},
        {0x0Fu,0x10u,Z80_F_H},
        {0x1Fu,0x20u,Z80_F_H|Z80_F_5},
        {0x7Fu,0x80u,Z80_F_S|Z80_F_H|Z80_F_PV},
        {0xFFu,0x00u,Z80_F_H|Z80_F_Z}
    };
    for(size_t i=0;i<sizeof(cases)/sizeof(cases[0]);++i) {
        for(unsigned carry=0;carry<=1u;++carry) {
            setup();
            LOAD(0,0xFD,0x34,0xFE); /* INC (IY-2) */
            cpu.iy=0xC102u;
            cpu.a=0xE2u;
            cpu.f=(uint8_t)(Z80_F_N|Z80_F_PV|Z80_F_H|Z80_F_C);
            if(!carry) cpu.f=(uint8_t)(cpu.f&~Z80_F_C);
            assert(ys_sms_bus_write(&bus,0xC100u,cases[i].old));
            assert(ys_z80_step(&cpu)==Z80_RUNNING);
            assert(ys_sms_bus_read(&bus,0xC100u)==cases[i].next);
            assert(cpu.f==(uint8_t)(cases[i].flags|
                       (carry?Z80_F_C:0u)) &&
                   cpu.a==0xE2u && cpu.iy==0xC102u &&
                   cpu.pc==3u && cpu.last_tstates==23u &&
                   cpu.total_tstates==23u && cpu.steps==1u);
        }
    }
}

/* Indexed SUB flags are independent of prior carry, including borrow,
   half-borrow, signed overflow, and undocumented result bits 3/5. */
static void test_pc18_indexed_sub_flags(void) {
    static const struct {
        uint8_t a,rhs,result,flags;
    } cases[]={
        {0x80u,0x01u,0x7Fu,
         Z80_F_5|Z80_F_3|Z80_F_H|Z80_F_PV|Z80_F_N},
        {0x7Fu,0xFFu,0x80u,Z80_F_S|Z80_F_PV|Z80_F_N|Z80_F_C},
        {0x00u,0x00u,0x00u,Z80_F_Z|Z80_F_N},
        {0x00u,0x01u,0xFFu,
         Z80_F_S|Z80_F_5|Z80_F_3|Z80_F_H|Z80_F_N|Z80_F_C}
    };
    for(size_t i=0;i<sizeof(cases)/sizeof(cases[0]);++i) {
        setup();
        LOAD(0,0xFD,0x96,0xFE); /* SUB (IY-2), negative offset */
        cpu.iy=0xC102u;
        cpu.a=cases[i].a;
        cpu.f=0xFFu;
        assert(ys_sms_bus_write(&bus,0xC100u,cases[i].rhs));
        assert(ys_z80_step(&cpu)==Z80_RUNNING);
        assert(cpu.a==cases[i].result && cpu.f==cases[i].flags &&
               ys_sms_bus_read(&bus,0xC100u)==cases[i].rhs &&
               cpu.iy==0xC102u && cpu.pc==3u &&
               cpu.last_tstates==19u && cpu.total_tstates==19u);
    }
}

/* ROM-write rejection must leave flags and memory unchanged; no clocks
   or instructions are committed. Also verify indexed address wrap. */
static void test_pc18_indexed_inc_write_guard(void) {
    setup();
    LOAD(0,0xDD,0x34,0x01);
    cpu.ix=0xFFFFu; /* IX+1 -> ROM CPU $0000 */
    cpu.f=Z80_F_C|Z80_F_Z|Z80_F_N;
    assert(ys_z80_step(&cpu)==Z80_BAD_WRITE);
    assert(cpu.fault_pc==0u && cpu.pc==0u && cpu.ix==0xFFFFu &&
           cpu.f==(Z80_F_C|Z80_F_Z|Z80_F_N) &&
           rom[0]==0xDDu && cpu.steps==0u &&
           cpu.last_tstates==0u && cpu.total_tstates==0u);
    setup();
    LOAD(0,0xFD,0x34,0xFF);
    cpu.iy=0x8000u; /* IY-1 -> ROM CPU $7FFF */
    cpu.f=0xFFu;
    rom[0x7FFFu]=0x10u;
    assert(ys_z80_step(&cpu)==Z80_BAD_WRITE);
    assert(cpu.pc==0 && cpu.fault_pc==0 && cpu.f==0xFFu &&
           rom[0x7FFFu]==0x10u && cpu.steps==0u);
    setup();
    LOAD(0,0xDD,0x34,0x01);
    cpu.ix=0xBFFFu; /* IX+1 -> WRAM CPU $C000 */
    cpu.f=Z80_F_C;
    assert(ys_sms_bus_write(&bus,0xC000u,0xFEu));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(ys_sms_bus_read(&bus,0xC000u)==0xFFu &&
           cpu.pc==3u && cpu.last_tstates==23u &&
           cpu.f==(Z80_F_C|Z80_F_S|Z80_F_5|Z80_F_3));
}


/* PC-19: original physical bank2 $084F1-$084F8 instruction bytes.
   The fixture uses controlled WRAM; these are not original run states. */
static void test_pc19_sound_pointer_loads(void) {
    setup();
    LOAD(0,0xDD,0x5E,0x03, /* LD E,(IX+3)  $84F1 */
           0xDD,0x56,0x04, /* LD D,(IX+4)  $84F4 */
           0x1A,           /* LD A,(DE)    $84F7 */
           0x13);          /* INC DE       $84F8 */
    cpu.ix=0xC100u;
    cpu.d=0x9Eu; cpu.e=0xA7u;
    cpu.a=0x3Cu; cpu.f=0xFFu;
    cpu.sp=0xC300u;
    cpu.h=0x15u; cpu.l=0x02u;
    assert(ys_sms_bus_write(&bus,0xC103u,0x56u));
    assert(ys_sms_bus_write(&bus,0xC104u,0xC2u));
    assert(ys_sms_bus_write(&bus,0xC256u,0xD4u));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.e==0x56u && cpu.d==0x9Eu && cpu.a==0x3Cu &&
           cpu.ix==0xC100u && cpu.f==0xFFu &&
           cpu.pc==3u && cpu.last_tstates==19u &&
           cpu.total_tstates==19u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.d==0xC2u && cpu.e==0x56u && cpu.f==0xFFu &&
           cpu.pc==6u && cpu.last_tstates==19u &&
           cpu.total_tstates==38u && cpu.ix==0xC100u &&
           cpu.sp==0xC300u && cpu.h==0x15u && cpu.l==0x02u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0xD4u && cpu.pc==7u &&
           cpu.last_tstates==7u && cpu.f==0xFFu);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.d==0xC2u && cpu.e==0x57u &&
           cpu.last_tstates==6u && cpu.pc==8u &&
           cpu.steps==4u && cpu.total_tstates==51u);
    assert(ys_sms_bus_read(&bus,0xC103u)==0x56u &&
           ys_sms_bus_read(&bus,0xC104u)==0xC2u &&
           ys_sms_bus_read(&bus,0xC256u)==0xD4u);
}

/* IX/IY negative offset, address overflow and mapper-qualified ROM read.
   All LD D/E indexed variants preserve every bit of flags. */
static void test_pc19_indexed_load_boundaries(void) {
    setup();
    LOAD(0,0xFD,0x56,0xFE, /* LD D,(IY-2) */
           0xFD,0x5E,0xFF);/* LD E,(IY-1) */
    cpu.iy=0xC110u;
    cpu.a=0x87u; cpu.d=0x11u; cpu.e=0x22u;
    cpu.f=Z80_F_S|Z80_F_N|Z80_F_Z|Z80_F_C;
    assert(ys_sms_bus_write(&bus,0xC10Eu,0x00u));
    assert(ys_sms_bus_write(&bus,0xC10Fu,0xF5u));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.d==0x00u && cpu.e==0x22u &&
           cpu.f==(Z80_F_S|Z80_F_N|Z80_F_Z|Z80_F_C) &&
           cpu.pc==3u && cpu.last_tstates==19u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.e==0xF5u && cpu.d==0 &&
           cpu.f==(Z80_F_S|Z80_F_N|Z80_F_Z|Z80_F_C) &&
           cpu.a==0x87u && cpu.iy==0xC110u &&
           cpu.pc==6u && cpu.total_tstates==38u);

    setup();
    LOAD(0,0xDD,0x5E,0x01); /* IX+1 => $0000 via 16-bit wrap */
    cpu.ix=0xFFFFu; cpu.f=0xFFu;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.e==0xDDu && cpu.pc==3u && cpu.f==0xFFu &&
           cpu.last_tstates==19u);

    setup();
    LOAD(0,0xFD,0x56,0x10);
    cpu.iy=0x8000u;
    cpu.d=0xACu; cpu.f=Z80_F_Z|Z80_F_C;
    /* Physically mapped bank 3 at slot2 ($8000-$BFFF). */
    rom[3u*0x4000u+0x10u]=0x6Du;
    assert(ys_sms_bus_write(&bus,0xFFFFu,3u));
    assert(bus.mapped_bank[2]==3u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.d==0x6Du && cpu.iy==0x8000u &&
           cpu.f==(Z80_F_Z|Z80_F_C) &&
           bus.mapped_bank[2]==3u && cpu.pc==3u &&
           cpu.last_tstates==19u);
}


/* PC-20: original bank2 $85D3 DD 86 05, indexed ADD A,(IX+5).
   Genuine opcode, controlled register/WRAM inputs; not source-runtime state. */
static void test_pc20_indexed_add_sound_event(void) {
    setup();
    LOAD(0,0xDD,0x86,0x05,0x21,0x58,0x8A,0x08);
    cpu.ix=0xC100u;
    cpu.a=0x7Fu;
    cpu.f=0xFFu;
    cpu.d=0xB6u;cpu.e=0x54u;cpu.sp=0xC700u;
    assert(ys_sms_bus_write(&bus,0xC105u,0x01u));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0x80u &&
           cpu.f==(Z80_F_S|Z80_F_H|Z80_F_PV) &&
           cpu.ix==0xC100u && cpu.d==0xB6u && cpu.e==0x54u &&
           cpu.pc==3u && cpu.sp==0xC700u &&
           cpu.last_tstates==19u && cpu.total_tstates==19u &&
           cpu.steps==1u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.h==0x8Au && cpu.l==0x58u &&
           cpu.pc==6u && cpu.last_tstates==10u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a_alt==0x80u &&
           cpu.f_alt==(Z80_F_S|Z80_F_H|Z80_F_PV) &&
           cpu.pc==7u && cpu.last_tstates==4u &&
           cpu.total_tstates==33u);
}

static void test_pc20_indexed_add_flags_and_mapping(void) {
    static const struct {
        uint8_t lhs,rhs,result,flags;
    } cases[]={
        {0x00u,0x00u,0x00u,Z80_F_Z},
        {0x0Fu,0x01u,0x10u,Z80_F_H},
        {0x7Fu,0x01u,0x80u,Z80_F_S|Z80_F_H|Z80_F_PV},
        {0xFFu,0x01u,0x00u,Z80_F_Z|Z80_F_H|Z80_F_C},
        {0x88u,0x98u,0x20u,Z80_F_5|Z80_F_H|Z80_F_PV|Z80_F_C},
        {0x01u,0x07u,0x08u,Z80_F_3}
    };
    for(size_t i=0;i<sizeof(cases)/sizeof(cases[0]);++i) {
        setup();
        LOAD(0,0xFD,0x86,0xFE); /* ADD A,(IY-2) */
        cpu.iy=0xC102u;
        cpu.a=cases[i].lhs;
        cpu.f=0xFFu;
        assert(ys_sms_bus_write(&bus,0xC100u,cases[i].rhs));
        assert(ys_z80_step(&cpu)==Z80_RUNNING);
        assert(cpu.a==cases[i].result && cpu.f==cases[i].flags &&
               cpu.iy==0xC102u && cpu.pc==3u &&
               cpu.last_tstates==19u && cpu.total_tstates==19u &&
               ys_sms_bus_read(&bus,0xC100u)==cases[i].rhs);
    }
    setup();
    LOAD(0,0xDD,0x86,0x01);
    cpu.ix=0xFFFFu; /* indexed CPU address wraps to $0000 */
    cpu.a=0x01u;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0xDEu && cpu.f==(Z80_F_S|Z80_F_3) &&
           cpu.pc==3u && cpu.last_tstates==19u);
    setup();
    LOAD(0,0xDD,0x86,0x04);
    cpu.ix=0x8000u;
    cpu.a=0x10u;
    rom[4u*0x4000u+4u]=0x17u;
    assert(ys_sms_bus_write(&bus,0xFFFFu,4u));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0x27u && cpu.f==Z80_F_5 &&
           cpu.ix==0x8000u && bus.mapped_bank[2]==4u &&
           cpu.pc==3u && cpu.last_tstates==19u);
}


/* PC-21 original source $850F-$8518 sound table writes.
   The surrounding source (HL), INC HL, BIT instruction shapes are exact;
   RAM and VDP state are an isolated fixture, not observed original state. */
static void test_pc21_indexed_sound_table_writes(void) {
    setup();
    LOAD(0,0x7E,0xDD,0x77,0x0E,0x23,0x7E,0xDD,0x77,0x0F);
    cpu.ix=0xC100u;
    cpu.h=0xC2u;cpu.l=0x00u;
    cpu.f=0xFFu;
    assert(ys_sms_bus_write(&bus,0xC200u,0x41u));
    assert(ys_sms_bus_write(&bus,0xC201u,0xE3u));
    run(9u,5u);
    assert(ys_sms_bus_read(&bus,0xC10Eu)==0x41u &&
           ys_sms_bus_read(&bus,0xC10Fu)==0xE3u &&
           cpu.a==0xE3u && cpu.f==0xFFu &&
           cpu.ix==0xC100u && cpu.h==0xC2u && cpu.l==0x01u &&
           cpu.last_tstates==19u && cpu.steps==5u &&
           cpu.total_tstates==56u);
}

/* Exactly indexed A/B/C/D/E source stores and B/C indexed reads.
   Neither 0x74 nor 0x75 is admitted before IXH/IXL source review. */
static void test_pc21_indexed_register_store_read(void) {
    setup();
    LOAD(0,0xDD,0x70,0x05,0xDD,0x71,0x06,
           0xFD,0x72,0xFE,0xFD,0x73,0xFF,
           0xDD,0x46,0x05,0xFD,0x4E,0xFE,
           0xDD,0x77,0x07);
    cpu.ix=0xC100u;cpu.iy=0xC202u;
    cpu.b=0x37u;cpu.c=0x64u;
    cpu.d=0xA3u;cpu.e=0xB6u;cpu.a=0xF8u;
    cpu.f=Z80_F_C|Z80_F_Z|Z80_F_N|Z80_F_PV;
    assert(ys_z80_run_until(&cpu,21u,7u)==Z80_RUNNING);
    assert(cpu.pc==21u && cpu.steps==7u &&
           cpu.total_tstates==133u && cpu.last_tstates==19u);
    assert(ys_sms_bus_read(&bus,0xC105u)==0x37u &&
           ys_sms_bus_read(&bus,0xC106u)==0x64u &&
           ys_sms_bus_read(&bus,0xC200u)==0xA3u &&
           ys_sms_bus_read(&bus,0xC201u)==0xB6u &&
           ys_sms_bus_read(&bus,0xC107u)==0xF8u);
    assert(cpu.b==0x37u && cpu.c==0xA3u &&
           cpu.d==0xA3u && cpu.e==0xB6u &&
           cpu.ix==0xC100u && cpu.iy==0xC202u &&
           cpu.f==(Z80_F_C|Z80_F_Z|Z80_F_N|Z80_F_PV));
    setup();
    LOAD(0,0xDD,0x74,0x03);
    cpu.ix=0xC100u;
    assert(ys_z80_step(&cpu)==Z80_UNSUPPORTED);
    assert(cpu.pc==0u && cpu.fault_pc==0u &&
           cpu.steps==0u && cpu.last_tstates==0u);
    setup();
    LOAD(0,0xFD,0x75,0x03);
    cpu.iy=0xC100u;
    assert(ys_z80_step(&cpu)==Z80_UNSUPPORTED);
    assert(cpu.pc==0u && cpu.fault_pc==0u &&
           cpu.steps==0u && cpu.last_tstates==0u);
}

static void test_pc21_indexed_rom_write_guard(void) {
    setup();
    LOAD(0,0xDD,0x77,0x01);
    cpu.ix=0xFFFFu; /* IX+1 wraps to physical ROM CPU $0000. */
    cpu.a=0x55u;
    cpu.f=0xFFu;
    assert(ys_z80_step(&cpu)==Z80_BAD_WRITE);
    assert(cpu.pc==0u && cpu.fault_pc==0u && cpu.f==0xFFu &&
           cpu.ix==0xFFFFu && rom[0]==0xDDu &&
           cpu.steps==0u && cpu.total_tstates==0u &&
           cpu.last_tstates==0u);
    setup();
    LOAD(0,0xFD,0x72,0xFE);
    cpu.iy=0x8000u;cpu.d=0x77u;cpu.f=Z80_F_C;
    rom[0x7FFEu]=0x24u;
    assert(ys_z80_step(&cpu)==Z80_BAD_WRITE);
    assert(cpu.pc==0u && cpu.fault_pc==0u && cpu.f==Z80_F_C &&
           rom[0x7FFEu]==0x24u && cpu.steps==0u);
    setup();
    LOAD(0,0xDD,0x77,0x01);
    cpu.ix=0xBFFFu;cpu.a=0x79u;cpu.f=0xFFu;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(ys_sms_bus_read(&bus,0xC000u)==0x79u &&
           cpu.f==0xFFu && cpu.last_tstates==19u);
}

int main(void) {
    test_first_boot_dispatch_and_palette_copy();
    test_rld_nibble_rotation_and_rom_guard();
    test_pc12_source_set_bits();
    test_pc15_sound_sub_immediate();
    test_pc15_sound_rra_nibble();
    test_pc16_sound_ex_de_hl();
    test_pc17_original_psg_instruction_path();
    test_pc17_indexed_displacements();
    test_pc17_add_immediate_flags();
    test_pc18_indexed_sound_counter_prefix();
    test_pc18_indexed_inc_flags();
    test_pc18_indexed_sub_flags();
    test_pc18_indexed_inc_write_guard();
    test_pc19_sound_pointer_loads();
    test_pc19_indexed_load_boundaries();
    test_pc20_indexed_add_sound_event();
    test_pc20_indexed_add_flags_and_mapping();
    test_pc21_indexed_sound_table_writes();
    test_pc21_indexed_register_store_read();
    test_pc21_indexed_rom_write_guard();
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
