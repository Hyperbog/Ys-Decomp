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
        puts("The trace ends at a bounded reconstruction checkpoint.");
    }
    return 0;
}
