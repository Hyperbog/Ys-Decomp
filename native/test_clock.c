#include "sms_runtime.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static YsSmsClock clock_;
static YsSmsVdp vdp;
static uint8_t rom[YS_ROM_BYTES];
static YsSmsBus bus;
static YsZ80 cpu;

static void test_ntsc_vblank_boundaries(void) {
    assert(ys_sms_clock_reset(&clock_,YS_SMS_NTSC));
    ys_sms_vdp_reset(&vdp);
    assert(ys_sms_clock_tstates_per_frame(&clock_)==59736u);
    assert(ys_sms_clock_advance(&clock_,&vdp,
                               191u*YS_SMS_TSTATES_PER_LINE + 227u));
    assert(clock_.line==191 && clock_.tstates==227 && vdp.status==0);
    assert(ys_sms_clock_advance(&clock_,&vdp,1));
    assert(clock_.line==192 && clock_.tstates==0);
    assert(clock_.vblank_events==1 && vdp.status==0x80u);
    assert(!ys_sms_clock_vblank_irq(&clock_,&vdp));
    vdp.registers[1]=0x20u;
    assert(ys_sms_clock_vblank_irq(&clock_,&vdp));
    assert(ys_sms_clock_advance(&clock_,&vdp,70u*228u));
    assert(clock_.line==0 && clock_.frames==1);
    assert(clock_.vblank_events==1 && (vdp.status&0x80u));
    assert(ys_sms_clock_advance(&clock_,&vdp,2u*59736u));
    assert(clock_.frames==3 && clock_.vblank_events==3);
    uint8_t status=0;
    assert(ys_sms_vdp_read(&vdp,0xBF,&status));
    assert(status==0x80u && vdp.status==0);
    assert(!ys_sms_clock_vblank_irq(&clock_,&vdp));
}

static void test_pal_and_validation(void) {
    assert(ys_sms_clock_reset(&clock_,YS_SMS_PAL));
    ys_sms_vdp_reset(&vdp);
    assert(ys_sms_clock_tstates_per_frame(&clock_)==71364u);
    assert(ys_sms_clock_advance(&clock_,&vdp,262u*228u));
    assert(clock_.line==262 && clock_.frames==0 &&
           clock_.vblank_events==1);
    assert(ys_sms_clock_advance(&clock_,&vdp,51u*228u));
    assert(clock_.line==0 && clock_.frames==1);
    assert(!ys_sms_clock_reset(&clock_,(YsSmsRegion)2));
    assert(!ys_sms_clock_reset(NULL,YS_SMS_NTSC));
    assert(!ys_sms_clock_advance(NULL,&vdp,1));
    assert(!ys_sms_clock_advance(&clock_,NULL,1));
    assert(!ys_sms_clock_vblank_irq(NULL,&vdp));
}

static void test_cpu_irq_event_and_status_acknowledgment(void) {
    memset(rom,0,sizeof(rom));
    assert(ys_sms_bus_init(&bus,rom,sizeof(rom)));
    ys_sms_vdp_reset(&vdp);
    ys_z80_reset(&cpu,&bus);
    ys_z80_attach_vdp(&cpu,&vdp);
    cpu.interrupt_mode=1;
    cpu.sp=0xDFF0;
    rom[0]=0xFB; /* EI */
    rom[1]=0x00; /* next instruction delays IRQ recognition */
    rom[0x38]=0xDB;rom[0x39]=0xBF; /* IN A,($BF): acknowledge */
    YsSmsRuntime runtime;
    assert(!ys_sms_runtime_bind(&runtime,&cpu,(YsSmsRegion)2));
    assert(ys_sms_runtime_bind(&runtime,&cpu,YS_SMS_NTSC));
    assert(ys_sms_runtime_step(&runtime,4u)==Z80_RUNNING);
    assert(cpu.iff1 && cpu.ei_delay==1);
    vdp.registers[1]=0x20u;
    bool delivered=false;
    assert(ys_sms_runtime_advance(&runtime,192u*228u-4u,&delivered));
    assert(!delivered && runtime.recognized_irqs==0);
    assert(ys_sms_clock_vblank_irq(&runtime.clock,&vdp));
    /* Next executed instruction enables IRQ at its boundary. */
    assert(ys_sms_runtime_step(&runtime,4u)==Z80_RUNNING);
    assert(cpu.pc==0x0038 && cpu.sp==0xDFEE);
    assert(runtime.recognized_irqs==1);
    assert(ys_sms_bus_read(&bus,0xDFEE)==2);
    assert(ys_sms_runtime_step(&runtime,11u)==Z80_RUNNING);
    assert(cpu.a==0x80 && vdp.status==0);
    assert(!ys_sms_clock_vblank_irq(&runtime.clock,&vdp));
    assert(!ys_z80_irq(&cpu));
    assert(ys_sms_runtime_advance(&runtime,0,&delivered));
    assert(!delivered && runtime.recognized_irqs==1);
    assert(!ys_sms_runtime_advance(NULL,4,&delivered));
    assert(!ys_sms_runtime_bind(NULL,&cpu,YS_SMS_NTSC));
    assert(!ys_sms_runtime_bind(&runtime,NULL,YS_SMS_NTSC));
}

int main(void) {
    test_ntsc_vblank_boundaries();
    test_pal_and_validation();
    test_cpu_irq_event_and_status_acknowledgment();
    puts("PASS: NTSC/PAL scanline clock, sticky VBlank, I/O acknowledgment and deferred IM1 IRQ");
    return 0;
}
