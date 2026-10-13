# M32 — Timed Ys original VDP init → first frame-wait source checkpoint

## Original code and target

Reference: `Ys/src/phase16/bank00_symbolic.asm` (bank-0 symbolic listing).

| PC | Source instruction | Expected effect |
| --- | --- | --- |
| `$0764` | `POP AF` | Restore video setup's pre-RST accumulator and flags |
| `$0765` | `OUT ($BE),A` | Write authentic initialization data to VDP |
| `$0767` | `RET` | Return from the original `$00BE CALL $0749` to `$00C1` |
| `$00C1` | `CALL $0BC5` | Begin source first frame-wait bridge |
| `$0BC5-$0BD7` | `PUSH AF/BC/DE/HL; EX AF; EXX; PUSH alternate registers; PUSH IX/IY; PUSH mapper bank` | Preserve original startup context |
| `$0BD9` | `CALL $0042` | Enter source VBlank wait |
| `$0042` | `LD ($C021),A` | Set wait flag to 1 |
| `$0045` | `EI` | Arm interrupts after one-instruction delay |
| `$0046` | `LD A,($C021)` | Stop **before** executing the first wait poll |

This continuation begins *after* the M30 verified sequence of a first
clock-generated IM1 interrupt at PC=$0764, a pending second VBlank
immediately accepted at the original ISR `EI; RET`, and a **stable
return** to `$0764`. No new IRQ injection or CPU/mapper/VDP
manipulation is allowed.

## Acceptance (gated source-ROM build)

`native/trace_timed.c` maintains M29+M30 invariants and then
executes the original `POP AF / OUT ($BE),A / RET` and VBlank-wait
bridge. It validates:

- `PC=$00C1` reached in **three instructions** from `$0764`,
  with restored startup SP `$DFF0` and ROM bank 2 mapped.
- `PC=$0046` reached in bounded source instructions through
  `CALL $0BC5`, with `$C021=1`, `IFF1=1`, `EI` delay still pending.
- Exactly **two** accepted IM1 interrupts, preserving the M30
  initial six frame VBlank events.
- No emulator-side frame injection, stack correction, forced mapper
  updates or controller emulation.
- Optional `--frame checkpoint.ppm` produces a real
  **256×192 RGB P6** frame from the actual cartridge VDP state.
  The file is validated as 147471 bytes and the exact P6 header.

A separate ROM-free CPU regression fixture in
`native/test_timing.c` encodes real bank-0 `$0764` and `$00C1`
instructions, validates POP AF stack ordering, OUT port, RET and
entry to `$0BC5` with a 48-T-state total.

## Windows Development testing

`START_HERE.cmd` menu **3** accepts a user-owned 256 KiB Ys
Master System ROM, executes the timed diagnostic with
`--frame checkpoint.ppm`, and opens the result in
`ys-native-window.exe --ppm checkpoint.ppm`. The Win32 viewer
parses only an exact-sized uncompressed 256×192 P6 RGB file.
It is intentionally read-only; the separate synthetic sprite
animation remains menu **1**.

**The image may be blank or incomplete**: game boot has not yet
loaded the title-screen tiles and enabled the display. The real
cartridge program is no longer running in the viewer. This
does **not** satisfy `boot_to_title`, `video_renderer`,
`live_controls` or `interactive_gameplay` Alpha gates.

## Reconstruction policy

The original 16 source-only ROM banks and prior M25/M29/M30
source-ROM checkpoints are checked only on explicitly tagged
`[rom-check]` commits or `rom_trace` workflow dispatch.
No `Ys/**` decompilation sources change in M32. The expected
unmodified M10 SHA256 is
`02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.

The next game-execution milestone should continue from
`$0046` through the first natural wait-loop completion, followed
by the state dispatcher at `$00C4`, not claim title/gameplay
until full VDP state and interactive controls are validated.

## Reproduction contract

The source-ROM verification workflow calls `ys-native-timed-rom`
with `--frame`, rejects any unexpected instruction/port failure,
checks the original frame-wait address and wait flag, and requires
an exact 147471-byte `P6\\n256 192\\n255\\n` export. The Windows
Development workflow separately tests opening a generated PPM in the
self-contained GUI, without needing ROM assets or a desktop session.
These checks deliberately do not certify a live, playable screen.
