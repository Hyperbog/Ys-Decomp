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
    setup(); LOAD(0,0xFF);
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
int main(void) {
    test_extended_startup_instructions();
    test_vdp_cpu_ports_and_rst();
    boot_prefix_source_fixture();
    test_control_and_stack();
    test_flags_and_relative_jumps();
    test_ldir_and_mapper();
    test_fail_closed();
    puts("PASS: Z80 startup, flags, calls, stack, LDIR, mapper and fail-closed errors");
}
