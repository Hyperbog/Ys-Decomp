/* M29 original-ROM reset to FIRST CLOCK-GENERATED VBlank IM1.
   This is a strictly bounded diagnostic, not interactive gameplay.
   It never injects a VBlank or calls ys_z80_irq directly. */
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

int main(int argc,char **argv) {
    if (argc!=2) {
        fputs("usage: ys-native-timed-rom user-supplied-Ys.sms\n"
              "Stop after first source-ROM IM1 ISR acknowledges timed VBlank.\n",
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
    puts("Stop at PC=$003B before interpreting the rest of first timed ISR.");
    free(rom);free(bus);free(vdp);free(sound);
    return EXIT_SUCCESS;
}
