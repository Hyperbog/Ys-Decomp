#include "sms_bus.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: ys-native-probe /path/to/source-built.sms\n");
        return EXIT_FAILURE;
    }
    FILE *fp = fopen(argv[1], "rb");
    if (!fp) { perror("open ROM"); return EXIT_FAILURE; }
    uint8_t *rom = malloc(YS_ROM_BYTES);
    if (!rom) { fclose(fp); return EXIT_FAILURE; }
    const size_t n = fread(rom, 1, YS_ROM_BYTES, fp);
    const int trailing = fgetc(fp);
    fclose(fp);
    if (n != YS_ROM_BYTES || trailing != EOF || memcmp(rom + 0x7FF0, "TMR SEGA", 8)) {
        fprintf(stderr, "Expected unheadered 256 KiB SMS image with TMR SEGA header\n");
        free(rom);
        return EXIT_FAILURE;
    }
    YsSmsBus *bus = malloc(sizeof(*bus));
    if (!bus || !ys_sms_bus_init(bus, rom, n)) {
        fprintf(stderr, "Bus initialization failed\n");
        free(bus); free(rom); return EXIT_FAILURE;
    }
    printf("Ys C11 memory prototype: reset bytes %02X %02X %02X %02X\n",
           ys_sms_bus_read(bus, 0), ys_sms_bus_read(bus, 1),
           ys_sms_bus_read(bus, 2), ys_sms_bus_read(bus, 3));
    puts("Memory mapper probe completed. Use ys-native-trace for bounded CPU/VDP/audio/input execution; no native gameplay or rendering yet.");
    free(bus); free(rom);
    return EXIT_SUCCESS;
}
