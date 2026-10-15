## Enhanced native Ys PC port (new track)

**PC-14 sprite integration:** [Original 64-record bank-6 SAT source pipeline](native/research/PC14_ORIGINAL_SPRITE_SAT.md)
is reproduced independently in native C11 and checked against
192 original-Z80 SAT hash cases. F12 displays a read-only
sprite-coordinate marker diagnostic; **no original playable
scene, player sprite identity, palette or Alpha gate is claimed**.

**PC-13 Alpha-path rehearsal:** [Two-room native prototype campaign](native/research/PC13_CAMPAIGN_VERTICAL_SLICE.md)
is an opt-in source-free progression loop with linked
canonical scene IDs, full button-input replay tests and
persistent player HP/defeat count. It is **not** a recovered
Ys level, a genuine original encounter or a release Alpha.
Run `ys-native-game --prototype-campaign` to try the
two-room prototype; the default one-room placeholder is unchanged.

**PC-12 original CPU research:** [Bounded post-M45 collision-call watch](native/research/PC12_RUNTIME_COLLISION_WATCH.md)
is an opt-in, read-only attempt to observe the actual source
mapper and IX inputs at original bank-1 collision PCs.
A terminated or unobserved watch is explicitly a gameplay
evidence blocker; it does not add a native Ys area.

**PC-11 source collision routing:** [Bank-1 collision-call provenance](native/research/PC11_BANK1_COLLISION_ROUTES.md)
now proves the `$476C` entry path selects physical bank 4 before
three original `$807C` calls, and reproduces the source byte-bound
producer in native C11. This is conditional source control-flow
evidence, **not** a confirmed live gameplay mapper trace or a
playable original Ys map.

**PC-10 mod-forward adoption:** [Ys-specific support profile](native/YS_MODDING_PROFILE.md)
and [canonical experimental scene-content foundation](native/research/PC10_CANONICAL_CONTENT.md)
specify a versioned in-memory prototype scene with stable symbolic IDs,
strict validation and deterministic explicit replacement/addition. The
original **PC-0 placeholder gameplay is unchanged**; no actual end-user
mod loader/editor or authentic Ys level is implemented.

The new [PC-0 foundation](native/ENHANCED_PC_PORT.md) and
[PC-1 source-verified tile gallery](native/research/PC1_BANK3_TILE_GALLERY.md)
and [PC-2 verified map-object record ledger](native/research/PC2_BANK7_MAP_RECORDS.md)
and [PC-4 conditional original object initializer](native/research/PC4_OBJECT_TYPE_INITIALIZER.md)
and [PC-5 verified scene routing](native/research/PC5_SCENE_SELECTORS.md)
and [PC-6 original name-table initialization data](native/research/PC6_INITIAL_NAMETABLE.md)
and [PC-7 source-backed graphic composition](native/research/PC7_PATTERN_NAME_PREVIEW.md)
and [PC-8 actual simultaneous VDP checkpoint](native/research/PC8_SIMULTANEOUS_VDP.md)
and [PC-9 original object collision predicate](native/research/PC9_SOURCE_COLLISION.md)
plus [PC-3 source work-field projection](native/research/PC3_OBJECT_WORK_PROJECTION.md)
introduce
an independent C11 game-state core and SDL2-native `ys-native-game`
prototype with keyboard/controller input. Its room, art and combat values
are **placeholders**, not verified content from Ys. Z80 execution and
ROM rebuilding remain reverse-engineering tools, not the intended PC
runtime. The original-release Alpha/Beta/Final gates remain unchanged.

---

## Ys PC builds: Development / Alpha / Beta / Final

**Universal mod-forward development policy:** [MOD_FORWARD_METHODOLOGY.md](MOD_FORWARD_METHODOLOGY.md) sets the shared standard for replaceable content, stable resource IDs, extensible menus, deterministic mod resolution, save compatibility and editor-ready data across DOS, NES, SNES, SMS, Genesis and future ports. It is a development policy, not a claim that the current Ys native build has a mod loader or editor.

The native C11 Ys branch now has a [versioned, cross-platform development-build process](native/BUILD_CHANNELS.md), now at M44 with self-contained Windows click-to-run diagnostics and verified original source-ROM graphics decompression, including downloadable Windows/Linux/macOS diagnostics tied to exact commits, local packaging commands, automated checks and gated promotion requirements. **The current Development binaries are not a playable PC game.** Alpha requires interactive native gameplay; Beta requires an end-to-end game; Final requires cross-platform fidelity/release sign-off. No ROM image is bundled.

---

## External-tool integration — M11 (first independent Emulicious boot)

The M10-generated ROM and the fingerprinted owner ROM were launched in separate
**Emulicious** JVMs under Linux, and the 220 × 160 stable title-art pixel sample
matched exactly, with 15 observed colors. This is a **real third-party emulator
boot/render test**, not a full game-equivalence or audio certification. The JAR
is an external user-supplied dependency, not part of Git. Reproduce with
`cd Ys && make emulator-verify EMULICIOUS_JAR=/tools/Emulicious.jar ROM=/owned/Ys.sms`.
See [M11 emulator report](Ys/whole_system/M11_EMULATOR.md).

The user-supplied **WLA-DX v10.7 Win32/Win64** archives contain Windows PE
executables, so native Linux WLA-DX assembly is still **unverified**. The native compiler adapter now defaults to a pinned public Git clone:
`cd Ys && make wla-build-native`. It caches source and built tools outside Git.
When container network access is blocked, supply a source ZIP using
`make wla-build-native WLA_SOURCE_ZIP=/tools/wla-dx-v10.7-SOURCE.zip`.
Public visibility does not override container DNS or outbound-network restrictions.
A successful native WLA-DX build and full Ys assembly comparison remain unverified.

---

## Current whole-system checkpoint — M10 (full ROM-independent byte rebuild)

All **16 of 16 Sega Master System ROM banks** of *Ys: The Vanished Omens* now regenerate from checked-in code and data source **without the original ROM template**; the 256-KiB image matches the original SHA-256. **This is byte-exact binary-source reconstruction, not fully decoded assets or gameplay semantics.** The final four banks contain 64,439 bytes of explicitly unresolved asset source. Third-party Z80 assembler compilation and full-system emulator comparison are not verified.

From the project root: `cd Ys && make source-cartridge-check`. Optionally write the privately generated ROM outside Git: `python tools/build_system_m10.py --out /tmp/rebuilt.sms`. Full verification with an owner ROM: `make verify ROM='/path/to/Ys.sms'`. Details: [M10 technical report](Ys/whole_system/M10_README.md).

---

# SMS / NES Decomp

Reverse-engineering workspace for Sega Master System and Nintendo Entertainment System titles.

## Git branches

- `main` — project landing branch.
- `SMS` — Sega Master System decompilation work.

The `SMS` branch contains `Ys/` for *Ys: The Vanished Omens* (USA/Europe), with Phases 1–3 of bounded Z80 control-flow and banked update analysis.

Commercial game ROM images are not tracked. Use an independently supplied ROM with each title's verification script.

## Repeatable verification and progress

- [PROCESS.md](PROCESS.md): evidence standards, iteration cycle, testing gates.
- [Ys/PROGRESS.md](Ys/PROGRESS.md): verified findings, gaps, and checkpoints.
- `python Ys/tests_check.py "/path/to/Ys - The Vanished Omens (USA, Europe).sms"`
  tests the unchanged ROM and the rejection of modified inputs.

## Phase 2

- [Ys/phase2/README.md](Ys/phase2/README.md): newly traced routines and RAM ledger.
- `python Ys/tools/z80_regions.py /path/to/Ys.sms --check` regenerates and
  compares a 612-byte instruction listing and 54 bytes of constant data.
- `python Ys/tests_phase2.py /path/to/Ys.sms` checks seven Phase 2 assertions.

The branch remains local until an explicit target remote repository is supplied.

## Phase 3

- [Ys/phase3/README.md](Ys/phase3/README.md): bank-2 updater, secondary
  interrupt dispatch, and confirmed SRAM initialization boundaries.
- `python Ys/tools/z80_regions.py /path/to/Ys.sms --phase 3 --check`
- `python Ys/tools/check_partial_asm.py /path/to/Ys.sms`
- `python Ys/tests_phase3.py /path/to/Ys.sms` (15 checks).

Current classified coverage: 1,465 of 262,144 bytes (0.56%).
The code has **not** been assembled into a matching full ROM.

## Current Ys checkpoint: Phase 5

The local `SMS` branch now includes `Ys/phase5` with 4,934 more independently
checked ROM bytes (4,154 decoded Z80 instruction bytes plus 780 data bytes).
It uses a bank-aware control-flow walker and preserves unresolved banked calls.
See `Ys/phase5/README.md` and `Ys/tests_phase5.py`. The full game is not yet
source-rebuilt or runtime verified.

## Current checkpoint: Phase 6

`Ys/phase6` exceeds the requested doubling of Phase 5's throughput:
**14,521 new classified bytes** versus 4,934 in Phase 5, bringing the total
to **21,523 / 262,144 ROM bytes (8.21%)**. Phase 6 adds a 41-entry state
jump table, nine-entry scene table, 41-entry resource pointer directory, and
84 ROM-backed audio channel descriptor references. Sound event streams remain
opaque; their raw contents are not included. See `Ys/phase6/README.md`,
`Ys/tests_phase6.py`, and `Ys/phase6/coverage.json`.

The branch is local and has not been pushed to a GitHub remote. Matching
assembled source and emulator runtime verification remain future tasks.

## Current checkpoint — Phase 7

Local `SMS` branch. See [`Ys/phase7/README.md`](Ys/phase7/README.md) for
bank-1 control-flow tracing and the conservatively classified bank-3 payload.
Phase 7 adds 763 decoded, byte-matched instruction bytes and 14,541
provisional opaque payload bytes, **15,304 new candidate bytes total**.
Cumulative *candidate* coverage is 36,827 / 262,144 (14.05%). This does
**not** mean 14.05% of game logic is decompiled; binary build and emulator
behavioral equivalence remain unverified.

## Current checkpoint — Phase 8

[`Ys/phase8/README.md`](Ys/phase8/README.md) documents path-local mapper
resolution, **797 additional decoded instruction bytes** from five physical
banks, and a **124-byte four-byte-stride lookup table**. This adds **921 new
distinct classified ROM bytes**. It also decodes **5,632 previously counted
opaque bytes** into 176 reversible SMS Mode-4-compatible tiles, without
counting those bytes twice. Cumulative *candidate* footprint: **37,748 /
262,144 (14.40%)**; this is not a decompilation completion percentage.

Reproduce with `python Ys/tests_phase8.py /path/to/your/Ys.sms`. Source and
metadata only; raw ROM and extracted game tiles remain outside Git. The
`SMS` branch is still local, and no assembler-built or emulator-equivalent
full game is claimed.

## Current checkpoint — Phase 9B: first byte-matching assembly

[`Ys/phase9/README.md`](Ys/phase9/README.md) now documents the correction of
Phase 9A's relative branch-label error. The standalone restricted two-pass
Z80 assembler independently emits **111 matching bytes** for four selected
fixed-bank routines (11 labels). `Ys/tests_phase9.py` checks opcode generation,
VDP upload provenance, branch destinations, source/encoder/report mutations and
corrupt ROM rejection. All Phase 1–8 suites passed, and Phase 9B passed on its
own invocation after a combined-run timeout. The cumulative classified/candidate
footprint is unchanged at **37,748 bytes (14.40%)**. No complete ROM rebuild,
external assembler comparison, or runtime/gameplay equivalence is claimed.

## Current checkpoint — Phase 10B: expanded sparse assembly matching

`Ys/phase10/PHASE10B.md` documents repaired and independently tested mnemonic
encoding for **4,960 Z80 instructions / 10,188 original-ROM matching bytes**
across eight physical ROM banks. Accounting for 61 bytes overlapping the
111-byte Phase 9B assembly subset, the unique assembler-matched footprint is
**10,238 bytes (3.91% of the 256-KiB ROM)**. All ten phase regression suites
pass. This is not new ROM classification: the separate cumulative candidate
coverage remains **37,748 bytes (14.40%)**, including provisional data.
No external Z80 assembler comparison, whole-ROM rebuild, or emulator behavior
match has been demonstrated. Git branch `SMS` remains local.

## Phase 11A — expanded binary-matched code (partial test checkpoint)

`Ys/phase11/README.md` documents 6,158 in-project encoder-verified instructions
(12,439 ROM-matching code bytes), 128 new bytes of structured bank-6 pointers,
and 5,632 reversible previously classified graphics bytes. Combined distinct
code/data reconstruction footprint: 18,199 bytes; candidate classified ROM
footprint: 38,279 bytes. All ten older regression suites pass. The new Phase
11 suite is **blocked by a legacy Python import error** and must be fixed and
run before this phase is promoted to fully regression-verified status. No
external assembler or full-ROM build has been verified.

### Latest Ys progress: Phase 11B

- 12,439 sparse Z80 instruction bytes match through the project encoder.
- Bank 6's 64 indexed variable-length records are now fully boundary-parsed,
  structurally decoded and reversibly verified (6,322 previously unclassified
  bytes; 2,086 elements). The 128-byte pointer directory was known in 11A.
- 44,601 distinct ROM bytes are candidates/classified (17.01%). Of those,
  24,521 have either assembler-byte verification or a reversible structural
  interpretation (9.35% of ROM); these confidence levels are distinct.
- See [`Ys/phase11/PHASE11B.md`](Ys/phase11/PHASE11B.md) and the metadata at
  `Ys/phase11/bank6_records.json`. No original ROM is committed.

## Latest Ys checkpoint — Phase 12: verified sprite rendering path

`Ys/phase12/README.md` connects the bank-6 indexed records to 64-sprite
attribute-table uploads at VDP VRAM `$3F00/$3F80`. The complete **7,192-byte
bank-6 interval** `$18000–$19C17` has a non-overlapping code/structured-data
partition. The new contribution is 241 in-project-assembler-matched instruction
bytes and 98 newly structured pointer/offset bytes (**339 new distinct bytes**).
Cumulative in-project-assembly match: **12,680 bytes**; reversible data:
**12,180 bytes**; stronger union: **24,860 bytes**; candidate/classified
footprint: **44,940 / 262,144 (17.14%)**. The commercial ROM is not in Git.
No emulator trace, external assembler test, or complete matching build is
claimed. Reproduce with `python Ys/tests_phase12.py <ROM>`.

## Latest Ys checkpoint — Phase 13: bank-7 graphical transfer data

[`Ys/phase13/README.md`](Ys/phase13/README.md) establishes a complete,
nonoverlapping **13,631-byte bank-7 classification** from physical ROM
`$1C000–$1F53E`: 64 graphics/code directory entries, 64 secondary pointers,
1,345 new sparse Z80 assembly-matched bytes, 438 previously known code bytes,
10,056 source graphics bytes, and 1,408 bytes of 22-byte-stride secondary records.
The new contribution is **13,193 distinct ROM bytes**. Cumulative metrics:
**14,025** in-project-assembled code bytes, **24,028** reversible structured
bytes, **38,053** combined strong reconstruction bytes, and **58,133**
candidate/classified bytes (**22.18% of ROM**). The last metric includes earlier
provisional data and is not a percentage of recovered game functionality.
Use `python Ys/tests_phase13.py <ROM>` for independent negative tests.
Neither the commercial ROM nor extracted asset payloads are tracked.

## Workflow research checkpoint — October 2026

Research into [decomp.dev](https://decomp.dev/) and [decomp.me](https://decomp.me/)
identified practices we can apply to Z80 work without claiming unsupported
site/tool integrations. See [`DECOMP_RESEARCH_2026-10-11.md`](DECOMP_RESEARCH_2026-10-11.md).
Try a local per-module matching loop with `Ys/tools/scratch_compare.py` and
its regression suite `Ys/tests_scratch_workflow.py`. These operate entirely
on the user's locally provided ROM and the existing in-project assembler.

### Source-overlay build (Phase 14)

`Ys/tools/build_sms_phase14.py` now integrates the 11 reconstructed Z80 modules
into a 256-KiB output image **using the locally provided original ROM as a
fallback template**. It matches 14,025 source bytes, while preserving 248,119
bytes from the original input. This is useful for deterministic integration and
regression checks; it is **not** a source-only rebuild. See
`Ys/phase14/README.md` for usage, the bank-aware reference index, and the
optional real-SJAsmPlus validation mode.

### Phase 15 update — source-backed tables

Under `Ys/phase15/`, the project now reconstructs **678 additional ROM
bytes from `DB` / `DW` sources** without needing the ROM to generate those
bytes. Together with 14,025 assembly-matched code bytes, the template-assisted
rebuild has **14,703 source-backed bytes** and 247,441 copied fallback bytes.
Candidate coverage is unchanged because these tables were already identified.
See `Ys/phase15/README.md` for the symbol index, commands and limitations.

### Phase 16 update — source-backed sprite and graphics metadata

[`Ys/phase16/README.md`](Ys/phase16/README.md) documents another **7,902
previously classified bytes** reconstructed as editable, semantic `DB` records:
6,322 bank-6 counted sprite bytes, 48 sprite offsets, 1,408 bank-7
secondary pairs and 124 bank-4 indexed bytes. The source-backed image now
covers **22,605 bytes (8.62%)**; the original-ROM fallback is **239,539
bytes**. This is **not** 7,902 newly discovered ROM bytes: candidate footprint
remains 58,133. The derived JSON contains some original asset values in
structured form (unlike earlier metadata-only phases), but no complete ROM.
Phase 16 also supplies three symbolic Z80 views, without double-counting
their 8,579 previously matched instruction bytes.

### Phase 17 — source-backed tile graphics

`Ys/phase17/` now holds reversible per-pixel sources for 5,632 bytes of bank-3
4bpp tiles and 10,056 bytes of bank-7 monochrome tile records. Regeneration
from the checked-in JSON does not require the ROM; full-image verification
requires the user's original ROM. **38,293 bytes** are source-backed and
**223,851 bytes** still use original-ROM fallback. See `Ys/phase17/README.md`.
The derived graphics JSON/assembly contain proprietary asset values; they
are not just hashes or metadata. No independent emulator trace is claimed.

### Phase 18 — bounded CPU instruction traces

`Ys/tools/phase18_z80_trace.py` executes real ROM opcodes from four graphics
uploader paths, the sprite-table transfer routine and 64 unrolled bank-7
transfer entries using controlled register/RAM initial states. The combined
output is **46,912 VDP data bytes across 69 isolated runs**; this is neither
46,912 newly reconstructed ROM bytes nor a full-game execution trace. The
checkpoint preserves Phase 17's **38,293 source-backed bytes**, **223,851
fallback bytes**, and **58,133 candidate/classified bytes**. See
`Ys/phase18/README.md` for exact trace constraints and test commands.

### Phase 19 — sprite producer and VDP SAT integration

`Ys/tools/phase19_sprite_execution.py` executes the original fixed-bank mapper
setup and bank-6 sprite producer, then runs the SAT uploader against the RAM
buffers created by that same execution. **192** constrained executions
(64 records × 3 origins) match independent buffer calculations and verify
**36,864 VDP output bytes in separate transfers**. New ROM coverage remains
zero; source-backed total remains 38,293 bytes. See `Ys/phase19/README.md`
and run `Ys/tests_phase19.py` against your local original ROM. This is a
bounded instruction interpreter, **not** a full SMS gameplay emulator.

### Phase 20 — bank-6 object path + WLA-DX preflight

`Ys/phase20/` records 192 controlled bank-6 `$9966 -> $9932 -> $9AA9` sprite-object executions followed by the original SAT upload, each checked against separately recomputed RAM/VDP data. The 14 new tests and full **23/23 historical suite run** pass. `Ys/Makefile` provides one-command build/verification entrypoints; the regression runner supports bounded parallel execution. The WLA-DX fixture is prepared, **not independently assembled** because executables are unavailable. No ROM byte coverage is added; source-backed remains **38,293 / 262,144 bytes**. See `Ys/phase20/README.md`.

## Latest verified checkpoint — Phase 21 (authoritative current status)

[Phase 21 report](Ys/phase21/README.md) | [Build tool](Ys/tools/build_phase21.py) | [Typed source](Ys/phase21/source.json) | [Regression runner](Ys/tools/run_regressions_phase21.py)

The local `SMS` branch now source-generates **46,349 / 262,144 bytes (17.68%)**, while **215,795** bytes still use the exact source-ROM template. Candidate classified bytes are **58,490 (22.31%)**, including **357 newly reconstructed count-prefixed variable music descriptor header bytes**. Phase 21 converted an additional 8,056 source bytes, including partial/opaque glyph/control tokens in bank 3; these tokens do not constitute decoded dialogue. The ROM overlay matches the original SHA-256 exactly, and all 24 independent regression suites pass.

`cd Ys && make verify ROM='/path/to/Ys.sms'` runs all suites concurrently; `make data-verify` verifies new source bytes **without** the original ROM. Independent external WLA-DX output, full-system emulator behavior and a true source-only 256-KiB ROM build are **not yet achieved**. Earlier sections above are historical checkpoints rather than current coverage figures.

## Whole-bank / whole-system decompilation track

The project has transitioned from small byte checkpoints to **complete-bank and connected-subsystem targets**. Physical ROM banks **3 and 7 (32,768 bytes total)** now recompile independently from source, byte-identical to the owner's ROM, via `Ys/tools/build_whole_system.py --standalone-banks`. The full 16-bank ROM is still partial: 53,249 source-backed bytes, 208,895 bytes supplied by the owner's ROM as fallback. Unresolved byte sources do **not** imply complete semantic understanding. See [`WHOLE_SYSTEM_PLAN.md`](WHOLE_SYSTEM_PLAN.md) and [`Ys/whole_system/README.md`](Ys/whole_system/README.md).


## Cross-project AI/decomp workflow toolkit

`AGENTS.md`, `AI_DECOMP_ADOPTION.md`, and `shared_decomp/` provide a portable evidence/coverage audit, bounded context packet extraction and fail-closed matching-attempt guard. The portable package is intended for reuse with Z80, 6502, and compiled PC games; it does **not** imply other repositories have been modified. See `shared_decomp/README.md`.

## Current whole-system evidence graph

The Ys project's static cross-bank inventory, bounded AI query tool, and incomplete bank-0 entrypoint queue are in [`Ys/whole_system/EVIDENCE_GRAPH.md`](Ys/whole_system/EVIDENCE_GRAPH.md). Use `make -C Ys system-graph ROM='/path/to/Ys.sms'`. All matched source code bytes are rechecked against the original ROM before generating CFG/effect metadata. The two source-only banks remain 3 and 7; the complete 16-bank build still depends on original-ROM fallback. The local `SMS` branch has no configured upstream Git remote.

### Whole-system M3: source-only fixed ROM bank 0

Source-only 16-KiB builds now cover **banks 0, 3, and 7** (three of 16 banks).
The total source-backed footprint is **61,391 / 262,144 bytes (23.42%)**;
200,753 bytes still come from the local original ROM in the whole-ROM overlay.
See `Ys/whole_system/M3_README.md` and `Ys/wholebank00/README.md`.
Use `cd Ys && make system-m3-verify ROM=/path/to/Ys.sms` for all regression
suites and source-independent bank checks. External WLA-DX and emulator
verification remain unresolved, not implied by matching output hashes.


## Latest SMS milestone: Whole-system M4 (sprite/object bank 6)

Four independently byte-complete 16-KiB banks: **0, 3, 6, 7**. Build without
ROM input via `cd Ys && make four-bank-source`. Full system: `make verify
ROM=/path/to/Ys.sms`. Total project source-backed: **70,583 / 262,144 bytes**
(26.93%), with 191,561 original-ROM fallback bytes in twelve banks. Seven
sprite count-prefixed triplet layouts are bounded in bank6; its graphics
encoding remains undecoded. The byte-identical overlay is **not** a complete
source-only ROM. See `Ys/whole_system/M4_README.md` and
`Ys/wholebank06/README.md` for provenance and limits.


## Latest SMS milestone: Whole-system M5 (sound bank 2)

**Five independent source-only physical banks: 0, 2, 3, 6, 7 (81,920 bytes).**
The project source-backs 83,182 of 262,144 bytes (31.73%); 178,962 bytes
remain ROM-template fallback in eleven incomplete banks. Bank2's existing Z80
sound engine, 73+73 note register words, lookup tables, 55-song directory,
channel descriptors and 24 bounded variable song event streams reassemble
without the original ROM. **Most event bytes remain semantically unresolved;
no sound playback or full-system emulator equivalence is claimed.**

Reproduce: `cd Ys && make five-bank-source`;
`make verify ROM='/path/to/Ys.sms'` checks the ROM and historical suites.
See `Ys/whole_system/M5_README.md`, `Ys/wholebank02/README.md`. WLA-DX
fixtures prepare; actual independent assembler execution remains outstanding.

## Whole-system M6 — sixth source-only bank (bank 1)

Bank 1 joins 0, 2, 3, 6, and 7 as the sixth ROM-independent 16-KiB build. Total source-backed content: **98,787 / 262,144 bytes (37.6842%)**; remaining ROM fallback: **163,357 bytes**. The new code is ROM-matched static-candidate Z80, while **13,528 bank-1 bytes remain semantically unresolved**. Bank completion here measures source-backed binary reconstruction, not solved gameplay logic or external assembler validation.

From `Ys`, run `make six-bank-source`, `make six-bank-rom-verify ROM=/path/to/original.sms`, and `make system-m6-verify ROM=/path/to/original.sms`. See `Ys/whole_system/M6_README.md` and `Ys/wholebank01/README.md`.

## Whole-System M7 — seventh source-only bank (bank 4)

Seven independent 16-KiB ROM bank builds now succeed: **0, 1, 2, 3, 4, 6, 7**. Total source-backed **115,009 / 262,144 bytes** (43.8725%); fallback **147,135**. Bank 4 includes a ROM-matched 31-entry rectangle/collision table, a 38-byte Z80 collision predicate, and **3,968 ROM-instruction bounded collision tests** cross-checked with a direct model. The large remaining bank4 lane region has *unproven* graphical semantics and the test harness is *not* full emulator execution. From `Ys/`, run `make seven-bank-source` then `make system-m7-verify ROM=/path/to/original.sms`. See `Ys/whole_system/M7_README.md`.

## Whole-System M8 — nine independently rebuildable banks

Physical banks **0, 1, 2, 3, 4, 6, 7, 8, 10** assemble to byte-identical
16-KiB source images without accessing the original ROM. A separate full-ROM
build uses the owner's original ROM only for seven incomplete banks; source-backed
coverage is now **147,564 / 262,144 bytes (56.2912%)**. See
`Ys/whole_system/M8_README.md` and run `make -C Ys nine-bank-source` or
`make -C Ys build-verify ROM=/path/to/Ys.sms`.

The bank-8 script and bank-10 resource bodies remain **unresolved source byte
arrays**, not decompiled game logic; no external Z80 assembler match or full-game
emulator run has been established.

## Whole-System M9 — twelve source-only banks / 75% cartridge

Banks **0,1,2,3,4,6,7,8,9,10,11,12** each rebuild as an independently byte-identical 16-KiB image without the ROM. The total **196,608 bytes / 75%** are source-backed; the remaining 65,536 bytes in banks 5,13,14,15 still require the user's ROM for the full cartridge. Bank 9's `$BEFB` VDP writer and eight six-byte glyph records are structurally recovered, and its output loop passes 24 bounded ROM-instruction executions. Most other newly owned bytes remain semantically unresolved. Read [`Ys/whole_system/M9_README.md`](Ys/whole_system/M9_README.md) and run `make -C Ys system-m9-verify ROM=/path/to/Ys.sms`.

## M12: independent instruction assembly

The user-provided Emulicious emulator includes an independent Z80 assembler.
`cd Ys && make emulicious-assembler-verify EMULICIOUS_JAR=/path/to/Emulicious.jar`
assembles every mnemonic in the sixteen complete-bank sources and compares it
with the source-only ROM. See `Ys/whole_system/M12_README.md` for recorded
coverage and external linker limitations. The full WLA-DX build remains pending.
