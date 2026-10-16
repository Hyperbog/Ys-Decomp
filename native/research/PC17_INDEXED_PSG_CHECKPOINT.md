# PC-17 — source-verified indexed PSG operations and original continuation

## Scope and source evidence

The prior PC-16 implementation removed the original sound-engine
`$8307: EX DE,HL` execution blocker, moving the passive trace from
5,850 to 5,858 post-M45 source instructions. The next stop was
`$8A4B` in physical ROM bank 2.

The independent `Ys/phase5/code.lst` listing and the hash-gated,
source-only reconstructed 262,144-byte cartridge establish:

```text
ROM $08A4B  CPU $8A4B  DD 7E 08  LD A,(IX+8)
ROM $08A4E  CPU $8A4E  E6 0F     AND $0F
ROM $08A50  CPU $8A50  DD B6 01  OR (IX+1)
ROM $08A53  CPU $8A53  C6 10     ADD A,$10
ROM $08A55  CPU $8A55  D3 7F     OUT ($7F),A
ROM $08A57  CPU $8A57  C9        RET
```

The checker `native/tools/verify_pc17_psg_source.py` independently
compares the full source-cartridge digest, each physical byte and each
Phase 5 mnemonic. The `[rom-check]` workflow invokes that checker
after a fresh source-only build. No commercial ROM image is committed.

## Bounded reference implementation

In `native/z80.c`, the bounded Z80 *reference interpreter* now
supports `DD/FD 7E d: LD A,(IX/IY+d)` and
`DD/FD B6 d: OR (IX/IY+d)`, each with a signed 8-bit displacement,
16-bit effective-address wrap and 19 nominal T-states. The indexed
load preserves F; indexed OR updates Z80 S/Z/PV/F3/F5 and clears
H/N/C. Existing SMS mapper/bus reads are used without synthesizing
ROM or RAM values.

`C6 n: ADD A,n` uses the existing 8-bit arithmetic flag oracle
and 7 nominal T-states. The test module exercises a six-instruction
source-byte PSG fixture with controlled RAM and attached PSG observer,
signed IX/IY displacements, ROM mapping, address wrap, flag
preservation and half-carry/overflow/carry/zero. A synthetic PSG
fixture is **not** a recorded source-game sound event.

First implementation commit:
[c30b1af](https://github.com/Hyperbog/Ys-Decomp/commit/c30b1af64e4043cf030ec38f43a07353572c254a).

CI on that exact commit:

- [Native C11 and original source watch PASS](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38823891573):
  **30/30 CTest** and original PSG byte/listing check passed.
- [M13–M17 source integrity PASS](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38823891584).
- [SMS/GG adapter PASS](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38823891678).

## Actual original-source continuation

The unchanged original M45 source CPU/VDP/mapper/IRQ state, with the
unpressed input fixture and no fake scene or program counter, now
produces the following result in the PC-12 and PC-15 passive
observer runs:

| Observed field | CI value |
| --- | --- |
| Post-M45 continuation steps | **6,009** |
| Previous PC-16 continuation steps | 5,858 |
| New stop CPU address / original physical bank | **$8947 / bank 2** |
| Stop reason | **unsupported reference Z80 opcode** |
| Mapped physical slot 1 / slot 2 | **1 / 2** |
| Natural accepted IRQs / VBlank events | **57 / 61** |
| Observed original mapped bank-1 collision calls | **0** |
| Observed original mapped bank-6 `$9932` sprite producer calls | **0** |
| Original player, active sprite record and game scene | **UNOBSERVED** |

The independently reconstructed Phase 5 source listing identifies
the *next* opcode at physical `$08947`, CPU `$8947`:

```text
$8947  DD 34 0B    INC (IX+11)
$894A  DD 7E 0A    LD A,(IX+10)
$894D  DD 96 0B    SUB (IX+11)
$8950  CC F1 84    CALL Z,$84F1
```

**Do not claim execution of these instructions.** They are the next
source-backed implementation candidates. The immediate gap is the
indexed read-modify-write `INC (IX+d)`, requiring correct Z80
flags (carry preserved), cycle timing, signed address calculation,
bus/ROM-write guarding and independent tests. The following indexed
subtraction is a separate coverage gap; implement only when justified
and continue until the next *actual* bounded execution stop.

## Release boundary

**M45 remains the verified Development release.** PC-17 added no
authenticated original playable Ys frame, map collision event,
player/actor identity, automatic live controls or PC native sound
playback. All five authentic Ys Alpha gates are still false.
Do not merge draft PR #3 or declare the separate M46c frame-wait
experiment verified on the basis of this bounded source trace.
