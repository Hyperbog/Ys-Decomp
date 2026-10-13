# M35 — Original Ys four-level palette fade across twelve timed VBlanks

## Actual source control flow

In `Ys/src/phase16/bank00_symbolic.asm`, the source palette initializer
at `$0AE8` completes a `$0B10` 32-byte staging copy and enters the
32-iteration `RLD` nibble transform at `$0B22`. M34's continuous ROM
execution already reached `$0AF6` after its first `A=0` transform,
with 24,468 interpreted source instructions, 416,854 nominal CPU
T-states, three IM1 interrupts, and seven clock-generated VBlanks.

The next original code is:

```asm
$0AF4 ld b,$03
$0AF6 call $0BC5  ; real VBlank wait, preserves registers
$0AF9 djnz $0AF6  ; three waits per palette level
$0AFB inc a
$0AFC cp $04
$0AFE jr nz,$0AEC ; next RLD palette transform A=1,2,3
$0B00 ld a,$07    ; beginning of ROM bank-7 palette-data transfer
```

There are **four palette levels (A=0,1,2,3)** and **three VBlank waits
per level**, for twelve source wait-bridge returns before reaching
`$0B00`. No actual bank-7 data transfer is claimed at this boundary.

The original `$0BC5` bridge preserves both register sets and IX/IY,
sets A=1 for the authentic `$0042` flag-based VBlank polling routine,
and returns to `$0AF9` only after the game's ISR acknowledges VBlank,
processes VDP/sprite data and source sound, and clears `$C021`.
No host clock sleeps, injected IRQs or patched state are permitted.

## Acceptance criteria

`native/trace_timed.c` runs from CPU reset through the previously verified
M29–M34 stages, then advances via `ys_sms_runtime_step_auto`:

- Require exactly twelve `$0BEE RET` to `$0AF9` source wait returns,
  with `$C021=0` at each return and no unexpected frame/IRQ jumps.
- Detect three subsequent palette transform returns
  `$0B4D RET -> $0AEF`, completing four palette passes in total.
- Preserve original stack pointer, IX/IY, mapper control and slot-2 bank
  at each wait return. Validate stack depth when source CALL enters
  `$0BC5`.
- Reject an unsupported instruction, I/O port, invalid IRQ vector or
  unexpected multiple VBlank events in a single instruction.
- Verify the loop exits normally at **`PC=$0B00`** with
  `A=4`, `B=0`, the wait flag `$C021=0`, palette control
  `$C02C=1`, and further VRAM/PSG writes from authentic frame ISRs.
- Keep a 300,000-instruction bound from M34 to M35, and always fail
  closed with the actual PC, SP, IRQ count, VBlank count and hardware
  counters if any invariant fails.
- Optional `--frame` creates the authentic 256×192 PPM video snapshot
  at the **end of four fade levels**, not a playable game window.

A ROM-free regression in `native/test_timing.c` uses the actual source
`LD B,3 / CALL $0BC5 / DJNZ $0AF6` opcodes combined with a synthetic
frame-wait bridge/ISR continuation. It verifies three naturally clocked
IM1 interrupts, three completed waits, stack restoration, B=0 and
status acknowledgment. It is not a substitute for the real ROM ISR.

## Source reconstruction and release eligibility

No `Ys/**` original decompilation sources or original cartridge bytes
change. The source-only ROM reconstruction remains gated by
`[rom-check]` and must retain 16/16 source banks, 262,144 bytes,
zero fallback, SHA-256:

`02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.

Both the M25 explicit-IRQ legacy trace and complete M29–M34 automatic
frame trace must continue to pass. Alpha/Beta/Final gates remain false;
passing twelve frame waits does **not** demonstrate a Ys title
screen, a synchronized desktop game loop, live controls or audio output.
