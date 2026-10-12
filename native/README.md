# Ys native C11 — M20: continuous banked sound + VDP startup

This is a **bounded execution harness**, not a playable port or a complete
Z80/Sega Master System emulator. The verified ROM-source baseline, ROM digest,
and existing decompilation artifacts remain unchanged.

## Execute fast native tests

```sh
cmake -S native -B build-native -DCMAKE_BUILD_TYPE=Debug
cmake --build build-native --parallel
ctest --test-dir build-native --output-on-failure
```

The default native workflow now runs **only the native C11 unit tests**. No
full 256 KiB ROM reconstruction is run on ordinary native commits. To validate
the full cartridge when a new boot boundary warrants it, push a commit whose
message includes `[rom-check]`, or manually trigger the native workflow with
`rom_trace=true`. The separate M13–M17 cartridge-integrity workflow runs on
`Ys/**`, changes to its own workflow, or `AGENTS.md` (not native-only
changes). Its on-demand `workflow_dispatch` entry also remains available.

## Explicit cartridge checkpoint (slow)

```sh
python3 Ys/tools/build_system_m10.py --check --out /tmp/ys-source-built.sms
./build-native/ys-native-trace /tmp/ys-source-built.sms
```

M10 verifies SHA-256
`02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
The native tracer checks the image size/header, *not* its digest; do not use
unverified ROM inputs. Never commit the reconstructed commercial game ROM.

### Continuous execution

The trace now executes real Ys instructions from the reset vector at
`$0000`, through the `$079A` SRAM signature setup, the `$00A5` work RAM
clear, physical ROM Bank 2's `$8803` sound initializer (including
`$8842` and its `$8883` delay stub), and Bank 0's `$0749` VDP initializer.
The trace halts at `$00C1`, **before `CALL $0BC5`**.

The sound initialization routine sends 11 literal bytes from physical ROM
Bank 2 `$8878` to PSG port `$7F`, then selects YM2413 FM registers
`$20–$25` through `$F0` and writes zero through `$F1`. The output sink
(`sms_sound.c`) observes I/O bytes and stores initial register state only.
**No audio synthesis, frequency timing, or player output is present.**

The VDP routine writes 11 register values from Bank 0 table `$0768` to VDP
control port `$BF`, copies that table into work RAM, and writes one zero byte
to CRAM at `$10` through data port `$BE`. Unlike the previous milestone,
this VDP call is now reached through normal reset execution without manually
seeding the routine's CPU stack.

### Additional Z80 subset

- `LDI`, `OUTI`, `OUT (C),r`, `ADD HL,rr` (with documented flags).
- Existing `LDIR` support is still bounded and approximate for undocumented
  flags; only the executed opcodes are supported.
- The fail-closed port dispatch distinguishes VDP `$BE/$BF` from PSG `$7F`
  and FM `$F0/$F1`; other I/O ports are rejected.
- Synthetic unit fixtures exercise the above instructions with mapper-selected
  bank 2; real cartridge instructions are tested in the explicitly gated
  trace step.

## Unimplemented

Further CPU instructions, cycle-accurate flags/interrupt scheduling, VDP
frame/scanline timing and rendering, PSG/YM2413 synthesis, controller input,
SDL3 frontend, save RAM persistence and full boot/gameplay. The Sega mapper
model retains its documented Phase 1 hardware-revision assumptions. Neither
the source-built ROM nor the C11 runtime has yet produced native frames.

Next milestone: continue from `$0BC5` through interrupt/state initialization
using evidence-driven CPU/port expansions, and introduce deterministic native
VDP state checks.
