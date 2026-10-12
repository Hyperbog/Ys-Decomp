# Ys native C11 runtime — Phase 2 (bounded Z80 bootstrap)

This is a standalone, **not-yet-playable** native implementation alongside the
existing exact Z80/Python cartridge reconstruction. The original 16-bank source
build and all M10–M17 verification files remain authoritative and unchanged.

## Build and run

```sh
cmake -S native -B /tmp/ys-native-build -DCMAKE_BUILD_TYPE=Debug
cmake --build /tmp/ys-native-build --parallel
ctest --test-dir /tmp/ys-native-build --output-on-failure
cd Ys
python3 tools/build_system_m10.py --check --out /tmp/ys-source-built.sms
cd ..
/tmp/ys-native-build/ys-native-trace /tmp/ys-source-built.sms
```

The M10 builder compares the rebuilt cartridge against SHA-256
`02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
Do not commit the output ROM. The native executable checks file length and SMS
header only, so use the SHA-verified source builder to produce its input.

## Source-backed execution checkpoint

`native/z80.c` implements a bounded subset of the real Z80, connected to the
Sega memory mapper from Phase 1. It implements DI, IM 1, LD SP/HL/DE/BC immediate,
LD register/memory forms, INC/DEC, XOR/OR/AND A, CP immediate, JP, JR, CALL,
RET, stack PUSH/POP, and LDIR. Unsupported instructions, ports and ROM writes
are explicit errors. LDIR runs one repeat iteration per interpreter step.

`ys-native-trace` checks the real cartridge boot sequence from reset at `$0000`
through the first `CALL $079A` (17 executed instructions) and stops **before**
executing the first instruction at `$079A`. Required resulting state:

- `PC=$079A`, `SP=$DFEE`, `A=$FF`, interrupt mode 1, interrupts disabled.
- Sega mapper control `$80`, 16 KiB slots `[0, 1, 2]`.
- Console RAM `$C001=$FF` and `$DE60=$00`.
- Stack holds the return address `$00A5`.

The C tests cover the same boot instructions in a synthetic-ROM fixture plus
stack behavior, flags, forward/backward branching, bounded LDIR, mapper writes,
step-budget termination, invalid writes, unsupported opcodes, and port access.
GitHub CI additionally runs the trace on the *actual source-built, hash-checked*
Ys cartridge. No commercial ROM or extracted assets are tracked.

## Deliberately incomplete features

The C11 module is **not a full Z80 emulator**. It does not implement the
complete opcode matrix, register shadow set, indexed prefixes, cycle timing,
interrupt delivery, refresh-register behavior, all undocumented flags, or
accurate EI interrupt deferral. LDIR's undocumented flag bits 3 and 5 are
deferred. There is no VDP, PSG/FM, input, frame scheduler, save RAM persistence,
or SDL3 frontend. The ROM bus also retains the initial Phase-1
mapper-revision assumptions. Native ROM inspection and boot tracing **do not**
demonstrate playable gameplay or title-screen rendering.

Next milestone: trace `$079A` and other startup callees against the verified
Z80 source, add the required opcode/port support with independent differential
tests, and establish a VDP command/write trace before attempting SDL3 rendering.
