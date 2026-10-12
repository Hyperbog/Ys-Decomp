# Whole-System Milestone 10 — ROM-independent 256-KiB cartridge reconstruction

**Binary build status:** All **16 physical banks** are now completely source-backed and can regenerate the complete 262,144-byte SMS ROM without loading the owner's game ROM or prebuilt bank binaries. The source-built SHA-256 is:

`02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`

**Do not confuse byte-identity with full decompilation.** The final four banks contain **64,439 bytes of explicitly unresolved assets**, 100 bytes of a structurally verified 50-word bank-13 pointer directory, and 997 bytes of verified `FF` fill. Several earlier banks also retain many source-backed but semantically unresolved bytes, some of which may be unidentified code. No newly recovered Z80 instruction bytes are claimed for M10. Much of the source reproduces data captured from the owner's ROM; reconstructing those bytes is not equivalent to understanding the encoding or design. This is the completion of the **binary-source ownership and rebuild** milestone, not complete source-level reverse engineering.

## New source ownership

| Bank | ROM offsets | Source ownership | Evidence |
|---|---|---|---|
| 5 | `$14000–$17FFF` | Unresolved resource bytes `$8000–$BC5A`, `FF` fill `$BC5B–$BFFF` | Full 16-KiB digest; 933 fill bytes |
| 13 | `$34000–$37FFF` | Unresolved bytes `$8000–$BF89`; 50 LE pointers `$BF8A–$BFED`; fill `$BFEE–$BFFF` | All 50 pointer values uniquely target `$8000–$BF89`; 18 fill bytes |
| 14 | `$38000–$3BFFF` | Unresolved bytes `$8000–$BFD5`; fill `$BFD6–$BFFF` | Full digest; 42 fill bytes |
| 15 | `$3C000–$3FFFF` | Unresolved bytes `$8000–$BFFB`; fill `$BFFC–$BFFF` | Full digest; 4 fill bytes |

The 50 bank-13 pointers are an observed directory. Their target-format semantics and runtime consumers are **not established**. Neither these pointers nor repeated FF bytes establish a graphics or text encoding. No evidence-backed instruction entrypoints were identified in these four banks in this milestone.

## Source-only build, no game ROM required

```sh
cd Ys
python tools/build_system_m10.py --check
python tools/build_system_m10.py --out /tmp/reconstructed_ys.sms
python tools/whole_banks05_13_14_15.py --verify-mixed
```

These commands use committed source and the in-project restricted Z80 encoder. The `--out` path is deliberately outside Git, and a ROM file is not committed or distributed. Optionally compare against a privately held owner ROM:

```sh
python tools/build_system_m10.py --check --verify-rom '/path/to/owner/Ys.sms'
python tools/run_system_m10_regressions.py '/path/to/owner/Ys.sms' --jobs 4 --timeout 600
```

## Reproduction controls

- All 16 bank sources contribute exactly 16,384 bytes with no overlap, missing section, or fallback.
- The standalone full-cartridge builder enforces the **original 262,144-byte SHA-256** even when no ROM is supplied.
- For the four new banks, the committed combined `DB`/`DW` assembly is regenerated from versioned source JSON; it must match exactly and round-trip through the in-project mixed assembler.
- Negative tests reject bad asset bytes, chunk gaps, malformed pointers, changed pointer aliases, invalid fill lengths, changed source schemas, and incorrect owner ROMs.
- Project-wide regression tests and the architecture-neutral evidence audit check source ownership and per-bank fingerprints.
- The WLA-DX adapter prepares all 16 banks. Without installed `wla-z80` and `wlalink`, **no external assembler result is certified**.

## Remaining whole-system work, in priority order

1. **Independent assembler:** successfully assemble/link all bank sources using a third-party Z80 assembler (WLA-DX preferred). Resolve any syntax/placement discrepancies without altering the ROM reference or hiding mismatches.
2. **Full-system emulator verification:** boot the ROM in an independent, accurate SMS emulator; exercise menu/gameplay; record frame, mapper, VDP, PSG and YM2413 observable traces; compare ROM-derived baseline and rebuilt cartridge.
3. **Semantic decoding of resources:** recover compression schemes, tile/script layouts, all text and audio command formats, and the actual consumers of the bank-13 resource directory. Preserve reproducible back-and-forth converters and assertions.
4. **Resolve code/data ambiguities:** disambiguate overlapping entrypoints, code hidden in still-opaque resource regions, and mapper-dependent call targets. Replace opaque `DB` statements with actual mnemonics **only where evidence supports executable code**.
5. **Source quality and modding:** meaningfully name functions/RAM entities, deduplicate data models, document system-level inputs/outputs, and validate changes on the emulator in addition to matching the original ROM.

A 100% source-backed byte count is a **binary reconstruction metric only**. It is not a game-functionality decompilation percentage, a compiler-independent proof, or a full-game behavioral equivalence result.
