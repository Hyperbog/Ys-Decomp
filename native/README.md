# M28 — CPU-timed VBlank runtime (Development build)

The native Z80 core now records per-instruction T-state counts and a
running total. `ys_sms_runtime_step_auto` advances the M27 NTSC/PAL
frame clock from those counts, including conditional-branch timing,
a 13-T IM1 acknowledge, and 4-T refresh while HALTed. This enables
automatic *hardware event recognition* without manually injecting IRQ
events, but it is not yet a playable or faithfully synchronized Ys game.

The ROM-independent Development executable
`ys-native-timing --check` verifies the full synthetic NOP/EI → VBlank
→ IM1 `$0038` → status-acknowledge sequence. This new milestone does
**not** change the source-ROM execution boundary at M25 PC `$0B22`.
No proprietary ROM, assets, or full reconstruction are required.

See [M28 timing contract and tests](research/M28_TIMING.md). Alpha
promotion gates remain false pending genuine game-frame execution,
desktop game rendering, live input, and interactive gameplay.

## Previous milestone: M27

# M27 — Frame clock, automatic VBlank recognition and synthetic live frames

The native C11 Development build now includes an explicitly T-state-driven
SMS NTSC/PAL scanline clock, an IM1 VBlank-delivery bridge, and a
ROM-independent `ys-native-frames` CLI capable of exporting a sequence of
animated 256×192 PPM frames. No original ROM/image assets are bundled.

```sh
bin/ys-native-frames --check
bin/ys-native-frames demo 12 ntsc
bin/ys-native-frames demo-pal 12 pal
```

The second command writes `demo-000.ppm` through `demo-011.ppm`.
Each image uses the synthetic M26 tile-and-sprite fixture, not Ys game art.
On systems where the SDL2 development library was installed when CMake
configured the build, an **optional** `ys-native-display` executable
opens a scaled desktop window with this *same synthetic animation*.
The SDL2 runtime library must also be installed on the recipient machine.
The cross-platform downloadable Development build **always** supports
headless PPM sequences but **may not** include the optional window binary.

Core device interfaces: `sms_clock.[ch]` emits NTSC 262-line and PAL
313-line clocks with 228 caller-supplied Z80 T-states per line. Line 192
sets the sticky VDP VBlank status bit (0x80), which persists until a VDP
status-port read. `sms_runtime.[ch]` advances this clock and automatically
vectors an eligible IM1 CPU interrupt when VBlank is enabled in VDP
register 1, bit 5, respecting CPU IFF1 and EI delay.

**Timing limitation:** `z80.c` does not yet report instruction T-state
durations. The runtime bridge consumes T-states supplied by its caller.
Its synthetic animation advances a whole frame clock per generated image;
it does not claim Z80 instruction-accurate gameplay frames. The existing
source-ROM execution trace still stops before `$0B22` after 17,224
instructions and one specifically injected VBlank. This milestone
**does not** pass a new original-ROM checkpoint, so no M10 rebuild is
required and original ROM/source files are unchanged.

The Alpha gates for boot-to-title, frame accuracy, finished renderer,
live game controls and interactive gameplay all remain false.

## Previous checkpoint — M26

# M26 — Native SMS video snapshots (Development build)

The Development artifacts now contain **ys-native-preview**, a standalone
256×192 Sega Master System mode-4 video diagnostic that writes a portable
PPM image. It uses an entirely synthetic tile/sprite scene; it is **not**
a screenshot of Ys, and it does not require or bundle game assets.

From a released Development ZIP (or locally built binaries):

```sh
bin/ys-native-preview synthetic.ppm
bin/ys-native-preview --check
bin/ys-native-trace /path/to/your/Ys.sms --frame checkpoint.ppm
```

The third command renders the current VRAM, CRAM and register state from the
**actual user-supplied cartridge** at the already-verified M25 execution
boundary (PC=$0B22). The scene is not yet fully initialized and may appear
mostly blank. The standalone preview is the recommended way to test the
renderer itself. Both PPM files can be opened in many graphics editors or
converted to PNG with image tools.

`native/sms_video.c` implements stateless 256×192 mode-4 background tile
decoding, CRAM RGB222→RGB888, horizontal/vertical scroll, tile flips,
palette selection and priority, the left 8-pixel mask, sprite-pattern and
attribute lookup, sprite order, transparency, 8-per-scanline limit, size
8×16 and zoom. Tests cover the individual behaviors and PPM format.
It does **not** emulate 224/240-line modes, scanline timing, collisions as
CPU-visible status or a screen window. It does not draw a completed game
frame without the game's ROM code having first initialized its VRAM.

**Build and packaging:** `native/release/gates.json` names checkpoint M26;
the `dev` archive includes the preview executable and unchanged diagnostic
probe/trace utilities. Alpha's `video_renderer` gate stays **false**
because an interactive video window, actual frame pacing and complete title
screen are not proven.

**No new ROM reconstruction** is required: this change does not advance Z80
execution beyond the already source-verified M25 $0B22 boundary. Native
builds and video test fixtures run with no game ROM.

## Earlier milestones

# Ys native C11 — M25: state-table dispatch enters scene preparation

The continuous source-ROM trace now follows the first two startup states
after the fully verified initial VBlank interrupt and return.
The dispatch loop at `$00C4` reads `$C01F=0` and vectors via `RST $08`
to `$00FC`, which sets state `$C01F=1` and returns.
The next dispatch resolves the ROM word table to `$0C4A` and calls
`$0A5B` → `$0A80` → `$0AE8` → `$0B10`. The final routine copies 32
bytes from `$C160` into `$C530`; the acceptance point is PC=`$0B22`,
**before executing the palette/tile nibble conversion**.

The Z80 core adds `ED 6F` (`RLD`) for upcoming nibble-processing code,
with carry-preserving flags and fail-closed writes. A source-backed
nonzero WRAM fixture and dedicated `RLD` tests validate the new behavior.
See [M25 source trace](research/M25_SOURCE_TRACE.md).

Ordinary native CI continues to run six fast test suites without
ROM rebuilding. An explicitly tagged `[rom-check]` commit or manual
`rom_trace=true` dispatch can validate this new ROM-dependent boundary.
Automatic VBlank frames, rendering, sound synthesis, live controller
events, fully loaded title-screen data and playable gameplay remain out
of scope.

## Previous milestones
# Ys native C11 — M24: first VBlank interrupt returns to startup

The current source-ROM trace reaches **PC=$00C4 / SP=$DFF0** after
**17,052 Z80 instructions** from reset and one explicitly injected VBlank.
All main and alternate general registers, IX/IY, stack and mapper state
were verified against the pre-interrupt snapshot. The bank-2 $8000
sound-update path writes 22 cumulative PSG bytes and 12 FM register/data
pairs (including the repeat initialization at $8803).

New bounded CPU instructions: indexed and nonindexed BIT, LD IX/IY,nn,
ADD IX/IY,rr, CP r and conditional CALL cc,nn. The source-backed tests
cover first-frame sound idle-channel scans and zero-bit flags.

All six native CTest suites and the explicitly requested 256 KiB
source-ROM checkpoint passed in CI:
https://github.com/Hyperbog/Ys-Decomp/actions/runs/38334911711

See [M24 source tracing](research/M24_SOURCE_TRACE.md) for opcode evidence.

Routine native commits do **not** rebuild the cartridge: use
workflow_dispatch rom_trace=true or a [rom-check] commit marker.
The original decompilation is unchanged and no ROM binary is committed.

The opcode at $00C4 has **not** executed yet. Video frame clocks,
automatic interrupts, native rendering, sound synthesis, controller
event polling and playable game logic remain unfinished.

## Previous checkpoint — M23
# Ys native C11 — M23: first-frame sprite upload and controller sample

The bounded CPU/VDP runtime now extends the *first manually triggered*
VBlank service sequence from bank 0's `$01B4` through its `$0427` sprite
attribute-table upload, `$03E8` conditional return, EI, bank 0's `$0773`
controller sampler, and dispatch into the `$8000` sound-frame update.
Execution stops **before the first instruction at `$8000`**.

## Native CI and reconstruction policy

```sh
cmake -S native -B build-native -DCMAKE_BUILD_TYPE=Debug
cmake --build build-native --parallel
ctest --test-dir build-native --output-on-failure
```

Fast default CI executes all native unit suites without reconstructing ROM
banks. Run the ROM-dependent trace **only** when it advances a meaningful
source-backed checkpoint, by an explicit `workflow_dispatch` with input
`rom_trace=true` or a commit containing `[rom-check]`.
For a manual source-verified test:

```sh
python3 Ys/tools/build_system_m10.py --check --out /tmp/ys-source-built.sms
./build-native/ys-native-trace /tmp/ys-source-built.sms
```

The source reconstruction asserts the original 256 KiB cartridge SHA-256
`02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
No commercial ROM or image/assets are committed.

## VBlank sprite transfer

Recovered bank-0 ROM source shows `$0427` setting VDP VRAM write addresses
`$3F00` and `$3F80`, then executing 64 and 128 literal `OUTI` instructions.
These copy the byte ranges `$DD00-$DD3F` (sprite Y coordinates) and
`$DD40-$DDBF` (sprite X/tile values) to the corresponding VDP sprite
attribute table. The model validates the 192 bytes and total write count,
including address wrapping at `$3FFF`, without drawing actual sprites.

The source-backed `$03E8` handler sees `$C02C=0` following reset and
returns to `$0125`. The code re-enables interrupts with EI and calls the
controller sampler at `$0773`. `sms_input.[ch]` supplies explicit active-low
snapshots at ports `$DC/$DD`, initially `$FF` for no input. It does **not**
automatically poll a keyboard/controller or implement other SMS I/O ports.

Additional bounded Z80 opcodes: conditional `RET` family, register
`AND/XOR/OR` forms, and `CPL`; invalid/unsupported instructions and ports
still fail closed. `test_irq.c` tests the actual source-backed sprite
upload sequence with nonzero synthetic data and controller sampling with
both pressed and unpressed buttons.

## Explicit non-goals

The full first VBlank ISR **has not returned** to the interrupted caller;
`$8000` is the next unexecuted instruction. No reliable emulated frame
clock, H/VBlank scheduling, audio synthesis, controller polling, video
rendering, SDL frontend or playable game loop is present. Existing SMS
mapper-revision assumptions and incomplete Z80 opcode/flag coverage remain.

## Earlier milestones

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
