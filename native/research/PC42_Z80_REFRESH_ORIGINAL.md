# PC-42 — original Z80 refresh register, interrupt state and LD A,R

## Research gate

The complete 256-KiB reconstructed **original Sega Master System Ys**
ROM passed through its authentic reset, M45, and 531,478 iterations
of the unchanged bounded PC-34 button-1 input experiment at PC-41.
The native reference interpreter stopped at authentic bank0 `$141A`,
bytes `ED 5F E6 0F`: `LD A,R`; `AND $0F`.

The Z80 `R` register is *not* a random byte and is not the Z80
instruction counter. PC-42 reconstructs R from actual M1 bus cycles.
A read-only original-program checkpoint at the EXACT PC-41
531,478-iteration position verifies authentic PC, mapped ROM
banks, IRQ/VBlank, mode selector, sprite-handler and SAT uploader
entry counts, then logs the actual R and IFF2 before executing
`LD A,R`. Any historical mismatch **fails the entire run**.

## Correct instruction and interrupt semantics

The native C11 Z80 interpreter now models:

- R low seven bits increment exactly once per **M1 opcode/prefix fetch**;
  R bit 7 is preserved. Ordinary immediate operands do not increment R.
- Single-byte instructions: one refresh increment; ordinary ED/CB,
  DD/FD prefix instructions: two. **DD/FD CB d op: exactly two**, not
  four. Repeated LDIR instructions each perform two M1 cycles.
- Every **4-T-state HALT refresh cycle** increments R once, with
  no extra instruction retired or PC increment.
- An **accepted IM1 maskable interrupt** performs one extra R M1
  increment, clears **both** IFF1 and IFF2 and vectors to `$0038`;
  a rejected stack write leaves R and both IFFs unchanged.
- `ED 4F LD R,A` stores all eight bits and takes 9 T-states.
- `ED 5F LD A,R` samples R **after both opcode M1 increments**
  (9 T-states); S/Z/F3/F5 follow the loaded R byte, PV follows
  IFF2, H and N clear, C unchanged.
- Also supports `ED 47 LD I,A` and `ED 57 LD A,I` with
  the same documented IFF2/PV semantics and 9 T-states.

References: Zilog *Z80 CPU User Manual* UM0080, the
[Z80 refresh register reference](https://www.worldofspectrum.net/faq/reference/z80reference.htm).
Neither source substitutes for independent cycle-exact hardware
or an emulator reference trace.

## Tests and reproduction

Independent strict C11 `test_pc42_refresh.c` validates M1/prefix/
indexed-bit counts, R bit7 retention across two wraps, LD R,A and
LD A,R/I flags, ALT register stability, HALT refresh, EI delay,
IM1 acknowledgement, IFF2 clearing, fail-closed stack pushes,
and LDIR repetition. Prior complete native test suite remains
mandatory, as do ROM SHA, M13–M17 source rebuild, PC34–PC41
original provenance and 300k prefix, and the malformed JSON
rejection CI check.

No ROM or media bytes are committed. This is source-only
interpreter progress, **not** original game recreation,
an independently confirmed player sprite, a real original
collision call, or any original-game Alpha milestone.
Source-only YS release at M45 stays unchanged. The PC-42
feature branch is draft, stacked on PC-41, and unmerged.
