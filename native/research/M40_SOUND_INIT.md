# M40 — Real bank-2 sound-register initialization and SMS/GG Recomp boundaries

## Source-backed native path

M39 established a natural cross-bank CALL from bank-0 `$0C52`
into physical bank-2 `$8803`, retaining authentic return address
`$0C55`. The next bank-2 code is explicitly identified in
`Ys/phase2/code.lst` as source offset `$08803–$08877`:

| PC range | Original instructions | Expected observable effect |
| --- | --- | --- |
| `$8803–$880C` | `PUSH HL/DE/BC`, `LD HL,$DE63`, `LD DE,$DE64`, `LD (HL),0` | Preserve caller registers; seed zero-valued sound state |
| `$880E–$8820` | Ten sequential `LDI` | Overlapping forward copies zero `$DE63–$DE6D` |
| `$8822–$8838` | Eight `DJNZ` channel-record iterations | Reset sound workspace fields in WRAM |
| `$883A–$883F` | `LD A,$E4`, `LD ($DE68),A`, restore BC/DE/HL | Seed sound-state control byte |
| `$8842–$885D` | Save registers, eleven `OUTI` to port `$7F` | Write original PSG setup bytes at physical bank-2 `$8878–$8882` |
| `$885F–$8872` | Six repetitions of `OUT (C),D` and `OUT ($F1),A` | Write YM2413 addresses `$20–$25` to `$F0`, with zero values to `$F1` |
| `$8874–$8877` | Restore DE/BC/HL and `RET` | Return to source bank-0 `PC=$0C55` |

The native `ys_sms_sound_write` model **records** PSG and FM
writes. It does **not** synthesize sound or drive an audio device.

## Test contract

The M40 `native/test_timing.c` ROM-free fixture uses the
byte-identical bank-2 `$8803–$8821` instructions in the actual
mapper's physical bank 2, with sentinels initialized in
`$DE63–$DE6D`. It verifies exactly ten `LDI` operations,
natural exit at `$8822`, source stack saves, register increments,
and eleven zero bytes without IRQ or timer manipulation.

The gated `ys-native-timed-rom` trace continues **from real Ys reset**
through M29–M39 and executes actual source bank-2 bytes at
`$8803–$8877`. It must:
- reach `$0C55` naturally in a bounded instruction budget;
- verify ten overlapping LDI operations, eleven original `OUTI`
  writes and six each of FM address/data writes;
- verify source zero-cleared command data `$DE63–$DE6D`,
  `$DE68=$E4`, and YM2413 registers `$20–$25` set to zero;
- maintain original bank-2 mapper, stack, HL/DE/BC caller state,
  interrupt counts and VDP write counters;
- fail closed with real CPU fault PC and sound-port counters on any
  unsupported opcode, invalid port, or invariant violation.

`[rom-check]` is required to reconstruct all 16 original ROM
banks (256 KiB, zero binary fallback) and run the authentic trace.
No `Ys/**` original decompilation source bytes, ROMs, or generated
C are edited, committed or distributed.

## SMS/GG Recomp Phase-1 integration review

The connected adapter is `shared_decomp/smsgg_recomp.py`,
configured with `Ys/recomp/game.toml`, Make targets
`recomp-preflight`, `recomp-generate`, `recomp-verify`,
and `recomp-tests`, and CI
`.github/workflows/smsgg-recomp-adapter.yml`.

**Verified integration so far:** SHA-256 plus CRC-32 ROM identity
and a synthetic external-tool mock, three expected generated C file
names (`ys_sms_full.c`, `ys_sms_dispatch.c`,
`ys_sms_layout.c`), tampering detection and generated report
provenance. Gated M39 checked real original source-ROM
SHA-256 `02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`
and CRC-32 `B33E2827`.

**Not verified:** invocation of a real SmsRecomp upstream binary,
compilation/linking of produced C, runtime CPU/mapper/VDP/PSG ABI,
cycle parity, or working game. Such code should remain external and
untrusted until independently reviewed and compared to this
continuous interpreted source trace. Generated proprietary content
must remain out of version control and Development ZIP artifacts.

All Alpha, Beta, and Final release gates remain blocked.

## Real cartridge verification

[CI 38453169948](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38453169948)
passed on [commit b6a7ce1104](https://github.com/Hyperbog/Ys-Decomp/commit/b6a7ce110410e19c4da81d690b8235a2e8758f68):

```text
M10: 16/16 source-only banks, 262144 bytes; ROM fallback=0
SHA256=02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9
PASS Ys source bank-2 sound handoff: PC=$8803 savedPC=$0C55 bank2=2 opcode=$E5 steps=104749 T-states=1194183 IRQ=16 VBlank=20
PASS authentic Ys bank-2 sound init return: PC=$0C55 LDI=10 PSG=11 FMaddr=6 FMdata=6 steps=105009 T-states=1196582 IRQ=16 VBlank=20
PASS authentic timed VDP image: 147471 bytes
```

All 13 native CTest cases passed. This proves register-level
sound initialization on the original source-ROM interpreter;
it is not native audio playback, a statically recompiled runner
or a playable Ys game.
