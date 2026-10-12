# Phase 21 — Recover bank-2 variable music headers and source-backed candidate glyph lanes

## Evidence and status

Input: **Ys: The Vanished Omens (USA, Europe)**, 256 KiB, exact SHA-256 in `../manifest.json`.
Git branch: `SMS` (local only). All 16 physical bank boundaries in the builder are unchanged.

**Distinct new structural classification:** 357 bytes, comprising all 24 count-prefixed **variable music descriptor headers** in physical ROM bank 2 at CPU `$B319–$B6E7`. The 55-entry directory at `$8C90–$8CFD` supplies exact starts. Entries 31–54 point to 24 strictly increasing starts `$B319..$B6CA`. Each header starts with channel count **1 or 2** and contains that many nine-byte channel records. Each record contains a 16-bit little-endian stream pointer in bytes +3/+4, and every variable pointer is at or after its header end but before its *next* header. The last event stream ends in `$FF` at `$B6E7`; `$B6E8` is an investigated boundary, *not* an established general music parser rule. The **618 bytes** of event trailers within the 975-byte span remain **opaque, fallback-sourced**, and are not counted as newly structurally classified.

The 21 regular descriptors at `$AA77–$AD7F` comprise four nine-byte channel records each (`21 × 37 = 777` source bytes), plus the song directory (`110` bytes). The 23 nine-byte fixed-bank resource records `$2585–$2653` (`207` bytes) have established nine-byte boundaries from the `$2533` lookup directory, but their inner field meanings remain unidentified. These three regions were already in earlier candidate coverage; they have become byte-for-byte source regenerable here.

The remaining 6,605 bytes of the previously provisionally counted bank-3 span `$DF00–$F8CC` are now represented as **candidate glyph slots (`$C3..$DC`), repeated `$E7`, `$FE`, and `$FF` markers, and explicit unresolved bytes**. The byte-to-symbol transform is deterministic and reversible; it **does not decode the game's text, establish literal English letters, assign control-command semantics, or establish reachability**. In particular, numeric glyph slots `0–25` are *not* an ASCII alphabet. These were already classified as opaque candidate data in Phase 7, so the new source backing is not new candidate coverage. The JSON source contains transformed content from the user's original ROM.

## Source-backed ROM accounting

| Newly source-backed data | Bytes | Coverage meaning |
|---|---:|---|
| 23 × 9-byte bank-0 resource records | 207 | Existing classified opaque records, field structure still unknown |
| 55 bank-2 song pointers | 110 | Existing classified pointer directory |
| 21 four-channel regular audio headers | 777 | Existing classified audio descriptors |
| 24 one/two-channel variable audio headers | **357** | **New structural classification** |
| Bank-3 candidate glyph/control token stream | 6,605 | Existing provisional region, unknown control grammar |
| **Phase21 new source-backed total** | **8,056** | ROM-independent emission from checked-in structured source |
| Prior backed total | 38,293 | Code, tables, sprite/graphics sources through Phase17 |
| **Cumulative backed** | **46,349 / 262,144 (17.68%)** | Stand-alone *partial* source; full ROM still uses fallback |
| **Original-ROM fallback** | **215,795** | Unknown/unreconstructed bytes provided by original cartridge |
| **Cumulative candidate classification** | **58,490 / 262,144 (22.31%)** | Prior 58,133 + new 357, not completion percentage |

## Technical implementation

`tools/phase21_semantic_sources.py` reads only committed `phase21/source.json` and `digests.json` in normal operation. It byte-emits a typed record directory, nine-byte audio channel records (prefix bytes 0–2, LE pointer bytes 3–4, flags/unknown bytes 5–8), count-prefixed headers, and candidate glyph-slot/control token spans. ROM access is **only** by explicit `--extract` to create the checked-in source once, or by the complete build for the final strict fingerprint/byte comparison. Extraction is never necessary for ordinary source generation.

`tools/build_phase21.py` extends the earlier verified Phase17 ROM overlay, strictly rejects old/new overlap and source drift, and checks every emitted byte against the user's full, SHA-verified ROM. The output ROM's SHA-256 exactly matches `../manifest.json`. The source-backed coverage ledger is per physical bank, and the 357 previously unclassified header bytes are distinguished from already counted fallback upgrades. `tools/run_regressions_phase21.py` runs all prior suites independently with the established Phase14/15 contracts and adds new Phase21 and exact build verification.

**Integrity limits:** partial ROM source, no independent WLA-DX output, no full-system emulator trace, no decoded dialogue/audio opcode grammar. Existing bounded Z80 tests do not imply full-game execution. Treat apparent English-like glyph slot strings as numeric indices only.

## Reproduce

```sh
ROM='/path/to/Ys - The Vanished Omens (USA, Europe).sms'
cd Ys
python tools/phase21_semantic_sources.py --verify  # no ROM required
python tools/build_phase21.py "$ROM" --check
python tests_phase21.py "$ROM"
python tools/run_regressions_phase21.py "$ROM" --jobs 4 --timeout 120
make data-verify
make verify ROM="$ROM"
# Requires independent executable installation, NOT a passing check here:
make wla-verify ROM="$ROM"
```

## Follow-on priorities

1. Independently assemble bank-7's 1,345-byte module using `wla-z80`/`wlalink` once their binaries are installed. The checked-in adapter is only a fixture when no executables exist. Search for distro/toolchain availability or use a controlled machine for that comparison.
2. Reverse the bank-3 glyph mapping and `$FE/$FF` control grammar by identifying actual code consumers. Only then convert numeric glyph tokens into readable text source; do not infer semantics from visual coincidence.
3. Execute the bank-2 sound command parser against described record inputs under an instruction-level harness; verify YM2413/PSG writes and new variable channel-pointer handling.
4. Recover more Z80 source from CFG-anchored control flow and eventually replace all 215,795 original-ROM fallback bytes, without treating raw opaque dumps as understood source.
