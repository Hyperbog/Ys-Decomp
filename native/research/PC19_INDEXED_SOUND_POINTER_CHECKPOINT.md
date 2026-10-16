# PC-19 — original bank-2 indexed D/E pointer reads

## Source and implementation boundary

PC-18's passive, authentic source-cartridge continuation stopped at
physical bank 2 `$84F1` after **6,013 post-M45 instructions**.
The original source at physical `$084F1–$084F8` is independently
documented in `Ys/phase5/code.lst`:

```text
$084F1  $84F1  DD 5E 03  LD E,(IX+3)
$084F4  $84F4  DD 56 04  LD D,(IX+4)
$084F7  $84F7  1A        LD A,(DE)
$084F8  $84F8  13        INC DE
```

The PC-19 addition in `native/z80.c` implements
`DD/FD 5E d: LD E,(IX/IY+d)` and
`DD/FD 56 d: LD D,(IX/IY+d)`, both **19 nominal Z80 T-states**.
Both use signed 8-bit displacement, wrapping 16-bit effective
address and existing SMS bus/mapper reads. They change only the
specified D or E register and leave all Z80 flags unchanged.
The following `LD A,(DE)` and `INC DE` were already supported.

`native/test_z80.c` includes an exact four-instruction source-byte
fixture, independent expected D/E/A/flags/PC/T-state values,
IX/IY positive/negative displacements, 16-bit address overflow,
physical bank 3 mapped into slot 2, and unchanged memory/index
and stack. The controlled fixture is not the original game's RAM.

`native/tools/verify_pc19_sound_pointer.py` checks the
unmodified 262144-byte reconstructed original ROM's known
SHA-256, exact physical bytes and all four Phase 5 listing
lines. No ROM, image or music assets are committed.

**Implementation commit:**
[8ef39a4](https://github.com/Hyperbog/Ys-Decomp/commit/8ef39a4c4f3e510f942db4edc58a9d4c680a2911).

## CI validation of implementation commit

All three workflows on **8ef39a4** completed successfully:

- [Native C11/VDP/sound](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38825718689):
  **30/30 CTest passed**; original source-pointer provenance
  check passed; passive original source watches completed with
  an explicitly unsupported next boundary.
- [M13–M17 source integrity](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38825718628):
  PASS.
- [SMS/GG recomp adapter](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38825718658):
  PASS.

## Measured original-source continuation, no injected game state

The passive reference CPU watch resumes actual source state from
M45 PC=`$0C92`, preserving original mapping, VBlank/IRQ,
unchanged controller state and all game RAM. No forced jump,
actor, scene, player position, sound command or sprite index
is injected to advance execution.

| Measured item | PC-18 | PC-19 |
| --- | --- | --- |
| Post-M45 CPU instruction/refresh steps | 6,013 | **6,027** |
| Next unsupported CPU PC | `$84F1` | **`$85D3`** |
| Physical slot1/slot2 banks | 1 / 2 | **1 / 2** |
| Natural recognized IRQs/VBlanks | 57 / 61 | **57 / 61** |
| Mapper-qualified original collision calls | 0 | **0** |
| Mapped physical bank-6 `$9932` sprite producer hits | 0 | **0** |
| Stop reason | unsupported | **unsupported** |

The source Phase 5 listing establishes that the next original
instruction, **not yet executed**, is:

```text
physical $085CF  CPU $85CF  D6 80     SUB $80
physical $085D1  CPU $85D1  28 03     JR Z,$85D6
physical $085D3  CPU $85D3  DD 86 05  ADD A,(IX+5)
physical $085D6  CPU $85D6  21 58 8A  LD HL,$8A58
```

PC-20 should independently implement/test the Z80
`ADD A,(IX/IY+d)` opcode (`DD/FD 86 d`, nominal **19 T-states**)
with correct S/Z/H/PV/C/N/F3/F5 flags, signed address
calculation, mapper-qualified reads and a passive source
continuation to the next **observed** stop, not an inferred
code target.

## Authenticity and release gate

This reference-CPU source-sound trace is not native audio
playback or gameplay. The five original-game Alpha gates,
live player identity, sprite producer entry and collision
calls remain unverified. The verified Development baseline
remains **M45**. Feature PR #3 stays draft, not merged.
