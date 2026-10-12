# Whole-system reconstruction checkpoint — 2 complete source-only banks

Source truth: supplied 256-KiB USA/Europe Ys SMS ROM, SHA-256 `02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.

## Architecture and verification

Bank 3 and bank 7 are **complete standalone, ROM-independent 16-KiB images**. Their generated combined Z80/DB/DW listings each independently reassemble using the in-project Z80 encoder and data assembler. **The complete 16-bank ROM is NOT source-only**: it still requires 208,895 previously unresolved bytes from the user's original ROM. This distinction is verified in `build_report.json`.

| Metric | Previous | Whole-bank checkpoint |
|---|---:|---:|
| Entirely source-backed ROM bytes | 46,349 | **53,249** |
| Template fallback bytes | 215,795 | **208,895** |
| Byte-complete 16-KiB banks | 0 | **2 (3, 7)** |
| New source-backed bytes | — | **6,900** |
| Newly bounded non-padding bytes | — | **1,969** |
| Newly recognized bank-end padding | — | **1,888** |
| Preserved unresolved visual data bytes | — | **3,043** |
| Newly assembled Z80 instructions | — | **173 bytes** |
| Candidate ROM coverage, including provisional | 58,490 | **60,459** |

No candidate coverage is claimed for 1,888 padding bytes or the 3,043 new unresolved visual bytes. The 6,900 newly source-backed bytes were **not all decoded**. Most game logic outside the two complete banks still requires decompilation.

## Whole bank 3 — exact ownership map

| CPU address (physical bank 3) | Size | Source encoding / confidence |
|---|---:|---|
| `$8000–$95FF` | 5,632 | 176 editable Mode4 tile records (Phase17) |
| `$9600–$9DA2` | 1,955 | Undecoded likely visual/packed data, explicit reversible byte source; not decoded |
| `$9DA3–$9E92` | 240 | 60 four-byte entries: two unknown parameter bytes plus LE text-region pointer |
| `$9E93–$9EFF` | 109 | Candidate glyph/control prefix, byte-accurate, meaning not fully known |
| `$9F00–$B8CC` | 6,605 | Previously source-backed numeric glyph/control lane; not plaintext deciphered |
| `$B8CD–$BFFF` | 1,843 | Verified homogeneous `$FF` padding |
| **Total** | **16,384** | Zero source fallback within bank 3 |

The 60 directory pointers target `$9E93–$B8CC`, and the first pointer is `$9E93`; duplicates and non-monotonic pointers are allowed. Some leading directory parameters appear to be flags/dimensions but **are not assigned invented meanings**.

## Whole bank 7 — exact ownership map

| CPU address (physical bank 7) | Size | Source encoding / confidence |
|---|---:|---|
| `$8000–$80FF` | 256 | Graphics transfer entry and graphics-record pointers |
| `$8100–$817F` | 128 | Secondary-record pointers |
| `$8180–$86C0` | 1,345 | Unrolled Z80 graphics uploader, mnemonics |
| `$86C1–$8876` | 438 | Grid/graphics engine, mnemonics |
| `$8877–$AFBE` | 10,056 | Pixel-level 64 primary graphics records |
| `$AFBF–$B53E` | 1,408 | 64 × 22-byte secondary graphics records |
| `$B53F–$B595` | 87 | RAM initialization Z80 routine, mnemonics |
| `$B596–$B9D5` | 1,088 | Undecoded likely visual/packed data, explicit reversible byte source |
| `$B9D6–$BA0E` | 57 | State-selection Z80 logic, mnemonics |
| `$BA0F–$BA1D` | 15 | Five 3-byte parameter triples, referenced by state logic |
| `$BA1E–$BA3A` | 29 | RAM state-counter Z80 routines, mnemonics |
| `$BA3B–$BA66` | 44 | 22-item pointer directory |
| `$BA67–$BDBE` | 856 | 22 groups of 4-byte tuples with optional zero terminators |
| `$BDBF–$BDD3` | 21 | Selector-byte indices |
| `$BDD4–$BDFD` | 42 | 21-item text pointer directory |
| `$BDFE–$BFD2` | 469 | Indexed text spans, encoded characters/control bytes; not fully deciphered |
| `$BFD3–$BFFF` | 45 | Verified `$FF` padding |
| **Total** | **16,384** | Zero source fallback within bank 7 |

The map-record tuple field meanings and visual coding are still partly uncertain. Pointer-count, boundary, terminator, source digest and identity tests protect these sources.

## Artifact topology

* `tools/whole_bank03.py`, `tools/whole_bank07.py`: completely source-only bank builders; do not require input ROM except explicitly for one-time `--capture`.
* `src/wholebank03/bank03_complete.asm`, `src/wholebank07/bank07_complete.asm`: generated complete mixed instruction/data source listings. Normal checks regenerate them from committed structured sources and require textual identity.
* `tools/build_whole_system.py`: strict whole-ROM overlay; only banks 3 and 7 are complete source-only.
* `tools/wla_whole_system.py`: prepare both external WLA-DX fixtures, or run and verify them **only when actual wla-z80/wlalink are available**. Fixture preparation is not assembly verification.
* `tests_whole_bank03.py`, `tests_whole_bank07.py`, `tests_whole_system.py`: positive and mutation/ownership/system tests.
* `tools/run_whole_system_regressions.py`: legacy regression suites plus new closure gates, machine-readable results in `regression_report.json`.

## Physical-bank closure matrix

| Bank | Source backed | Original-ROM fallback | Byte-complete |
|---:|---:|---:|:---:|
| 0 | 8,242 | 8,142 | No |
| 1 | 779 | 15,605 | No |
| 2 | 3,785 | 12,599 | No |
| 3 | 16,384 | 0 | Yes |
| 4 | 162 | 16,222 | No |
| 5 | 0 | 16,384 | No |
| 6 | 7,192 | 9,192 | No |
| 7 | 16,384 | 0 | Yes |
| 8 | 138 | 16,246 | No |
| 9 | 0 | 16,384 | No |
| 10 | 75 | 16,309 | No |
| 11 | 0 | 16,384 | No |
| 12 | 108 | 16,276 | No |
| 13 | 0 | 16,384 | No |
| 14 | 0 | 16,384 | No |
| 15 | 0 | 16,384 | No |

**Interpretation:** "Yes" means exact 16-KiB byte regeneration with no input ROM, not fully interpreted gameplay. Fourteen banks still contain fallback. The 16-bank matrix is produced and checked by the strict system builder.

## Limitations and next goals

This is **whole-bank source reconstruction**, not completed whole-game decompilation. Two data spans totaling 3,043 bytes are still stored as unresolved byte values. Bank-3/7 text/code-table semantics are not fully determined. The remaining fourteen banks retain original-ROM fallback. Neither independent WLA-DX assembly nor full emulator gameplay traces has been verified in this environment.

Future checkpoints should complete an entire bank or integrated subsystem and pass all regression suites. The next strong candidates are fixed bank 0 and bank 6 sprite/object system. See project root `WHOLE_SYSTEM_PLAN.md` for release criteria.
