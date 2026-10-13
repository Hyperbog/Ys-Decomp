# Ys native C11 — M22: first VBlank VDP dispatch checkpoint

## M22 acceptance boundary

The bounded native interpreter now executes the real bank-0 ISR from
`$0108` through the Z80 `OUTD`/indirect-port register transfers and
one-based `RST $08` dispatch, stopping **before the handler at `$01B4`**.
The prior source-ROM trace reaches `$0108` from reset, the SRAM and WRAM
initializers, the bank-2 sound initializer, the VDP initializer, and an
**explicitly injected** IM 1 VBlank interrupt. M22 adds no automatic clock,
frame generation, or fabricated return from that handler.

The ROM-dependent trace checks:
- Four additional VDP register commands for registers 10, 9, 8 and 5.
- Source-RAM bytes `$C01A`, `$C019`, `$C018`, and constant `$FF`
  are written to those registers in that order.
- A total of 15 VDP register writes and 32 VDP control-port bytes
  since initial native VDP reset.
- `RST $08` indexes the ROM word table at `$01AA` with selector 1,
  resolves target `$01B4`, and leaves return address `$0125`
  on the stack. The test does not execute the `$01B4` routine.

Native Z80 additions are `OUTD` (`ED AB`), `ADD A,r` (8-bit),
`JP (HL)` and the eight Z80 `RST` opcodes. `test_irq.c` executes
source-backed synthetic bytes for both the ISR and `RST $08`
helper, including VDP register and stack assertions.

### Efficient verification

The GitHub native workflow runs CMake/CTest **without** rebuilding the
cartridge on routine pushes and pull requests. Full ROM reconstruction is
reserved for an explicit workflow dispatch with `rom_trace=true`, or a
commit message containing `[rom-check]`. The independent integrity workflow
still runs for changes to the original `Ys/**` source and on manual dispatch.
A source-ROM rebuild is warranted for this new `$01B4` checkpoint.

### Limits

No clock-driven interrupts, ISR return, main loop dispatch, controller polling,
VDP rendering, audio synthesis, SDL display or playable PC build are claimed.
The original ROM reconstruction, source data and digests remain untouched.
The next objective is to investigate the handler at `$01B4` and its callees,
then resume the interrupted startup after independently verified state changes.

## Earlier milestone notes

# Ys native C11 — M21 interrupt-entry checkpoint

Current M21 boundary: continuous reset executes through the banked sound
initializer and initial VDP register programming, then enters the actual
$0BC5 bridge and $0042 VBlank wait. The test explicitly injects one IM 1
interrupt **after EI defer expires** and runs the original $0038 handler
through $0102 to the $0108 branch point. The event is manually injected;
there is no frame clock or automatic interrupt delivery.

Implemented M21 Z80 support: EX AF/AF', EXX, PUSH/POP IX/IY, conditional JP,
RETI/RETN, EI deferral and externally delivered maskable interrupts. Synthetic
and source-backed unit cases are in test_irq.c. All unsupported IX/IY prefixed
opcodes still fail closed.

Fast CI runs the five native test suites without cartridge reconstruction.
The ROM-dependent trace runs only when explicitly requested with rom_trace=true
or a [rom-check] commit marker. No playable native game loop, graphics renderer,
audio output, clock-driven IRQs or controller input is claimed.

## Prior checkpoint: M20

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
