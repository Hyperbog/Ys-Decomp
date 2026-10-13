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

static void test_source_zero_state_isr_branch_and_mapper_save(void) {
    setup();
    /* Original bank-0 opcodes $003B-$0041 / $0102-$0107, followed by
       the unmodified zero-state prologue $0148-$0168.  $8000 itself
       is deliberately NOT executed in this synthetic fixture. */
    CODE(0x003B,0xB7,0xF2,0x40,0x05,0xC3,0x02,0x01);
    CODE(0x0102,0x3A,0x21,0xC0,0xB7,0x28,0x40);
    CODE(0x0148,0xC5,0xD5,0xE5,0x08,0xD9,
         0xF5,0xC5,0xD5,0xE5,0xDD,0xE5,0xFD,0xE5,
         0x3A,0xFF,0xFF,0xF5,0x3A,0xFC,0xFF,0xF5,
         0xAF,0x32,0xFC,0xFF,0x3E,0x02,0x32,0xFF,0xFF,
         0xCD,0x00,0x80);
    cpu.pc=0x003B;
    cpu.sp=0xDFF0;
    cpu.a=0x80u;
    cpu.f=0u;
    cpu.ix=0x1234u;cpu.iy=0x5678u;
    cpu.a_alt=0x9Au;cpu.f_alt=0x42u;
    assert(ys_sms_bus_write(&bus,0xFFFCu,0x80u));
    assert(ys_sms_bus_write(&bus,0xFFFFu,0x03u));
    assert(ys_sms_bus_write(&bus,0xC021u,0u));
    assert(ys_sms_runtime_bind(&runtime,&cpu,YS_SMS_NTSC));
    for(unsigned i=0;cpu.pc!=0x8000u && i<45u;++i)
        assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING);
    assert(cpu.pc==0x8000u && cpu.sp==0xDFD8u);
    assert(runtime.recognized_irqs==0u);
    assert(bus.mapper_control==0 && bus.mapped_bank[2]==2u);
    assert(ys_sms_bus_read(&bus,cpu.sp)==0x69u);
    assert(ys_sms_bus_read(&bus,(uint16_t)(cpu.sp+1u))==0x01u);
    assert(ys_sms_bus_read(&bus,(uint16_t)(cpu.sp+3u))==0x80u);
    assert(ys_sms_bus_read(&bus,(uint16_t)(cpu.sp+5u))==0x03u);
    assert(cpu.ix==0x1234u && cpu.iy==0x5678u);
}

static void test_pending_vblank_reenters_after_ei_ret(void) {
    setup();
    /* Original bank-0 $01AA EI / $01AB RET behavior: a VBlank that
       arrives during the ISR is pending at the RET boundary. */
    CODE(0x01AA,0xFB,0xC9);
    cpu.pc=0x01AAu;
    cpu.interrupt_mode=1;
    cpu.sp=0xDFF0u;
    assert(ys_sms_bus_write(&bus,0xDFF0u,0x64u));
    assert(ys_sms_bus_write(&bus,0xDFF1u,0x07u));
    vdp.registers[1]=0x20u;
    vdp.status=0x80u; /* The prior frame left a pending VBlank. */
    assert(ys_sms_runtime_bind(&runtime,&cpu,YS_SMS_NTSC));
    assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING);
    assert(cpu.pc==0x01ABu && cpu.ei_delay==1u &&
           runtime.recognized_irqs==0u);
    assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING);
    assert(cpu.pc==0x0038u && cpu.sp==0xDFF0u &&
           cpu.ei_delay==0u && !cpu.iff1 && cpu.iff2 &&
           runtime.recognized_irqs==1u &&
           cpu.total_tstates==27u); /* EI 4 + RET 10 + IM1 13. */
    assert(ys_sms_bus_read(&bus,cpu.sp)==0x64u);
    assert(ys_sms_bus_read(&bus,(uint16_t)(cpu.sp+1u))==0x07u);
}
static void test_source_vdp_init_returns_into_wait_bridge(void) {
    setup();
    /* Exact source $0764 POP AF / OUT ($BE),A / RET and $00C1 CALL $0BC5.
       A ROM-free fixture verifies the original return/stack edges. */
    CODE(0x0764,0xF1,0xD3,0xBE,0xC9);
    CODE(0x00C1,0xCD,0xC5,0x0B);
    cpu.pc=0x0764u;
    cpu.sp=0xDFEAu;
    assert(ys_sms_bus_write(&bus,0xDFEAu,0x40u));
    assert(ys_sms_bus_write(&bus,0xDFEBu,0x00u));
    assert(ys_sms_bus_write(&bus,0xDFECu,0xC1u));
    assert(ys_sms_bus_write(&bus,0xDFEDu,0x00u));
    assert(ys_sms_runtime_bind(&runtime,&cpu,YS_SMS_NTSC));
    assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING);
    assert(cpu.pc==0x0765u && cpu.sp==0xDFECu &&
           cpu.a==0u && cpu.f==0x40u && cpu.last_tstates==10u);
    assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING);
    assert(cpu.pc==0x0767u && cpu.last_tstates==11u);
    assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING);
    assert(cpu.pc==0x00C1u && cpu.sp==0xDFEEu && cpu.last_tstates==10u);
    assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING);
    assert(cpu.pc==0x0BC5u && cpu.sp==0xDFECu &&
           cpu.last_tstates==17u && cpu.total_tstates==48u);
    assert(ys_sms_bus_read(&bus,cpu.sp)==0xC4u &&
           ys_sms_bus_read(&bus,(uint16_t)(cpu.sp+1u))==0x00u);
}
static void test_source_busy_wait_wakes_with_natural_irq(void) {
    setup();
    /* Real bank-0 polling opcodes at $0046:
       LD A,($C021); OR A; JR NZ,$0046; RET.
       Handler is intentionally SYNTHETIC after the original $0038
       PUSH AF / $0039 IN A,($BF) prologue. Full handler is checked
       only by the gated original-ROM source trace. */
    CODE(0x0046,0x3A,0x21,0xC0,0xB7,0x20,0xFA,0xC9);
    CODE(0x0038,0xF5,0xDB,0xBF,0xAF,0x32,0x21,0xC0,0xF1,0xFB,0xC9);
    assert(ys_sms_bus_write(&bus,0xC021u,1u));
    cpu.pc=0x0046u;
    cpu.sp=0xDFF0u;
    cpu.iff1=cpu.iff2=true;
    cpu.ei_delay=1u; /* authentic $0045 EI just executed */
    cpu.interrupt_mode=1u;
    vdp.registers[1]=0x20u;
    assert(ys_sms_runtime_bind(&runtime,&cpu,YS_SMS_NTSC));
    unsigned loops=0;
    while(cpu.pc!=0x004Cu && loops<18000u) {
        assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING);
        ++loops;
    }
    assert(loops>100u && loops<18000u);
    assert(cpu.pc==0x004Cu && cpu.sp==0xDFF0u);
    assert(ys_sms_bus_read(&bus,0xC021u)==0);
    assert(runtime.recognized_irqs==1u &&
           runtime.clock.vblank_events==1u);
    assert(vdp.status==0u && cpu.iff1);
    assert(cpu.total_tstates>=192u*228u);
}

static void test_m34_palette_z80_rotates_and_subtract(void) {
    setup();
    CODE(0,0x3E,0x00,0x0E,0x03,0x91,0x07,0x0F);
    measured(7u,2u); /* LD A,0 */
    measured(7u,4u); /* LD C,3 */
    measured(4u,5u); /* SUB C; A becomes $FD with borrow. */
    assert(cpu.a==0xFDu && cpu.f==0xBBu);
    measured(4u,6u); /* RLCA $FD -> $FB; F3/F5 set, SZPV kept. */
    assert(cpu.a==0xFBu && cpu.f==0xA9u);
    measured(4u,7u); /* RRCA $FB -> $FD; carry from bit 0. */
    assert(cpu.a==0xFDu && cpu.f==0xA9u);
    setup();
    CODE(0,0x3E,0x80,0x0E,0x01,0x91,0x07,0x0F);
    measured(7u,2u); measured(7u,4u); measured(4u,5u);
    assert(cpu.a==0x7Fu && cpu.f==0x3Eu); /* overflow, no borrow */
    measured(4u,6u); /* RLCA of $7F -> $FE, no carry */
    assert(cpu.a==0xFEu && cpu.f==0x2Cu);
    measured(4u,7u); /* RRCA of $FE -> $7F, no carry */
    assert(cpu.a==0x7Fu && cpu.f==0x2Cu);
}

static void test_m34_original_palette_nibble_loop(void) {
    setup();
    /* Byte-identical bank-0 source $0B22-$0B4D copied into ROM-free
       fixture; 32 iterations of real RLD/SUB C/RRCA/RLCA.
       All actual Ys ROM bytes are verified separately in gated CI. */
    CODE(0x0B22,
         0x21,0x60,0xC1,0xF5,0x4F,0x06,0x20,
         0xED,0x6F,0xE6,0x03,0x91,0x30,0x01,0xAF,
         0xED,0x6F,0x5F,0x0F,0x0F,0xE6,0x03,
         0x91,0x30,0x01,0xAF,0x07,0x07,0x57,
         0x7B,0xE6,0x03,0x91,0x30,0x01,0xAF,
         0xB2,0xED,0x6F,0x23,0x10,0xDD,0xF1,0xC9);
    cpu.pc=0x0B22u;cpu.sp=0xDFF0u;
    cpu.a=0u;cpu.f=Z80_F_C; /* AF must be restored by final POP. */
    assert(ys_sms_bus_write(&bus,0xDFF0u,0xEFu));
    assert(ys_sms_bus_write(&bus,0xDFF1u,0x0Au));
    assert(ys_sms_bus_write(&bus,0xC15Fu,0xA5u));
    assert(ys_sms_bus_write(&bus,0xC180u,0x5Au));
    for(unsigned i=0;i<32u;++i)
        assert(ys_sms_bus_write(&bus,(uint16_t)(0xC160u+i),
                                (uint8_t)(0x53u+i*5u)));
    assert(ys_sms_runtime_bind(&runtime,&cpu,YS_SMS_NTSC));
    unsigned steps=0;
    while(cpu.pc!=0x0AEFu && steps<1300u) {
        assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING);
        ++steps;
    }
    assert(cpu.pc==0x0AEFu && steps>450u && steps<1300u);
    assert(cpu.sp==0xDFF2u && cpu.a==0u && cpu.f==Z80_F_C);
    assert(cpu.h==0xC1u && cpu.l==0x80u &&
           cpu.b==0u && cpu.c==0u);
    assert(ys_sms_bus_read(&bus,0xC15Fu)==0xA5u);
    assert(ys_sms_bus_read(&bus,0xC180u)==0x5Au);
    assert(runtime.recognized_irqs==0u && runtime.clock.vblank_events==0u);
}

static void test_m35_three_natural_palette_waits(void) {
    setup();
    /* Source $0AF4: LD B,3 / CALL $0BC5 / DJNZ $0AF6.
       Synthetic frame bridge / IRQ tail; real ROM ISR remains a
       separate, stricter gated source-dependent regression. */
    CODE(0x0AF4,0x06,0x03,0xCD,0xC5,0x0B,0x10,0xFB);
    CODE(0x0BC5,0xF5,0xC5,0x3E,0x01,0xCD,0x42,0x00,
                0xC1,0xF1,0xC9);
    CODE(0x0042,0x32,0x21,0xC0,0xFB,0x3A,0x21,0xC0,
                0xB7,0x20,0xFA,0xC9);
    CODE(0x0038,0xF5,0xDB,0xBF,0xAF,0x32,0x21,0xC0,
                0xF1,0xFB,0xC9);
    cpu.pc=0x0AF4u;cpu.sp=0xDFF0u;cpu.interrupt_mode=1u;
    vdp.registers[1]=0x20u;
    assert(ys_sms_runtime_bind(&runtime,&cpu,YS_SMS_NTSC));
    unsigned steps=0,returns=0;
    while(cpu.pc!=0x0AFBu && steps<55000u) {
        uint16_t prior=cpu.pc;
        assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING);
        ++steps;
        if(prior==0x0BCEu && cpu.pc==0x0AF9u) {
            ++returns;
            assert(ys_sms_bus_read(&bus,0xC021u)==0u);
        }
    }
    assert(cpu.pc==0x0AFBu && cpu.sp==0xDFF0u &&
           cpu.a==0 && cpu.b==0 && returns==3u);
    assert(runtime.recognized_irqs==3u &&
           runtime.clock.vblank_events==3u);
    assert(vdp.status==0u && cpu.iff1 &&
           cpu.total_tstates>163000u);
}

static void test_m36_original_bank7_rom_transfer(void) {
    setup();
    /* ROM-free fixture using byte-identical source bank-0 instructions
       $0B00-$0B0F and $0B19-$0B21. Source bank 7 at $B9C3 supplies
       16 deterministic bytes through the *real* Sega ROM mapper. */
    CODE(0x0B00,
         0x3E,0x07,0x32,0xFF,0xFF,0x21,0xC3,0xB9,
         0x11,0x70,0xC1,0x01,0x10,0x00,0x18,0x09);
    CODE(0x0B19,0xF5,0xED,0xA0,0x78,0xB1,0x20,0xFA,0xF1,0xC9);
    cpu.pc=0x0B00u;cpu.sp=0xDFF0u;cpu.a=4u;cpu.f=Z80_F_C;
    assert(ys_sms_bus_write(&bus,0xFFFCu,0x80u));
    assert(ys_sms_bus_write(&bus,0xDFF0u,0x83u));
    assert(ys_sms_bus_write(&bus,0xDFF1u,0x0Au));
    for(unsigned i=0;i<16u;++i) {
        const uint8_t expected=(uint8_t)(i*11u+0x29u);
        rom[7u*YS_ROM_BANK_BYTES+0x39C3u+i]=expected;
        assert(ys_sms_bus_write(&bus,(uint16_t)(0xC170u+i),0xFFu));
    }
    assert(ys_sms_bus_write(&bus,0xC16Fu,0xA5u));
    assert(ys_sms_bus_write(&bus,0xC180u,0x5Au));
    assert(ys_sms_runtime_bind(&runtime,&cpu,YS_SMS_NTSC));
    unsigned steps=0,ldi=0;
    while(cpu.pc!=0x0A83u && steps<160u) {
        const uint16_t prior=cpu.pc;
        assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING);
        ++steps;
        if(prior==0x0B1Au && cpu.pc==0x0B1Cu) ++ldi;
    }
    assert(cpu.pc==0x0A83u && steps>60u && steps<160u && ldi==16u);
    assert(cpu.sp==0xDFF2u && cpu.a==7u && cpu.f==Z80_F_C);
    assert(cpu.h==0xB9u && cpu.l==0xD3u &&
           cpu.d==0xC1u && cpu.e==0x80u &&
           cpu.b==0u && cpu.c==0u);
    assert(bus.mapper_control==0x80u && bus.mapped_bank[2]==7u);
    assert(ys_sms_bus_read(&bus,0xC16Fu)==0xA5u);
    assert(ys_sms_bus_read(&bus,0xC180u)==0x5Au);
    for(unsigned i=0;i<16u;++i)
        assert(ys_sms_bus_read(&bus,(uint16_t)(0xC170u+i))==
               rom[7u*YS_ROM_BANK_BYTES+0x39C3u+i]);
    assert(runtime.recognized_irqs==0u && runtime.clock.vblank_events==0u);
}

static void test_m37_original_vram_word_clear(void) {
    setup();
    /* Byte-exact original bank-0 $0A5E-$0A76 and $0028-$0030,
       $06D4-$06E7: scroll R8/R9 setup + 32 word writes.
       Synthetic ROM is used only to isolate the helper; gated
       continuous original-ROM trace supplies the real CPU context. */
    CODE(0x0A5E,
         0x11,0x00,0x88,0xEF,0x14,0xEF,0xAF,
         0x32,0x18,0xC0,0x32,0x19,0xC0,
         0x21,0x00,0x00,0x11,0x00,0x40,
         0x01,0x20,0x00,0xCD,0xD4,0x06);
    CODE(0x0028,0xF3,0x7B,0xD3,0xBF,0x7A,
         0xD3,0xBF,0xFB,0xC9);
    CODE(0x06D4,0xEF,0x79,0xB7,0x28,0x01,0x04,
         0x7D,0xD3,0xBE,0xF5,0xF1,0x7C,0xD3,0xBE,
         0x0D,0x20,0xF5,0x10,0xF3,0xC9);
    cpu.pc=0x0A5Eu;cpu.sp=0xDFF0u;
    vdp.registers[8]=0x56u;vdp.registers[9]=0x78u;
    for(unsigned i=0;i<64u;++i) vdp.vram[i]=0xACu;
    assert(ys_sms_bus_write(&bus,0xC018u,0x95u));
    assert(ys_sms_bus_write(&bus,0xC019u,0x27u));
    assert(ys_sms_runtime_bind(&runtime,&cpu,YS_SMS_NTSC));
    unsigned executed=0u;
    while(cpu.pc!=0x0A77u && executed<800u) {
        assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING);
        ++executed;
    }
    assert(cpu.pc==0x0A77u && executed>200u && executed<800u);
    assert(cpu.sp==0xDFF0u &&
           cpu.h==0u && cpu.l==0u &&
           cpu.d==0x40u && cpu.e==0u &&
           cpu.b==0u && cpu.c==0u);
    assert(vdp.registers[8]==0u && vdp.registers[9]==0u);
    assert(vdp.register_writes==2u &&
           vdp.vram_writes==64u && vdp.cram_writes==0u);
    assert(vdp.code==1u && vdp.address==0x40u);
    assert(ys_sms_bus_read(&bus,0xC018u)==0u &&
           ys_sms_bus_read(&bus,0xC019u)==0u);
    for(unsigned i=0;i<64u;++i) assert(vdp.vram[i]==0u);
    assert(runtime.recognized_irqs==0u &&
           runtime.clock.vblank_events==0u);
}

static void test_m38_source_name_table_clear_tail_return(void) {
    setup();
    /* Exact bank-0 $0A77-$0A7F JP to $06D4, source $06D4-$06E7,
       and original $0028-$0030 RST. BC=$0380 covers precisely
       896 words / 1792 VDP data bytes at VRAM $3800-$3EFF.
       The tail JP finishes at the original caller $0C4D,
       NOT the adjacent source address $0A80. */
    CODE(0x0A77,0x11,0x00,0x78,0x01,0x80,0x03,0xC3,0xD4,0x06);
    CODE(0x0028,0xF3,0x7B,0xD3,0xBF,0x7A,
         0xD3,0xBF,0xFB,0xC9);
    CODE(0x06D4,0xEF,0x79,0xB7,0x28,0x01,0x04,
         0x7D,0xD3,0xBE,0xF5,0xF1,0x7C,0xD3,0xBE,
         0x0D,0x20,0xF5,0x10,0xF3,0xC9);
    cpu.pc=0x0A77u;cpu.sp=0xDFF0u;
    cpu.h=0;cpu.l=0;
    assert(ys_sms_bus_write(&bus,0xDFF0u,0x4Du));
    assert(ys_sms_bus_write(&bus,0xDFF1u,0x0Cu));
    memset(vdp.vram+0x3800u,0xABu,0x700u);
    assert(ys_sms_runtime_bind(&runtime,&cpu,YS_SMS_NTSC));
    unsigned steps=0u,low_writes=0u,high_writes=0u;
    while(cpu.pc!=0x0C4Du && steps<12000u) {
        uint16_t prior=cpu.pc;
        assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING);
        ++steps;
        if(prior==0x06DBu) ++low_writes;
        if(prior==0x06E0u) ++high_writes;
    }
    assert(cpu.pc==0x0C4Du && steps>5000u && steps<12000u);
    assert(low_writes==896u && high_writes==896u);
    assert(vdp.vram_writes==1792u &&
           vdp.code==1u && vdp.address==0x3F00u &&
           vdp.cram_writes==0u);
    assert(cpu.sp==0xDFF2u && cpu.h==0u && cpu.l==0u &&
           cpu.d==0x78u && cpu.e==0u &&
           cpu.b==0u && cpu.c==0u);
    for(unsigned i=0;i<0x700u;++i)
        assert(vdp.vram[0x3800u+i]==0u);
    assert(runtime.recognized_irqs==0u);
}

static void test_m39_source_bank2_sound_call_handoff(void) {
    setup();
    /* Exact original Ys bank-0 opcodes $0C4D-$0C54:
       LD A,$02; LD (MapperSlot2),A; CALL $8803.
       ROM-free fixture verifies actual bank-2 mapper and CALL stack. */
    CODE(0x0C4D,0x3E,0x02,0x32,0xFF,0xFF,0xCD,0x03,0x88);
    cpu.pc=0x0C4Du;cpu.sp=0xDFF0u;
    rom[2u*YS_ROM_BANK_BYTES+0x0803u]=0xC9u;
    rom[7u*YS_ROM_BANK_BYTES+0x0803u]=0x76u;
    assert(ys_sms_bus_write(&bus,0xFFFFu,0x07u));
    assert(bus.mapped_bank[2]==7u);
    assert(ys_sms_runtime_bind(&runtime,&cpu,YS_SMS_NTSC));
    measured(7u,0x0C4Fu);
    measured(13u,0x0C52u);
    assert(bus.mapped_bank[2]==2u && bus.bank_select[2]==2u);
    measured(17u,0x8803u);
    assert(cpu.sp==0xDFEEu && cpu.a==2u);
    assert(ys_sms_bus_read(&bus,cpu.sp)==0x55u);
    assert(ys_sms_bus_read(&bus,(uint16_t)(cpu.sp+1u))==0x0Cu);
    assert(ys_sms_bus_read(&bus,0x8803u)==0xC9u);
    assert(cpu.steps==3u && cpu.total_tstates==37u);
    assert(runtime.recognized_irqs==0u &&
           runtime.clock.vblank_events==0u);
    measured(10u,0x0C55u);
    assert(cpu.sp==0xDFF0u && cpu.total_tstates==47u);
}

static void test_m40_bank2_sound_workspace_cascade(void) {
    setup();
    /* Byte-identical source-ROM bank-2 $8803-$8821. The overlapping
       LDI chain clears eleven sound command bytes without patching
       the CPU or bypassing the Sega slot-2 mapper. */
    const uint8_t source[]={
        0xE5,0xD5,0xC5,0x21,0x63,0xDE,0x11,0x64,0xDE,0x36,0x00,
        0xED,0xA0,0xED,0xA0,0xED,0xA0,0xED,0xA0,0xED,0xA0,
        0xED,0xA0,0xED,0xA0,0xED,0xA0,0xED,0xA0,0xED,0xA0
    };
    memcpy(rom+2u*YS_ROM_BANK_BYTES+0x0803u,source,sizeof(source));
    for(unsigned i=0;i<11u;++i)
        assert(ys_sms_bus_write(&bus,(uint16_t)(0xDE63u+i),0x5Au));
    assert(ys_sms_bus_write(&bus,0xFFFFu,2u));
    cpu.pc=0x8803u;cpu.sp=0xDFF0u;
    cpu.h=0x12u;cpu.l=0x34u;
    cpu.d=0x56u;cpu.e=0x78u;
    cpu.b=0u;cpu.c=11u;
    assert(ys_sms_runtime_bind(&runtime,&cpu,YS_SMS_NTSC));
    unsigned steps=0u,ldi=0u;
    while(cpu.pc!=0x8822u && steps<32u) {
        uint16_t prior=cpu.pc;
        assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING);
        ++steps;
        if(prior>=0x880Eu && prior<=0x8820u &&
           !(prior&1u) && cpu.pc==(uint16_t)(prior+2u))
            ++ldi;
    }
    assert(cpu.pc==0x8822u && steps==16u && ldi==10u);
    assert(cpu.sp==0xDFEAu && cpu.h==0xDEu && cpu.l==0x6Du &&
           cpu.d==0xDEu && cpu.e==0x6Eu &&
           cpu.b==0u && cpu.c==1u);
    for(unsigned i=0;i<11u;++i)
        assert(ys_sms_bus_read(&bus,(uint16_t)(0xDE63u+i))==0u);
    assert(bus.mapped_bank[2]==2u && runtime.recognized_irqs==0u);
    assert(runtime.clock.vblank_events==0u);
}

static void test_m41_bank5_rle_and_ed73_stack_save(void) {
    setup();
    /* Exact bank-0 startup opcodes $0C55-$0C66, including ED 73
       LD ($C02E),SP. Then the source $0C20 RLE/incrementing
       routine with independent bank-5 synthetic compressed data. */
    CODE(0x0C55,0xED,0x73,0x2E,0xC0,0x3E,0x05,
         0x32,0xFF,0xFF,0x21,0x1A,0xB6,
         0x11,0x00,0xC6,0xCD,0x20,0x0C);
    CODE(0x0C20,0x7E,0x23,0xB7,0xC8,0xF2,0x33,0x0C,
         0xE6,0x7F,0x47,0x7E,0x12,0x13,0x23,
         0x10,0xFA,0xC3,0x20,0x0C,
         0x47,0x7E,0x12,0x13,0x3C,0x10,0xFB,
         0x23,0xC3,0x20,0x0C);
    const uint8_t stream[]={0x83u,0x10u,0x20u,0x30u,
                            0x04u,0x40u,0x00u};
    memcpy(rom+5u*YS_ROM_BANK_BYTES+0x361Au,stream,sizeof(stream));
    cpu.pc=0x0C55u;
    cpu.sp=0xDFE8u;
    cpu.f=Z80_F_C;
    assert(ys_sms_bus_write(&bus,0xFFFCu,0x80u));
    measured(20u,0x0C59u);
    assert(ys_sms_bus_read(&bus,0xC02Eu)==0xE8u);
    assert(ys_sms_bus_read(&bus,0xC02Fu)==0xDFu);
    assert(cpu.f==Z80_F_C && cpu.sp==0xDFE8u);
    assert(ys_sms_runtime_bind(&runtime,&cpu,YS_SMS_NTSC));
    unsigned steps=0u;
    while(cpu.pc!=0x0C67u && steps<150u) {
        assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING);
        ++steps;
    }
    assert(cpu.pc==0x0C67u && steps<150u);
    assert(bus.mapped_bank[2]==5u &&
           cpu.sp==0xDFE8u &&
           cpu.h==0xB6u && cpu.l==0x21u &&
           cpu.d==0xC6u && cpu.e==0x07u);
    const uint8_t decoded[]={0x10u,0x20u,0x30u,
                              0x40u,0x41u,0x42u,0x43u};
    for(unsigned i=0;i<sizeof(decoded);++i)
        assert(ys_sms_bus_read(&bus,(uint16_t)(0xC600u+i))==decoded[i]);
    assert(ys_sms_bus_read(&bus,0xC02Eu)==0xE8u &&
           ys_sms_bus_read(&bus,0xC02Fu)==0xDFu);
    assert(runtime.recognized_irqs==0u &&
           runtime.clock.vblank_events==0u);
}

static void test_m42_source_two_row_staging(void) {
    setup();
    /* Byte-for-byte bank-0 opcodes at $0C67-$0C6F and
       $0BEF-$0C1F; synthetic row data exercises both literal
       and repeat commands and two interleaved destination rows.
       Real ROM source data is verified separately in gated CI. */
    CODE(0x0C67,0x21,0x00,0xC6,0x11,0x00,0xD6,
                0x0E,0x02,0xCD,0xEF,0x0B);
    CODE(0x0BEF,
         0x41,0xD5,0xC5,0x7E,0xB7,0x28,0x23,
         0xF2,0x0A,0x0C,0xE6,0x7F,0x47,0x23,
         0x7E,0x12,0x79,0x83,0x5F,0x30,0x01,
         0x14,0x10,0xF5,0x23,0x18,0xE8,
         0x47,0x23,0x7E,0x12,0x79,0x83,0x5F,
         0x30,0x01,0x14,0x10,0xF6,0x23,0x18,0xD9,
         0xC1,0xD1,0x13,0x23,0x10,0xD1,0xC9);
    const uint8_t encoded[]={0x82,0x11,0x22,0x03,0xA0,0x00,
                             0x02,0x55,0x81,0x66,0x00};
    for(unsigned i=0u;i<sizeof(encoded);++i)
        assert(ys_sms_bus_write(&bus,(uint16_t)(0xC600u+i),encoded[i]));
    for(unsigned i=0u;i<16u;++i)
        assert(ys_sms_bus_write(&bus,(uint16_t)(0xD600u+i),0xEEu));
    assert(ys_sms_bus_write(&bus,0xD5FFu,0x6Bu));
    assert(ys_sms_bus_write(&bus,0xD610u,0x4Cu));
    cpu.pc=0x0C67u;cpu.sp=0xDFF0u;
    cpu.a=0x85u;cpu.f=Z80_F_C;
    assert(ys_sms_runtime_bind(&runtime,&cpu,YS_SMS_NTSC));
    unsigned steps=0u;
    while(cpu.pc!=0x0C72u && steps<600u) {
        assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING);
        ++steps;
    }
    assert(cpu.pc==0x0C72u && steps>70u && steps<600u);
    assert(cpu.sp==0xDFF0u && cpu.b==0u && cpu.c==2u);
    assert(cpu.h==0xC6u && cpu.l==0x0Bu &&
           cpu.d==0xD6u && cpu.e==0x02u);
    const uint8_t expected[]={
        0x11,0x55,0x22,0x55,0xA0,0x66,0xA0,0xEE,
        0xA0,0xEE,0xEE,0xEE,0xEE,0xEE,0xEE,0xEE
    };
    for(unsigned i=0u;i<sizeof(expected);++i)
        assert(ys_sms_bus_read(&bus,(uint16_t)(0xD600u+i))==expected[i]);
    assert(ys_sms_bus_read(&bus,0xD5FFu)==0x6Bu);
    assert(ys_sms_bus_read(&bus,0xD610u)==0x4Cu);
    assert(runtime.recognized_irqs==0u &&
           runtime.clock.vblank_events==0u &&
           vdp.vram_writes==0u);
}

static void test_m43_source_1536_byte_vdp_outi(void) {
    setup();
    /* Byte-exact bank-0 $0C72-$0C7D and $06C1-$06D3,
       with the original RST $28 VDP-port helper.
       Real source-ROM execution is verified separately. */
    CODE(0x0C72,0x21,0x00,0xD6,0x11,0x00,0x79,
         0x01,0x00,0x06,0xCD,0xC1,0x06);
    CODE(0x06C1,0xEF,0x79,0xB7,0x28,0x01,0x04,
         0x78,0x41,0x0E,0xBE,0xED,0xA3,0x00,
         0x20,0xFA,0x3D,0x20,0xF7,0xC9);
    CODE(0x0028,0xF3,0x7B,0xD3,0xBF,0x7A,
         0xD3,0xBF,0xFB,0xC9);
    cpu.pc=0x0C72u;
    cpu.sp=0xDFF0u;
    for(unsigned i=0;i<0x600u;++i) {
        uint8_t expected=(uint8_t)((i*23u+(i>>4)+0x37u)&0xFFu);
        assert(ys_sms_bus_write(&bus,(uint16_t)(0xD600u+i),expected));
        vdp.vram[0x3900u+i]=0xAAu;
    }
    vdp.vram[0x38FFu]=0x5Au;
    vdp.vram[0x3F00u]=0xD0u;
    assert(ys_sms_runtime_bind(&runtime,&cpu,YS_SMS_NTSC));
    unsigned steps=0u,outi=0u;
    while(cpu.pc!=0x0C7Eu && steps<15000u) {
        uint16_t previous=cpu.pc;
        assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING);
        if(previous==0x06CBu) ++outi;
        ++steps;
    }
    assert(cpu.pc==0x0C7Eu && steps>4500u &&
           steps<15000u && outi==0x600u);
    assert(cpu.sp==0xDFF0u && cpu.h==0xDCu && cpu.l==0u &&
           cpu.d==0x79u && cpu.e==0u &&
           cpu.b==0u && cpu.c==0xBEu);
    assert(vdp.code==1u && vdp.address==0x3F00u &&
           vdp.vram_writes==0x600u && vdp.cram_writes==0u);
    assert(vdp.vram[0x38FFu]==0x5Au && vdp.vram[0x3F00u]==0xD0u);
    for(unsigned i=0;i<0x600u;++i)
        assert(vdp.vram[0x3900u+i]==
               ys_sms_bus_read(&bus,(uint16_t)(0xD600u+i)));
    assert(runtime.recognized_irqs==0u &&
           runtime.clock.vblank_events<=2u);
}

static void test_m44_cb_res_flags_and_cycles(void) {
    setup();
    CODE(0,0x06,0xFF,0xCB,0xB8,0x21,0x00,0xC0,0xCB,0xBE);
    assert(ys_sms_bus_write(&bus,0xC000u,0xFFu));
    cpu.f=Z80_F_S|Z80_F_Z|Z80_F_C;
    uint8_t prior=cpu.f;
    measured(7u,2u);  /* LD B,$FF */
    measured(8u,4u);  /* source $06A0: RES 7,B */
    assert(cpu.b==0x7Fu && cpu.f==prior);
    measured(10u,7u); /* LD HL,$C000 */
    measured(15u,9u); /* RES 7,(HL), flags unchanged */
    assert(ys_sms_bus_read(&bus,0xC000u)==0x7Fu && cpu.f==prior);
}

static void test_m44_interleaved_pattern_rom_fixture(void) {
    setup();
    /* Byte-identical bank-0 $0695-$06C0, and $0C7E-$0C86
       from the original Ys cartridge, with the real $0028
       VDP control-port helper. The ROM-free bank-2 fixture
       exercises repeated and literal RLE plus an empty row. */
    CODE(0x0C7E,0x21,0x00,0x80,0x11,0x00,0x40,0xCD,0x95,0x06);
    CODE(0x0695,0x0E,0x04,0x41,0xC5,0xD5,0x7E,0x23,0xB7,
         0x28,0x1C,0x47,0xCB,0xB8,0x07,0x08,0xEF,0x7E,
         0xD3,0xBE,0x08,0x30,0x01,0x23,0x08,0x79,0x83,
         0x5F,0x30,0x01,0x14,0x10,0xEF,0x08,0x38,0xE2,
         0x23,0x18,0xDF,0xD1,0x13,0xC1,0x10,0xD8,0xC9);
    CODE(0x0028,0xF3,0x7B,0xD3,0xBF,0x7A,
         0xD3,0xBF,0xFB,0xC9);
    const uint8_t packed[]={
        0x03,0x11,0x00,       /* row 0: repeat 3 at VRAM 0,4,8 */
        0x82,0x22,0x33,0x00,  /* row 1: literal 2 at 1,5 */
        0x01,0x44,0x00,       /* row 2: repeat 1 at 2 */
        0x00};                /* row 3: empty */
    memcpy(rom+2u*YS_ROM_BANK_BYTES,packed,sizeof(packed));
    for(unsigned i=0;i<16u;++i) vdp.vram[i]=0xA5u;
    cpu.pc=0x0C7Eu;cpu.sp=0xDFF0u;
    assert(ys_sms_runtime_bind(&runtime,&cpu,YS_SMS_NTSC));
    unsigned steps=0u,outputs=0u;
    while(cpu.pc!=0x0C87u && steps<1200u) {
        uint16_t prior=cpu.pc;
        assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING);
        if(prior==0x06A6u) ++outputs;
        ++steps;
    }
    assert(cpu.pc==0x0C87u && steps>80u && steps<1200u);
    assert(outputs==6u && vdp.vram_writes==6u &&
           vdp.cram_writes==0u && vdp.control_writes==12u);
    assert(cpu.sp==0xDFF0u && cpu.b==0u && cpu.c==4u &&
           cpu.h==0x80u && cpu.l==0x0Bu &&
           cpu.d==0x40u && cpu.e==4u);
    assert(vdp.vram[0]==0x11u && vdp.vram[4]==0x11u &&
           vdp.vram[8]==0x11u &&
           vdp.vram[1]==0x22u && vdp.vram[5]==0x33u &&
           vdp.vram[2]==0x44u);
    for(unsigned i=0;i<16u;++i)
        if(i!=0u && i!=1u && i!=2u && i!=4u && i!=5u && i!=8u)
            assert(vdp.vram[i]==0xA5u);
    assert(runtime.recognized_irqs==0u &&
           runtime.clock.vblank_events==0u);
}

static void test_m45_source_four_column_resource(void) {
    setup();
    /* Byte-identical source bank-0 $0C87-$0C91 and $0BEF-$0C1F.
       Synthetic ROM data exercises four columns, literals, repeats,
       an empty column and sentinel preservation. */
    CODE(0x0C87,0x21,0xD1,0xA4,0x11,0x00,0xC6,
         0x0E,0x04,0xCD,0xEF,0x0B);
    CODE(0x0BEF,
         0x41,0xD5,0xC5,0x7E,0xB7,0x28,0x23,
         0xF2,0x0A,0x0C,0xE6,0x7F,0x47,0x23,
         0x7E,0x12,0x79,0x83,0x5F,0x30,0x01,
         0x14,0x10,0xF5,0x23,0x18,0xE8,
         0x47,0x23,0x7E,0x12,0x79,0x83,0x5F,
         0x30,0x01,0x14,0x10,0xF6,0x23,0x18,0xD9,
         0xC1,0xD1,0x13,0x23,0x10,0xD1,0xC9);
    const uint8_t encoded[]={
        0x03,0x11,0x00,             /* column 0: positions 0,4,8 */
        0x82,0x22,0x33,0x00,        /* column 1: positions 1,5 */
        0x01,0x44,0x00,             /* column 2: position 2 */
        0x00                        /* column 3: empty */
    };
    memcpy(rom+2u*YS_ROM_BANK_BYTES+0x24D1u,encoded,sizeof(encoded));
    cpu.pc=0x0C87u;cpu.sp=0xDFF0u;
    for(unsigned i=0u;i<16u;++i)
        assert(ys_sms_bus_write(&bus,(uint16_t)(0xC600u+i),0xA5u));
    assert(ys_sms_bus_write(&bus,0xC5FFu,0x6Bu));
    assert(ys_sms_bus_write(&bus,0xC610u,0x4Cu));
    assert(ys_sms_runtime_bind(&runtime,&cpu,YS_SMS_NTSC));
    unsigned steps=0u;
    while(cpu.pc!=0x0C92u && steps<1000u) {
        assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING);
        ++steps;
    }
    assert(cpu.pc==0x0C92u && steps>60u && steps<1000u);
    assert(cpu.sp==0xDFF0u &&
           cpu.h==0xA4u && cpu.l==0xDCu &&
           cpu.d==0xC6u && cpu.e==4u &&
           cpu.b==0u && cpu.c==4u);
    assert(bus.mapped_bank[2]==2u && vdp.vram_writes==0u);
    assert(ys_sms_bus_read(&bus,0xC600u)==0x11u &&
           ys_sms_bus_read(&bus,0xC604u)==0x11u &&
           ys_sms_bus_read(&bus,0xC608u)==0x11u &&
           ys_sms_bus_read(&bus,0xC601u)==0x22u &&
           ys_sms_bus_read(&bus,0xC605u)==0x33u &&
           ys_sms_bus_read(&bus,0xC602u)==0x44u);
    for(unsigned i=0u;i<16u;++i)
        if(i!=0u && i!=1u && i!=2u &&
           i!=4u && i!=5u && i!=8u)
            assert(ys_sms_bus_read(&bus,(uint16_t)(0xC600u+i))==0xA5u);
    assert(ys_sms_bus_read(&bus,0xC5FFu)==0x6Bu &&
           ys_sms_bus_read(&bus,0xC610u)==0x4Cu);
    assert(runtime.recognized_irqs==0u &&
           runtime.clock.vblank_events==0u);
}


/* M46a: original bank-0 $0C92-$0C9B, immediately after M45's
   four-column resource staging. This is a synthetic execution fixture,
   not a full source-ROM runtime verification or title-screen proof. */
static void test_m46_video_setup_prefix(void) {
    setup();
    CODE(0x0C92,0x3E,0x20,0x32,0x19,0xC0,
         0x3E,0x81,0x32,0x64,0xDE);
    cpu.pc=0x0C92u;
    cpu.f=(uint8_t)(Z80_F_S|Z80_F_C);
    assert(ys_sms_bus_write(&bus,0xC018u,0x6Bu));
    assert(ys_sms_bus_write(&bus,0xC019u,0x55u));
    assert(ys_sms_bus_write(&bus,0xC01Au,0x72u));
    assert(ys_sms_bus_write(&bus,0xDE63u,0x39u));
    assert(ys_sms_bus_write(&bus,0xDE64u,0x66u));
    assert(ys_sms_bus_write(&bus,0xDE65u,0x4Cu));
    assert(ys_sms_runtime_bind(&runtime,&cpu,YS_SMS_NTSC));
    const uint16_t next_pc[]={0x0C94u,0x0C97u,0x0C99u,0x0C9Cu};
    const uint8_t cycles[]={7u,13u,7u,13u};
    for(unsigned i=0u;i<4u;++i) {
        assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING);
        assert(cpu.pc==next_pc[i] && cpu.last_tstates==cycles[i]);
    }
    assert(cpu.steps==4u && cpu.total_tstates==40u);
    assert(cpu.a==0x81u && cpu.f==(Z80_F_S|Z80_F_C));
    assert(cpu.sp==0xDFF0u && bus.mapped_bank[2]==2u);
    assert(ys_sms_bus_read(&bus,0xC018u)==0x6Bu);
    assert(ys_sms_bus_read(&bus,0xC019u)==0x20u);
    assert(ys_sms_bus_read(&bus,0xC01Au)==0x72u);
    assert(ys_sms_bus_read(&bus,0xDE63u)==0x39u);
    assert(ys_sms_bus_read(&bus,0xDE64u)==0x81u);
    assert(ys_sms_bus_read(&bus,0xDE65u)==0x4Cu);
    assert(vdp.vram_writes==0u && runtime.recognized_irqs==0u &&
           runtime.clock.vblank_events==0u);
}


/* M46b original $0C9C CALL $0AA7 to $0AB2 via $0028 RST helper.
   Synthetic source opcodes, not a replacement for ROM-backed CI. */
static void test_m46b_source_vdp_irq_gate(void) {
    setup();
    CODE(0x0C9C,0xCD,0xA7,0x0A);
    CODE(0x0AA7,0x3A,0x11,0xC0,0x5F,0x16,0x81,
         0xCB,0xEB,0xEF,0xDB,0xBF);
    CODE(0x0028,0xF3,0x7B,0xD3,0xBF,0x7A,0xD3,0xBF,
         0xFB,0xC9);
    cpu.pc=0x0C9Cu;
    cpu.f=(uint8_t)(Z80_F_Z|Z80_F_C);
    cpu.sp=0xDFF0u;
    assert(ys_sms_bus_write(&bus,0xC011u,0x80u));
    assert(ys_sms_bus_write(&bus,0xC012u,0x67u));
    vdp.registers[1]=0x80u;
    vdp.status=0x40u; /* Status read-to-clear, no pending VBlank IRQ. */
    cpu.interrupt_mode=1u;
    assert(ys_sms_runtime_bind(&runtime,&cpu,YS_SMS_NTSC));
    const uint16_t pc_seq[]={0x0AA7u,0x0AAAu,0x0AABu,0x0AADu,
                             0x0AAFu,0x0028u,0x0029u,0x002Au,
                             0x002Cu,0x002Du,0x002Fu,0x0030u,
                             0x0AB0u,0x0AB2u};
    const uint8_t cycles[]={17u,13u,4u,7u,8u,11u,4u,4u,
                            11u,4u,11u,4u,10u,11u};
    for(unsigned i=0u;i<14u;++i) {
        assert(ys_sms_runtime_step_auto(&runtime)==Z80_RUNNING);
        assert(cpu.pc==pc_seq[i] && cpu.last_tstates==cycles[i]);
    }
    assert(cpu.steps==14u && cpu.total_tstates==119u);
    assert(cpu.sp==0xDFEEu && cpu.f==(Z80_F_Z|Z80_F_C));
    assert(cpu.d==0x81u && cpu.e==0xA0u && cpu.a==0x40u);
    assert(cpu.iff1 && cpu.iff2 && cpu.ei_delay==0u);
    assert(vdp.registers[1]==0xA0u && vdp.status==0u);
    assert(vdp.control_writes==2u && vdp.register_writes==1u);
    assert(vdp.vram_writes==0u && vdp.cram_writes==0u);
    assert(bus.mapped_bank[2]==2u && runtime.recognized_irqs==0u);
    assert(runtime.clock.vblank_events==0u);
    assert(ys_sms_bus_read(&bus,0xC011u)==0x80u);
    assert(ys_sms_bus_read(&bus,0xC012u)==0x67u);
    assert(ys_sms_bus_read(&bus,0xDFEEu)==0x9Fu);
    assert(ys_sms_bus_read(&bus,0xDFEFu)==0x0Cu);
    assert(ys_sms_bus_read(&bus,0xDFECu)==0xB0u);
    assert(ys_sms_bus_read(&bus,0xDFEDu)==0x0Au);
}


static void test_m46b_cb_set_register_and_memory(void) {
    setup();
    CODE(0,0xCB,0xEB,0xCB,0xFE,0xCB,0xC6);
    cpu.e=0u;cpu.h=0xC0u;cpu.l=0x00u;
    cpu.f=(uint8_t)(Z80_F_Z|Z80_F_C);
    assert(ys_sms_bus_write(&bus,0xC000u,0u));
    assert(ys_sms_bus_write(&bus,0xC001u,0x57u));
    measured(8u,0x0002u); /* SET 5,E */
    assert(cpu.e==0x20u && cpu.f==(Z80_F_Z|Z80_F_C));
    measured(15u,0x0004u); /* SET 7,(HL) */
    assert(ys_sms_bus_read(&bus,0xC000u)==0x80u);
    measured(15u,0x0006u); /* SET 0,(HL) */
    assert(ys_sms_bus_read(&bus,0xC000u)==0x81u);
    assert(ys_sms_bus_read(&bus,0xC001u)==0x57u);
    assert(cpu.f==(Z80_F_Z|Z80_F_C) && cpu.total_tstates==38u);
}

int main(void) {
    test_m46b_cb_set_register_and_memory();
    test_m46b_source_vdp_irq_gate();
    test_m46_video_setup_prefix();
    test_m45_source_four_column_resource();
    test_m44_cb_res_flags_and_cycles();
    test_m44_interleaved_pattern_rom_fixture();
    test_m43_source_1536_byte_vdp_outi();
    test_m42_source_two_row_staging();
    test_m41_bank5_rle_and_ed73_stack_save();
    test_m40_bank2_sound_workspace_cascade();
    test_m39_source_bank2_sound_call_handoff();
    test_m38_source_name_table_clear_tail_return();
    test_m37_original_vram_word_clear();
    test_m36_original_bank7_rom_transfer();
    test_m35_three_natural_palette_waits();
    test_m34_palette_z80_rotates_and_subtract();
    test_m34_original_palette_nibble_loop();
    test_source_busy_wait_wakes_with_natural_irq();
    test_source_vdp_init_returns_into_wait_bridge();
    test_pending_vblank_reenters_after_ei_ret();
    test_source_zero_state_isr_branch_and_mapper_save();
    test_bank0_source_isr_first_natural_vblank();
    test_reset_prefixes_memory_and_nibbles();
    test_conditional_branches();
    test_unsupported_and_halt();
    test_automatic_vblank_after_ei_delay();
    test_halt_waits_for_vblank();
    puts("PASS timed Z80: conditional/repeated cycles, EI VBlank recognition, HALT refresh and IM1 13T");
    return 0;
}
