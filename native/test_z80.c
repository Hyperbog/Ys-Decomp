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
           cpu.total_tstates==58u);
}

/* Exact indexed A/B/C/D/E source stores and B/C indexed reads.
   Ordinary H/L variants are independently covered by PC-22 tests. */
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


/* PC-22: $89D1 DD 6E 0E / $89D4 DD 66 0F. The independent
   Zilog documented indexed-(HL) rule targets H/L, NOT IXH/IXL.
   The Phase5 mnemonics saying ixl/ixh are historical listing labels,
   not a reason to mutate the index register. */
static void test_pc22_indexed_hl_source_sequence(void) {
    setup();
    LOAD(0,0xDD,0x6E,0x0E,0xDD,0x66,0x0F,
           0xDD,0x75,0x10,0xDD,0x74,0x11);
    cpu.ix=0xC100u;
    cpu.h=0xA1u;cpu.l=0xB2u;cpu.a=0x55u;
    cpu.f=0xFFu;
    assert(ys_sms_bus_write(&bus,0xC10Eu,0x34u));
    assert(ys_sms_bus_write(&bus,0xC10Fu,0xC2u));
    run(6u,2u);
    assert(cpu.h==0xC2u && cpu.l==0x34u &&
           cpu.ix==0xC100u && cpu.f==0xFFu &&
           cpu.last_tstates==19u && cpu.total_tstates==38u);
    run(12u,2u);
    assert(ys_sms_bus_read(&bus,0xC110u)==0x34u &&
           ys_sms_bus_read(&bus,0xC111u)==0xC2u &&
           cpu.h==0xC2u && cpu.l==0x34u &&
           cpu.ix==0xC100u && cpu.f==0xFFu &&
           cpu.steps==4u && cpu.last_tstates==19u &&
           cpu.total_tstates==76u);
}

static void test_pc22_indexed_hl_iy_and_write_guards(void) {
    setup();
    LOAD(0,0xFD,0x66,0xFE,0xFD,0x6E,0xFF,
           0xFD,0x74,0x01,0xFD,0x75,0x02);
    cpu.iy=0xC102u;
    cpu.h=0x6Au; cpu.l=0x29u;cpu.f=Z80_F_C|Z80_F_Z;
    assert(ys_sms_bus_write(&bus,0xC100u,0xFEu));
    assert(ys_sms_bus_write(&bus,0xC101u,0xDCu));
    run(12u,4u);
    assert(cpu.h==0xFEu && cpu.l==0xDCu &&
           cpu.iy==0xC102u && cpu.f==(Z80_F_C|Z80_F_Z) &&
           ys_sms_bus_read(&bus,0xC103u)==0xFEu &&
           ys_sms_bus_read(&bus,0xC104u)==0xDCu &&
           cpu.total_tstates==76u);
    setup();
    LOAD(0,0xDD,0x66,0x01); /* IX+1 wraps $FFFF to ROM $0000 */
    cpu.ix=0xFFFFu;cpu.h=0u;cpu.f=0xFFu;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.h==0xDDu && cpu.ix==0xFFFFu &&
           cpu.f==0xFFu && cpu.last_tstates==19u);
    setup();
    LOAD(0,0xDD,0x75,0x01); /* fail-closed ROM store */
    cpu.ix=0xFFFFu;cpu.l=0x76u;cpu.f=0xFFu;
    assert(ys_z80_step(&cpu)==Z80_BAD_WRITE);
    assert(cpu.fault_pc==0u && cpu.pc==0u &&
           cpu.ix==0xFFFFu && cpu.l==0x76u &&
           cpu.f==0xFFu && rom[0]==0xDDu &&
           cpu.steps==0u && cpu.total_tstates==0u);
}


/* PC-23: source $88FF LD (IX+7),$00 and following PSG command.
   The bytes are original; RAM/register fixture is isolated. */
static void test_pc23_sound_zerostore_and_psg(void) {
    setup();
    YsSmsSound sound;
    ys_sms_sound_reset(&sound);
    ys_z80_attach_sound(&cpu,&sound);
    LOAD(0,0xDD,0x36,0x07,0x00,
           0x3E,0xFF,0xD3,0x7F,0xC9);
    cpu.ix=0xC100u;
    cpu.sp=0xC300u;
    cpu.f=0xFFu;
    assert(ys_sms_bus_write(&bus,0xC107u,0xE8u));
    assert(ys_sms_bus_write(&bus,0xC300u,0x00u));
    assert(ys_sms_bus_write(&bus,0xC301u,0x20u));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(ys_sms_bus_read(&bus,0xC107u)==0u &&
           cpu.ix==0xC100u && cpu.f==0xFFu &&
           cpu.pc==4u && cpu.last_tstates==19u &&
           cpu.total_tstates==19u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0xFFu && cpu.pc==6u &&
           cpu.last_tstates==7u && cpu.f==0xFFu);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(sound.psg_write_count==1u &&
           sound.psg_prefix[0]==0xFFu &&
           cpu.last_tstates==11u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.pc==0x2000u && cpu.sp==0xC302u &&
           cpu.f==0xFFu && cpu.steps==4u &&
           cpu.last_tstates==10u && cpu.total_tstates==47u);
}

static void test_pc23_indexed_immediate_boundary(void) {
    setup();
    LOAD(0,0xFD,0x36,0xFE,0x5Au); /* LD (IY-2),$5A */
    cpu.iy=0xC102u;cpu.f=Z80_F_S|Z80_F_C;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(ys_sms_bus_read(&bus,0xC100u)==0x5Au &&
           cpu.pc==4u && cpu.iy==0xC102u &&
           cpu.f==(Z80_F_S|Z80_F_C) &&
           cpu.last_tstates==19u && cpu.total_tstates==19u);
    setup();
    LOAD(0,0xDD,0x36,0x01,0xC3); /* wraps IX+1 to $0000 */
    cpu.ix=0xFFFFu;cpu.f=Z80_F_Z|Z80_F_C;
    assert(ys_z80_step(&cpu)==Z80_BAD_WRITE);
    assert(cpu.pc==0u && cpu.fault_pc==0u &&
           cpu.ix==0xFFFFu && cpu.f==(Z80_F_Z|Z80_F_C) &&
           rom[0]==0xDDu && cpu.total_tstates==0u &&
           cpu.last_tstates==0u && cpu.steps==0u);
    setup();
    LOAD(0,0xFD,0x36,0xFF,0x77);
    cpu.iy=0x8000u;cpu.f=0xFFu;
    rom[0x7FFFu]=0x90u;
    assert(ys_z80_step(&cpu)==Z80_BAD_WRITE);
    assert(cpu.pc==0u && cpu.fault_pc==0u &&
           cpu.f==0xFFu && rom[0x7FFFu]==0x90u);
}


/* PC-24: source fixed-bank $0DB2 FD 23 INC IY. All flags unaffected;
   the control flow may later enter original bank1 collision callers,
   but this independent fixture does not claim that runtime entry. */
static void test_pc24_indexed_inc_dec_16(void) {
    setup();
    LOAD(0,0xFD,0x23,0xFD,0x2B,0xDD,0x23,0xDD,0x2B);
    cpu.iy=0xFFFFu;cpu.ix=0x0000u;
    cpu.f=0xFFu;cpu.a=0x55u;cpu.h=0xC2u;cpu.l=0x06u;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.iy==0u && cpu.ix==0u &&
           cpu.pc==2u && cpu.f==0xFFu &&
           cpu.last_tstates==10u && cpu.total_tstates==10u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.iy==0xFFFFu && cpu.f==0xFFu &&
           cpu.pc==4u && cpu.last_tstates==10u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.ix==1u && cpu.iy==0xFFFFu &&
           cpu.pc==6u && cpu.last_tstates==10u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.ix==0u && cpu.iy==0xFFFFu &&
           cpu.h==0xC2u && cpu.l==0x06u &&
           cpu.a==0x55u && cpu.f==0xFFu &&
           cpu.pc==8u && cpu.steps==4u &&
           cpu.last_tstates==10u && cpu.total_tstates==40u);
}

static void test_pc24_original_fixedbank_pointer_loop_step(void) {
    setup();
    /* Exact bytes from bank0 $0DAA onward (source cycle fragment):
       LD A,(IY+0); ADD A,D; LD (IY+0),A; INC HL; INC IY. */
    LOAD(0,0xFD,0x7E,0x00,0x82,0xFD,0x77,0x00,
           0x23,0xFD,0x23);
    cpu.iy=0xC160u;cpu.h=0xB8u;cpu.l=0x20u;
    cpu.d=3u;cpu.f=Z80_F_C|Z80_F_Z;
    assert(ys_sms_bus_write(&bus,0xC160u,0x21u));
    run(10u,5u);
    assert(cpu.a==0x24u &&
           ys_sms_bus_read(&bus,0xC160u)==0x24u &&
           cpu.iy==0xC161u && cpu.h==0xB8u && cpu.l==0x21u &&
           cpu.pc==10u && cpu.last_tstates==10u &&
           cpu.total_tstates==58u);
    /* Unmodified ROM and untouched neighboring WRAM. */
    assert(ys_sms_bus_read(&bus,0xC161u)==0u);
}


/* PC-28 original $0CC2: ED 7B 2E C0 LD SP,($C02E).
   WRAM is a controlled CPU fixture, not an original runtime snapshot.
   Source suffix $0CC6-$0CCB writes selector $02 and jumps to $0B56. */
static void test_pc28_original_button_dispatch_transition(void) {
    setup();
    LOAD(0,0xED,0x7B,0x2E,0xC0,
           0x3E,0x02,
           0x32,0x1F,0xC0,
           0xC3,0x56,0x0B);
    cpu.sp=0xDFF0u;
    cpu.a=0x5Eu;cpu.f=0xFFu;
    cpu.b=0xA7u;cpu.c=0x20u;cpu.d=0xC3u;cpu.e=0x42u;
    cpu.h=0x18u;cpu.l=0x81u;cpu.ix=0xBEEFu;cpu.iy=0xC150u;
    assert(ys_sms_bus_write(&bus,0xC02Eu,0x00u));
    assert(ys_sms_bus_write(&bus,0xC02Fu,0xC8u));
    assert(ys_sms_bus_write(&bus,0xC01Fu,0x01u));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.sp==0xC800u && cpu.pc==4u &&
           cpu.last_tstates==20u && cpu.total_tstates==20u &&
           cpu.f==0xFFu && cpu.a==0x5Eu &&
           cpu.b==0xA7u && cpu.c==0x20u &&
           cpu.d==0xC3u && cpu.e==0x42u &&
           cpu.h==0x18u && cpu.l==0x81u &&
           cpu.ix==0xBEEFu && cpu.iy==0xC150u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0x02u && cpu.pc==6u && cpu.f==0xFFu &&
           cpu.last_tstates==7u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(ys_sms_bus_read(&bus,0xC01Fu)==0x02u &&
           cpu.pc==9u && cpu.last_tstates==13u && cpu.f==0xFFu);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.pc==0x0B56u && cpu.sp==0xC800u &&
           cpu.steps==4u && cpu.total_tstates==50u &&
           cpu.f==0xFFu);
}

/* Correct low/high byte order, mapper-qualified reads, 16-bit wrap,
   and non-modifying Z80 flags when source bytes are zero or $FFFF. */
static void test_pc28_indirect_stack_pointer_bus_boundaries(void) {
    setup();
    LOAD(0,0xED,0x7B,0xFF,0xBF);
    cpu.sp=0xA001u; cpu.f=Z80_F_S|Z80_F_Z|Z80_F_C;
    rom[2u*0x4000u+0x3FFFu]=0x34u;
    assert(ys_sms_bus_write(&bus,0xC000u,0x12u));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.sp==0x1234u && cpu.pc==4u &&
           cpu.f==(Z80_F_S|Z80_F_Z|Z80_F_C) &&
           cpu.last_tstates==20u);
    setup();
    LOAD(0,0xED,0x7B,0x11,0x90);
    cpu.sp=0xFFFFu;cpu.f=0xFFu;
    rom[5u*0x4000u+0x1011u]=0xFEu;
    rom[5u*0x4000u+0x1012u]=0xCAu;
    assert(ys_sms_bus_write(&bus,0xFFFFu,5u));
    assert(bus.mapped_bank[2]==5u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.sp==0xCAFEu && cpu.f==0xFFu &&
           cpu.pc==4u && cpu.last_tstates==20u &&
           bus.mapped_bank[2]==5u);
    setup();
    LOAD(0,0xED,0x7B,0xFF,0xFF);
    cpu.f=Z80_F_C|Z80_F_N;
    rom[0]=0xEDu; /* high byte read wraps to source ROM at $0000. */
    /* $FFFF reads its WRAM mirror; mapper reset select2=2 is not a
       substitute for a real source write into that readable mirror. */
    assert(ys_sms_bus_write(&bus,0xFFFFu,2u));
    assert(ys_sms_bus_read(&bus,0xFFFFu)==2u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    /* $FFFF reads the explicitly written bank-selector RAM mirror. */
    assert(cpu.sp==0xED02u && cpu.f==(Z80_F_C|Z80_F_N) &&
           cpu.pc==4u && cpu.total_tstates==20u);
}


/* PC-29: original physical bank0 $0F8D-$0F9D: RLCA then CB 11 RL C.
   Controlled flags/WRAM inputs; no claim to original title parameters. */
static void test_pc29_original_rl_c_carry_and_flags(void) {
    static const struct {
        uint8_t old,carry,result,flags;
    } cases[]={
        {0x80u,0u,0x00u,Z80_F_Z|Z80_F_PV|Z80_F_C},
        {0x7Fu,1u,0xFFu,Z80_F_S|Z80_F_5|Z80_F_3|Z80_F_PV},
        {0x10u,0u,0x20u,Z80_F_5},
        {0x00u,0u,0x00u,Z80_F_Z|Z80_F_PV},
        {0x80u,1u,0x01u,Z80_F_C},
        {0x00u,1u,0x01u,0u}
    };
    for(size_t i=0;i<sizeof(cases)/sizeof(cases[0]);++i) {
        setup();
        LOAD(0,0xCB,0x11); /* authentic $0F8E RL C */
        cpu.c=cases[i].old;cpu.a=0x4Au;cpu.ix=0xCA00u;
        cpu.f=(uint8_t)(Z80_F_S|Z80_F_Z|Z80_F_N|Z80_F_H|
                        Z80_F_PV|Z80_F_3|Z80_F_5|
                        (cases[i].carry?Z80_F_C:0u));
        assert(ys_z80_step(&cpu)==Z80_RUNNING);
        assert(cpu.c==cases[i].result && cpu.f==cases[i].flags &&
               cpu.a==0x4Au && cpu.ix==0xCA00u &&
               cpu.pc==2u && cpu.last_tstates==8u &&
               cpu.total_tstates==8u && cpu.steps==1u);
    }
    setup();
    LOAD(0,0x07,0xCB,0x11); /* source $0F8D RLCA; $0F8E RL C */
    cpu.a=0x80u;cpu.c=0x40u;cpu.f=0u;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0x01u && (cpu.f&Z80_F_C) &&
           cpu.pc==1u && cpu.last_tstates==4u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.c==0x81u &&
           cpu.f==(Z80_F_S|Z80_F_PV) &&
           cpu.pc==3u && cpu.total_tstates==12u);
}

/* PC-29 RL covers all 8 standard CB r/(HL) fields and protects ROM. */
static void test_pc29_rl_register_and_memory(void) {
    setup();
    LOAD(0,0xCB,0x10, /* RL B */
           0xCB,0x13, /* RL E */
           0xCB,0x17);/* RL A */
    cpu.b=0x80u;cpu.e=0x12u;cpu.a=0x04u;cpu.f=Z80_F_C;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.b==0x01u && cpu.f==Z80_F_C);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.e==0x25u && cpu.f==Z80_F_5);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0x08u && cpu.f==Z80_F_3 &&
           cpu.pc==6u && cpu.total_tstates==24u);
    setup();
    LOAD(0,0xCB,0x16); /* RL (HL) in WRAM */
    cpu.h=0xC2u;cpu.l=0x00u;cpu.f=Z80_F_C|Z80_F_N;
    assert(ys_sms_bus_write(&bus,0xC200u,0x40u));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(ys_sms_bus_read(&bus,0xC200u)==0x81u &&
           cpu.f==(Z80_F_S|Z80_F_PV) && cpu.pc==2u &&
           cpu.last_tstates==15u && cpu.total_tstates==15u);
    setup();
    LOAD(0,0xCB,0x16);
    cpu.h=0x40u;cpu.l=0x20u;cpu.f=0xFFu;
    rom[0x4020u]=0x80u;
    assert(ys_z80_step(&cpu)==Z80_BAD_WRITE);
    assert(cpu.pc==0u && cpu.fault_pc==0u &&
           cpu.f==0xFFu && rom[0x4020u]==0x80u &&
           cpu.steps==0u && cpu.total_tstates==0u);
}


/* PC-30: original $0FEB RRA / $0FEC CB 19 RR C source combination.
   These are controlled register cases, not original-runtime values. */
static void test_pc30_source_rr_c_and_flags(void) {
    static const struct {
        uint8_t old,carry,result,flags;
    } cases[]={
        {0x00u,0u,0x00u,Z80_F_Z|Z80_F_PV},
        {0x01u,0u,0x00u,Z80_F_Z|Z80_F_PV|Z80_F_C},
        {0x80u,1u,0xC0u,Z80_F_S|Z80_F_PV},
        {0x01u,1u,0x80u,Z80_F_S|Z80_F_C},
        {0xFFu,0u,0x7Fu,Z80_F_5|Z80_F_3|Z80_F_C},
        {0xFFu,1u,0xFFu,Z80_F_S|Z80_F_5|Z80_F_3|Z80_F_PV|Z80_F_C}
    };
    for(size_t i=0;i<sizeof(cases)/sizeof(cases[0]);++i) {
        setup();
        LOAD(0,0xCB,0x19);
        cpu.c=cases[i].old;cpu.a=0x55u;cpu.b=0x63u;
        cpu.f=(uint8_t)(Z80_F_S|Z80_F_Z|Z80_F_H|Z80_F_N|
                        Z80_F_PV|Z80_F_3|Z80_F_5|
                        (cases[i].carry?Z80_F_C:0u));
        assert(ys_z80_step(&cpu)==Z80_RUNNING);
        assert(cpu.c==cases[i].result && cpu.f==cases[i].flags &&
               cpu.a==0x55u && cpu.b==0x63u &&
               cpu.pc==2u && cpu.last_tstates==8u &&
               cpu.total_tstates==8u && cpu.steps==1u);
    }
    setup();
    LOAD(0,0x1F,0xCB,0x19,0x47); /* original fixed-bank prefix */
    cpu.a=0x03u;cpu.c=0x02u;cpu.f=0u;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0x01u && cpu.f==Z80_F_C && cpu.pc==1u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.c==0x81u && cpu.f==(Z80_F_S|Z80_F_PV) &&
           cpu.pc==3u && cpu.last_tstates==8u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.b==0x01u && cpu.a==0x01u && cpu.c==0x81u &&
           cpu.pc==4u && cpu.total_tstates==16u);
}

/* RR r/(HL) must implement register and RAM variants, keep ROM read-only. */
static void test_pc30_rr_register_memory_and_guard(void) {
    setup();
    LOAD(0,0xCB,0x18,0xCB,0x1Bu,0xCB,0x1Fu);
    cpu.b=0x01u;cpu.e=0x04u;cpu.a=0x02u;cpu.f=Z80_F_C;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.b==0x80u && cpu.f==(Z80_F_S|Z80_F_C));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.e==0x82u && cpu.f==(Z80_F_S|Z80_F_PV));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0x01u && cpu.f==0u &&
           cpu.pc==6u && cpu.total_tstates==24u);
    setup();
    LOAD(0,0xCB,0x1E); /* RR (HL), WRAM */
    cpu.h=0xC2u;cpu.l=0x00u;cpu.f=Z80_F_C|Z80_F_N;
    assert(ys_sms_bus_write(&bus,0xC200u,0x01u));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(ys_sms_bus_read(&bus,0xC200u)==0x80u &&
           cpu.f==(Z80_F_S|Z80_F_C) &&
           cpu.pc==2u && cpu.last_tstates==15u);
    setup();
    LOAD(0,0xCB,0x1E);
    cpu.h=0x40u;cpu.l=0x20u;cpu.f=0xFFu;
    rom[0x4020u]=0x01u;
    assert(ys_z80_step(&cpu)==Z80_BAD_WRITE);
    assert(cpu.pc==0u && cpu.fault_pc==0u &&
           cpu.f==0xFFu && rom[0x4020u]==0x01u &&
           cpu.steps==0u && cpu.total_tstates==0u);
}


/* PC-31 source original physical bank8 $23F18 LD ($C1A1),DE.
   Original instruction bytes, independent controlled WRAM registers. */
static void test_pc31_original_bank8_pointer_store(void) {
    setup();
    LOAD(0,0xED,0x53,0xA1,0xC1,
           0x7E,0x32,0x2A,0xC2);
    cpu.d=0xC5u;cpu.e=0x37u;
    cpu.sp=0xDFE0u;cpu.a=0x91u;cpu.f=0xFFu;
    cpu.ix=0xC100u;cpu.iy=0xC200u;
    cpu.h=0xC1u;cpu.l=0xA1u;
    assert(ys_sms_bus_write(&bus,0xC1A1u,0x00u));
    assert(ys_sms_bus_write(&bus,0xC1A2u,0x00u));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(ys_sms_bus_read(&bus,0xC1A1u)==0x37u &&
           ys_sms_bus_read(&bus,0xC1A2u)==0xC5u &&
           cpu.pc==4u && cpu.last_tstates==20u &&
           cpu.total_tstates==20u && cpu.steps==1u &&
           cpu.d==0xC5u && cpu.e==0x37u &&
           cpu.f==0xFFu && cpu.a==0x91u &&
           cpu.sp==0xDFE0u && cpu.ix==0xC100u &&
           cpu.iy==0xC200u && cpu.h==0xC1u && cpu.l==0xA1u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0x37u && cpu.pc==5u && cpu.f==0xFFu &&
           cpu.last_tstates==7u && cpu.total_tstates==27u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(ys_sms_bus_read(&bus,0xC22Au)==0x37u &&
           cpu.pc==8u && cpu.last_tstates==13u &&
           cpu.total_tstates==40u);
}
static void test_pc31_store_de_mapper_and_rom_guard(void) {
    setup();
    LOAD(0,0xED,0x53,0xFF,0xDF); /* WRAM $DFFF,$E000 */
    cpu.d=0xABu;cpu.e=0x12u;cpu.f=Z80_F_C|Z80_F_Z;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(ys_sms_bus_read(&bus,0xDFFFu)==0x12u &&
           ys_sms_bus_read(&bus,0xE000u)==0xABu &&
           cpu.f==(Z80_F_C|Z80_F_Z) && cpu.pc==4u &&
           cpu.last_tstates==20u);
    setup();
    LOAD(0,0xED,0x53,0x00,0x80);
    cpu.d=0xABu;cpu.e=0xCDu;cpu.f=0xFFu;
    rom[2u*0x4000u]=0x44u;
    assert(ys_z80_step(&cpu)==Z80_BAD_WRITE);
    assert(cpu.pc==0u && cpu.fault_pc==0u &&
           cpu.f==0xFFu && cpu.d==0xABu && cpu.e==0xCDu &&
           rom[2u*0x4000u]==0x44u &&
           cpu.steps==0u && cpu.total_tstates==0u);
    setup();
    LOAD(0,0xED,0x53,0x20,0x90);
    cpu.d=0xFEu;cpu.e=0x42u;cpu.f=0x80u;
    assert(ys_sms_bus_write(&bus,0xFFFCu,0x08u));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(ys_sms_bus_read(&bus,0x9020u)==0x42u &&
           ys_sms_bus_read(&bus,0x9021u)==0xFEu &&
           cpu.f==0x80u && cpu.last_tstates==20u &&
           cpu.pc==4u);
}


/* PC-32: original fixed bank0 $2657/$265B LD (nn),DE/BC.
   Both writes are executed in a controlled WRAM source prefix. */
static void test_pc32_original_pointer_save_pair(void) {
    setup();
    LOAD(0,0xED,0x53,0x84,0xC1,0xED,0x43,0x10,0xC2,0xC9);
    cpu.b=0x91u;cpu.c=0x72u;
    cpu.d=0xB8u;cpu.e=0x21u;
    cpu.sp=0xC300u;cpu.a=0xCAu;cpu.f=0xFFu;
    assert(ys_sms_bus_write(&bus,0xC300u,0x00u));
    assert(ys_sms_bus_write(&bus,0xC301u,0x20u));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(ys_sms_bus_read(&bus,0xC184u)==0x21u &&
           ys_sms_bus_read(&bus,0xC185u)==0xB8u &&
           cpu.pc==4u && cpu.last_tstates==20u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(ys_sms_bus_read(&bus,0xC210u)==0x72u &&
           ys_sms_bus_read(&bus,0xC211u)==0x91u &&
           cpu.b==0x91u && cpu.c==0x72u &&
           cpu.d==0xB8u && cpu.e==0x21u &&
           cpu.a==0xCAu && cpu.f==0xFFu &&
           cpu.sp==0xC300u && cpu.pc==8u &&
           cpu.last_tstates==20u && cpu.total_tstates==40u &&
           cpu.steps==2u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.pc==0x2000u && cpu.sp==0xC302u &&
           cpu.last_tstates==10u && cpu.total_tstates==50u);
}
static void test_pc32_bank0_store_bc_boundaries(void) {
    setup();
    LOAD(0,0xED,0x43,0xFF,0xDF); /* $DFFF -> $E000 */
    cpu.b=0xEDu;cpu.c=0x17u;cpu.f=Z80_F_S|Z80_F_C;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(ys_sms_bus_read(&bus,0xDFFFu)==0x17u &&
           ys_sms_bus_read(&bus,0xE000u)==0xEDu &&
           cpu.f==(Z80_F_S|Z80_F_C) &&
           cpu.pc==4u && cpu.last_tstates==20u);
    setup();
    LOAD(0,0xED,0x43,0x01,0x80);
    cpu.b=0x11u;cpu.c=0xFFu;cpu.f=0xFFu;
    rom[2u*0x4000u+1u]=0x3Du;
    assert(ys_z80_step(&cpu)==Z80_BAD_WRITE);
    assert(cpu.pc==0u && cpu.fault_pc==0u &&
           cpu.f==0xFFu && cpu.b==0x11u && cpu.c==0xFFu &&
           rom[2u*0x4000u+1u]==0x3Du &&
           cpu.steps==0u && cpu.total_tstates==0u);
    setup();
    LOAD(0,0xED,0x43,0x20,0x90);
    cpu.b=0x3Au;cpu.c=0xD1u;cpu.f=0x00u;
    assert(ys_sms_bus_write(&bus,0xFFFCu,0x08u));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(ys_sms_bus_read(&bus,0x9020u)==0xD1u &&
           ys_sms_bus_read(&bus,0x9021u)==0x3Au &&
           cpu.f==0u && cpu.pc==4u &&
           cpu.last_tstates==20u);
}

/* PC-40 original bank0 $267E/$2693/$26C3 opcode semantics.
   ROM-free synthetic fixtures; source bytes independently SHA-gated. */
static void test_pc40_original_neg_and_flags(void) {
    static const struct {uint8_t a,result,flags;} cases[]={
        {0x00u,0x00u,0x42u},{0x01u,0xFFu,0xBBu},
        {0x80u,0x80u,0x87u},{0x7Fu,0x81u,0x93u}
    };
    for(unsigned i=0;i<sizeof(cases)/sizeof(cases[0]);++i) {
        setup();
        LOAD(0x267Eu,0xEDu,0x44u);
        cpu.pc=0x267Eu;cpu.a=cases[i].a;cpu.f=0xFFu;
        assert(ys_z80_step(&cpu)==Z80_RUNNING);
        assert(cpu.a==cases[i].result && cpu.f==cases[i].flags);
        assert(cpu.pc==0x2680u && cpu.last_tstates==8u);
        assert(cpu.steps==1u && cpu.instruction_pc==0x267Eu);
    }
}
static void test_pc40_sbc_hl_16bit_carry_overflow(void) {
    static const struct {
        uint16_t lhs,rhs,result;
        uint8_t carry,flags;
    } cases[]={
        {0x0000u,0x0000u,0x0000u,0u,0x42u},
        {0x0000u,0x0000u,0xFFFFu,1u,0xBBu},
        {0x8000u,0x0001u,0x7FFFu,0u,0x3Eu},
        {0x7FFFu,0xFFFFu,0x8000u,0u,0x87u}
    };
    for(unsigned i=0;i<sizeof(cases)/sizeof(cases[0]);++i) {
        setup();
        LOAD(0x2693u,0xEDu,0x52u); /* original SBC HL,DE */
        cpu.pc=0x2693u;
        cpu.h=(uint8_t)(cases[i].lhs>>8u);cpu.l=(uint8_t)cases[i].lhs;
        cpu.d=(uint8_t)(cases[i].rhs>>8u);cpu.e=(uint8_t)cases[i].rhs;
        cpu.f=cases[i].carry?Z80_F_C:0u;
        assert(ys_z80_step(&cpu)==Z80_RUNNING);
        assert(((uint16_t)cpu.h<<8u|cpu.l)==cases[i].result);
        assert(cpu.f==cases[i].flags);
        assert(cpu.last_tstates==15u && cpu.pc==0x2695u);
    }
    /* All four documented rr forms, including HL-HL-C and stack. */
    for(unsigned i=0;i<4u;++i) {
        setup();
        LOAD(0x100u,0xEDu,0x42u);rom[0x101u]=(uint8_t)(0x42u+0x10u*i);
        cpu.pc=0x100u;cpu.h=0x33u;cpu.l=0x44u;cpu.b=0x01u;cpu.c=0x02u;
        cpu.d=0x02u;cpu.e=0x03u;cpu.sp=0x0304u;
        assert(ys_z80_step(&cpu)==Z80_RUNNING);
        uint16_t rhs=i==0u?0x0102u:i==1u?0x0203u:
                     i==2u?0x3344u:0x0304u;
        assert(((uint16_t)cpu.h<<8u|cpu.l)==(uint16_t)(0x3344u-rhs));
        assert(cpu.last_tstates==15u);
    }
}
static void test_pc40_original_ld_bc_indirect(void) {
    setup();
    LOAD(0x26C3u,0xEDu,0x4Bu,0x10u,0xC2u);
    assert(ys_sms_bus_write(&bus,0xC210u,0xB5u));
    assert(ys_sms_bus_write(&bus,0xC211u,0x3Fu));
    cpu.pc=0x26C3u;cpu.b=0xFFu;cpu.c=0xFFu;cpu.f=0xA7u;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.pc==0x26C7u && cpu.b==0x3Fu && cpu.c==0xB5u);
    assert(cpu.f==0xA7u && cpu.last_tstates==20u);
    /* Mapped ROM read crosses 0x9000 in slot 2, never writes memory. */
    setup();
    LOAD(0x110u,0xEDu,0x4Bu,0x00u,0x90u);
    bus.mapped_bank[2]=6u;
    rom[6u*YS_ROM_BANK_BYTES+0x1000u]=0x79u;
    rom[6u*YS_ROM_BANK_BYTES+0x1001u]=0x28u;
    cpu.pc=0x110u;cpu.f=0xFFu;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.b==0x28u && cpu.c==0x79u && cpu.f==0xFFu);
    assert(cpu.last_tstates==20u);
}
static void test_pc40_original_graphics_ldd(void) {
    /* ED A8 is the Z80 backward block move used directly after LDI
       at original bank0 $2AFE and again at $2B4B. */
    setup();
    LOAD(0x2AFEu,0xEDu,0xA8u);
    assert(ys_sms_bus_write(&bus,0xC011u,0x22u));
    cpu.pc=0x2AFEu;cpu.h=0xC0u;cpu.l=0x11u;
    cpu.d=0xC0u;cpu.e=0x21u;cpu.b=0u;cpu.c=2u;
    cpu.a=0x10u;cpu.f=Z80_F_S|Z80_F_Z|Z80_F_C|Z80_F_H|Z80_F_N;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(ys_sms_bus_read(&bus,0xC021u)==0x22u);
    assert(cpu.h==0xC0u && cpu.l==0x10u);
    assert(cpu.d==0xC0u && cpu.e==0x20u);
    assert(cpu.b==0u && cpu.c==1u);
    assert(cpu.f==0xE5u); /* S/Z/C kept, PV=BC!=0, Y from A+byte */
    assert(cpu.pc==0x2B00u && cpu.last_tstates==16u);

    setup();
    LOAD(0x2B4Bu,0xEDu,0xA8u);
    assert(ys_sms_bus_write(&bus,0xC000u,0x33u));
    cpu.pc=0x2B4Bu;cpu.h=0xC0u;cpu.l=0x00u;
    cpu.d=0xC0u;cpu.e=0x00u;cpu.b=0u;cpu.c=1u;
    cpu.a=0u;cpu.f=Z80_F_C;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.h==0xBFu && cpu.l==0xFFu);
    assert(cpu.d==0xBFu && cpu.e==0xFFu);
    assert(cpu.b==0u && cpu.c==0u);
    assert(!(cpu.f & Z80_F_PV) && (cpu.f & Z80_F_C));
    assert(cpu.pc==0x2B4Du && cpu.last_tstates==16u);

    /* Fail-closed ROM writes cannot advance pointers or flags. */
    setup();
    LOAD(0x100u,0xEDu,0xA8u);
    assert(ys_sms_bus_write(&bus,0xC000u,0x44u));
    cpu.pc=0x100u;cpu.h=0xC0u;cpu.l=0u;
    cpu.d=0x40u;cpu.e=0u;cpu.b=0u;cpu.c=1u;cpu.f=0xA5u;
    assert(ys_z80_step(&cpu)==Z80_BAD_WRITE);
    assert(cpu.pc==0x100u && cpu.fault_pc==0x100u);
    assert(cpu.h==0xC0u && cpu.l==0u &&
           cpu.d==0x40u && cpu.e==0u && cpu.c==1u);
    assert(cpu.f==0xA5u && rom[0x4000u]==0u);
}
static void test_pc40_original_bank2_indexed_dec(void) {
    static const struct { uint8_t start,result,carry,flags; } cases[]={
        {0x00u,0xFFu,1u,0xBBu},
        {0x80u,0x7Fu,0u,0x3Eu},
        {0x01u,0x00u,1u,0x43u}
    };
    for(unsigned i=0;i<sizeof(cases)/sizeof(cases[0]);++i) {
        setup();
        LOAD(0x100u,0xDDu,0x35u,0x09u);
        cpu.pc=0x100u;cpu.ix=0xC000u;
        assert(ys_sms_bus_write(&bus,0xC009u,cases[i].start));
        cpu.f=cases[i].carry?Z80_F_C:0u;
        assert(ys_z80_step(&cpu)==Z80_RUNNING);
        assert(ys_sms_bus_read(&bus,0xC009u)==cases[i].result);
        assert(cpu.f==cases[i].flags);
        assert(cpu.pc==0x103u && cpu.last_tstates==23u);
        assert(cpu.ix==0xC000u);
    }
    /* Negative signed displacement with IY, no index-register change. */
    setup();
    LOAD(0x100u,0xFDu,0x35u,0xFFu);
    cpu.pc=0x100u;cpu.iy=0xC100u;
    assert(ys_sms_bus_write(&bus,0xC0FFu,0x20u));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(ys_sms_bus_read(&bus,0xC0FFu)==0x1Fu);
    assert(cpu.f==0x1Au && cpu.iy==0xC100u);
    assert(cpu.last_tstates==23u);

    /* ROM target: fail before updating memory, flags or IX/IY. */
    setup();
    LOAD(0x100u,0xDDu,0x35u,0xFFu);
    cpu.pc=0x100u;cpu.ix=0xC000u;cpu.f=0xA5u;
    assert(ys_z80_step(&cpu)==Z80_BAD_WRITE);
    assert(cpu.pc==0x100u && cpu.fault_pc==0x100u);
    assert(cpu.f==0xA5u && cpu.ix==0xC000u);
    assert(cpu.last_tstates==0u && rom[0xBFFFu]==0u);
}
static void test_pc40_original_bank1_srl(void) {
    static const struct {uint8_t initial,result,flags;} cases[]={
        {0x00u,0x00u,0x44u},{0x01u,0x00u,0x45u},
        {0x80u,0x40u,0x00u},{0xFFu,0x7Fu,0x29u}
    };
    for(unsigned i=0;i<sizeof(cases)/sizeof(cases[0]);++i) {
        setup();
        LOAD(0x100u,0xCBu,0x3Fu); /* original $61B1 SRL A */
        cpu.pc=0x100u;cpu.a=cases[i].initial;cpu.f=0xFFu;
        assert(ys_z80_step(&cpu)==Z80_RUNNING);
        assert(cpu.a==cases[i].result && cpu.f==cases[i].flags);
        assert(cpu.pc==0x102u && cpu.last_tstates==8u);
    }
    setup();
    LOAD(0x100u,0xCBu,0x3Eu); /* SRL (HL) */
    assert(ys_sms_bus_write(&bus,0xC000u,0x01u));
    cpu.pc=0x100u;cpu.h=0xC0u;cpu.l=0u;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(ys_sms_bus_read(&bus,0xC000u)==0u);
    assert(cpu.f==0x45u && cpu.last_tstates==15u);
    /* Memory-operand ROM write must fail without clobbering flags. */
    setup();
    LOAD(0x100u,0xCBu,0x3Eu);
    cpu.pc=0x100u;cpu.h=0x40u;cpu.l=0u;cpu.f=0xA5u;
    assert(ys_z80_step(&cpu)==Z80_BAD_WRITE);
    assert(cpu.pc==0x100u && cpu.fault_pc==0x100u);
    assert(cpu.f==0xA5u && cpu.last_tstates==0u);
}
static void test_pc40_original_bank1_ld_de_indirect(void) {
    setup();
    LOAD(0x100u,0xEDu,0x5Bu,0xA1u,0xC1u);
    assert(ys_sms_bus_write(&bus,0xC1A1u,0xCDu));
    assert(ys_sms_bus_write(&bus,0xC1A2u,0xABu));
    cpu.pc=0x100u;cpu.d=0u;cpu.e=0u;cpu.f=0xA5u;
    cpu.b=0x12u;cpu.c=0x34u;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.d==0xABu && cpu.e==0xCDu);
    assert(cpu.b==0x12u && cpu.c==0x34u && cpu.f==0xA5u);
    assert(cpu.pc==0x104u && cpu.last_tstates==20u);
    /* Low/high bytes cross the WRAM mirror E000 boundary naturally. */
    setup();
    LOAD(0x100u,0xEDu,0x5Bu,0xFFu,0xDFu);
    assert(ys_sms_bus_write(&bus,0xDFFFu,0xEFu));
    assert(ys_sms_bus_write(&bus,0xE000u,0xBEu));
    cpu.pc=0x100u;cpu.f=0xFFu;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.d==0xBEu && cpu.e==0xEFu);
    assert(cpu.f==0xFFu && cpu.last_tstates==20u);
}
/* PC-41 independently computed ADC/SBC arithmetic oracle. The oracle
   uses SIGNED mathematical range checks, while the implementation
   uses Z80 bit algebra; this catches PV and carry-in regressions. */
static unsigned pc41_expected_alu(unsigned lhs,unsigned rhs,
                                 unsigned carry,bool subtract) {
    unsigned result=(lhs+(subtract ? 256u-rhs-carry : rhs+carry))&255u;
    int a_signed=lhs<128u?(int)lhs:(int)lhs-256;
    int b_signed=rhs<128u?(int)rhs:(int)rhs-256;
    int signed_full=subtract ? a_signed-b_signed-(int)carry :
                               a_signed+b_signed+(int)carry;
    unsigned flags=result&(Z80_F_S|Z80_F_5|Z80_F_3);
    if(!result) flags|=Z80_F_Z;
    if(((lhs^rhs^result)&0x10u)!=0u) flags|=Z80_F_H;
    if(signed_full>127 || signed_full< -128) flags|=Z80_F_PV;
    if(subtract) flags|=Z80_F_N;
    if(subtract ? ((int)lhs-(int)rhs-(int)carry)<0 :
                  lhs+rhs+carry>255u) flags|=Z80_F_C;
    return (flags<<8u)|result;
}
static void test_pc41_alu_oracle_exhaustive(void) {
    setup();
    /* CPU itself executes original Z80 instruction 88 at bank0 $1A0A
       as well as the generalized SBC A,B. Enumerate EVERY 8-bit
       input pair and both carry-in states (262144 executions). */
    LOAD(0x100u,0x88u); /* ADC A,B */
    LOAD(0x102u,0x98u); /* SBC A,B */
    for(unsigned subtract=0u;subtract<2u;++subtract) {
        unsigned pc=subtract?0x102u:0x100u;
        for(unsigned lhs=0u;lhs<256u;++lhs)
            for(unsigned rhs=0u;rhs<256u;++rhs)
                for(unsigned carry=0u;carry<2u;++carry) {
                    cpu.pc=(uint16_t)pc;
                    cpu.status=Z80_RUNNING;
                    cpu.a=(uint8_t)lhs;cpu.b=(uint8_t)rhs;
                    cpu.f=(uint8_t)(carry?Z80_F_C:0u);
                    unsigned expected=pc41_expected_alu(
                        lhs,rhs,carry,subtract!=0u);
                    assert(ys_z80_step(&cpu)==Z80_RUNNING);
                    assert(cpu.a==(uint8_t)expected);
                    assert(cpu.f==(uint8_t)(expected>>8u));
                    assert(cpu.pc==pc+1u && cpu.last_tstates==4u);
                    assert(cpu.b==rhs);
                }
    }
    /* Also execute actual mapped (HL), immediate and A-self forms;
       these exercise bus reads and the differing timing classes. */
    const unsigned input_values[]={0u,1u,15u,16u,63u,127u,128u,129u,
                                   240u,254u,255u};
    for(unsigned subtract=0u;subtract<2u;++subtract)
        for(unsigned carry=0u;carry<2u;++carry)
            for(unsigned i=0u;i<sizeof(input_values)/sizeof(input_values[0]);++i)
                for(unsigned j=0u;j<sizeof(input_values)/sizeof(input_values[0]);++j) {
                    unsigned lhs=input_values[i],rhs=input_values[j];
                    unsigned expected=pc41_expected_alu(
                        lhs,rhs,carry,subtract!=0u);
                    uint8_t opcode=subtract?0x9Eu:0x8Eu; /* (HL) */
                    rom[0x120u]=opcode;
                    assert(ys_sms_bus_write(&bus,0xC000u,(uint8_t)rhs));
                    cpu.status=Z80_RUNNING;cpu.pc=0x120u;
                    cpu.h=0xC0u;cpu.l=0u;cpu.a=(uint8_t)lhs;
                    cpu.f=carry?Z80_F_C:0u;
                    assert(ys_z80_step(&cpu)==Z80_RUNNING);
                    assert(cpu.a==(uint8_t)expected);
                    assert(cpu.f==(uint8_t)(expected>>8u));
                    assert(cpu.last_tstates==7u && cpu.pc==0x121u);
                    assert(ys_sms_bus_read(&bus,0xC000u)==rhs);
                    /* A-self: operand must be the ORIGINAL accumulator. */
                    rom[0x122u]=subtract?0x9Fu:0x8Fu;
                    expected=pc41_expected_alu(lhs,lhs,carry,subtract!=0u);
                    cpu.status=Z80_RUNNING;cpu.pc=0x122u;
                    cpu.a=(uint8_t)lhs;cpu.f=carry?Z80_F_C:0u;
                    assert(ys_z80_step(&cpu)==Z80_RUNNING);
                    assert(cpu.a==(uint8_t)expected &&
                           cpu.f==(uint8_t)(expected>>8u));
                    assert(cpu.last_tstates==4u);
                    /* ADC A,n / SBC A,n read immediate through ROM bus. */
                    rom[0x124u]=subtract?0xDEu:0xCEu;
                    rom[0x125u]=(uint8_t)rhs;
                    expected=pc41_expected_alu(lhs,rhs,carry,subtract!=0u);
                    cpu.status=Z80_RUNNING;cpu.pc=0x124u;
                    cpu.a=(uint8_t)lhs;cpu.f=carry?Z80_F_C:0u;
                    assert(ys_z80_step(&cpu)==Z80_RUNNING);
                    assert(cpu.a==(uint8_t)expected &&
                           cpu.f==(uint8_t)(expected>>8u));
                    assert(cpu.pc==0x126u && cpu.last_tstates==7u);
                }
    puts("PASS PC-41: 262144 carry-aware ADC/SBC register vectors plus"
         " memory/self/immediate and T-state/bus guard fixtures");
}
static void test_pc41_original_indexed_set_res(void) {
    /* Exhaust all eight BIT numbers, all indexed register-result
       codes and both RES/SET families with actual Z80 instructions. */
    for(unsigned set=0u;set<2u;++set)
        for(unsigned bit=0u;bit<8u;++bit)
            for(unsigned reg_code=0u;reg_code<8u;++reg_code) {
                setup();
                uint8_t operation=(uint8_t)((set?0xC0u:0x80u)|
                                                (bit<<3u)|reg_code);
                LOAD(0x100u,0xDDu,0xCBu,0x01u,0u);
                rom[0x103u]=operation;
                cpu.pc=0x100u;cpu.ix=0xC010u;
                cpu.a=0xEEu;cpu.b=0xEDu;cpu.c=0xECu;
                cpu.d=0xEBu;cpu.e=0xEAu;
                cpu.h=0xE9u;cpu.l=0xE8u;cpu.f=0xA5u;
                assert(ys_sms_bus_write(&bus,0xC011u,0x55u));
                uint8_t mask=(uint8_t)(1u<<bit);
                uint8_t expected=set?(uint8_t)(0x55u|mask):
                                     (uint8_t)(0x55u&~mask);
                assert(ys_z80_step(&cpu)==Z80_RUNNING);
                assert(ys_sms_bus_read(&bus,0xC011u)==expected);
                assert(cpu.f==0xA5u && cpu.ix==0xC010u);
                assert(cpu.pc==0x104u && cpu.last_tstates==23u);
                uint8_t copy=reg_code==0u?cpu.b:
                             reg_code==1u?cpu.c:
                             reg_code==2u?cpu.d:
                             reg_code==3u?cpu.e:
                             reg_code==4u?cpu.h:
                             reg_code==5u?cpu.l:cpu.a;
                if(reg_code!=6u) assert(copy==expected);
                else assert(cpu.a==0xEEu && cpu.b==0xEDu &&
                            cpu.c==0xECu && cpu.h==0xE9u);
            }
    /* Original $1AC4 DD CB 01 C6: SET 0,(IX+1); flags unchanged. */
    setup();
    LOAD(0x1AC4u,0xDDu,0xCBu,0x01u,0xC6u);
    cpu.pc=0x1AC4u;cpu.ix=0xC000u;cpu.f=0xD7u;
    assert(ys_sms_bus_write(&bus,0xC001u,0xA0u));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(ys_sms_bus_read(&bus,0xC001u)==0xA1u);
    assert(cpu.f==0xD7u && cpu.pc==0x1AC8u);
    assert(cpu.last_tstates==23u);
    /* FD CB FF BF = RES 7,(IY-1),A: signed d, copies to A. */
    setup();
    LOAD(0x100u,0xFDu,0xCBu,0xFFu,0xBFu);
    cpu.pc=0x100u;cpu.iy=0xC012u;cpu.f=0xE7u;cpu.a=0xFFu;
    assert(ys_sms_bus_write(&bus,0xC011u,0xE5u));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(ys_sms_bus_read(&bus,0xC011u)==0x65u);
    assert(cpu.a==0x65u && cpu.f==0xE7u && cpu.iy==0xC012u);
    assert(cpu.last_tstates==23u);
    /* Any DD/FD CB d BIT has 20 T, not 23, even with low register
       opcode bits set; do not copy a BIT result to that register. */
    setup();
    LOAD(0x100u,0xFDu,0xCBu,0xFFu,0x7Fu); /* BIT 7,(IY-1),A */
    cpu.pc=0x100u;cpu.iy=0xC012u;cpu.a=0xA5u;cpu.f=Z80_F_C;
    assert(ys_sms_bus_write(&bus,0xC011u,0x80u));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0xA5u && cpu.last_tstates==20u);
    assert(ys_sms_bus_read(&bus,0xC011u)==0x80u);
    assert((cpu.f & Z80_F_C)!=0u && (cpu.f & Z80_F_Z)==0u);
    /* Mapper side-effect: source DD CB opcode is fetched from bank6,
       but sets mapper bank2 via WRAM $FFFF. Timing must remain 23T
       based on the opcode latched BEFORE the bank switch. */
    setup();
    const unsigned bank=6u*YS_ROM_BANK_BYTES+0x0100u;
    rom[bank]=0xDDu;rom[bank+1u]=0xCBu;
    rom[bank+2u]=0x01u;rom[bank+3u]=0xC6u;
    /* Configure mapper through the real register, so its WRAM
       mirror also contains 6. SET bit0 then maps slot2 to bank7. */
    assert(ys_sms_bus_write(&bus,0xFFFFu,6u));
    assert(bus.mapped_bank[2]==6u);
    cpu.pc=0x8100u;cpu.ix=0xFFFEu;cpu.f=0xA5u;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(bus.mapped_bank[2]==7u); /* initially 6 -> SET low bit */
    assert(cpu.f==0xA5u && cpu.pc==0x8104u &&
           cpu.last_tstates==23u && cpu.instruction_bank==6u);
    /* Refused ROM store cannot mutate target registers or flags. */
    setup();
    LOAD(0x100u,0xDDu,0xCBu,0x01u,0xC0u); /* SET 0,(IX+1),B */
    cpu.pc=0x100u;cpu.ix=0x3FFFu;cpu.b=0x77u;cpu.f=0xA5u;
    assert(ys_z80_step(&cpu)==Z80_BAD_WRITE);
    assert(cpu.pc==0x100u && cpu.fault_pc==0x100u);
    assert(cpu.b==0x77u && cpu.f==0xA5u &&
           cpu.ix==0x3FFFu && cpu.last_tstates==0u);
    assert(rom[0x4000u]==0u);
    puts("PASS PC-41: 128 indexed RES/SET bit/register combinations,"
         " original DD CB 01 C6, IY signed d, mapped timing/ROM guard");
}
static void test_pc42_refresh_ld_a_r_and_irq(void) {
    /* Real source bank0 $141A ED 5F observes the R value after
       BOTH ED and 5F M1 fetches, including bit7 preservation. */
    for(unsigned r=0;r<256u;++r) for(unsigned iff=0;iff<2u;++iff) {
        setup();
        LOAD(0x100u,0xEDu,0x5Fu);
        cpu.pc=0x100u;cpu.r=(uint8_t)r;
        cpu.iff2=iff!=0;cpu.f=Z80_F_C|Z80_F_H|Z80_F_N;
        assert(ys_z80_step(&cpu)==Z80_RUNNING);
        uint8_t expect=(uint8_t)((r&0x80u)|((r+2u)&0x7Fu));
        uint8_t flags=(uint8_t)((expect&(Z80_F_S|Z80_F_3|Z80_F_5))|
            (expect==0?Z80_F_Z:0u)|(iff?Z80_F_PV:0u)|Z80_F_C);
        assert(cpu.r==expect && cpu.a==expect && cpu.f==flags);
        assert(cpu.pc==0x102u && cpu.last_tstates==9u);
    }
    /* Normal opcodes fetch M1 once; CB/ED and DD/FD prefixed opcodes
       each fetch two; indexed DD CB d operation byte is NOT M1. */
    setup();
    LOAD(0x100u,0x00u,0xCBu,0x3Fu,0xDDu,0x21u,0x00u,0xC0u,
         0xDDu,0xCBu,0x01u,0xC6u);
    cpu.pc=0x100u;cpu.r=0xFEu;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.r==0xFFu);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.r==0x81u); /* low7 wraps from 127 through 0 to 1 */
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.ix==0xC000u && cpu.r==0x83u);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.r==0x85u && cpu.last_tstates==23u);
    assert(ys_sms_bus_read(&bus,0xC001u)==1u);
    /* HALT performs an M1 on entry and one on each subsequent 4T
       refresh; it does not increment completed Z80 instructions. */
    setup();
    LOAD(0x100u,0x76u);
    cpu.pc=0x100u;cpu.r=0x7Eu;
    assert(ys_z80_step(&cpu)==Z80_HALTED);
    assert(cpu.r==0x7Fu && cpu.steps==1u);
    ys_z80_refresh_halt(&cpu);
    assert(cpu.r==0u && cpu.steps==1u);
    ys_z80_refresh_halt(&cpu);
    assert(cpu.r==1u && cpu.steps==1u);
    cpu.status=Z80_RUNNING;
    ys_z80_refresh_halt(&cpu);
    assert(cpu.r==1u); /* non-HALT callback must not tick */
    /* IM1 acknowledge is an M1; it resets BOTH IFFs and must not
       pretend RETN restores IFF1 after a maskable interrupt. */
    setup();
    LOAD(0x0038u,0xEDu,0x45u); /* RETN */
    cpu.pc=0x1234u;cpu.sp=0xC200u;cpu.r=0x7Fu;
    cpu.iff1=true;cpu.iff2=true;cpu.interrupt_mode=1u;
    assert(ys_z80_irq(&cpu));
    assert(cpu.pc==0x0038u && cpu.r==0u);
    assert(!cpu.iff1 && !cpu.iff2 && cpu.sp==0xC1FEu);
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.pc==0x1234u && !cpu.iff1 && !cpu.iff2);
    assert(cpu.r==2u && cpu.last_tstates==14u);
    puts("PASS PC-42: 512 LD A,R combinations, bit7 wrap, prefixes,"
         " HALT M1, IM1 IFF1/IFF2 and RETN");
}
static void test_pc42_original_xor_immediate(void) {
    /* Original source $13F5 EE 80; exhaustive independent truth table
       for immediate XOR including all 8-bit accumulator and operands. */
    setup();
    LOAD(0x100u,0xEEu,0x00u);
    for(unsigned a=0;a<256u;++a)
        for(unsigned rhs=0;rhs<256u;++rhs) {
            rom[0x101u]=(uint8_t)rhs;
            cpu.status=Z80_RUNNING;cpu.pc=0x100u;
            cpu.a=(uint8_t)a;cpu.f=0xFFu;
            uint8_t result=(uint8_t)(a^rhs);
            unsigned odd=0u;
            for(unsigned bit=0u;bit<8u;++bit) odd+=(result>>bit)&1u;
            uint8_t expected=(uint8_t)((result&0xA8u)|
                (result==0u?Z80_F_Z:0u)|
                ((odd&1u)==0u?Z80_F_PV:0u));
            assert(ys_z80_step(&cpu)==Z80_RUNNING);
            assert(cpu.a==result && cpu.f==expected);
            assert(cpu.pc==0x102u && cpu.last_tstates==7u);
            assert(cpu.instruction_pc==0x100u);
        }
    setup();
    LOAD(0x13F5u,0xEEu,0x80u);
    cpu.pc=0x13F5u;cpu.a=0x80u;cpu.f=0xFFu;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0u && cpu.f==(Z80_F_Z|Z80_F_PV));
    assert(cpu.pc==0x13F7u && cpu.last_tstates==7u);
    puts("PASS PC-42: 65536 independent XOR n vectors plus original $13F5");
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
    test_pc22_indexed_hl_source_sequence();
    test_pc22_indexed_hl_iy_and_write_guards();
    test_pc23_sound_zerostore_and_psg();
    test_pc23_indexed_immediate_boundary();
    test_pc24_indexed_inc_dec_16();
    test_pc24_original_fixedbank_pointer_loop_step();
    test_pc28_original_button_dispatch_transition();
    test_pc28_indirect_stack_pointer_bus_boundaries();
    test_pc29_original_rl_c_carry_and_flags();
    test_pc29_rl_register_and_memory();
    test_pc30_source_rr_c_and_flags();
    test_pc30_rr_register_memory_and_guard();
    test_pc31_original_bank8_pointer_store();
    test_pc31_store_de_mapper_and_rom_guard();
    test_pc32_original_pointer_save_pair();
    test_pc32_bank0_store_bc_boundaries();
    test_pc40_original_neg_and_flags();
    test_pc40_sbc_hl_16bit_carry_overflow();
    test_pc40_original_ld_bc_indirect();
    test_pc40_original_graphics_ldd();
    test_pc40_original_bank2_indexed_dec();
    test_pc40_original_bank1_srl();
    test_pc40_original_bank1_ld_de_indirect();
    test_pc41_alu_oracle_exhaustive();
    test_pc41_original_indexed_set_res();
    test_pc42_refresh_ld_a_r_and_irq();
    test_pc42_original_xor_immediate();
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
