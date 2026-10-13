/* M30 original-ROM reset through TWO clock-generated VBlank IM1 events,
   including legitimate immediate re-entry and a stable return to $0764.
   This is a bounded diagnostic, never interactive gameplay. No injected IRQ. */
#include "sms_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int fail(const char *message, const YsSmsRuntime *rt) {
    const YsZ80 *cpu=rt->cpu;
    fprintf(stderr,"FAIL timed source-ROM %s: steps=%llu PC=$%04X"
            " fault=$%04X SP=$%04X status=%s lastT=%u"
            " totalT=%llu line=%u hpos=%u frames=%llu"
            " VBlank=%llu IRQ=%llu VDPstatus=%02X reg1=%02X\n",
            message,(unsigned long long)cpu->steps,cpu->pc,cpu->fault_pc,
            cpu->sp,ys_z80_status_name(cpu->status),cpu->last_tstates,
            (unsigned long long)cpu->total_tstates,rt->clock.line,
            rt->clock.tstates,(unsigned long long)rt->clock.frames,
            (unsigned long long)rt->clock.vblank_events,
            (unsigned long long)rt->recognized_irqs,
            cpu->vdp->status,cpu->vdp->registers[1]);
    return EXIT_FAILURE;
}

/* Compare architectural registers, not PC, IRQ state or step counters. */
static bool same_registers(const YsZ80 *a, const YsZ80 *b) {
    return a->a==b->a && a->f==b->f &&
        a->b==b->b && a->c==b->c && a->d==b->d && a->e==b->e &&
        a->h==b->h && a->l==b->l &&
        a->a_alt==b->a_alt && a->f_alt==b->f_alt &&
        a->b_alt==b->b_alt && a->c_alt==b->c_alt &&
        a->d_alt==b->d_alt && a->e_alt==b->e_alt &&
        a->h_alt==b->h_alt && a->l_alt==b->l_alt &&
        a->ix==b->ix && a->iy==b->iy;
}

int main(int argc,char **argv) {
    if (argc!=2) {
        fputs("usage: ys-native-timed-rom user-supplied-Ys.sms\n"
              "Stop after two real timed VBlank ISRs return to source PC $0764.\n",
              stderr);
        return EXIT_FAILURE;
    }
    FILE *in=fopen(argv[1],"rb");
    if(!in) {perror("open ROM");return EXIT_FAILURE;}
    uint8_t *rom=malloc(YS_ROM_BYTES);
    YsSmsBus *bus=malloc(sizeof(*bus));
    YsSmsVdp *vdp=malloc(sizeof(*vdp));
    YsSmsSound *sound=malloc(sizeof(*sound));
    if(!rom || !bus || !vdp || !sound) {
        fclose(in);free(rom);free(bus);free(vdp);free(sound);
        return EXIT_FAILURE;
    }
    size_t size=fread(rom,1,YS_ROM_BYTES,in);
    int extra=fgetc(in);
    fclose(in);
    if(size!=YS_ROM_BYTES || extra!=EOF ||
       memcmp(rom+0x7FF0,"TMR SEGA",8)!=0 ||
       !ys_sms_bus_init(bus,rom,size)) {
        fputs("invalid ROM size or SMS header; this tool does not ship ROMs\n",stderr);
        free(rom);free(bus);free(vdp);free(sound);
        return EXIT_FAILURE;
    }
    ys_sms_vdp_reset(vdp);
    ys_sms_sound_reset(sound);
    YsSmsInput input;
    ys_sms_input_reset(&input);
    YsZ80 cpu;
    ys_z80_reset(&cpu,bus);
    ys_z80_attach_vdp(&cpu,vdp);
    ys_z80_attach_sound(&cpu,sound);
    ys_z80_attach_input(&cpu,&input);
    YsSmsRuntime runtime;
    if(!ys_sms_runtime_bind(&runtime,&cpu,YS_SMS_NTSC)) {
        free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
    }
    unsigned long iterations=0;
    while(runtime.recognized_irqs==0u && iterations<1000000ul) {
        Z80Status status=ys_sms_runtime_step_auto(&runtime);
        if(status!=Z80_RUNNING && status!=Z80_HALTED) {
            int result=fail("CPU stopped before first automatic IRQ",&runtime);
            free(rom);free(bus);free(vdp);free(sound);return result;
        }
        ++iterations;
    }
    if(runtime.recognized_irqs!=1u || cpu.pc!=0x0038u ||
       cpu.interrupt_mode!=1u || cpu.iff1 ||
       runtime.clock.vblank_events==0u ||
       (vdp->status&0x80u)==0u ||
       (vdp->registers[1]&0x20u)==0u ||
       cpu.total_tstates<YS_SMS_VISIBLE_LINES*YS_SMS_TSTATES_PER_LINE ||
       cpu.sp<0xC000u || cpu.sp>0xFFFDu) {
        int result=fail("first real timed VBlank IRQ not at source vector",&runtime);
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    const YsZ80 interrupted=cpu;
    const uint8_t control_before=bus->mapper_control;
    const uint8_t slot2_before=bus->mapped_bank[2];
    uint16_t saved=(uint16_t)((uint16_t)ys_sms_bus_read(bus,cpu.sp) |
                     ((uint16_t)ys_sms_bus_read(bus,(uint16_t)(cpu.sp+1u))<<8));
    /* At $0038 the source code PUSH AF precedes IN A,($BF). Run it,
       then verify the actual status-port read consumes the VBlank bit. */
    if(ys_sms_runtime_step_auto(&runtime)!=Z80_RUNNING ||
       cpu.pc!=0x0039u ||
       ys_sms_runtime_step_auto(&runtime)!=Z80_RUNNING ||
       cpu.pc!=0x003Bu ||
       (cpu.a&0x80u)==0u || (vdp->status&0x80u)!=0u ||
       runtime.recognized_irqs!=1u) {
        int result=fail("real $0038 ISR failed to acknowledge VBlank",&runtime);
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    printf("PASS timed actual Ys reset to first IM1: instructions=%llu"
           " T-states=%llu VBlank=%llu IRQ=%llu savedPC=$%04X"
           " PC=$%04X SP=$%04X\n",
           (unsigned long long)cpu.steps,
           (unsigned long long)cpu.total_tstates,
           (unsigned long long)runtime.clock.vblank_events,
           (unsigned long long)runtime.recognized_irqs,
           saved,cpu.pc,cpu.sp);
    puts("No injected IRQ; source ISR status acknowledgment verified.");
    puts("M29 timed ISR status acknowledgment at PC=$003B verified.");
    /* M30: continue this SAME clock-generated interrupt through the
       source zero-state branch $0102->$0148, the real bank-2 $8000
       sound update and the register/mapper restore at $0194-$01AB.
       No injection, timing reset, stack patch or artificial return. */
    unsigned long handler_steps=0;
    while(cpu.pc!=saved && handler_steps<4000ul &&
          runtime.recognized_irqs==1u) {
        Z80Status status=ys_sms_runtime_step_auto(&runtime);
        if(status!=Z80_RUNNING) {
            int result=fail("first zero-state ISR stopped before return",&runtime);
            free(rom);free(bus);free(vdp);free(sound);return result;
        }
        ++handler_steps;
    }
    /* At this phase of cold boot, a sixth VBlank becomes pending *during*
       the first sound update.  The original $01AA EI / $01AB RET
       restores the interrupted $0764 context; the pending IM1 is then
       recognized immediately at the RET boundary.  Do not suppress it. */
    bool bounced=saved==0x0764u && cpu.pc==0x0038u &&
        handler_steps>20u && runtime.recognized_irqs==2u &&
        runtime.clock.vblank_events==6u &&
        cpu.sp==interrupted.sp && !cpu.iff1 &&
        cpu.iff2 && (vdp->status&0x80u)!=0u &&
        same_registers(&cpu,&interrupted) &&
        bus->mapper_control==control_before &&
        bus->mapped_bank[2]==slot2_before &&
        ys_sms_bus_read(bus,0xC021u)==0u &&
        ys_sms_bus_read(bus,0xC10Fu)==1u &&
        (uint16_t)((uint16_t)ys_sms_bus_read(bus,cpu.sp) |
           ((uint16_t)ys_sms_bus_read(bus,(uint16_t)(cpu.sp+1u))<<8))==saved;
    if(!bounced) {
        int result=fail("first ISR return and legitimate second VBlank re-entry",&runtime);
        fprintf(stderr,"  expected return=$%04X IRQ=2 VBlank=6"
                       " regs=%s mapper=%02X/%02X bank2=%u/%u C10F=%02X\n",
                saved,same_registers(&cpu,&interrupted)?"restored":"different",
                bus->mapper_control,control_before,bus->mapped_bank[2],
                slot2_before,ys_sms_bus_read(bus,0xC10Fu));
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    printf("PASS natural second VBlank re-entry after $01AB RET:"
           " PC=$0038 savedPC=$%04X VBlank=%llu IRQ=%llu"
           " handler_steps=%lu\n",saved,
           (unsigned long long)runtime.clock.vblank_events,
           (unsigned long long)runtime.recognized_irqs,handler_steps);

    /* The sixth VBlank is cleared by the next genuine ISR read. With
       no seventh VBlank pending, the second ISR can fully RET to $0764.
       This is the first stable original startup resume in the timed path. */
    unsigned long second_handler_steps=0;
    while(cpu.pc!=saved && second_handler_steps<4000ul &&
          runtime.recognized_irqs==2u) {
        Z80Status status=ys_sms_runtime_step_auto(&runtime);
        if(status!=Z80_RUNNING) {
            int result=fail("second timed ISR stopped before stable return",&runtime);
            free(rom);free(bus);free(vdp);free(sound);return result;
        }
        ++second_handler_steps;
    }
    bool registers_restored=same_registers(&cpu,&interrupted);
    bool returned=bounced && registers_restored &&
        cpu.pc==saved && second_handler_steps>20u &&
        cpu.sp==(uint16_t)(interrupted.sp+2u) &&
        cpu.iff1 && cpu.iff2 && cpu.ei_delay==0u &&
        bus->mapper_control==control_before &&
        bus->mapped_bank[2]==slot2_before &&
        ys_sms_bus_read(bus,0xC021u)==0u &&
        ys_sms_bus_read(bus,0xC10Fu)==1u &&
        vdp->status==0u && runtime.recognized_irqs==2u &&
        runtime.clock.vblank_events==6u;
    if(!returned) {
        int result=fail("source zero-state ISR context/mapper restoration",&runtime);
        fprintf(stderr,"  expected PC=$%04X SP=$%04X mapper=%02X bank2=%u"
                       " AF=%02X%02X/%02X%02X C021=%02X C10F=%02X"
                       " shadow=%s steps=%lu\n",
                saved,(uint16_t)(interrupted.sp+2u),control_before,
                slot2_before,cpu.a,cpu.f,interrupted.a,interrupted.f,
                ys_sms_bus_read(bus,0xC021u),ys_sms_bus_read(bus,0xC10Fu),
                registers_restored?"restored":"different",handler_steps);
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    printf("PASS timed Ys second zero-state ISR stable return to $%04X:"
           " first_steps=%lu second_steps=%lu"
           " total_steps=%llu T-states=%llu SP=$%04X"
           " mapper=%02X bank2=%u IRQ=%llu\n",
           saved,handler_steps,second_handler_steps,
           (unsigned long long)cpu.steps,
           (unsigned long long)cpu.total_tstates,cpu.sp,
           bus->mapper_control,bus->mapped_bank[2],
           (unsigned long long)runtime.recognized_irqs);
    puts("Stop BEFORE executing $0764 POP AF; normal startup not yet resumed.");
    free(rom);free(bus);free(vdp);free(sound);
    return EXIT_SUCCESS;
}
