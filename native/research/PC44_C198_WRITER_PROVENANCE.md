# PC-44 — authentic physical $C198 WRAM writer provenance

## Question and source-ROM scope

The original Ys Z80 code's mapper-qualified physical bank-6
`$9966` handler conditionally calls the `$9932` sprite
producer. PC-43 demonstrated **13** real `$C198=0` reads,
13 zero-flag JR jumps to `$99C6`, and **zero** producer
calls in the same bounded original controller experiment.

PC-44 identifies which **successful console-WRAM bus stores**
actually maintained that zero. Sampling memory values once
per iteration is insufficient because an instruction may write
a byte equal to the previous contents.

The PC-39 optional successful-WRAM-write observer is reused,
filtered to physical offset `$0198` (`$C198` or `$E198`
logical). It attaches **before original-ROM reset-to-M45
execution**, then enters a separate second phase immediately
after the same natural M45 checkpoint and follows the exact
unchanged **600,000-iteration** PC-34 input schedule.
The trace never writes CPU/register/controller/mapper/RAM/VDP/
sound state, never replaces source opcodes, and does not count
SRAM-remapped stores or rejected ROM writes.

Each actual physical bus strobe records the original Z80
latched instruction-start PC, physical source bank, phase,
actual instruction count, continuation iteration, logical
destination, old/new byte, A/F, input selector, slot2 bank,
IM1 IRQ context, plus **HL/DE/BC before block-pointer
updates** and the memory byte then readable at HL.

## Verified source WRAM writes

The [original ROM-backed PC-44 native run](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38982392227)
passed all **36/36** strict C11 tests and the PC-34, PC-40,
PC-41, PC-42 and PC-43 source checks. Original-ROM source
integrity and the SMS/GG recomp adapter also passed.

| Phase | Iteration | Source PC / physical bank | Opcode | Physical before → after | Pre-write HL / DE / BC |
| --- | ---: | --- | --- | --- | --- |
| Reset → M45 | — | `$00B4` / bank 0 | `LDIR` | `00 → 00` | `C197 / C198 / 1CC8` |
| Post-M45 | **90,782** | `$0B1A` / bank 0 | `LDI` | `00 → 00` | `C197 / C198 / 0068` |
| Post-M45 | **420,484** | `$2041` / bank 0 | `LD ($C198),A` | `00 → 00` | `258D / C601 / 0001` |

Actual CPU instruction-step counts at the three stores are
**8,632**, **521,668**, and **851,370** respectively.
All three writes succeeded and stored an **identical zero**.
None changed the byte. No logical `$E198` mirror store was
observed, and the final physical WRAM byte was zero.

The two **block transfer** opcodes copy the byte at
`HL=$C197` into `DE=$C198` before incrementing HL and
DE. Their accumulator values (**128** and **104**) were
*not* the bytes stored. PC-44 includes a dedicated real-Z80
test distinguishing a source-byte copy from A.

The later `$2041` instruction instead writes **A=0**.
The immutable original fixed-bank listing proves the relevant
upstream code is:

```z80
xor a
bit 7,(hl)
jr z,$2041
inc a
ld ($C198),a
```

In this observed execution HL points to original fixed-bank0
ROM address **$258D**, and the code writes zero rather than
incrementing A. The independent verifier checks the **actual
ROM byte** at $258D and its bit7 value against the observed
write and the source SHA, instead of inventing a source flag.
The other source-listed explicit writer `$2281`
(`LD ($C198),A`, preceded by `XOR A`) did **not** appear
among the successful physical WRAM writes in either phase.

These data explain the **immediate upstream zero-value flow**
and why subsequent `$9966` JR Z instructions bypassed
`$9932` in this one original 600k-step controlled run.
They do not establish why the source record at $258D has its
particular flag value, nor whether an actual world/player
sprite would be produced under a different authentic game
state.

## Independent acceptance gates

`native/test_pc44_c198_writes.c` uses genuine native Z80
`LD ($C198),A`, `LDI`, and `LDIR` fixtures, verifying
same-value stores, changed bytes, true pre-copy source
registers, HL source bytes, mirrored `$E198` alias,
mapper SRAM exclusion, rejected ROM destinations and phase
transition/reporting.

`native/tools/verify_pc44_c198_writes.py` independently
checks the complete reconstructed original 262,144-byte
cartridge SHA (via PC-43/42 verifier), Phase6 listing/opcode
bytes `$0B1A`, `$2041`, `$2281`, the **exact three source
store PCs/times/bytes and pre-copy register goldens**, all
same-value / changed / alias counts, the source-record bit7
relation, physical WRAM chaining and agreement with **all 13
PC-43 actual bank6 branch reads**. It rejects malformed,
duplicate-key and inconsistent audit reports. PC-34 input,
PC-40/41 historic CPU checkpoints and PC-42 exact bounded
source execution remain unchanged.

No original Ys ROM, tile, audio or frame bytes are committed.
This remains source-ROM CPU execution research without an
independent SMS emulator/hardware comparison, a verified
player, true animation or collision, native world traversal
or any authenticated original-game Alpha gate. Keep the
stacked PR draft and unmerged; stable M45 branch unchanged.
