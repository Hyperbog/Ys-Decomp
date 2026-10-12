#include "z80.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr,"usage: ys-native-trace /path/to/source-built.sms\n");
        return EXIT_FAILURE;
    }
    FILE *in = fopen(argv[1],"rb");
    if (!in) { perror("open"); return EXIT_FAILURE; }
    uint8_t *rom = malloc(YS_ROM_BYTES);
    YsSmsBus *bus = malloc(sizeof(*bus));
    if (!rom || !bus) { fclose(in); free(rom); free(bus); return EXIT_FAILURE; }
    size_t size=fread(rom,1,YS_ROM_BYTES,in);
    int trailing=fgetc(in);
    fclose(in);
    if (size!=YS_ROM_BYTES || trailing!=EOF ||
        memcmp(rom+0x7FF0,"TMR SEGA",8)!=0 ||
        !ys_sms_bus_init(bus,rom,size)) {
        fputs("invalid Ys-sized image; full SHA-256 check is performed by M10 builder\n",stderr);
        free(rom);free(bus);return EXIT_FAILURE;
    }
    YsZ80 cpu;
    ys_z80_reset(&cpu,bus);
    Z80Status status=ys_z80_run_until(&cpu,0x079A,64);
    bool ok=status==Z80_RUNNING && cpu.pc==0x079A && cpu.steps==17 &&
        cpu.a==0xFF && cpu.sp==0xDFEE && cpu.interrupt_mode==1 &&
        bus->mapper_control==0x80 && bus->mapped_bank[0]==0 &&
        bus->mapped_bank[1]==1 && bus->mapped_bank[2]==2 &&
        ys_sms_bus_read(bus,0xC001)==0xFF &&
        ys_sms_bus_read(bus,0xDE60)==0;
    printf("Ys native Z80 bootstrap: %s; steps=%llu PC=$%04X SP=$%04X ",
           ok?"PASS":"FAIL",(unsigned long long)cpu.steps,cpu.pc,cpu.sp);
    printf("A=$%02X mapper=[%u,%u,%u] (%s)\n", cpu.a,
           bus->mapped_bank[0],bus->mapped_bank[1],bus->mapped_bank[2],
           ys_z80_status_name(status));
    if (ok) puts("Stop boundary $079A: no claim of full startup, VDP, sound, or gameplay.");
    free(bus);free(rom);
    return ok ? EXIT_SUCCESS : EXIT_FAILURE;
}
