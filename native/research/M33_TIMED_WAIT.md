# M33 — First source-ROM frame wait completed under automatic VBlank

## Source evidence

Continuation begins at the already gated M32 checkpoint `PC=$0046`
(17,227 instructions, `$C021=1`, two naturally accepted IM1 IRQs).
Original code is from `Ys/src/phase16/bank00_symbolic.asm`:

| Original bank-0 PC | Opcode/action |
| --- | --- |
| `$0046` | `LD A,($C021)` — poll active frame wait |
| `$0049` | `OR A` — test wait flag |
| `$004A` | `JR NZ,$0046` — do not continue until ISR clears flag |
| `$0038` | `PUSH AF; IN A,($BF)` — real clock-generated IM1 handler reads and clears VDP status |
| `$0102` | Read `$C021`, select **nonzero** first-wait branch via `$0108` |
| `$0108-$0124` | Copy source VDP update command data and dispatch the original sprite-table/renderer code |
| `$0125-$0138` | Restore live interrupt eligibility, scan input, map the actual bank-2 sound routine |
| `$013F-$0147` | Clear `$C021` and `$C10F`, restore AF and `RET` |
| `$004C` | Wait returns when `$C021=0` |
| `$0BDC-$0BEE` | `$0BC5` bridge restores bank, main/alternate registers, IX/IY and returns |
| `$00C4` | Original reset startup dispatcher resumes |

The previous M29-M30 early VBlank events occurred before the CPU
entered the `$0042` wait. **M33 verifies the first game-frame
synchronization wait itself**, not merely a VBlank occurring somewhere
during initialization.

## Native implementation acceptance

`native/trace_timed.c` executes original cartridge opcodes through
`ys_sms_runtime_step_auto`, without changing PC, SP, VDP, clock,
input or mapper state. New checks:

1. After M32 at `$0046`, run no more than 90,000 Z80 instructions
   until the source returns to `$00C4`.
2. When the next maskable IRQ is accepted, capture actual suspended
   PC from the live stack and require it within the source wait
   loop `$0046-$004C`. Assert VDP VBlank status bit 7 is pending
   and IRQ count advances naturally.
3. Require `$C021=0` and `$C10F=0` on return and SP=$DFF0,
   with ROM slot 2 selected, IX/IY preserved, and CPU still running.
4. Require an increased VDP VRAM-write count and PSG write count
   from the authentic wait-frame ISR, rather than pretending that
   a frame was rendered or synthesizing hardware activity.
5. Abort if unsupported opcode/port, multiple unexpected nested IRQs
   or invariant failure. Record the real suspended source PC and the
   actual instruction, IRQ, VBlank, VRAM, PSG and timing totals.
6. When `--frame` is supplied, export **the real VDP state at
   `$00C4`**, instead of the older `$0046` pre-wait snapshot.
   A 256×192 P6 RGB PPM is validated by the gated workflow.
   Even with VRAM writes this may not be a visible title image,
   because display enable and tile data are not initialized fully.

The ROM-independent `test_source_busy_wait_wakes_with_natural_irq`
fixture encodes the original `$0046/$0049/$004A` poll and a
**synthetic continuation** after the source `$0038/$0039` ISR
prologue. It proves the automatic IRQ/status/flag-clear loop
mechanism, but does not replace real cartridge verification.

## Reconstruction and releases

No `Ys/**` decompilation files or source-ROM bytes change.
Only a meaningful M33 checkpoint uses the expensive tagged
`[rom-check]` reconstruction. The original source-only ROM digest
must remain
`02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
The M25 manual-IRQ trace and M29-M32 automatic path are preserved
as independent regression checks.

The Windows Development launcher still opens a **saved static image**,
not a live game. An ISR/VRAM update is not the same as complete
title/gameplay execution. Alpha/Beta/Final gates remain blocked.
