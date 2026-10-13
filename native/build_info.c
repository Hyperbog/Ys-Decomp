#include <stdio.h>
#include <string.h>

#ifndef YS_BUILD_CHANNEL
#define YS_BUILD_CHANNEL "dev"
#endif
#ifndef YS_CHECKPOINT
#define YS_CHECKPOINT "M25"
#endif

int main(int argc, char **argv) {
    if (argc > 2 || (argc == 2 && strcmp(argv[1], "--version") != 0 &&
                     strcmp(argv[1], "--help") != 0)) {
        fprintf(stderr, "usage: ys-native-info [--version|--help]\n");
        return 2;
    }
    printf("Ys native C11 %s (%s)\n", YS_CHECKPOINT, YS_BUILD_CHANNEL);
    if (argc == 2 && strcmp(argv[1], "--help") == 0) {
        puts("Development builds contain diagnostic utilities, not a playable game.");
        puts("ys-native-probe <user-supplied 256 KiB SMS image>");
        puts("ys-native-trace <user-supplied 256 KiB SMS image>");
        puts("ys-native-preview output.ppm (synthetic mode-4 scene)");
        puts("ys-native-frames demo 12 ntsc (synthetic frame sequence)");
        puts("ys-native-timing --check (synthetic timed Z80 + VBlank)");
        puts("ys-native-timed-rom Ys.sms --frame checkpoint.ppm (real VRAM state)");
        puts("  Executes source-ROM through four palette fade levels and 12 IRQ waits to $0B00");
        puts("Windows: extract both ZIP layers, then double-click START_HERE.cmd");
        puts("Windows: bin/ys-native-window.exe opens a persistent synthetic SMS GUI");
        puts("Windows: bin/ys-native-window.exe --ppm checkpoint.ppm views ROM state");
        puts("ys-native-display (optional SDL2 diagnostic window)");
        puts("ys-native-trace ROM.sms --frame checkpoint.ppm (snapshot)");
        puts("The trace ends at a bounded reconstruction checkpoint.");
    }
    return 0;
}
