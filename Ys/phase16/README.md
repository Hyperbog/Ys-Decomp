# Phase 16 — Structured ROM sources and symbolic Z80 views

Checkpoint: 2026-10-11. This phase **upgrades previously classified ROM data to
buildable sources**; it does **not** discover 7,902 new ROM bytes.

## What changed

The source-backed ROM image has increased from **14,703 bytes** to **22,605
bytes** (8.6231% of the 256-KiB ROM). Remaining original-ROM fallback is
**239,539 bytes**. The full result has the expected SHA-256 only because the
unknown bytes are copied from the user's original ROM; this is **not** a
source-only rebuild or third-party-assembler match.

| Recovered data in new DB sources | Physical bank | Bytes | Evidence |
| --- | ---: | ---: | --- |
| 64 counted sprite records, delta arrays and delta/literal pairs | 6 | 6,322 | Phase 11B record sizes, hashes and `$9932` consumer |
| Two sprite-offset tables | 6 | 48 | Phase 12 bounded tables and hashes |
| 64 × 11-pair secondary graphics records | 7 | 1,408 | Phase 13 22-byte stride and per-record hashes |
| 31 × four-byte index records | 4 | 124 | Phase 8 bounded indexed lookup and SHA-256 |
| **Newly source-backed** | | **7,902** | All reencoded and ROM-matched |

The committed `records.json` stores **field-level byte arrays** for those
records. It is a transformed representation of some user-provided game asset
content, so unlike prior phases it **does include extracted data values**, but
still does not include a complete ROM, music streams or graphics bitmaps.
This distinction is intentional and should be considered before publishing
the repository publicly. Field names such as `delta_y`/`delta_x_and_tile` are
reverse-engineering hypotheses based on the consumer. The second records'
22-byte pairs and bank-4 quadruples do not yet have established semantic names.

`structured_data_phase16.py` has two modes:
- `--capture <original-ROM>` extracts transformed records **during development**.
  It checks the existing per-record digests and never accepts a different ROM.
- `--sync` or `--verify` generates or verifies the banked `DB` modules entirely
  from committed JSON, **without reading the original ROM**.

The existing canonical Z80 assembly is untouched. Three new views in
`src/phase16/` introduce symbolic hardware and RAM addresses via a strict EQU
substitution layer. They reencode to the **same 8,579 instruction bytes** as
the three original input modules and are deliberately **not counted again**
in coverage. This is not a general-purpose Z80 assembler's complete symbol
resolution; it is a constrained, tested preprocessing stage.

## Full-ROM ownership

| Provenance | Bytes |
| --- | ---: |
| In-project Z80 assembler-backed instructions | 14,025 |
| Phase 15 `DB`/`DW` tables | 678 |
| Phase 16 structured `DB` record sources | 7,902 |
| **Total source-backed** | **22,605** |
| Original-ROM fallback | 239,539 |
| **Total ROM** | **262,144** |

The previous **58,133-byte candidate/classified footprint (22.18%)** remains
unchanged. Reencoding a previously classified table improves provenance, not
unique ROM coverage. External assembler verification and emulator traces are
still pending.

## Reproduce

From the project root, with the original ROM provided separately:

```bash
python Ys/tools/structured_data_phase16.py --verify
python Ys/tools/symbolic_asm_phase16.py --verify
python Ys/tools/build_phase16.py '/path/to/Ys.sms' --verify
python Ys/tests_phase16.py '/path/to/Ys.sms'
```

Optional local full-image output (never commit the resulting ROM):

```bash
python Ys/tools/build_phase16.py '/path/to/Ys.sms' --verify --out /tmp/ys-phase16.sms
```

## Verification scope

- Rebuilds all 7,902 data bytes from semantic arrays without consulting the
  original ROM during source generation.
- Checks source-vs-ROM bytes, all per-record length/count invariants,
  per-record SHA-256, aggregate count, bank mapping and code/data overlap.
- Assembles three symbolic view modules and compares the emitted byte maps to
  existing ROM-matched Z80 instruction sources.
- Rejects mutated counts, data bytes, duplicate indices, wrong mapper/symbol
  addresses and invalid ROM fingerprints.
- Earlier regression suites have been exercised separately; consult the
  Phase 16 checkpoint log for exact scope.

## Next

Replace remaining fallback with semantic source wherever possible; avoid
copying opaque bytes solely to inflate metrics. Add emulator-backed runtime
mapper/VDP traces and test with a **real** external Z80 assembler when an
executable is available.
