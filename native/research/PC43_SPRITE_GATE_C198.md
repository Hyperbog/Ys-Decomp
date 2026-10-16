# PC-43 — physical bank-6 C198 sprite-production gate

## Original source control flow

PC-42 confirmed exactly 13 mapped physical-bank-6 `$9966`
entry sites and zero mapped `$9932` producer entries in the
source-only 600,000-iteration original Ys controller experiment.
The unmodified recovered original physical bank-6 source at
`Ys/src/wholebank06/bank06_complete.asm` contains:

```z80
; Original physical bank6 $9966 (CPU $8000–$BFFF)
ld a,($C198)     ; $9966, 3 bytes
or a             ; $9969
jr z,$99C6       ; $996A; branches over the producer call
call $9932       ; $996C, original ProduceSpriteBuffer
```

These instructions explain the **conditional dependency** but
do not, without observing the actual running original Z80,
establish the value of `$C198` or the branch taken.

## PC-43 authentic source observer

The optional sixth argument to the existing
`--pc40-source-route` CLI records the genuine original 600k
input sequence with a separate passive `pc43_sprite_gate`
observer; the original PC-42 5-argument command remains intact.
No PC, input schedule, stack, WRAM, VDP, mapper, R register,
clock or IRQ is modified to make a sprite appear.

For each physically bank-qualified entry at `$9966`, record
the current post-M45 iteration, actual CPU instruction count,
mapped bank, raw RAM `$C198`, selector `$C01F`, source
record selector `$C199`, and sprite-state `$C1B9`.
At real execution of `OR A` (`$9969`) and
`JR Z,$99C6` (`$996A`), capture the accumulator,
live `$C198`, exact Z flag, and whether an IRQ was
acknowledged during execution. After executing that single
original Z80 instruction, record the actual successor CPU PC
and compare it to the independent Z80 condition (`$99C6`
if Z, `$996C` otherwise) when no IRQ preempts the branch.
Also count original physical bank-6 visits to the producer
entry `$9932`, its `$996C` CALL instruction and the
skip destination `$99C6`.

`native/test_pc43_sprite_gate.c` executes the bank-6
original gate's actual Z80 bytes on ROM-free fixtures with
both zero and nonzero `$C198`, negative physical-mapper and
SRAM-remap cases, a real CALL stack, and strict JSON formatting.

`native/tools/verify_pc43_sprite_gate.py` independently
verifies the exact 262,144-byte original source-ROM SHA
(through the unchanged PC-42 oracle), the original bank-6
opcode sequence `3A 98 C1 B7 28 5A CD 32 99`,
source-assembly text, strict report schema, every observed
immediate JR successor and the previous exact PC-42 600k
CPU/mapper/IRQ/source-site golden. A malformed report must be
rejected by CI.

## Evidence limits

Observing a zero `$C198` and a taken branch would explain
why a particular **visited gate** skips `$9932`.
It does *not* establish why the game originally set
`$C198` to zero, nor player location, input interpretation,
sprite identity, collision or authenticated original gameplay.
The original source-ROM bytes must remain uncommitted.
Independent SMS emulation/hardware comparisons and all five
original-game Alpha gates remain outstanding.

This milestone is draft, stacked above PC-42 and unmerged
until the complete original source-ROM workflow and native
C11 tests are green. The stable M45 `Ys` branch is unchanged.
