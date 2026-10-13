/* ROM-free timed-CPU and VDP-VBlank integration smoke-test executable.
   All program bytes are synthetic; this does not boot Ys. */
#include "sms_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint8_t program[YS_ROM_BYTES];
static YsSmsBus bus;
static YsSmsVdp vdp;
static YsZ80 cpu;
static YsSmsRuntime runtime;

int main(int argc,char **argv) {
    if(argc!=2 || strcmp(argv[1],"--check")!=0) {
        fputs("usage: ys-native-timing --check\n"
              "Synthetic auto-timed IM1 VBlank test, not gameplay.\n",stderr);
        return EXIT_FAILURE;
    }
    memset(program,0,sizeof(program)); /* NOP-filled, no copyrighted bytes. */
    program[0]=0xFB; /* EI */
    program[0x38]=0xDB;program[0x39]=0xBF; /* IN A,(VDP status) */
    if(!ys_sms_bus_init(&bus,program,sizeof(program))) return EXIT_FAILURE;
    ys_sms_vdp_reset(&vdp);
    ys_z80_reset(&cpu,&bus);
    ys_z80_attach_vdp(&cpu,&vdp);
    cpu.sp=0xDFF0;
    cpu.interrupt_mode=1;
    vdp.registers[1]=0x20u;
    if(!ys_sms_runtime_bind(&runtime,&cpu,YS_SMS_NTSC)) return EXIT_FAILURE;
    for(unsigned n=0;n<12000u && runtime.recognized_irqs==0u;++n) {
        if(ys_sms_runtime_step_auto(&runtime)!=Z80_RUNNING) {
            fprintf(stderr,"CPU stopped at $%04X (%s)\n",
                    cpu.pc,ys_z80_status_name(cpu.status));
            return EXIT_FAILURE;
        }
    }
    if(runtime.recognized_irqs!=1 || cpu.pc!=0x38 ||
       runtime.clock.vblank_events!=1 || cpu.total_tstates<43789u ||
       cpu.steps==0u) {
        fputs("failed to reach auto-timed VBlank\n",stderr);
        return EXIT_FAILURE;
    }
    if(ys_sms_runtime_step_auto(&runtime)!=Z80_RUNNING ||
       cpu.a!=0x80u || vdp.status!=0u || cpu.last_tstates!=11u) {
        fputs("VDP IRQ acknowledgment failed\n",stderr);
        return EXIT_FAILURE;
    }
    printf("PASS M28 synthetic timed Z80/VBlank: steps=%llu"
           " T-states=%llu IRQs=%llu line=%u PC=$%04X\n",
           (unsigned long long)cpu.steps,
           (unsigned long long)cpu.total_tstates,
           (unsigned long long)runtime.recognized_irqs,
           (unsigned)runtime.clock.line,cpu.pc);
    puts("No Ys ROM was executed; source-ROM timing/fidelity remains unverified.");
    return EXIT_SUCCESS;
}
