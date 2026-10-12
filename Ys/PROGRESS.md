# Ys: The Vanished Omens — evidence and improvement log

## Checkpoint 001 — Phase 1 baseline

**Branch:** SMS. **Input:** USA/Europe SMS ROM, exactly 262,144 bytes.
**ROM SHA-256:** `02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
**Coverage:** ROM bank 0, file offsets `0x0000–0x0101` (258 bytes).

### Verified (exact ROM bytes)

- `0x0000`: `F3 ED 56 C3 89 00` (`DI`, `IM 1`, `JP 0x0089`).
- The code at `0x0089` writes the mapper ports at `0xFFFC–0xFFFF`.
- `0x00D4` contains 20 word-sized dispatch entries. The meanings of the
  dispatched game states are still unknown.
- The ROM header signature is `TMR SEGA`; calculated cartridge checksum
  `0x5298` matches header value.

### Supported, not yet runtime verified

- The startup sequence at `0x0089` initializes RAM, maps bank 2, and reaches
  a recurring state dispatcher at `0x00C4`.
- Calls into `0x8000–0xBFFF` depend on the active bank; record mapper writes
  before assigning physical ROM offsets.

### Known gaps / quality risks

- `src/bank00_boot.asm` has **not** been assembled into a matching ROM.
- Individual function names are analyst-supplied, not preserved source symbols.
- The existing listing verifier checks transcribed bytes but does not prove
  interpretation, instruction boundaries, or runtime control flow.
- No emulator trace has yet validated function purposes or bank transitions.
- A previous README incorrectly called the cartridge checksum a **BIOS**
  checksum. Correct terminology: **SMS cartridge-header checksum**.

### Improvements introduced at Checkpoint 002

- Persistent `PROCESS.md` with evidence classifications and validation gates.
- Regression tests to check that the ROM fingerprint and listing are accepted
  only when unmodified; wrong-ROM and corrupted-listing cases must fail.
- Explicitly distinguishes byte matching from assembler or behavioral proof.

### Next phase

Trace `0x0102` and startup call sites at `0x0749`, `0x079A`, `0x0BC5`,
`bank 2:$8803`, and `bank 2:$8842`; capture active mapper slot and RAM effects.

## Future checkpoints

Append the next finding with address, evidence, confidence level, test result,
root cause for any failed assumption, and its regression test.

## Checkpoint 003 — Phase 2, bounded Z80 tracing

**Branch:** `SMS`. **Input SHA-256:** same as Checkpoint 001.
**New instruction coverage:** 7 non-overlapping explicit regions; 612 ROM bytes.
**New non-code anchors:** 4 data regions totaling 54 bytes.
**Cumulative non-overlapping ROM bytes classified/checked:** 924
(258 Phase 1 + 612 Phase 2 instructions + 54 Phase 2 data; 0.35% of ROM).
These figures are **byte coverage**, not percentage of game behavior decompiled.

### Results and reasons

- **VERIFIED bytes:** `0102–01AB`, `0540–05F1`, `0749–0767`,
  `0773–0781`, `079A–07D4`, `0BC5–0BEE` in bank 0, and
  `8803–8877` in bank 2. See `phase2/regions.json` and `code.lst`.
- **VERIFIED data bytes:** `01AC–01B3`, `0768–0772`, `0782–0799`,
  `8878–8882`. All match SHA-256-checked ROM.
- **SUPPORTED interpretation:** `079A` verifies and, when needed,
  initializes cartridge save RAM; `0773` updates normalized controller
  state and rising-edge bits; `0540` dispatches through RAM C022;
  bank-2 init at `8803` intentionally falls through into `8842`.
- **POTENTIAL HAZARD:** The interrupt dispatch at `0121` indexes
  from `01AA`, but the four known table entries begin at `01AC`.
  A=0 would select two bytes of executable code. Do not normalize
  this to a zero-based table or assume an unobserved selector range.
- **HARDWARE:** Cart RAM is mapped into `8000–BFFF` when bit 3 of
  `FFFC` is set. Validated against SMS Power mapper documentation.

### Improvement / correction log

- The new scanner uses explicit bounded regions, preserves bank and
  CPU/file addresses independently, rejects unknown ED encodings,
  checks code/data overlap, and compares output against a fixed snapshot.
- A first draft of the region manifest incorrectly ended the 0540
  region inside an instruction at 05D9; corrected the boundary and
  expanded the traced continuation through 05F1. The 0BC5 wrapper
  now includes its complete register-restore epilogue through 0BEE.
- A first draft incorrectly evaluated all relative branch operands
  while building a mnemonic selection tuple. Fixed operand selection
  before consuming branch bytes. Added exact byte-boundary checks.
- Regression checks include acceptance of original ROM and listing,
  refusal of modified ROM, modified listing, and modified data anchor.

### Tests

- Phase 1: `python tests_check.py <ROM>` — **PASS**.
- Phase 2: `python tools/z80_regions.py <ROM> --check` — **PASS**.
- Phase 2: `python tests_phase2.py <ROM>` — **PASS** (8 checks; count corrected in Phase 3).

### Next checkpoint

Analyze the branch-2 entry at `8000`, the 01AC dispatcher targets,
SRAM structure, and verified mapper state across bank-changing calls.
Run a hardware/emulator trace before asserting precise frame behavior.
Do not claim assembler-level or full-ROM binary equality.

## Checkpoint 004 — Phase 3, secondary dispatch and bank-2 updater

**Branch:** `SMS`. **ROM:** same verified SHA-256 as preceding checkpoints.
**New verified code bytes:** 523 in five disjoint bounded regions.
**New verified data bytes:** 18 (secondary dispatch table at `01EB–01FC`).
**Cumulative distinct classified bytes:** 1,465 / 262,144 (0.56%).

### New evidence

- **VERIFIED table:** `01EB–01FC` consists of 9 little-endian destinations
  indexed by the byte at `C105` through `RST 08` after mapping bank 3.
  Zero entry points at a standalone `RET` at `01FD`. No index range beyond
  0–8 is assumed. The table was initially easy to mistake for Z80 code.
- **VERIFIED control flow:** `01C6` selects slot-2 bank 7 before jumping
  to `8819`; `01DA` selects slot-2 bank 3; `$8000` in bank 2 calls `8067`,
  `8080`, `80C0`, `81D9`. No analysis proceeds across untracked remapping.
- **SUPPORTED ledger:** SRAM signature occupies CPU `$8010–$8027`;
  mismatch clears `$8010–$9FFE`. The rest of the save format is unknown.
  Bank 2 uses `$DE60–$DEAF` and 32-byte-stride update records; exact
  use (sound, animation, etc.) is unverified.
- **INCREMENTAL ASSEMBLY:** `src/bank02_update.asm` reconstructs 67
  instructions at bank 2 `$8000–$808E`; all labels and mnemonics agree
  with ROM-backed decoding. No external Z80 assembler executed yet.

### Process improvement

- Reused one bounded scanner for `--phase 2` and `--phase 3` while
  preserving the Phase 2 snapshot byte-for-byte. New tests detect
  overlapping ROM coverage, corrupted secondary tables and code listings.
- Added `tools/check_partial_asm.py` as an intermediate verification gate
  for source label placement and textual instruction alignment. It is
  explicitly **not** an assembler or proof of emitted byte equality.
- Corrected a reporting-only oversight: Phase 2 actually had **8**
  assertions, although its summary previously reported 7.

### Tests

- `tests_check.py` — **PASS**.
- `tests_phase2.py` — **PASS** (8 checks).
- `z80_regions.py --phase 2 --check` — **PASS**.
- `z80_regions.py --phase 3 --check` — **PASS**.
- `check_partial_asm.py` — **PASS** (67 instructions, 11 symbols).
- `tests_phase3.py` — **PASS** (15 checks including negative tests).

### Next checkpoint

Trace bank-2 helpers at `808F` and `81D9`, locate producers of `DE60`,
`DE61`, `DE62` and the 32-byte record arrays. Validate SRAM structure
from emulator snapshots; do not infer save-slot semantics from blanking.

## Checkpoint 005 — Phase 4: command dispatch, FM/PSG identification

**Git branch:** `SMS`. **ROM:** unchanged verified SHA-256.
**New code:** 528 bytes. **New data:** 75 bytes. **New distinct total:** 603.
**Cumulative classified:** 2,068 bytes / 262,144 (0.79%).

### Verified

- The main bank-2 updater and its `$81D9` dispatcher operate on sound
  control: code explicitly writes YM2413 ports `$F0/$F1` and PSG port `$7F`.
- Queued command at `$DE63` selects cases `$81..$9F`, `$A0..$B7`,
  `$B8..$BB`, `$BC/$BD`, or reset, with special `$80` early return.
- ROM table `$81B1` contains two pointers to 18-byte FM register-write
  programs. ROM table `$8CFE` holds the BC and BD handler addresses.
- ROM bytes `$8D40..$8D5E` are loaded by the `$81..$9F` case into
  `$DE61/$DE62` as timing bytes.
- 8 versus 6 update records live in overlapping groups of `$20`-byte
  structures. Decoded record `+3/+4` pointer and `+10/+11` timer accesses.
- The 22-instruction `$81D9..$8203` annotated source is checked against
  byte-based mnemonic decoding; no actual assembly has been performed.

### Iteration improvements and corrections

- Retained verified 1–3 snapshots and added Phase 4 snapshot gating.
- The first new test had a hard-coded instruction boundary off by one
  (`$80FF` instead of `$80FE`); corrected from ROM hex dump, then
  re-ran the new suite.
- Kept data regions out of linear code decoding, especially FM preset
  words and streams embedded between executable functions.
- New tests reject modified listing, data anchor and annotated source.
- Report **14** Phase 4 assertions (do not confuse number of assertions
  with the number of automated test files).

### Current limitations and next

- No runtime sound logging, save-slot identification, or assembler-built
  ROM equivalence yet. The classification ratio is not game completion.
- Next: implement one emitter for actual byte-verifiable assemblable
  segments, trace per-voice FM and PSG event parsing and request producers.

## Checkpoint 007 — Phase 5, large-region sound and state tracing

**Branch:** `SMS`, local. **ROM SHA-256:** same as Checkpoint 001.
**New instruction coverage:** 2,055 decoded instructions, 4,154 bytes
(2,499 fixed bank 0; 1,655 bank 2). **New anchored data:** 780 bytes.
**New distinct total:** 4,934 bytes; **cumulative:** 7,002 / 262,144 (2.67%).

### Evidence

- `phase5/code.lst` and `phase5/coverage.json` are generated deterministically
  by `tools/z80_cfg_phase5.py`; data digests and entrypoints are recorded in
  `phase5/regions.json`.
- A 40-byte dispatch table at bank 2 `8600–8627` contains 20 addresses, all
  pointing to decoded instruction starts. The walker traces the event decoders
  and related FM/PSG routines through `8A57` without treating data tables as code.
- Five additional audio lookup/data spans (`8A58–8D3F`, except Phase 4's
  existing `8CFE–8D01`) account for 740 bytes. Their inner semantics are not
  completely resolved. The `8600` table contributes the other 40 bytes.
- In fixed bank 0, additional state/control/graphics code is byte-matched in
  11 disjoint instruction islands. Functional labels remain provisional.

### Corrected method / failure prevented

- **BANK AMBIGUITY:** The first exploratory walker followed bank-0 call `0DDA
  -> 86C1` into physical bank 2, creating a mid-instruction code collision.
  This is not a valid deduction without the active mapper state. The production
  walker blocks bank-0 -> slot-2 traversals and emits an unresolved edge.
- Static recursive descent from trusted roots is stronger than blind linear
  scanning, but neither guarantees that all labeled bytes run on hardware.
- The scanner separately checks ROM identity, existing classified regions,
  instruction overlap, table SHA-256 hashes, stored listing and metrics.

### Validation

- Original Phase 1–4 checks pass unchanged.
- `tests_phase5.py` passes **15 substantive checks**, including independent
  instruction-byte comparisons and deliberate corrupted snapshots, metadata,
  entrypoints, and ROM rejection.
- **Not verified:** assembled binary round-trip, runtime audio behavior,
  complete bank switching, save format, or full-game execution.

**Next:** track mapper state at `0DDA`, inspect audio stream data beyond `8D5F`,
and convert one isolated routine into a byte-identical assembled module.

## Checkpoint 008 — Phase 6, doubled byte coverage

**Branch:** local `SMS`. **Source:** exact SHA-256 in `manifest.json`.
**Target:** >= 9,868 new bytes. **Delivered:** 14,521 new bytes, comprising
4,474 bank-0 instruction bytes and 10,047 table/opaque-data bytes.
**Cumulative:** 21,523 / 262,144 (8.21%). This is byte typing, **not**
percent of recovered game logic or executable behavior.

### ROM-backed structural evidence

- The `$205A` jump table has 41 words; `$2C24` has nine; their destinations
  are crosschecked against instruction starts from the conservative CFG.
- `$2533` holds 41 references to 23 unique nine-byte records at `$2585`.
- Bank-2 song directory `$8C90` holds 55 entries but 45 unique addresses.
- The first 21 referenced song descriptors are exactly 37 bytes each,
  containing four nine-byte channel records and 84 stream pointers
  (77 distinct). `phase6/audio_descriptors.csv` records only offsets,
  pointer values and byte-hashes.
- Sound byte spans `$8D5F–$AA76`, `$AA77–$AD7F`, `$AD80–$B318`
  are ROM-digest anchored. The first is an opaque event-data area,
  NOT 7,448 bytes of understood music events. A pointer to `$8D57` overlaps
  a previously classified timing table, not counted a second time.

### Safety checks and next objective

- All previous Phase 1–5 regression suites pass; Phase 6 adds independent
  parsing, negative mutation, disjointness, table validity and record checks.
- Omitted `$B319–$B6ED` (981 bytes) from the verified totals rather than
  assert unproven bounds. No audio-event data dumps are tracked.
- Unresolved mapper calls remain logged. No assembler output or emulator
  tracing is claimed. Next: music opcode grammar and assembler round-trip.

## Checkpoint 008 — Phase 7: bank-1 CFG and bank-3 reconnaissance

- **ROM SHA-256:** unchanged. **Git branch:** `SMS`.
- **New static decoded instruction coverage:** 763 bytes / 376 starts, from six
  distinct prior fixed-bank reference targets in physical bank 1.
- **New SHA-256-anchored candidate data:** 14,541 bytes in four physical bank-3
  regions. Their internal meaning remains opaque and provisional.
- **Excluded:** 1,843 bytes of terminal all-`FF` padding from `$F8CD–$FFFF`.
- **Total new candidates:** 15,304 distinct bytes (versus Phase 6's 14,521).
  **Cumulative candidate footprint:** 36,827 / 262,144 (14.05%).
- **Important qualification:** 14,541 new bytes are *not* decoded features or
  proven non-code by a runtime trace. Do not equate candidate footprint with
  decompilation completeness.
- **Bank ambiguity:** calls at bank-1 offsets `47C2`, `486C` and `48DF`
  target CPU `807C`, whose physical bank is unproven.
- **Quality improvements:** script derives bank-1 entrypoints from earlier
  classified fixed-bank code; scans for padding rather than hard-coding it;
  reports evidence tiers and tests rejection of changed ROM or snapshots.
- **Regression:** Phase 1–7 suites and all reproducibility checks passed.
- **Unverified:** Z80 assembler output, runtime mapper states, opaque bank-3
  record grammar, music playback equivalence.

Next: emulator mapper trace, typed bank-3 decoding, an independent Z80
assembler-built byte-for-byte subset. Do not inflate progress by treating
uninterpreted data spans as completed decompilation.

## Checkpoint 009 — Phase 8: contextual bank mapping and Mode-4 tile interpretation

- Corrected an important Phase 5 ambiguity: `$0DD7` writes `$07` to `$FFFF`, so the immediately following call `$0DDA -> $86C1` targets physical ROM bank 7, offset `$1C6C1`, not automatically bank 2. The direct bank-2 `$8803` calls are separately anchored at `$0C52` and `$1D8A`.
- Reconstructed 797 new ROM-backed instruction bytes (502 instruction starts) from conditional roots in banks 4, 7, 8, 10, and 12; recorded 46 slot-2 mapper writes and their directly adjacent constants.
- Recovered a new bank-4 31 × 4-byte lookup-table prefix (124 bytes) indexed by code at `$807C`; contents remain semantically unnamed.
- Reinterpreted 5,632 Phase-7 provisional bytes as 176 reversible Mode-4-compatible 8×8 bitplane tiles; **no double-counting** of these offsets in cumulative coverage. $D600 onward remains opaque.
- **921 new distinct classified bytes; 37,748 cumulative candidate bytes (14.40%).** Binary build equivalence and runtime execution remain unverified.
- Phase 8 adds 14 independent regression/negative checks, restoring reproducible per-bank SHA-256 evidence and pixel round trips. Store code+metadata rather than committing raw game tile payloads or the ROM.

**Next:** instrument live mapper writes and port-BE uploads; independently assemble an extracted Z80 unit, byte-compare output, and probe opaque compressed/text payload grammar by callers.

## Phase 9A — Verified bank-3 graphics upload provenance (partial checkpoint)

- Four fixed-bank call sites to `$0BA1` establish 3,248 source-byte reads, 6,496 emitted VDP bytes, and an 1,184-byte distinct bank-3 source union (already counted earlier).
- Runtime graphics source is grouped into 16-byte units, interleaved with zeros into Mode-4-format VDP data; Phase 8 direct 32-byte tile grouping cannot be assumed to be the on-screen usage for these addresses.
- Restricted two-pass assembly draft is **not yet verified**: original `$06E4=F5`, draft `$06E4=F6`. Proposed fix: move `.WordLoop` to cover `LD A,L` at `$06DA`, not first `OUT` at `$06DB`.
- Original cumulative distinct candidate coverage remains **37,748 bytes (14.40%)**; **0** additional unique ROM bytes classified in this partial phase.
- See `phase9/README.md`. No claims of runtime equivalence or byte-identical rebuild.

## Phase 9B — First assembler-generated byte-identity checkpoint

- **Fixed:** `.WordLoop` is now `$06DA`; both `$06E3` and `$06E5` relative branches land on `LD A,L` rather than `OUT ($BE),A`. Previous `$06E4` mismatch `$F6` versus `$F5` is resolved.
- **Verified:** Independent restricted two-pass Z80 encoder emits **111 bytes** across fixed-ROM ranges `$05F2–$0623`, `$06C1–$06D3`, `$06D4–$06E7`, and `$0BA1–$0BB6`, matching original ROM exactly (11 symbols). `phase9/assembly_report.json` records per-range digests and provenance.
- **Tests:** New `tests_phase9.py` checks instruction-boundary alignment independently, ROM identity, assembly output, VDP callsite analysis, JR/DJNZ destinations and mutations of source, encoder, ROM and derived snapshots. Phase 1–8 suites passed; Phase 9B suite passed separately after a combined-run timeout.
- **Coverage:** 0 additional distinct bytes; **37,748 candidate bytes (14.40%)** remain classified, with substantial opaque/provisional data. **111 assembled bytes** is a separate metric and does not mean 111 new bytes.
- **Not yet verified:** third-party assembler, matching complete 256 KiB ROM, emulator execution, renderer timing or sound playback.

## Phase 10A — experiment paused after two corrections

- Inspected 4,960 previously decoded Z80 instruction starts / 10,188 instruction bytes across the Phase 5–8 listings as candidate assembly-round-trip source (not new coverage).
- Drafted a separate Z80 opcode encoder at `phase10/experimental_z80_roundtrip.py` but stopped after a second failure (`IndentationError` line 168); see `phase10/README.md` for the full traceback and proposed repair.
- No newly matching assembled bytes claimed. Phase 9B's 111 confirmed bytes remain unchanged.
- External assembler unavailable in current environment; no emulator trace or full matching build.

## Phase 10B — recovered production Z80 encoding and sparse bank sources

- Repaired the Phase 10A syntax issue, DD/FD CB opcode selection, missing
  `ADD IX/IY,rr`, and `RLD` versus `RL D` mnemonic collision.
- Generated sparse mnemonic assembly sources for 8 physical banks, covering
  **4,960 instructions / 10,188 unique bytes** from Phase 5–8 static listings.
  Every emitted byte matches both its listing and the original SHA-256-verified
  ROM. Separate decoder checks confirm every instruction length.
- With the Phase 9B subset (111 bytes, 61 overlapping), assembler-output
  union is **10,238 distinct bytes**, no double-counting. **No newly classified
  byte offsets**; cumulative candidate coverage stays 37,748 (14.40%).
- All 10 regression suites passed separately during the same checkpoint.
  New mutation tests reject altered source instructions, listing bytes,
  duplicated offsets, incorrect mapper addresses and changed ROM bytes.
- Limitation: restricted project encoder only, not a third-party assembler,
  full ROM build, dynamic mapper trace, or runnable game rebuild.
- Next: independent external toolchain; faithful symbolic labeling; extend
  original-source code recovery to new, well-supported regions.

## Phase 11A — Sparse Z80 expansion / bank-6 directory (partial)

- The Phase 11 generator successfully assembled **6,158 instructions / 12,439 unique code bytes** from existing Phase 1–10B instruction ranges plus 403 new bank-6 code bytes. This increases code-assembly matching by **2,201 unique bytes** over Phase 10B's all-phase union (no double-counting).
- Bank 6: rooted `$9932` and `$9966` code paths in locally selected `$FFFF=06` contexts, plus a newly classified 64 × 2-byte pointer table at physical `$18000–$1807F`. New classified bytes: **531**. Cumulative candidate footprint: **38,279 / 262,144 = 14.60%**.
- Separate data-reencoding: 5,632 previously classified ROM bytes interpreted as reversible tile bitplanes; combined code+data footprint 18,199 distinct bytes (6.94%). These are different evidence tiers; no runtime-verified semantics claimed.
- All 10 prior-phase regression suites passed when rerun independently. **New Phase 11 test runner is blocked by legacy package imports** (`ModuleNotFoundError: No module named 'z80_regions'` from `bank_trace_phase8.py`). Reached two-attempt correction limit; stopped without claiming a Phase 11 regression pass.
- Status **partial**. See `phase11/README.md` for evidence, exact traceback, and next correction. Git branch remains local.

## Phase 11B — Bank-6 indexed record grammar / regression completion

- **Regression repair:** `tests_phase11.py` adds the `Ys/tools` module path
  before importing `tools.rebuild_phase11`; all 15 Phase 11A assertions and
  mutation gates now pass, resolving the prior `z80_regions` import failure.
- **Verified ROM data:** 64 entries in bank-6 pointer directory at physical
  `$18000–$1807F` point to 64 unique records at `$18080–$19931` (CPU
  `$8080–$9931`). Each record begins with `n` (27–38), followed by `n` bytes
  and `n` pairs of bytes: precisely `1 + 3*n` bytes per record. There are
  2,086 elements and **6,322 contiguous payload bytes**, no overlaps or gaps.
- **SUPPORTED semantics:** `$9932–$9965` has two loops. The first produces
  `n` running-sum bytes starting from memory `$C210` and writes through
  the pointer at `$C028`; the second produces `2*n` bytes, combining running
  sums from `$C211` with a directly copied second byte of each source pair,
  through the pointer at `$C02A`. These are instruction-derived, not
  emulator-traced buffer contents or named game coordinates.
- **New original-ROM classification:** +6,322 distinct structured data
  bytes, bringing candidate coverage to **44,601 / 262,144 (17.01%)**.
  Cumulative assembler-matched Z80 code remains **12,439 bytes**, and
  reversible data increases to **12,082 bytes** (including previously
  classified graphics and the 128-byte pointer table). Combined distinct
  assembly-matched code and reversibly decoded data: **24,521 (9.35%)**.
- **Artifacts:** `phase11/bank6_records.json` stores 64 digests and offsets,
  not payload; `tools/recover_bank6_records_phase11b.py` reversibly decodes
  source bytes and simulates count-delimited loops; `tests_phase11b.py`
  checks size, origins, mutations, and legacy 12,439-byte source stability.
- **Limitations:** No third-party assembler, runnable ROM rebuild, or emulator
  observation yet. `n` is structurally established; interpreting the output
  as player/map/graphics coordinates is only a hypothesis.

## Checkpoint 013 — Phase 12: Sprite attribute table consumer chain

- **ROM-byte verified:** mapper value 6 at fixed-bank `$26F3/$2BF1`, RAM
  output pointers `$C028->$DD00`, `$C02A->$DD40`, producer bank6 `$9932`
  and fixed-bank VDP uploader `$0427–$053F` (64 + 128 `OUTI` bytes).
- **Supported interpretation:** the records describe sprite Y positions and
  interleaved X/tile pairs in the SMS sprite attribute table, rather than
  generic undifferentiated work records. The VDP/SAT behavior is hardware-
  documented but has **not** been independently emulator traced.
- **New:** 119 previously omitted bank6 sprite-handler instructions, 241
  exact ROM-matching bytes through the in-project assembler; 17 object-record
  words, eight handler pointer words, 28+20 byte sprite offset arrays,
  totaling 98 newly modeled data bytes.
- **Contiguous interval audit:** all 7,192 bytes at physical ROM
  `$18000–$19C17` are partitioned into 644 assembler-matched code bytes and
  6,548 structurally audited data bytes, without overlap or unknown fill.
- **Coverage:** 12,680 code; 12,180 reversible data; union 24,860;
  candidate 44,940 (17.14%) — only 339 distinct bytes added this phase.
- **Quality gate:** independent source/ROM decoder comparison and mutation
  rejection of altered dispatcher/table/VDP bytes, edited source, and inflated
  metadata. See `phase12/README.md` and `tests_phase12.py`.

## Phase 13 — Bank-7 data-to-code transfer dispatch

- Reconstructed all of physical bank 7 `$1C000–$1F53E` as **13,631 gap-free
  bytes**: 1,345 new assembler-matched bytes, 438 previously matched code
  bytes, and 11,848 new structurally bounded data bytes.
- The 64-entry directory at CPU `$8000` pairs an unrolled transfer-code
  entrypoint with a variable graphics-source pointer; the 64-entry directory
  at `$8100` indexes 64 fixed 22-byte records. All pointers, lengths,
  boundaries, and hashes are verified against the ROM.
- `$8856` dispatches using `PUSH DE; RET`; 168 copies of `OUTI` followed by
  three `OUT ($BE),A` instructions expand one source byte to four VRAM-write
  bytes with three zero planes. All 64 record boundaries are exact and the
  expansion is reversible.
- Adds 673 ROM-checked instructions and 13,193 new classified ROM bytes.
  Cumulative: 14,025 ASM-matched code, 24,028 reversible data, 38,053 combined
  strong classification, 58,133 candidate/classified bytes (22.18%).
- The source is verified using the in-project encoder, not an external Z80
  assembler or an emulator gameplay trace. Raw graphics bytes remain outside Git.

## Workflow research checkpoint — 2026-10-11

Reviewed decomp.dev's public implementation, decomp.me's FAQ/platform list,
objdiff and decompedia; full notes in `../DECOMP_RESEARCH_2026-10-11.md`.
Added an offline per-module Z80 matching loop and a negative regression suite.
The Phase-13 bank-7 assembly still emits **1,345 exact matching bytes** under
the in-project encoder; a mutated mnemonic is rejected. This adds **0** new
classified bytes and **0** new independent-assembler verified bytes.
Next priorities: full-ROM link/rebuild, independent assembler, unified segment
manifest, stable symbol ledger, and dynamic VDP/mapper traces.

### Phase 14 — full-image integration harness
- Rebuild mode: original-ROM template plus 11 verified sparse Z80 ASM modules.
- Exact bytes emitted by assembly source: **14,025** (unchanged from Phase 13).
- Original-ROM fallback bytes: **248,119**, not counted as completed assembly.
- Full-image SHA-256 checked; wrong ROM/source and overlapping modules rejected.
- Syntactic cross-references: **1,196**, of which **426 mapper unresolved**.
- External SJAsmPlus integration is implemented but has **not** run here (binary
  unavailable). Phase 14 regression suite: **9/9 pass**.
- Candidate footprint still **58,133** bytes; no new classified ROM region.

## Phase 15 — Source-backed data / symbol graph (2026-10-11)

- 678 previously classified bytes now rebuild from local `DB`/`DW` source alone:
  bank 0 = 100, bank 1 = 16, bank 6 = 178, bank 7 = 384.
- Source-backed code + data = 14,703 bytes, with 247,441 original-ROM fallback.
- Candidate coverage unchanged: 58,133 bytes (22.18%), because this is a
  provenance upgrade, not discovery of new ROM content.
- Bank-aware symbol graph: 23 symbols, 1,196 static crossrefs, 12
  mapper-bank candidates from adjacent immediate write/call sequences.
- All 12 Phase 15 regressions pass. No independent assembler/emulator validation.
- Source files exclude raw proprietary graphics and music payloads.

## Phase 16 — structured data provenance / symbolic Z80 (2026-10-11)

- Promoted 7,902 previously classified bytes to declarative, regenerable
  `DB` sources across bank 4 (124), bank 6 (6,370), and bank 7 (1,408).
- Source-backed total: **22,605** = 14,025 assembly code + 8,580 sourced data.
  Original ROM fallback: **239,539** bytes. Candidate/classified 58,133
  bytes (22.18%) unchanged.
- 3 symbolic mnemonic views reassemble 8,579 existing bytes unchanged;
  these are alternate representations, not new byte matches.
- The committed derived JSON contains asset bytes as count/delta/pair fields;
  do not describe this phase as containing only metadata digests.
- Still no independently installed third-party assembler or runtime trace.

## Phase 17 — editable Mode-4 and bank-7 tile sources (2026-10-11)

- Reencoded 176 bank-3 4bpp tiles (5,632 ROM bytes) as pixel-row sources.
- Reencoded 64 bank-7 1bpp graphics records (10,056 ROM bytes) as binary pixel rows;
  lengths and each record SHA checked against Phase 13.
- Source-backed bytes: **38,293**, fallback: **223,851**; original 256-KiB image
  is byte-identical under the template-assisted overlay builder.
- The entire bank-7 interval `$1C000–$1F53E` (13,631 bytes) is now represented
  by code, pointer tables and structured graphics/data sources without fallback.
- Previously classified bytes upgraded: 15,688; newly classified bytes: 0.
  Candidate coverage remains 58,133 / 262,144 (22.18%).
- The new project archive contains user-ROM-derived pixel data, though no ROM image.
  Third-party assembler and emulator runtime validation remain outstanding.

## Phase 18 — bounded executable mapper and VDP checks (2026-10-11)

- Introduced a strictly limited ROM-opcode interpreter, **not** a full emulator.
- Four existing bank-3 call paths actually execute and produce 6,496 VDP data
  writes with SHA-256s matching independently recorded static expectations.
- The fixed-bank sprite routine executes 206 instructions and transfers 192
  bytes to `$3F00` and `$3F80` from synthetically seeded RAM buffers.
- 64 bank-7 unrolled instruction entries execute, yielding 40,224 expanded
  output bytes across individual runs, matching record-specific expansions.
- All **46,912 bytes are VDP output**, not newly classified/source-backed ROM.
- **0** newly classified ROM bytes, **0** new source-backed bytes; source-backed
  total 38,293, candidate total 58,133 (unchanged).
- See `phase18/README.md`; full-system mapper/VDP gameplay traces and a
  third-party assembler remain outstanding.

## Phase 19 — Bank-6 sprite generation and SAT transfer integration (2026-10-11)

- Execute **192** complete ROM-opcode chains (64 sprite record indices × 3
  origin pairs) from fixed-bank `$26F3` through mapped bank-6 `$9932` and then
  fixed-bank SAT upload `$0427` without reseeding the generated RAM buffers.
- Trace `$FFFF=06`, `$C028/$C02A` pointer advancement, `$DD00/$DD40` output,
  `$D0` terminator and the full 192-byte VDP port-$BE transfer per case.
- Compare independently recomputed Y/X/tile arrays and SHA-256 digests for all
  cases, a total of **36,864 VDP bytes across separate runs**.
- New Phase 19 tests: **18/18 passed**. See `phase19/execution_report.json`.
- New classified ROM bytes: **0**; source-backed ROM: **38,293**; candidate
  footprint: **58,133**; fallback ROM bytes: **223,851** (unchanged).
- No full-system emulator observation, renderer verification or independent
  third-party assembler validation is claimed.
- Historical regression validation: **22/22 suites passed** using the Phase 19
  unified runner (includes Phase 11B, matching workflow, and full ROM overlay).

## Phase 20 — Alternate sprite object dispatch and independent-toolchain preparation (2026-10-11)

- Execute 192 bounded ROM-opcode cases through physical bank 6 `$9966 -> $9932 -> $9AA9`, then the original fixed-bank SAT uploader `$0427`. Object attributes are **synthetic**, mapper bank 6 is explicitly selected, and no full-game gameplay or cycle accuracy is claimed.
- Independently calculate the original record buffer bytes, four object-added Y positions/X positions and ROM tile bytes, then match the final 192-byte SAT image per case. Total **36,864 VDP data writes** across 192 separate tests, not new ROM bytes.
- Added **14 Phase 20 tests** including ROM-opcode corruption, wrong bank, budget exhaustion, skip flag and fixture drift rejection.
- Prepared a portable WLA-DX bank-7 test module; `--prepare` passes, but **external WLA assembly was not run** because `wla-z80` and `wlalink` are not installed.
- Added `Ys/Makefile` and a concurrent (up to 4 workers) unified regression runner. The full **23/23 suites passed** and the result is in `phase20/regression_report.json`.
- No new classified/source-backed ROM bytes. Source-backed 38,293; original-ROM fallback 223,851; candidate classification 58,133. No source-only complete build yet.

## Checkpoint — Phase 21: typed music headers and glyph-lane source

- **New structural discovery:** 24 variable bank-2 music headers, `$B319–$B6E7`, 357 bytes in total; the remaining 618 event bytes are pointer-bounded but have no decoded command grammar and remain fallback.
- **Source-backed upgrade:** 8,056 additional bytes from independently regenerated source fields/tokens: 207 bank-0 resource records, 110 bank-2 directory bytes, 777 regular descriptor bytes, 357 new variable header bytes, and 6,605 provisional bank-3 glyph/control bytes.
- **Source-backed union:** 46,349 / 262,144 (17.68%); **remaining ROM fallback:** 215,795. **Candidate classification:** 58,490 / 262,144 (22.31%), +357 distinct bytes, never confused with percentage game functionality.
- Source hash-checked, ROM byte-match gated, explicit old/new ownership checks, and no change to prior assembler-matched code claims. Candidate glyph slots are not decoded plaintext or resolved control messages.
- External WLA-DX not installed; original ROM still needed as a template; no full-system emulator confirmation.

## Whole-system checkpoint — complete physical banks 3 and 7

**Strategy change:** future checkpoints target whole-bank or whole-subsystem closure, not isolated byte-count increments. See project `WHOLE_SYSTEM_PLAN.md` and `whole_system/README.md`.

Both bank 3 and bank 7 independently rebuild all 16,384 bytes each with **no original-ROM fallback**. Total source-backed 53,249/262,144 bytes (20.31%), remaining fallback 208,895. The whole-ROM template-assisted build remains exact. New source backing +6,900 over Phase21. New anchored nonpadding classification +1,969 bytes; new code +173 bytes, explicit FF padding +1,888 bytes; 3,043 visual-looking bytes preserved as **semantically unresolved** source values, not claimed interpreted.

The two-bank output uses our encoder, not a verified external WLA-DX assembly run. Full-system emulator tracing remains outstanding. Detailed per-bank provenance and test commands are in `whole_system/README.md`.

### Whole-system static control-flow inventory (after AI workflow adoption)

A ROM-checked, bank-aware CFG/evidence graph now covers **7,047 reconstructed Z80 instructions / 14,198 bytes**, partitioned into **1,765 basic blocks** with 8,155 classified edges and exits. Its five missing fixed-bank-0 entrypoint candidates and 17 unresolved mapper-dependent references are recorded in `whole_system/frontier.json`. This is **not new classified code or new source-backed ROM data**. Source-backed coverage remains **53,249 bytes** and standalone banks remain **3 and 7**. The system graph is now in the whole-system regression runner; third-party assembly and full-emulator traces remain outstanding. See `whole_system/EVIDENCE_GRAPH.md`.

## Whole-system M3 — physical fixed bank 0 byte closure

Fixed ROM bank0 ($0000–$3FFF) is now a standalone, ROM-independent 16-KiB
image from previous sources + `wholebank00` records + 6,518 additional Z80
instruction bytes in 35 bounded source ranges. Of the 1,624 new sourced data
bytes, 463 are typed pointer/title/padding and 1,161 remain semantically
unresolved. The 16-bank original-ROM overlay is still exact but **only banks
0, 3 and 7 have zero fallback**.

Current source-backed union: **61,391 of 262,144 bytes (23.42%)**; fallback:
**200,753 bytes**. Three standalone banks cover **49,152 bytes**. Static Z80
CFG: **20,716** machine-instruction bytes, **2,726** basic blocks and **11,818**
edges/exits. Five previously missing fixed-bank destinations are now source-
backed, with three new overlapping/nonaligned targets left unresolved
(`$1033`, `$1036`, `$1681`). These are candidate disassembly ambiguities;
linear roundtrip doesn't prove runtime use or disambiguate overlapping code.

External WLA-DX fixtures are prepared for all three complete banks, but
independent third-party assembly remains unexecuted. Full-emulator testing,
other 13 banks, unresolved data formats and complete system behavior remain
unfinished. See `whole_system/M3_README.md` and `wholebank00/README.md`.


## Whole-System M4 — Source-independent bank 6

Bank6 `$8000–$BFFF` assembles from source only, completing the previously
verified 7,192-byte producer/record section plus 9,192 newly source-generated
visual, sprite-layout, tile-index, and padding bytes. Seven count-prefixed
triplet records and two pointer directories round-trip. Existing Phase19/20
bounded sprite interpreter tests remain regression gates. Four complete banks
(0,3,6,7); 70,583 source-backed bytes (26.93%); 191,561 fallback bytes.
External independent assembly and whole-game runtime remain unverified.


## Whole-System M5 — Independent sound bank 2

Source-only physical bank 2 now joins 0,3,6,7. Bank2 contributes 12,599 new
source-owned bytes, including 16 Z80 instruction bytes; 24 song event bodies
are individually pointer-bounded. Unresolved sound-event grammar is not
misrepresented as decoded. Five complete physical banks = 81,920 bytes.
Total source-backed 83,182 (31.73%), remaining template bytes 178,962.
PSG/FM I/O is supported by ROM-assembled Z80 source, not yet emulator-observed.
Third-party assembler and full sound runtime are still unverified.

## Whole-System M6 — Physical bank 1 source closure

All 16 KiB of physical bank 1 now rebuild from checked-in source. Cumulative complete physical banks: **0, 1, 2, 3, 6, 7**, total **98,304** source-only complete-bank bytes. Source-backed total is **98,787** (37.6842%); fallback **163,357**. New source-backed content: 15,605 bytes (1,717 instruction-shaped mnemonic bytes and 13,888 data). Of that data, 13,528 bytes are unresolved. No new gameplay execution trace, external WLA-DX binary assembly, or complete-system semantic certification is claimed.

## Whole-System M7 — physical bank4 source closure and collision execution

Bank4 is now complete as a standalone source-only 16KiB image: **16,222 newly source-backed bytes**, all data (16,064 candidate grouped four-byte lanes + 86 undecoded trailer + 72 pad). Existing bank4 124-byte collision descriptors and 38-byte Z80 routine are kept. Cumulative seven source-only banks **0,1,2,3,4,6,7**, total 114,688 complete-bank bytes; **115,009** source-backed ROM bytes (43.8725%), **147,135** fallback bytes. No graphical tile format claimed proven. The `$807C` collision routine was executed for 3,968 synthetic conditions and checked against a separate field-level predicate; bank1 contains three static calls, but mapped bank4 at invocation is not runtime-confirmed. WLA-DX external verification still outstanding.


## Whole-System M8 — source-only bank 8 and bank 10 closure

Now **9/16 complete 16-KiB physical banks**: 0, 1, 2, 3, 4, 6, 7, 8 and 10.
The 256-KiB ROM has **147,564 source-backed bytes (56.2912%)** and **114,580 original-ROM fallback bytes**.
M8 adds 32,555 source-backed bytes, of which only 38 are newly reconstructed mnemonic instructions; the rest are currently unresolved source data and specifically bounded lookup/text records.

Bank 8 holds an 11x5 lookup table and two code routines. Bank 10 holds an
11-pointer/9-string directory plus a ROM-executed five-digit decimal VDP writer
verified for 265 seeded inputs. These are not proof that the complete game
engine, encoded scripts, or graphics formats are understood. Independent WLA-DX
assembly and full-system gameplay verification remain outstanding.

## Whole-System M10 — Binary reconstruction completed

All 16 physical 16-KiB banks rebuild without original ROM input; output SHA-256 matches `02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`. No template fallback. **The final four banks are predominantly undecoded asset bytes**; independent WLA-DX and full-emulator matching remain unverified. Binary-source completion is not a claim of fully decoded source or total game-logic completion. See `whole_system/M10_README.md`.

## Whole-System M11 — Independent Emulicious boot and WLA-DX source onboarding

- All 16 banks still regenerate from source with exact 256-KiB SHA-256;
  **no new ROM ownership or decoded code** is claimed in this phase.
- Emulicious.jar from the user's portable archive launches under Linux and
  displays the game. Original and M10 source-built ROMs produce exactly the
  same stable title-art pixel SHA-256 (`fea1432fc67f05d2ac2d63f2865392597964794978643f743726c73f5b40f39d`).
- `Ys/tools/emulicious_smoke_m11.py` is the reproducible emulator GUI boot gate;
  `whole_system/emulicious_report_m11.json` records actual external-tool evidence.
- Native WLA-DX adapter added with explicit rejection of user-supplied Windows
  PE releases. Native assembler comparison remains blocked on a source ZIP or
  Linux executables. No fake external-assembly pass is claimed.
- M10 historical regression recheck: 76/76 passed. M11 unit tests: 15/15.
- See `Ys/whole_system/M11_README.md` for commands and verification limits.

## M14 foundation — Bank 13 lossless RLE audit (2026-10-12)

- Source authority: the independent, ROM-free 16-KiB bank 13 build plus
  its 50-word resource directory. No commercial ROM or image previews committed.
- Verified 50 unique directory addresses, sorted by physical address (the
  directory entries themselves are not in ascending order).
- Decoded 50 resource streams with four separately zero-terminated blocks each:
  **200/200 blocks of 72 bytes**; **14,400 decoded bytes**.
- Packet-exact decode/re-encode preserves **10,659 compressed bytes**, with
  **49/49 adjacent pointer boundaries** matching precisely.
- Last resource ends at `$A9A3`. The following **5,607 bytes** through `$BF89`
  remain unresolved; the pointer directory begins at `$BF8A`.
- Per-resource 24×24-pixel/4-bitplane interpretation has a lossless inverse for
  all 50 resources. Source-side pixel indexing is a model and still needs
  independent consumer validation before pixel format is considered final.
- Added `tools/bank13_rle_m14.py`, `tests_bank13_rle_m14.py`, and the
  `whole_system/bank13_rle_m14.json` source-derived report. Tests: 8/8 pass.
- Existing M13 7/7 tests pass; M10 complete source-only cartridge still
  verifies to SHA-256 `02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
- **Next phase:** replace the 10,659 source-opaque compressed bytes with
  declarative decoded blocks and original-packet recipes, without shifting any
  addresses or altering the cartridge hash; analyze Banks 05 and 14–15 after.
