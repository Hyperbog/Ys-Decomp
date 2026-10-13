#include "sms_runtime.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static uint8_t rom[YS_ROM_BYTES];
static YsSmsBus bus;
static YsSmsVdp vdp;
static YsZ80 cpu;
static YsSmsRuntime runtime;

static void setup(void) {
    memset(rom,0,sizeof(rom));
    assert(ys_sms_bus_init(&bus,rom,sizeof(rom)));
    ys_z80_reset(&cpu,&bus);
    ys_sms_vdp_reset(&vdp);
    ys_z80_attach_vdp(&cpu,&vdp);
    cpu.sp=0xDFF0;
}
static void program(uint16_t at, const uint8_t *bytes, size_t length) {
    assert((size_t)at+length<=0x4000u);
    memcpy(rom+at,bytes,length);
}
#define CODE(at,...) do {const uint8_t data[]={__VA_ARGS__};\
                      program(at,data,sizeof(data));}while(0)
static void measured(uint8_t cost,uint16_t target) {
    uint64_t prior=cpu.total_tstates;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(cpu.pc==target);
    if(cpu.last_tstates!=cost)
        fprintf(stderr,"at PC=$%04X cost=%u expected=%u\n",
                target,cpu.last_tstates,cost);
    assert(cpu.last_tstates==cost);
    assert(cpu.total_tstates==prior+cost);
}
static void test_reset_prefixes_memory_and_nibbles(void) {
    setup();
    CODE(0,0x3E,0x05,0x06,0x02,0x80,0x32,0x00,0xC0,
         0x21,0x00,0xC0,0x36,0x12,0x7E,0xCB,0x46,
         0xDD,0x21,0x01,0xC0,0xDD,0xCB,0xFF,0x46,0xED,0x6F);
    measured(7,2);measured(7,4);measured(4,5);measured(13,8);
    measured(10,11);measured(10,13);measured(7,14);measured(12,16);
    measured(14,20);measured(20,24);measured(18,26);
    assert(cpu.total_tstates==122u);
    assert(ys_sms_bus_read(&bus,0xC000)==0x22u);
}
static void test_conditional_branches(void) {
    setup();
    CODE(0,0x20,0x02,0x00,0x00,0x10,0xFC);
    cpu.f=0;
    measured(12,4); /* JR NZ taken. */
    cpu.b=2;
    measured(13,2); /* DJNZ taken to $0002. */
    cpu.pc=4;cpu.b=1;
    measured(8,6); /* DJNZ not taken. */
    cpu.pc=0;cpu.f=Z80_F_Z;
    measured(7,2); /* JR NZ not taken. */
    setup();
    CODE(0,0xC0,0xC4,0x08,0x00); /* RET NZ; CALL NZ,$0008 */
    CODE(8,0xC9);
    cpu.f=Z80_F_Z;
    measured(5,1); /* RET NZ not taken */
    measured(10,4); /* CALL NZ not taken */
    cpu.pc=0;cpu.f=0;
    assert(ys_sms_bus_write(&bus,0xDFF0,0x34));
    assert(ys_sms_bus_write(&bus,0xDFF1,0x12));
    measured(11,0x1234); /* RET NZ taken */
    cpu.pc=1;cpu.sp=0xDFF0;
    measured(17,8); /* CALL NZ taken */
    measured(10,4);
    setup();
    CODE(0,0xED,0xB0); /* LDIR */
    assert(ys_sms_bus_write(&bus,0xC000,0xAA));
    assert(ys_sms_bus_write(&bus,0xC001,0xBB));
    cpu.h=0xC0;cpu.l=0x00;
    cpu.d=0xC1;cpu.e=0x00;
    cpu.b=0;cpu.c=2;
    measured(21,0);
    measured(16,2);
    assert(ys_sms_bus_read(&bus,0xC100)==0xAA);
    assert(ys_sms_bus_read(&bus,0xC101)==0xBB);
}
static void test_unsupported_and_halt(void) {
    setup();
    CODE(0,0xCB,0x00);
    assert(ys_z80_step(&cpu)==Z80_UNSUPPORTED);
    assert(cpu.last_tstates==0 && cpu.total_tstates==0 &&
           cpu.fault_pc==0);
    setup();
    CODE(0,0x76);
    assert(ys_z80_step(&cpu)==Z80_HALTED);
    assert(cpu.last_tstates==4 && cpu.total_tstates==4);
}
static void test_automatic_vblank_after_ei_delay(void) {
    setup();
    CODE(0,0xFB,0x00);
    CODE(0x38,0xDB,0xBF);
    assert(ys_sms_runtime_bind(&runtime,&cpu,YS_SMS_NTSC));
    vdp.registers[1]=0x20;
    cpu.interrupt_mode=1;
    assert(ys_sms_runtime_advance(&runtime,192u*228u-4u,NULL));
    assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING); /* EI */
    assert(cpu.pc==1 && cpu.ei_delay==1 &&
           cpu.total_tstates==4 && runtime.recognized_irqs==0);
    assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING); /* NOP */
    assert(cpu.pc==0x38 && cpu.sp==0xDFEE);
    assert(runtime.recognized_irqs==1 && cpu.total_tstates==21u);
    assert(runtime.clock.line==192 && runtime.clock.tstates==17);
    assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING); /* IN status */
    assert(cpu.a==0x80u && vdp.status==0);
    assert(cpu.last_tstates==11 && cpu.total_tstates==32u);
    assert(runtime.recognized_irqs==1 && runtime.clock.tstates==28);
}
static void test_halt_waits_for_vblank(void) {
    setup();
    CODE(0,0x76); /* HALT */
    assert(ys_sms_runtime_bind(&runtime,&cpu,YS_SMS_NTSC));
    cpu.interrupt_mode=1;cpu.iff1=true;
    vdp.registers[1]=0x20;
    assert(ys_sms_runtime_step_auto(&runtime)==Z80_HALTED);
    assert(cpu.total_tstates==4u && cpu.pc==1);
    assert(ys_sms_runtime_step_auto(&runtime)==Z80_HALTED);
    assert(cpu.total_tstates==8u && cpu.pc==1);
    assert(ys_sms_runtime_advance(&runtime,192u*228u-16u,NULL));
    assert(ys_sms_runtime_step_auto(&runtime)==Z80_HALTED);
    assert(cpu.total_tstates==12u);
    assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING);
    assert(runtime.recognized_irqs==1 && cpu.pc==0x38 &&
           cpu.total_tstates==29u);
    assert(ys_sms_bus_read(&bus,0xDFEE)==1u);
}
static void test_bank0_source_isr_first_natural_vblank(void) {
    setup();
    /* Bank 0 $0038: PUSH AF / IN A,($BF) / OR A.
       The idle loop below is synthetic; only the ISR prologue matches Ys. */
    CODE(0,0xFB,0x18,0xFE); /* EI; JR $0001 */
    CODE(0x38,0xF5,0xDB,0xBF,0xB7);
    cpu.interrupt_mode=1;
    vdp.registers[1]=0x20u;
    assert(ys_sms_runtime_bind(&runtime,&cpu,YS_SMS_NTSC));
    for(unsigned i=0;i<5000u && !runtime.recognized_irqs;++i)
        assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING);
    assert(runtime.recognized_irqs==1u &&
           runtime.clock.vblank_events==1u &&
           cpu.pc==0x38u && cpu.iff1==false &&
           (vdp.status&0x80u)!=0u &&
           ys_sms_bus_read(&bus,cpu.sp)==0x01u);
    uint16_t sp=cpu.sp;
    assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING);
    assert(cpu.pc==0x39u && cpu.sp==(uint16_t)(sp-2u));
    assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING);
    assert(cpu.pc==0x3Bu && (cpu.a&0x80u)!=0u &&
           vdp.status==0u && runtime.recognized_irqs==1u);
}

int main(void) {
    test_bank0_source_isr_first_natural_vblank();
    test_reset_prefixes_memory_and_nibbles();
    test_conditional_branches();
    test_unsupported_and_halt();
    test_automatic_vblank_after_ei_delay();
    test_halt_waits_for_vblank();
    puts("PASS timed Z80: conditional/repeated cycles, EI VBlank recognition, HALT refresh and IM1 13T");
    return 0;
}
