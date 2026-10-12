#include "z80.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int fail(const char *what, const YsZ80 *cpu) {
    fprintf(stderr,"FAIL %s: steps=%llu PC=$%04X fault=$%04X status=%s\n",
            what,(unsigned long long)cpu->steps,cpu->pc,cpu->fault_pc,
            ys_z80_status_name(cpu->status));
    return EXIT_FAILURE;
}
int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr,"usage: ys-native-trace /path/to/source-built.sms\n");
        return EXIT_FAILURE;
    }
    FILE *in=fopen(argv[1],"rb");
    if (!in) {perror("open");return EXIT_FAILURE;}
    uint8_t *rom=malloc(YS_ROM_BYTES);
    YsSmsBus *bus=malloc(sizeof(*bus));
    YsSmsVdp *vdp=malloc(sizeof(*vdp));
    if (!rom || !bus || !vdp) {
        fclose(in);free(rom);free(bus);free(vdp);return EXIT_FAILURE;
    }
    size_t size=fread(rom,1,YS_ROM_BYTES,in);
    int trailing=fgetc(in);
    fclose(in);
    if (size!=YS_ROM_BYTES || trailing!=EOF ||
        memcmp(rom+0x7FF0,"TMR SEGA",8)!=0 ||
        !ys_sms_bus_init(bus,rom,size)) {
        fputs("invalid Ys-sized image; SHA-256 check belongs to M10 builder\n",stderr);
        free(rom);free(bus);free(vdp);return EXIT_FAILURE;
    }
    YsZ80 cpu;
    ys_z80_reset(&cpu,bus);
    ys_sms_vdp_reset(vdp);
    ys_z80_attach_vdp(&cpu,vdp);
    Z80Status result=ys_z80_run_until(&cpu,0x00BB,50000);
    if (result!=Z80_RUNNING || cpu.pc!=0x00BB ||
        cpu.sp!=0xDFF0 || cpu.interrupt_mode!=1 ||
        bus->mapper_control!=0x80 || bus->mapped_bank[0]!=0 ||
        bus->mapped_bank[1]!=1 || bus->mapped_bank[2]!=2 ||
        ys_sms_bus_read(bus,0xC001)!=0xFF ||
        ys_sms_bus_read(bus,0xDE60)!=0 ||
        bus->cart_ram[0x0028]!=0 ||
        bus->cart_ram[0x1FFE]!=0 ||
        memcmp(bus->cart_ram+0x0010,rom+0x0782,0x18)!=0) {
        int code=fail("continuous reset/SRAM/WRAM trace",&cpu);
        free(rom);free(bus);free(vdp);return code;
    }
    printf("PASS continuous Ys reset: %llu instructions, PC=$%04X; SRAM signature copied, WRAM cleared, mapper restored\n",
           (unsigned long long)cpu.steps,cpu.pc);

    /* Separate, source-backed execution of the VDP initializer at $0749.
       Startup has NOT yet reached this routine through the bank-2 call. */
    ys_sms_vdp_reset(vdp);
    ys_z80_reset(&cpu,bus);
    ys_z80_attach_vdp(&cpu,vdp);
    cpu.pc=0x0749;cpu.sp=0xDFF0;
    (void)ys_sms_bus_write(bus,0xDFF0,0xAD);
    (void)ys_sms_bus_write(bus,0xDFF1,0x0B);
    result=ys_z80_run_until(&cpu,0x0BAD,1000);
    if (result!=Z80_RUNNING || cpu.pc!=0x0BAD ||
        cpu.sp!=0xDFF2 || vdp->register_writes!=11 ||
        vdp->control_writes!=24 || vdp->cram_writes!=1 ||
        vdp->vram_writes!=0 || vdp->code!=3 ||
        vdp->address!=0x0011 || vdp->cram[0x10]!=0 ||
        memcmp(vdp->registers,rom+0x0768,11)!=0 ||
        memcmp(bus->wram+0x0010,rom+0x0768,11)!=0) {
        int code=fail("separately invoked VDP initializer",&cpu);
        free(rom);free(bus);free(vdp);return code;
    }
    printf("PASS Ys VDP initializer $0749: %llu instructions, 11 registers, 24 control bytes, 1 CRAM byte\n",
           (unsigned long long)cpu.steps);
    puts("Boundaries: no full boot, video timing, interrupt delivery, renderer or gameplay yet.");
    free(rom);free(bus);free(vdp);
    return EXIT_SUCCESS;
}
