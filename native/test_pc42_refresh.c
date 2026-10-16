#include "sms_runtime.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

/* ROM-independent Z80 refresh/IRQ fixtures; no source ROM is included. */
static uint8_t rom[YS_ROM_BYTES];
static YsSmsBus bus;
static YsZ80 cpu;
static YsSmsVdp vdp;
static YsSmsRuntime rt;
static void reset(void) {
    memset(rom,0,sizeof(rom));
    assert(ys_sms_bus_init(&bus,rom,sizeof(rom)));
    ys_z80_reset(&cpu,&bus);
    ys_sms_vdp_reset(&vdp);
    ys_z80_attach_vdp(&cpu,&vdp);
    cpu.sp=0xDFF0u;
    assert(ys_sms_runtime_bind(&rt,&cpu,YS_SMS_NTSC));
}
#define CODE(at,...) do {const uint8_t d[]={__VA_ARGS__}; \
    assert((at)+sizeof(d)<=YS_ROM_BANK_BYTES); \
    memcpy(rom+(at),d,sizeof(d));} while(0)
static void step(uint16_t next,uint8_t ticks) {
    uint64_t t=cpu.total_tstates;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.pc==next && cpu.last_tstates==ticks);
    assert(cpu.total_tstates==t+ticks);
}
static void basic_m1_and_prefix(void) {
    reset();
    CODE(0,0x3Eu,0x99u,             /* LD A,n: one M1 */
         0xCBu,0x3Fu,              /* SRL A: two M1 */
         0xDDu,0x21u,0x00u,0xC0u,  /* LD IX,nn: two M1 */
         0xDDu,0xCBu,0x01u,0xC6u,  /* SET 0,(IX+1): two M1 */
         0xEDu,0x5Fu);             /* LD A,R: two M1 */
    step(2u,7u);assert(cpu.r==1u);
    step(4u,8u);assert(cpu.r==3u);
    step(8u,14u);assert(cpu.r==5u);
    assert(ys_sms_bus_write(&bus,0xC001u,0u));
    step(12u,23u);assert(cpu.r==7u);
    assert(ys_sms_bus_read(&bus,0xC001u)==1u);
    cpu.f=Z80_F_C;cpu.iff1=false;cpu.iff2=true;
    step(14u,9u);assert(cpu.r==9u && cpu.a==9u);
    assert(cpu.f==(Z80_F_C|Z80_F_PV|Z80_F_3));
}
static void r_write_bit7_low7_wrap_and_flags(void) {
    reset();
    CODE(0,0x3Eu,0xFEu,0xEDu,0x4Fu,
         0x00u,0x00u,0xEDu,0x5Fu);
    step(2u,7u);
    step(4u,9u);assert(cpu.r==0xFEu);
    step(5u,4u);assert(cpu.r==0xFFu);
    step(6u,4u);assert(cpu.r==0x80u);
    cpu.iff2=false;cpu.f=0xFFu;
    step(8u,9u);
    assert(cpu.r==0x82u && cpu.a==0x82u);
    assert(cpu.f==(Z80_F_S|Z80_F_C));
    /* R7 remains 1 across multiple wrapping low-seven increments. */
    for(unsigned i=0;i<256u;++i){
        cpu.pc=4u;cpu.status=Z80_RUNNING;
        step(5u,4u);
        assert(cpu.r&0x80u);
    }
    /* LD A,I preserves carry, copies IFF2, and leaves R as M1 count. */
    reset();
    CODE(0,0x3Eu,0x28u,0xEDu,0x47u,0xEDu,0x57u);
    step(2u,7u);step(4u,9u);assert(cpu.i==0x28u && cpu.r==3u);
    cpu.iff2=true;cpu.f=Z80_F_C;
    step(6u,9u);
    assert(cpu.r==5u && cpu.a==0x28u);
    assert(cpu.f==(Z80_F_5|Z80_F_3|Z80_F_PV|Z80_F_C));
}
static void irq_halt_refresh_and_fail_closed(void) {
    reset();
    CODE(0,0x76u); /* HALT opcode */
    cpu.iff1=cpu.iff2=true;cpu.interrupt_mode=1u;
    assert(ys_sms_runtime_step_auto(&rt)==Z80_HALTED);
    assert(cpu.pc==1u && cpu.r==1u && cpu.last_tstates==4u);
    assert(ys_sms_runtime_step_auto(&rt)==Z80_HALTED);
    assert(cpu.pc==1u && cpu.r==2u);
    assert(ys_sms_runtime_step_auto(&rt)==Z80_HALTED);
    assert(cpu.r==3u && cpu.total_tstates==12u);
    assert(ys_z80_irq(&cpu));
    assert(cpu.r==4u && cpu.pc==0x0038u &&
           !cpu.iff1 && !cpu.iff2 &&
           cpu.sp==0xDFEEu &&
           ys_sms_bus_read(&bus,0xDFEEu)==1u);
    /* A previously latched IFF2=1 is NOT retained by IM1. */
    CODE(0x0038u,0xEDu,0x5Fu);
    cpu.f=Z80_F_C;
    step(0x003Au,9u);
    assert(cpu.r==6u && cpu.a==6u && cpu.f==Z80_F_C);
    assert(!ys_z80_irq(&cpu));
    /* An invalid IM1 stack push cannot acknowledge IRQ or increment R. */
    reset();
    cpu.interrupt_mode=1u;cpu.iff1=cpu.iff2=true;
    cpu.sp=0x2002u;cpu.r=0x7Fu;
    assert(!ys_z80_irq(&cpu));
    assert(cpu.r==0x7Fu && cpu.iff1 && cpu.iff2);
    assert(cpu.pc==0u && cpu.fault_pc==0u);
}
static void interrupt_delay_and_repeat_r(void) {
    reset();
    CODE(0,0xFBu,0x00u,0xEDu,0xB0u);
    assert(ys_sms_bus_write(&bus,0xC000u,0xABu));
    cpu.interrupt_mode=1u;cpu.h=0xC0u;cpu.l=0u;
    cpu.d=0xC0u;cpu.e=0x10u;cpu.b=0u;cpu.c=2u;
    step(1u,4u);
    assert(cpu.iff1 && cpu.iff2 && cpu.ei_delay==1u && cpu.r==1u);
    assert(!ys_z80_irq(&cpu));
    step(2u,4u);
    assert(cpu.ei_delay==0u && cpu.r==2u);
    step(2u,21u);
    assert(cpu.r==4u);
    assert(ys_sms_bus_read(&bus,0xC010u)==0xABu);
    step(4u,16u);
    assert(cpu.r==6u && cpu.b==0u && cpu.c==0u);
    assert(ys_z80_irq(&cpu));
    assert(cpu.r==7u && !cpu.iff1 && !cpu.iff2);
}
static void xor_immediate_all_input_flags(void) {
    reset();
    CODE(0x100u,0xEEu,0x80u);
    for(unsigned lhs=0u;lhs<256u;++lhs)
        for(unsigned imm=0u;imm<256u;++imm) {
            rom[0x101u]=(uint8_t)imm;
            cpu.pc=0x100u;
            cpu.a=(uint8_t)lhs;
            cpu.f=0xFFu; /* XOR clears carry, half-carry, subtraction */
            uint8_t prev_r=cpu.r;
            assert(ys_z80_step(&cpu)==Z80_RUNNING);
            unsigned result=lhs^imm;
            unsigned count=0u;
            for(unsigned b=0u;b<8u;++b) count+=(result>>b)&1u;
            unsigned flags=(result&(Z80_F_S|Z80_F_3|Z80_F_5)) |
                           (result==0u?Z80_F_Z:0u) |
                           ((count&1u)==0u?Z80_F_PV:0u);
            assert(cpu.a==result && cpu.f==flags);
            assert(cpu.pc==0x102u && cpu.last_tstates==7u);
            assert(cpu.r==(uint8_t)((prev_r&0x80u) |
                                    ((prev_r+1u)&0x7Fu)));
        }
    /* Authentic source $13F5 (EE 80) on bank 0, with carry set. */
    reset();
    CODE(0x13F5u,0xEEu,0x80u);
    cpu.pc=0x13F5u;cpu.a=0x0Eu;cpu.f=0xFFu;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.a==0x8Eu);
    assert(cpu.f==0x8Cu); /* S + bit 3 + even parity */
    assert(cpu.pc==0x13F7u && cpu.last_tstates==7u);
    puts("PASS PC-42: exhaustive 65536 XOR immediate values/flags,"
         " real original $13F5 and R count");
}
int main(void) {
    basic_m1_and_prefix();
    r_write_bit7_low7_wrap_and_flags();
    irq_halt_refresh_and_fail_closed();
    interrupt_delay_and_repeat_r();
    xor_immediate_all_input_flags();
    puts("PASS PC-42: real Z80 M1 refresh, two-fetch ED/CB/DDCB,"
         " HALT, IM1, IFF2, R7 preservation and LD A,R/I flags");
    return 0;
}
