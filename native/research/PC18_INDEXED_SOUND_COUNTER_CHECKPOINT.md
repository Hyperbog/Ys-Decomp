# PC-18 — source-backed indexed sound counter and original execution checkpoint

## Source evidence and interpreter scope

The PC-17 genuine source continuation from M45 PC=$0C92 stopped at
physical bank-2 CPU `$8947` after **6,009** additional instructions.
The Phase 5 source listing and unmodified, hash-gated 256 KiB
source-reconstructed cartridge identify these four instructions:

```text
physical $08947  CPU $8947  DD 34 0B  INC (IX+11)
physical $0894A  CPU $894A  DD 7E 0A  LD A,(IX+10)
physical $0894D  CPU $894D  DD 96 0B  SUB (IX+11)
physical $08950  CPU $8950  CC F1 84  CALL Z,$84F1
```

`native/tools/verify_pc18_sound_counter.py` compares all twelve
consecutive physical ROM bytes, full ROM length and immutable
SHA-256, and four independent Phase 5 listing rows. This is byte
and mnemonic provenance; it is not gameplay evidence.

PC-18 implements Z80 `DD/FD 34 d` (indexed memory increment,
**23 T-states**) and `DD/FD 96 d` (indexed memory subtraction,
**19 T-states**) in `native/z80.c`. Both calculate effective
addresses using signed displacements, wrap at 16 bits and use
the existing SMS memory bus/physical bank mapper.

- `INC (IX/IY+d)` updates S/Z/H/PV/F3/F5, clears N and preserves
  carry from the original F register. The flags update **only
  after** a successful write; ROM writes fail closed.
- `SUB (IX/IY+d)` updates A and all Z80 subtraction flags without
  writing memory. Prior carry is ignored by SUB, as on original Z80.
- The existing `LD A,(IX/IY+d)` implementation is unchanged.
- This work extends the **source-reference interpreter**, not
  the native C11/SDL2 player/game scene/audio renderer.

## Tests and CI (verified implementation commit)

`native/test_z80.c` covers the exact four-instruction
`$8947-$8952` source prefix with a controlled RAM fixture and
both taken/not-taken source `CALL Z` outcomes; indexed IX/IY
signed addressing; arithmetic boundaries; flags F3/F5 and
carry/overflow/half-carry; 23/19 cycle timings; ROM-write
rejection; and address wrap at ROM/WRAM boundaries.

The first PC-18 CI run failed **only** on the new regression
expectation that `0x7F → 0x80` did not set H. Authentic Z80
`INC 0x7F` **does** set H (low nibble `F → 0`), so the
expected flag values were corrected; no interpreter implementation
change was needed.

- [PC-18 implementation](https://github.com/Hyperbog/Ys-Decomp/commit/6dfa909bcc1c2ac7c1f81db22ce9a6c5283b64dd)
- [Z80 test-expectation fix](https://github.com/Hyperbog/Ys-Decomp/commit/a6bba84c48c1d1ee71ed43bec7df2a9f69b603fd)

All **three** GitHub Actions workflows on corrected commit
`a6bba84` passed:

- [Native C11, source ROM check and watch](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38825147739):
  **30/30 CTest**, original `$08947` byte/listing check passed.
- [M13–M17 source integrity](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38825147905): PASS.
- [SMS/GG recomp adapter](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38825147722): PASS.

## Measured authentic source continuation

No forced PC, mapper, input, IRQ, RAM, sound command or scene
is injected during the passive original-source watch. CPU/VDP
state continues from verified M45 startup.

| Field | PC-17 | Corrected PC-18 |
| --- | --- | --- |
| Post-M45 genuine source instructions | 6,009 | **6,013** |
| Stop CPU PC | `$8947` | **`$84F1`** |
| Stop reason | unsupported Z80 operation | **unsupported Z80 operation** |
| Physical slot 1 / slot 2 | 1 / 2 | **1 / 2** |
| Recognized IRQs / VBlanks | 57 / 61 | **57 / 61** |
| Mapper-qualified bank1 collision calls | 0 | **0** |
| Physical bank6 `$9932` sprite producer events | 0 | **0** |

The four successfully continued source instructions include
a **naturally taken** `CALL Z,$84F1` at `$8950`. The Phase 5
source listing independently identifies the *next* unsupported
instructions:

```text
physical $084F1  CPU $84F1  DD 5E 03   LD E,(IX+3)
physical $084F4  CPU $84F4  DD 56 04   LD D,(IX+4)
physical $084F7  CPU $84F7  1A         LD A,(DE)
physical $084F8  CPU $84F8  13         INC DE
```

These following instructions are **not yet demonstrated as
executed**. The bounded PC-19 target should be the indexed
`LD E,(IX+d)`/`LD D,(IX+d)` operations (nominal 19 T-states),
with mapper-qualified reads, signed displacement, unchanged flags,
both IX/IY variants, and independent tests before another passive
original-ROM trace. Do not fake source calls to advance the trace.

## Release gates and limits

PC-18 proves no original gameplay collision, actor/player identity,
display-enabled gameplay frame, source bank6 sprite-producing
scene, native audio playback or completed M46c frame wait.
M45 remains the verified Development checkpoint. All five
original-game Alpha gates are false. Draft PR #3 is not promoted,
merged or released.
