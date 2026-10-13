# M46a — Original post-resource video-state prefix (candidate)

## Scope

The verified M45 source-ROM trace ends at `PC=$0C92`, before these
four original fixed-bank Z80 instructions from `Ys/phase5/code.lst`:

```z80
$0C92  3E 20        LD A,$20
$0C94  32 19 C0     LD ($C019),A
$0C97  3E 81        LD A,$81
$0C99  32 64 DE     LD ($DE64),A
$0C9C  CD A7 0A     CALL $0AA7   ; not executed in M46a
```

A separate, opt-in original-ROM path runs *only* these four instructions
after all M45 checks succeed. It expects 4 additional Z80 instructions,
40 nominal T-states, the two specified WRAM values, and no other changes
across the 8 KiB WRAM window. The trace also checks CPU flags, stack
pointer, mapper banks, accepted interrupts, VBlank events, VDP VRAM writes,
PSG write count and exact source opcodes. No RAM, CPU, mapper or IRQ state
is injected to reach the checkpoint.

A ROM-free synthetic unit fixture checks opcode execution, instruction
timings, WRAM writes and preservation of adjacent sentinels. The original
ROM trace remains distinct and is required for source-execution evidence.

## Run

```sh
cmake -S native -B build-native -DCMAKE_BUILD_TYPE=Debug
cmake --build build-native --parallel
ctest --test-dir build-native --output-on-failure
python3 Ys/tools/build_system_m10.py --check --out /tmp/ys-m46-source.sms
./build-native/ys-native-timed-rom /tmp/ys-m46-source.sms --m46-prefix
```

The existing no-option or `--frame` commands still stop at the certified
M45 `$0C92` boundary. This opt-in mode stops *before* `$0C9C CALL $0AA7`.

## Evidence and promotion

Status: **M46a branch candidate with passing gated original-ROM CI**.
[Actions run 38481243443](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38481243443)
passed 13/13 native C11 tests, 16/16 source-only ROM banks (262,144 bytes;
no binary fallback), and the full M45 checkpoint before the optional
M46a source trace. Original fixed-bank execution reached `PC=$0C9C`
after four further Z80 instructions and 40 nominal T-states. All 8 KiB
WRAM bytes matched the unchanged prestate except the expected
`$C019=$20` and `$DE64=$81`; CPU flags, SP, mapper, IRQ, VBlank,
VRAM and PSG invariants passed. Cumulative M46a count derived from the
verified M45 baseline is **430,890 instructions / 3,579,301 T-states**,
with **56 naturally accepted IRQs / 60 VBlanks**.

This is a verified *bounded source-interpreter path*, **not** a new
Development release promotion. The baseline milestone remains M45.
No generated-C code execution,
interactive title-screen rendering, gameplay, Alpha/Beta/Final promotion
or externally verified PC port is claimed.

The next scope, requiring separate approval, is to trace `CALL $0AA7`
and validate its real VDP/WRAM effects without skipping original code.
