# PC-16 — original bank-2 EX DE,HL execution checkpoint

## Boundary and source evidence

The last PC-15 authentic source-ROM continuation from independently
verified M45 `PC=$0C92` stopped at physical bank-2 `$8307` after
5,850 post-M45 steps. The opcode was unsupported by the bounded
reference Z80 interpreter, not invalid original game code.

`Ys/phase4/code.lst` and the source-only rebuilt, SHA-256-gated
262,144-byte SMS cartridge independently establish original ROM
physical offset `$08307`, CPU `$8307`: `EB — EX DE,HL`.
The consecutive source region is:

```text
$8302 E5          PUSH HL
$8303 21 13 00    LD HL,$0013
$8306 19          ADD HL,DE
$8307 EB          EX DE,HL
$8308 E1          POP HL
$8309 01 17 83    LD BC,$8317
$830C C5          PUSH BC
```

`native/tools/verify_pc16_sound_exchange.py` checks the original
cartridge digest, full size, contiguous bytes, and independent Phase 4
opcode/mnemonic listing. This is source provenance, **not** gameplay
or complete frame-wait evidence.

## Implementation and verification

`native/z80.c` implements `EX DE,HL` by swapping D↔H and E↔L
in the existing interpreter (4 nominal Z80 T-states). Flags,
accumulator, BC, alternate registers, IX/IY, SP, mapper, memory and
interrupt flip-flops are not modified by the opcode. These are
reference-interpreter semantics, not the C11/SDL2 PC gameplay engine.

`native/test_z80.c` exercises two successive exchanges, both pair
directions, boundary values, unchanged state/flags/memory and
instruction/total T-state accounting. No commercial ROM is committed.

First source-backed implementation commit:
[617812a](https://github.com/Hyperbog/Ys-Decomp/commit/617812a679f5063546be461d5f36ef589610fcff).

GitHub Actions on that exact commit:

- [Native C11 + source watch PASS](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38806564277):
  30/30 CTest cases; original ROM provenance check passed; PC-12/PC-15
  bounded genuine-source watches completed with explicitly blocked gameplay.
- [M13–M17 source integrity PASS](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38806564247).
- [SMS/GG recomp adapter PASS](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38806564604).

## Genuine original-source continuation after PC-16

The same original unpressed-input M45 reference state, without
forced PC, IRQ, mapper, VDP, RAM, palette or synthetic scene,
now reaches the next unsupported operation:

| Observation | Actual CI result |
| --- | --- |
| Continued post-M45 steps | **5,858** (eight beyond PC-15) |
| Stop physical/CPU bank | **bank 2, `$8A4B`** |
| Stop reason | **unsupported Z80 operation** |
| Physical bank mapped at slot 1 / slot 2 | **1 / 2** |
| Naturally accepted IRQs / VBlanks | **57 / 61** |
| Original bank-1 collision calls seen | **0** |
| Original mapped bank-6 `$9932` sprite producer hits | **0** |
| Original sprite record / playable scene identification | **UNOBSERVED** |

`Ys/phase5/code.lst` independently identifies next `$8A4B`
as `DD 7E 08 — LD A,(IX+8)` in the PSG routine, followed by
`AND $0F`, `OR (IX+1)`, `ADD A,$10`, `OUT ($7F),A`, `RET`.
These following instructions are **source listing only**; do not
claim that the interpreter executed them.

## Next independently bounded milestone

PC-17 should implement/test the original indexed `LD A,(IX+d)`
operation with signed displacement, correct nominal timing, and
mapper-qualified byte reads. Resume the passive original source
watch and report the next real stop. Do not inject controller
events or skip sound code to make the M46c frame-wait gate pass.

**Release status unchanged:** M45 remains the verified Development
checkpoint, both feature PRs remain draft, and all five
authentic-game Alpha gates are false. PC-16 did not produce
a playable original Ys frame, validated sprite record, native
music playback, or completion of M46c `$0BC5 → $0AB5`.
