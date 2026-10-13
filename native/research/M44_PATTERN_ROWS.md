# M44 — Source four-row interleaved graphics pattern upload

## Original cartridge path

After M43's verified 1,536-byte VRAM upload at CPU PC `$0C7E`,
bank-0 source at `Ys/src/phase16/bank00_symbolic.asm` continues:

```asm
$0C7E ld hl,$8000
$0C81 ld de,$4000
$0C84 call $0695  ; compressed graphics to interleaved VRAM
$0C87 ld hl,$A4D1 ; next resource staging; NOT executed in M44
```

The original helper `$0695-$06C0` processes four rows with stride
4 through SMS VDP control/data port writes. A zero header ends each
row; a nonzero header's low 7 bits specify the Z80 `DJNZ` count
(zero means 256); a header with bit 7 clear repeats the following
source byte, while one with bit 7 set reads literal bytes.
`HL` moves through the mapped `$8000-$BFFF` cartridge window.
The source's `RES 7,B` (`CB B8`) was missing from the bounded
native Z80 interpreter and is now implemented with correct 8T
register / 15T `(HL)` timing and no flag modifications.

## Independent differential reference

A small bounded host decoder computes expected VRAM byte writes into
an isolated buffer, with a separate changed-address mask, from the
actual immutable mapped ROM. It does not call Z80, modify VRAM,
synthesize interrupts, or patch source code. It rejects reads beyond
the 16 KiB mapper window, VRAM overflow, or unterminated rows.

The native source trace then executes the original cartridge
`LD HL`/`LD DE`/`CALL $0695`, counts each authentic
`$06A6 OUT ($BE),A`, and returns to `PC=$0C87`.
Acceptance requires:

- exact independent byte match at every pattern-touched VRAM address;
- exact number of actual VDP data outputs versus decoded bytes;
- four row terminations and the original source HL cursor;
- restored caller SP, DE `$4004`, B=0, C=4 and mapper stability;
- naturally generated frame/IRQ clock, never forced status/IRQ;
- bounded instruction budget and source fault diagnostics.

The ROM-free unit test uses *byte-identical bank-0 source opcodes*
for `$0695-$06C0`, `$0C7E-$0C86`, and `$0028-$0030`;
it supplies a synthetic ROM-2 compressed stream with repeated,
literal and empty rows and requires exact interleaved VRAM bytes,
sentinel preservation, real control-port writes and stack unwinding.
A second unit test verifies `RES 7,B` and `RES 7,(HL)` flags
and T-state costs.

## Stage and static recompilation boundary

This milestone uses the **existing C11 Z80 interpreter**, *not*
generated code from SMS/GG Recomp. The independently passing
SMS/GG adapter is limited to ROM identity, opt-in external C
generation, and provenance verification; no generated-C/native-runner
execution or gameplay equivalence has been established.

No `Ys/**` original source data, game ROM or generated C files
are changed or distributed. All Alpha/Beta/Final promotion gates
remain false until genuine interactive Ys PC gameplay is verified.

## Verified M44 source-ROM results

[CI run 38474627069](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38474627069)
passed for the original source-rebuilt 16-bank ROM, with
SHA-256 `02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`:

```text
PASS original Ys 4-row pattern decompression to $0C87: bytes=12288 OUT=12288 sourceHL=$A4D1 Z80steps=382973 T-states=3233133 IRQ=50 VBlank=54 VRAMwrites=18177
PASS authentic timed VDP image: 147471 bytes
```

The initial 200,000-instruction helper bound was insufficient
for 12,288 actual source `OUT` operations. A bounded increase
to 500,000 helper instructions allowed all four original rows
to complete; every expected VRAM output matched. No PC,
IRQ, hardware-state or cartridge contents were patched.
