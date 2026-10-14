# M46c — Natural frame wait: partially observed, blocked

**Status: NOT VERIFIED; DO NOT PROMOTE.** The source-ROM frame-wait
continuation is still an opt-in development diagnostic and currently
returns a nonzero failure exit. M45 remains the Development release;
M46a and M46b retain their separately passing gated evidence.

## Original control path

The M46b checkpoint stops at `PC=$0AB2`, immediately before
`CALL $0BC5`. The original bank-0 routine saves main and alternate
registers, IX/IY and the slot-2 mapper bank, enters the authentic
`$0042` / `$0046` VBlank polling loop, and restores the context
before returning to `$0AB5`. This return point has **not** been reached.

The `--m46c` candidate traces from original reset through both
verified M46a/b checkpoints, then runs the actual `CALL $0BC5`.
It checks the source polling opcodes, observes the real IM1 IRQ
acknowledgment, rejects interrupts originating outside the frame-wait
poll range, and requires a full register/stack/mapper return to
`$0AB5`. No VBlank, IRQ, RAM, mapper or CPU PC is injected.

A ROM-free C11 fixture separately checks the original
`$0AB2 → $0BC5 → $0042 → $0046` entry, stack return addresses,
`$C021=1` and the EI delay.

## New opcodes and independently passing regression tests

- Z80 `SUB n` (D6), 7 nominal T-states, arithmetic S/Z/H/PV/N/C
  flags; required at original bank-2 `$8204: SUB $81`. The tests
  verify negative and zero branches through `RET M`.
- Z80 `RRA` (1F), 4 nominal T-states, rotates A through carry,
  preserves S/Z/PV and updates 3/5 from the result; required at
  original bank-2 `$8191-$8194`.

Both changes compile under strict C11; **13/13 native tests passed** in
[run 38490065043](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38490065043).

## Original-ROM result: blocked

The 16-bank source-only reconstruction passed and the original
M46b checkpoint reproduced successfully. Natural execution continued
through the next VBlank/IM1:

```text
M46b PASS: PC=$0AB2, steps=430904, T-states=3579420,
           IRQ=56, VBlank=60
M46c FAIL: PC=$8307, steps=436736, T-states=3636697,
           IRQ=57, VBlank=61,
           unsupported opcode, SP=$DFC6
```

`Ys/phase4/code.lst` independently identifies bank-2
`$8307: EB — EX DE,HL`, which the bounded native interpreter
does not yet implement. The failing gated original-ROM run is:
[38490065043](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38490065043).

**No M46c source-ROM pass has occurred.** Observing one more natural
IRQ is not equivalent to finishing the wait or returning to
`$0AB5`. No title screen, interactive gameplay, static recompiler
execution or Alpha release is claimed.

## Next bounded proposal

After approval, independently implement/test `EX DE,HL` and resume
the source trace with a strict stop/diagnostics policy. If more
sound-engine opcodes are missing, consider separating sound-engine
coverage from frame-wait return verification; do not skip or fake
the interrupt handler and do not weaken the M46c source-ROM gate.
