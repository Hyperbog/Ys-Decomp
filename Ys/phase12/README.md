# Phase 12 — Sprite attribute table (SAT) and bank-6 sprite handlers

**ROM:** USA/Europe 256-KiB Sega Master System dump; exact SHA-256 in `../manifest.json`.
**Status:** Reproduced ROM-byte assembly and reversible data boundaries. No emulator trace, third-party assembly, or whole-ROM matching build.

## Corrected interpretation of the Phase 11B records

- At fixed bank `$26F3–$2706`, the game maps ROM bank 6 to CPU `$8000–$BFFF`, initializes RAM pointer `$C028` with `$DD00` and `$C02A` with `$DD40`, then calls bank 6 `$9932`. A second path at `$2BF1–$2C04` establishes the same mapper and destination pointers before jumping to `$9966`.
- Bank 6 `$9932` reads one of 64 count-prefixed records and writes **one byte per element** to the `$DD00`-rooted destination, and **two bytes per element** to the `$DD40`-rooted destination. The running-sum origins are `$C210` and `$C211`.
- Fixed bank `$0427–$053F` writes the RAM buffers to the VDP data port `$BE`. The first 64 `OUTI` operations read from `$DD00`; then the routine sets VDP address `$3F80` and performs 128 `OUTI` operations reading from `$DD40`. The two-byte control-port sequence first selects `$3F00`. On the SMS Mode-4 VDP, these are the two halves of the 64-entry sprite attribute table (Y; then X/tile-number pairs).
- Bank 6 `$9A71` emits `$D0` after the `$DD00` Y stream. This agrees with the SMS sprite termination convention **in 192-line display mode**; it does not prove all 64 records execute, that the active display mode has been traced, or that every candidate record represents one screen layout.
- The recovered record is therefore **sprite-position and tile-index candidate data**, not a generic compressed record. This is an inference supported by the ROM's producer → RAM buffer → VDP upload chain, *not* a runtime-observed behavioral claim.

## Bank-6 bounded region: contiguous 7,192 bytes

**Physical ROM `$18000–$19C17` (exclusive end `$19C18`).** The complete interval is accounted for without an unknown or opaque gap.

| Component | Physical offsets | Bytes | Verification |
|---|---|---:|---|
| 64 pointer words | `18000–1807F` | 128 | Phase 11A, referenced at `$9932` |
| 64 count/delta/literal records | `18080–19931` | 6,322 | Phase 11B, reversible parsing |
| Previously reconstructed bank-6 instructions | `19932–19AF6` and others | 403 | Phase 11A encoder |
| Newly reconstructed sprite-handler instructions | `$19A??–$19C17` excluding data islands | 241 | Phase 12 encoder, 119 instructions |
| 17 work-object pointer words | `19A77–19A98` | 34 | `$C200` through `$C500`, stride `$30` |
| 8-entry sprite-handler dispatch | `19A99–19AA8` | 16 | ROM `RST $08` dispatch from `$9A68` |
| 14-element sprite-offset data | `19B29–19B44` | 28 | Referenced by handler `$9AF7`, 14-iteration loop |
| 16-element sprite-offset data | `19B7C–19B8F` | 20 | Referenced by handler `$9B45`, 16-iteration loop plus four horizontal offsets |
| **Total** | `18000–19C17` | **7,192** | Complete non-overlapping byte partition |

The new region additions total **339 distinct ROM bytes**: 241 newly assembled instructions and 98 newly structured table bytes. All other bytes above were already counted. The 7,192-byte region is **not** new coverage, nor an indication that a 7-KB standalone ROM can execute.

## Dispatch pointers

The 8-entry function table at CPU `$9A99` contains: `$9AF6`, `$9AA9`, `$9AF7`, `$9B45`, `$9B90`, `$9BC1`, `$9BB9`, and `$9BF4`. The table's entries all point to decoded instruction boundaries. The indirect dispatcher is reached through `LD HL,$9A99; RST $08`; execution of a particular handler is conditional on a runtime index whose valid values have not been observed.

A second table at `$9A77` contains 17 RAM pointers `$C200,$C230,...,$C500`. The routine iterates over `$30`-byte-spaced object records; the `$9AA9` handler reads object offsets `+16/+17` and emits paired sprite positions and tile numbers to the two RAM buffers.

## Cumulative accounting

| Metric | Phase 11B | Phase 12 | Newly added |
|---|---:|---:|---:|
| In-project assembler-matched code | 12,439 | 12,680 | 241 |
| Reversibly structured data | 12,082 | 12,180 | 98 |
| Code + structured data (unique) | 24,521 | 24,860 | 339 |
| Candidate/classified ROM bytes | 44,601 | 44,940 | 339 |

The candidate footprint is **17.14%** of 262,144 ROM bytes; the stronger code/structured-data union is **9.48%**. Neither is the percentage of completed gameplay decompilation.

## Reproduce

```sh
python Ys/tools/phase12_sprite_pipeline.py '/path/to/Ys.sms' --check
python Ys/tests_phase12.py '/path/to/Ys.sms'
```

The generator verifies original ROM SHA-256, Phase 11 boundaries, new code and data islands, the SAT upload code, source mnemonic assembly, and metadata snapshots. Negative tests deliberately alter source listings, metadata, and ROM bytes. No copied record payloads or complete extracted game art are distributed in this repository.

## Next directions

1. Collect emulator RAM and VDP traces to confirm the `$DD00/$DD40` buffers and `$3F00/$3F80` destination behavior during play.
2. Identify which of the 64 indexed records are referenced under which stage/state and recover symbolic object and tile names.
3. Expand assembly verification to more physical banks; validate against a separately implemented assembler when available.

## Independent hardware references

- [SMS Power: Official Sega Master System documentation](https://www.smspower.org/Development/SMSOfficialDocs) — 256-byte sprite attribute table, 64 Y positions, X/tile pairs, default `$3F00` base.
- [SMS Power: VDP registers](https://www.smspower.org/Development/VDPRegisters) — register 5 selects the actual sprite table base.
- [SMS Power: Sprites](https://www.smspower.org/Development/Sprites) — `$3F00` Y field, `$3F80` interleaved X/tile pairs, `$D0` termination in 192-line mode.
