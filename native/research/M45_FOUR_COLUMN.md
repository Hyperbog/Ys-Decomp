# M45 — Original four-column resource decoder and SMS/GG reference boundary

## Source continuation after M44

M44 verified 12,288 real Z80-generated VRAM pattern bytes at
`PC=$0C87`, using 382,973 interpreted source instructions and an
independent reference decoder. The following original bank-0 path
(in `Ys/src/phase16/bank00_symbolic.asm`) is:

```asm
$0C87 ld hl,$A4D1
$0C8A ld de,$C600
$0C8D ld c,$04
$0C8F call $0BEF
$0C92 ld a,$20              ; M45 stops BEFORE this instruction
```

`$0BEF-$0C1F` is the same original interleaved ROM-data decoder
verified for *two* columns by M42; here `C=4` makes it process
four independent compressed resource columns with stride four.
Its zero commands terminate each column. Positive commands repeat
one byte; negative commands copy signed-length literals.
`B=0` on `DJNZ` means 256 iterations, not zero.

## Bounded verification

The native timed trace now:

1. Keeps all M29–M44 execution and source-only ROM checks unchanged.
2. Snapshots actual cartridge bytes at CPU `$A4D1–$BFFF` through
   the currently mapped Sega slot-2 bank, before original execution.
3. Uses an independent bounded host decoder that computes four
   interleaved WRAM columns and their write mask in a separate buffer
   (up to `$C600–$DBFF`); it does **not** write to the CPU or bus.
4. Executes the original `CALL $0BEF` and Z80 opcodes under automatic
   VBlank/IRQ/VDP/PSG timing until exact `PC=$0C92`.
5. Verifies *each* touched WRAM address, the source HL cursor,
   restored stack pointer, DE `$C604`, B=0, C=4,
   mapper stability, natural IRQ/clock monotonicity, source bytes
   consumed and strict instruction bounds.
6. Exports an optional real-ROM P6 frame at the resulting checkpoint
   (not an interactive or complete title screen).

A ROM-free timing fixture independently executes exact source
opcodes for `$0C87–$0C91` and `$0BEF–$0C1F` with a synthetic
ROM containing literal, repeat and empty columns. Sentinels verify
that surrounding WRAM is not overwritten.

## SMS/GG Static Recomp integration status

The SMS/GG adapter is separately implemented at
`shared_decomp/smsgg_recomp.py` with configuration in
`Ys/recomp/game.toml`. Its independent CI verifies hash/CRC
identity, safe external code generation, provenance of the
three C outputs and Ys Makefile integration. Its *gated original-ROM
preflight* runs during native source reconstruction.

This is **Phase 1 only**: no external SmsRecomp-generated C has been
compiled, linked, executed or differentially compared with the native
interpreter. M45 establishes the expected original Z80/WRAM/VDP/IRQ
execution boundary that such an experiment must match; it does not
claim that the recompiler produced a runnable Ys port.

No generated C, original ROM, or source assets may be committed.
Alpha/Beta/Final evidence remains false until genuine interactive
native Ys gameplay is verified. The following program at `$0C92`
and live title rendering remain outside this test.

## Independent source-data bounds correction

The initial gated CI run rejected the independent reference **before**
executing the M45 source routine because its 4,096-byte destination
buffer was too small. The repository's original bank-5 source data
(`Ys/wholebank05/source.json`, ROM-mapped `$A4D1`) decodes to
**exactly 5,344 WRAM writes**, four columns of 1,336 bytes,
consuming **4,425 source bytes** and finishing at
`HL=$B61A`. The final touched destination is `$DADF`.
The host reference now bounds output at `$C600–$DBFF`, verifies
**5,344 writes and 4,425 consumed bytes**, and still compares
every touched byte against independent cartridge-source decoding.
Neither the original game program nor any runtime state is
modified to accommodate the source stream.
