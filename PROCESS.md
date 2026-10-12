# Reverse-engineering process — SMS / NES

This file is the project's persistent operating procedure. Improvements are made
by updating the repository, tools, and tests; no model retraining is implied.

## Evidence and confidence

Every identified function, variable, mapper state, table, or hardware behavior
must carry evidence. Classify it as:

- **VERIFIED** — backed by exact ROM offsets/bytes and a passing automated test,
  or directly observed with a reproducible emulator trace.
- **SUPPORTED** — plausible interpretation supported by control/data flow and a
  documented hardware reference; not yet confirmed by runtime observation.
- **HYPOTHESIS** — tentative label, meaning or relationship awaiting evidence.

Keep CPU addresses separate from physical ROM offsets: banked CPU addresses are
not globally unique. Specify bank, slot, and mapper state where relevant.

## Iteration cycle

1. **Baseline:** fingerprint the input ROM (SHA-256, size, header and checksum),
   run the existing tests, record the current checked-byte range.
2. **Trace:** choose one reachable entry point or self-contained subsystem;
   distinguish code, tables, padding, and unknown bytes before assigning names.
3. **Record:** preserve original bytes, file offsets, CPU addresses, incoming
   references, register/flag effects, bank state, and confidence on symbols.
4. **Implement:** add only a small, reviewable assembly/source increment. Avoid
   silently substituting inferred logic for the original machine instructions.
5. **Validate:** compare every annotated byte to the original ROM; when a source
   assembler is configured, assemble and compare produced bytes. Confirm claimed
   behavior with emulator traces when available.
6. **Learn:** log failures, root causes, corrective changes, and a regression
   test. Commit the evidence and method with the result.

## Hard gates

- Never claim binary equivalence based solely on source-to-ROM listing checks.
- Never label a guess VERIFIED, even when a guessed label seems convincing.
- No copyrighted ROM images, extracted music or graphics bundled in commits.
- No expansion past a bank switch without mapping the active ROM slot.
- Stop rather than invent an opcode, jump target, address, or hardware behavior.
- A failing regression test blocks further assertions of success.
- Reconstructed assembly must be independently checked for label placement
  and mnemonic alignment before any assembler round-trip can be claimed.

## Efficiency practices

- Prioritize reset, interrupt vectors, mapper writes, main loops, and shared
  pointer/dispatch helpers before isolated gameplay routines.
- Use deterministic scripts for repetitive byte comparisons and reports.
- Reuse a central address/symbol ledger to avoid rediscovering functions.
- Group related calls/data flows in short phases; write a checkpoint before
  changing topics. Separate performance improvements from correctness claims.

## Checkpoint template

- ROM identification and tool versions:
- Branch / commit:
- Newly verified ranges and byte counts:
- New symbols (bank:CPU address = ROM offset):
- Tested runtime observations:
- Open questions / hypotheses:
- Tests run and results:
- Next smallest useful step:

Primary technical references: https://www.smspower.org/Development/ (SMS),
https://www.nesdev.org/wiki/Nesdev_Wiki (NES), and processor-specific manuals.


## Audio decompilation lessons (Phase 4)

- Verify target subsystem against actual I/O instructions before naming
  routines: `$F0/$F1` FM, `$7F` PSG make the bank-2 path audio logic.
- Track code and embedded tables separately. Never linearly disassemble
  `$81B1–$81D8`: it is two pointers plus FM register sequences.
- Keep each confidence claim local to its evidence. Static decoding does
  not prove frame timing, music behavior or bit-identical assembly.
- Reject mutated listings/tables/annotations in addition to verifying the
  original ROM; prevent regression tests from just rubber-stamping output.
- New findings belong in `Ys/PROGRESS.md` and each phase report so a
  future session can resume without relying on unrecorded conversation.

## Large-region static coverage lessons (Phase 5)

- For large decoding tasks, derive coverage from controlled entrypoints and
  instruction-level CFG edges; a linear ROM sweep mistakes pointer tables and
  note periods for Z80 instructions.
- Treat bank-0 -> CPU `$8000–$BFFF` calls as *unresolved* unless the actual
  mapper state is established. Physical bank 2 is not synonymous with slot 2.
- Put uncertain decoded destinations and traversal-window limits into a
  machine-generated unresolved-edge ledger; don't hide them in byte coverage.
- Independently validate listing bytes, raw-data SHA-256 regions, collision
  checks, and deliberate mutations; keep coverage figures distinct from
  assembler and runtime verification.

## Higher-throughput classification lessons (Phase 6)

- Increasing coverage must not mean guessing that arbitrary bytes are code.
  Use indexed dispatcher words as *entrypoint evidence*, and exclude tables
  from recursive descent before calculating instruction boundaries.
- Separate **ROM-byte provenance** (identity, offset, digest) from
  **semantic knowledge** (decoded instruction, recognized descriptor, opaque
  sound event data). A byte classified as opaque data has *not* had its
  format recovered or runtime consumption established.
- Only classify data ranges with defensible boundaries. Do not extend an
  audio stream span into later records to hit a numeric coverage goal;
  Phase 6 withheld `$B319–$B6ED` for this reason.
- Cross-check pointer directory sizes, repeated entries, record stride,
  and interior pointers independently of the CFG scanner. Record identical
  destinations once in the unique-target count.
- Exclude raw music-event payloads from checked-in listings and archives:
  ship reproducible hashes, offsets, and analytical metadata instead.
- Keep previously unresolved mapper questions open. Larger output is not
  permission to interpret slot `$8000` as physical ROM bank 2 everywhere.

## Phase 7 measurement discipline — code versus opaque candidates

Report **verified ROM instruction bytes** and **provisional opaque payload**
separately. A SHA-256-matched opaque block is proven to contain those bytes,
not proven to be data, executable, text, sound, or graphics until independently
supported by a pointer grammar, a reachable decoder or an emulator trace.
Excluded padding does not count as meaningful decompilation coverage.

The headline 'candidate coverage' is **not** a reconstructed or tested game
percentage. Assembler-produced binary equality and game behavior require
separate, independent tests; previously transcribed mnemonic checks do not
meet these standards.

## Phase 8 — resolving bank ambiguity using path-local evidence

- Track `LD A,bank ; LD ($FFFF),A` immediately followed by `CALL/JP` as a high-confidence **local mapper edge**. Unlike an arbitrary CPU address, this resolves the physical ROM bank at that particular call site. A preceding bank write in another routine is *not* enough unless the control-flow path is justified.
- Keep the static/path-conditional versus emulator-runtime distinction visible. An intervening nested call or interrupt can change mapper registers; do not claim dynamic reachability until traced.
- Count a byte once across phases. Refining previous `provisional_opaque_data` into decoded bitplane tiles improves structural coverage, but increases *new distinct byte coverage* by **zero** for those offsets.
- Require reversible decoders: for 8×8 Mode-4 graphics, 32 original ROM bytes -> 64 four-bit palette indexes -> identical 32 original bytes. Generate preview graphics only from the user's local ROM; do not add derived commercial artwork to the repository.
- Keep indexes and field labels source-grounded. A 4-byte stride observed in a Z80 indexed lookup establishes record boundaries, not their full semantic meaning.

## Phase 9B — Assembly-label regression policy

- Include an independent emitted-opcode comparison, not only a decompiler
  listing or original-byte annotation. A restricted assembler is acceptable for
  isolated proof-of-concept sections, but identify it as such and do not equate
  it to a full toolchain or full-game rebuild.
- For relative branches, independently calculate destination from original ROM
  displacement and `PC + 2`; test both destination and emitted displacement.
  Phase 9A's `.WordLoop` at `$06DB` instead of `$06DA` is the failure example.
- Add mutation tests that recreate the *specific historical failure* and show
  that `--check` rejects it. Independent decoding of source section boundaries
  is an extra guard against assembly/annotation drift.
- Keep **assembled-byte identity** separate from distinct ROM-byte coverage,
  structured-data understanding and emulator-observed behavior. Previously
  surveyed bytes that gain assembler proof are not newly classified bytes.
- If a combined test command times out, state precisely which suites completed
  and rerun uncompleted suites independently. Do not report an interrupted
  aggregate run as a completed aggregate verification.

## Phase 10B — reproducible sparse assembly by physical ROM bank

- Never infer source for an unclassified gap between discovered instructions.
  Preserve sparse `org` sections and emit separate source per physical bank to
  prevent CPU-slot address aliases from colliding.
- Use instruction text as input to an independently implemented opcode encoder.
  Verify opcode output against both ROM bytes and earlier opcode snapshots;
  independently decode each instruction's length using a different decoder.
- Normalize mnemonics without removing the mnemonic/operand separator:
  `RLD` (ED 6F) and `RL D` (CB 12) are different operations.
- For DD/FD CB sequences, emit `prefix CB displacement opcode`, not
  `prefix CB opcode displacement`. Validate relative displacement targets,
  indexed 16-bit `ADD`, and unsupported opcode rejection.
- Keep all three metrics separate: *newly classified ROM bytes*, *newly
  assembler-matched byte offsets*, and *the cumulative unique assembler-matched
  union*. Cross-check overlaps with prior phases instead of adding totals.
- The bankwise in-project encoder is not a third-party assembler and has no
  runtime/emulator validation. Reuse phase10 sources as audited skeletons, not
  evidence the full 256-KiB cartridge rebuilds or behaves identically.

## Phase 11B — Record grammar before raw-coverage expansion

- A program-consumed pointer table can reveal a much larger bounded payload
  without mislabeling arbitrary ROM data as instructions. The bank-6 table
  `$18000–$1807F` contains 64 unique pointers into `$18080–$19931`.
  Every target begins a record with a byte `n` and **exactly `1+3n`
  bytes**, and sorting all 64 records shows exact end-to-start adjacency.
- Decode the record as `n`, `n` first-stream delta bytes, then `n` pairs
  `(delta, literal)`. The `$9932` consumer loads two starting accumulators
  once from `$C210` and `$C211`, respectively; **sums are cumulative** and
  wrap modulo 256. The second pair member is copied unchanged by `LDI`.
  Merely adding the starting value independently to each delta is incorrect.
- Reencode all records to exactly their source bytes and test the consumer
  model at multiple bases. Store pointer locations, length fields, per-record
  checksums, and derived-output checksums rather than commercial payloads.
- Import older modules through a configured `Ys/tools` module path in the
  Phase 11 test harness rather than making an incidental import failure
  look like a bad ROM/decoder result. Protect the test-runner fix with a
  complete separate Phase 11A suite run.
- Keep candidate coverage, structured record coverage, and assembled code
  as separate quantities. Refining the old 128-byte pointer directory adds
  **zero** new bytes; the contiguous 6,322-byte record payload adds 6,322.

## Phase 12 — Trace producer to consumer before assigning semantics

- A ROM data format's meaning is materially stronger when **both sides** of
  its RAM handoff are identified. Bank6 writes one running-sum byte and one
  running-sum/literal pair per element to `$DD00` and `$DD40`. Fixed bank0
  uploads 64 bytes and 128 bytes, respectively, to SMS VDP SAT addresses
  `$3F00` and `$3F80`. This supports sprite coordinate/tile interpretation.
- Count a contiguous interval only after accounting for **every physical
  offset** using disjoint instruction-byte and bounded-data sets. For bank6
  `$18000–$19C17`, 644 assembled code + 6,548 structured data = 7,192 bytes.
  Most were already accounted for: only 339 bytes are new.
- Always compare dynamically resolved dispatch tables with exact decoded
  instruction *starts*, not merely with addresses falling inside code spans.
- Retain unknown runtime indices and lack of emulator traces as limitations;
  do not infer that all 64 records or all 8 dispatch handlers execute.

## Phase 13 — Jump-into-unrolled-code and paired data-directory checks

- Account for unusual jump mechanisms: bank7's `PUSH DE; RET` dynamically
  chooses one of several aligned instruction addresses. A normal CFG traversal
  starting only at CALL/JR/JP operands will miss these genuinely executable
  `OUTI` and `OUT ($BE),A` instructions.
- Use the first pointer of each 4-byte entry to derive exact transfer length
  from the fixed common `RET` terminus. Independently verify that the second
  pointer plus that length exactly reaches the next sorted data-record start.
  Reject any overlap, gap or malformed alignment.
- Distinguish **source ROM bytes** (10,056) from **total potential VDP output**
  (40,224). Output volume does not represent unique data on a single frame.
- The secondary pointer table's 22-byte stride is corroborated by a consumer
  executing 11 iterations of two source reads per iteration. Treat field
  semantics as pending until its bit operations are fully reconstructed.
- Negative tests should bypass the fingerprint *temporarily* for altered ROM
  cases, so they exercise internal structural validators independently of a
  trivial SHA failure. Always restore the original fingerprint.
- Publish physical ROM intervals as end-exclusive internally and clearly
  distinguish them from CPU slot-2 addresses; their offset delta for bank7 is
  `0x1C000 - 0x8000 = 0x14000`.

## Research checkpoint — 2026-10-11, decomp.dev / decomp.me practices

See `DECOMP_RESEARCH_2026-10-11.md` for research provenance and the implementation.
For Z80, borrow the **workflow**, not unsupported product claims: compare one
bounded bank-aware source module at a time; provide immediate first-byte diff;
keep matched-code progress distinct from structured and opaque data; reject
mutation inputs; and record every new hypothesis in a shared symbol ledger.
Run `Ys/tools/scratch_compare.py` offline for the first matching loop.
The in-project restricted Z80 encoder is *not* a third-party toolchain.
No data was submitted to decomp.me and the ROM remains local.

## Phase 14: template-assisted ROM build discipline

- The 256-KiB overlay build is an integration/integrity harness, **not** a
  source-only decompilation. Source-backed code is counted only at addresses
  emitted by `Ys/tools/build_sms_phase14.py`, using strict per-byte ownership.
- Never use full-ROM SHA equality alone as proof that source has been recovered:
  fallback bytes come from the original ROM, supplied only at runtime.
- Generated cross-references are syntactic. Bank 0 is fixed; slot-1 and slot-2
  destinations require independent mapper evidence before assigning banks.
- Independent assembler validation is **opt-in** with a real SJAsmPlus binary.
  Absence or failure does not silently downgrade to the built-in encoder.
- Keep original ROMs and any generated full `.sms` images outside Git history.
- Evidence files: `Ys/phase14/build_report.json`, `Ys/phase14/crossrefs.json`,
  plus ROM-backed negative regression tests in `Ys/tests_phase14.py`.

### Phase 15 — require distinct evidence for source backing

Distinguish three different counts: **newly classified bytes**, **source-backed
bytes**, and **ROM-template fallback**. Converting a known pointer table from
metadata into `DW` source counts toward the second only. Data modules must be
byte-identical to the reference ROM, nonoverlapping with Z80 instruction
modules, and regenerable from checked-in declarative metadata without the ROM.
A mapper-adjacent constant write supports a static target-bank candidate; it
does not establish runtime mapping or instruction reachability. Preserve the
original unresolved edge alongside the candidate and evidence offset.

### Phase 16 — structured source and symbol confidence

Prefer semantic, reversible declarative data to byte-copying opaque spans.
Explicitly disclose when derived source files contain game asset values even
though complete proprietary ROM images remain excluded. Validate length,
per-record digest, bank/physical address, full ownership partition, and a
mutated-data rejection case. Named EQU substitutions should be checked against
canonical mnemonic assembly and must not increase coverage totals unless they
represent new nonoverlapping physical ROM bytes. The original-ROM fallback
remains an integration mechanism, not a source-only compilation proof.

### Phase 17 — graphics source rules

Represent graphics in **editable pixel-level form** rather than only copied
opaque ROM bytes. For Sega Mode-4, reencode all four ordered bitplanes of every
8-pixel row; for the bank-7 1bpp transfer path, rebuild every source byte from
its eight pixel bits and prove directory pointer/length consistency. Check each
per-record hash, aggregate physical spans, source-generated `DB` drift and
nonoverlapping ROM ownership before calling data source-backed. Source-backed
asset values remain copyrighted material, even when no `.sms` file is shipped.
Never count hypothetical VDP output as ROM coverage or static control-flow
analysis as an actual emulator trace.

## Phase 18 trace confidence rule

An opcode-interpreter trace executed from original ROM bytes with *synthetic*
register/RAM setup is stronger than a static transfer estimate but weaker than
a full-emulator/gameplay breakpoint capture. Record those evidence types
separately. Check physical bank selection, VRAM command latch sequencing, byte
contents and ROM provenance for each execution. Use bounded instruction budgets
and reject unimplemented instructions, unexpected I/O ports and invalid VDP
commands. Never add emitted VRAM byte counts to source-backed ROM coverage.

## Phase 19 — producer/consumer integration verification

Trace shared state through the original machine instructions rather than
manually seeding the consumer buffer again. Require the mapper write and RAM
pointer updates on the actual fixed-bank call path, then run the consumer in
that same machine environment. Compare complete arrays and VDP destinations to
**independently derived** expectations for every record across multiple
origins. Report output byte totals separately from distinct ROM-source bytes;
192 transfers of 192 bytes do not imply 36,864 newly recovered ROM bytes.
The bounded opcode interpreter is not a full emulator, even when all such
isolated runs pass. See `Ys/phase19/README.md` for caveats and reproducible
checks.

### Regression execution hygiene (Phase 19)

Run each phase with its own process timeout, record explicit pass/fail/timeout
status and preserve the end of failure output. Phase 14/15 `unittest` files
are invoked *without* a ROM argument; other phase scripts take the ROM path.
Use `Ys/tools/run_regressions_phase19.py` to prevent false failures from
incorrect CLI invocation and to avoid treating a whole-batch timeout as a
regression assertion failure.

## Phase 20 — external toolchain readiness and regression throughput

- Follow published WLA-DX Z80 memory/ROM bank maps when preparing independently assemblable modules; `.BANK` and `.ORGA` must preserve physical offset and CPU execution address. Only claim external assembler verification after `wla-z80` and `wlalink` actually compile/link and produce ROM-identical bytes. A successful fixture-preparation check is not external assembly.
- For isolated sprite object paths, initialize all RAM object state explicitly and preserve the synthetic origin in reports. Independently derive expected SAT bytes from source ROM and record fields, not from the interpreter's own byte-read API. Differentiate object-path opcode execution from full gameplay or renderer output.
- Run the complete test suite through `Ys/tools/run_regressions_phase20.py` or `make -C Ys verify ROM=...`. Up to four suites can run concurrently with per-suite limits, deterministic final report order and fail-closed subprocess status. Report only finished passing suites.

## Phase 21 project-wide lesson: source backing versus semantic understanding

- Check an entire recovered record directory against *both* start and end boundaries before classifying bytes. Fixed and variable record formats can coexist in one index; in bank 2, 21 regular four-channel descriptors coexist with 24 variable one/two-channel descriptors.
- For variable music records, only the 1+9*N header bytes qualify as newly structured. Even if music-event trailers are located between consecutive descriptors, raw event payload is **not** classified as decoded commands or auto-promoted to source ownership.
- A **reversible numeric glyph slot** representation can help achieve ROM-independent emission, but glyph mappings and control opcodes remain unverified. Keep opaque bytes identified and never replace them with guessed plaintext.
- For every source-backed increment, maintain nonoverlapping physical offset ownership; compare against the original independently supplied ROM using an exact hash gate. Distinguish new candidate classification from existing candidate bytes newly converted to source. Full template-assisted byte equality is not evidence of source-only or independently assembled recompilation.
- Do not mark optional toolchain preparation as external verification. The actual assembler/linker binaries must execute and compare source-derived bytes against the original ROM for an independent assembler pass.

## Whole-bank and whole-system release policy (2026-10-11)

Checkpoint output must close a complete physical 16-KiB bank or coherent game subsystem. Byte coverage alone is not a release-worthy milestone. See `WHOLE_SYSTEM_PLAN.md`. Always distinguish source-only byte identity from semantic understanding and independent external assembler/runtime evidence. A complete bank with unresolved data still has an explicit semantic deficit. The project currently has **two byte-complete banks (3 and 7)**, not two fully decoded gameplay subsystems.

The mandatory system verification command is `make whole-system-verify ROM=/absolute/path/to/owned.sms` within `Ys/`. A source-only dry run is `make two-bank-source`. Never run a regression suite that silently copies the original ROM into a bank and then claims an independent build of that bank. The new 16-bank coverage ledger is `Ys/whole_system/build_report.json`.


## Portable AI-assisted decompilation controls (research adoption)

The root `AGENTS.md` and `shared_decomp/` toolkit provide cross-project matching-task safeguards and a whole-binary partition ledger audit. Use `python -m unittest discover -s shared_decomp/tests -v` and `python shared_decomp/workflow.py audit --manifest shared_decomp/examples/ys_sms_manifest.json` before claiming bank closure; the original ROM can be supplied via `--binary` to independently check all bank hashes. Every bank/section must be owned once, but this is **accounting only**, not source assembly or semantic proof. For bounded matching, lock original targets/build scripts and stop after two non-improving retries. See `AI_DECOMP_ADOPTION.md` for the source review and architecture-specific qualifications.

## Whole-system milestone gate: source-only fixed bank 0

Maintain separate evidence types: (a) ROM-checked Z80 mnemonics, (b) source-
regenerated typed records, (c) semantically unresolved but reversible bytes,
and (d) original-ROM fallback. A bank with (a)-(c) but no (d) is byte-closed,
**not** completely understood. The project has now byte-closed physical banks
0, 3, and 7; use `tools/build_system_m3.py` and `whole_system/build_report_m3.json`
for authoritative M3 accounting. Follow `wholebank00/README.md` for bounds.

Recompile full images with original-ROM fallback kept separate; never use an
original-ROM-sourced overlay hash alone as proof of source-only completion.
When external assembly is absent, preserve `external_wla_dx_verified=false`.
The full cross-bank CFG remains static evidence; an instruction encoded from
ROM does not establish runtime reachability or a correct data/code boundary.

## M4 evidence update — four source-independent banks

Fixed bank 0 and switchable banks 3, 6, and 7 are now byte-exact standalone
builds. Bank 6's new 9,192 bytes are represented by 926 eight-byte visual
lanes (unresolved encoding), 1,520 indexed tile bytes, two pointer directories
(16 bytes), seven count-prefixed sprite-triplet layouts (241 bytes), and seven
fill bytes. This is a **binary source-ownership** closure, not full semantic
reconstruction. Use `make four-bank-source` without any ROM and `make verify
ROM=/path/to/Ys.sms` for the 16-bank comparison and historical tests. The
project currently has **four** byte-complete banks, not four understood game
subsystems. External WLA verification remains absent.


## M5 sound-bank closure evidence

All 16,384 bytes of physical bank 2 are emitted without original-ROM input.
Prior 3,785 sound code/header bytes + 16 newly annotated mnemonic bytes +
12,583 new typed/explicitly unresolved data bytes. Data spanning `$8CFE–$AA76`,
`$AD80–$B318`, and `$B6E8–$BE56` is byte-preserving rather than decoded
music grammar. Ensure claim standards do not confuse *source-owned sound bytes*
with independently observed sound playback. Static source references to PSG
port `$7F` and YM2413 ports `$F0/$F1` are recorded in
`Ys/wholebank02/static_sound_links.json`.

## Whole-system M6 gate

`cd Ys && make system-m6-verify ROM=/path/to/original.sms` validates the six independent 16-KiB bank builds, all prior phases, and exact-ROM integration. Source-only bank1 status is separate from semantic interpretation: its 13,528 unresolved bytes must not be counted as decoded game logic. WLA-DX fixture preparation is not an external assembler test.

## Whole-System M7 evidence gate

A byte-complete bank build with unresolved data is not a semantically complete subsystem. Bank4's 502 × 32-byte groups are solely a byte-preserving partition, never treat them as verified graphics tiles. Bounded Z80 collision routine execution at `$807C` is machine-level evidence with seeded registers, not evidence of actual gameplay caller mapper state. All bank-wide claims must retain ROM-independent emit, full-ROM owner-ROM comparison, explicit provenance, source-mutation failure tests, and real external assembler unverified until executed. Default verification uses `Ys/tools/run_system_m7_regressions.py`.

### M8 ownership and validation protocol

* Banks 8 and 10 use `tools/whole_banks08_10.py`. One-time `--capture` mode
  requires a SHA-256-matched owner ROM; all normal assembly is source-only.
* Their large resource bodies are unresolved. Validated pointer tables and
  executable routines are separate evidence classes.
* `tools/bank10_decimal_trace.py` tests original decimal-output opcodes on
  explicitly seeded input; no unsupported frame/graphics claims.
* Nine complete banks must match their frozen SHA-256 and the entire M8 overlay
  must match the owner-supplied 256-KiB fingerprint before each commit.

## Whole-System M9 source-only bank handling

Close banks by proving total 16-KiB ownership without source-ROM reads during normal builds. Preserve opcode mnemonic bytes separately from unresolved data; validate full-bank fingerprints and the exact 256-KiB owner ROM SHA-256. Reconstruct pointer targets and transfer record widths where a genuine consumer supports them. Bank9's `OUTI` loop uses exactly eight pointer-selected six-byte records. Keep all unresolved resource spans explicitly classified; **source-only byte reproduction is not semantic decompilation**. Three additional banks (9,11,12) complete in M9. Remaining banks 5,13,14,15 are outstanding. Do not infer runtime semantics from mere byte-equality.


## Independent external-tool evidence (M11)

- Treat full-system emulator boot as a separate gate from emulator **gameplay**,
  timing, sound, or controller verification. A GUI window alone does not suffice:
  capture nontrivial framebuffer pixels, compare against an independently
  loaded owner-ROM baseline and store hashes rather than copyrighted assets.
- The approved Emulicious check recompiles all 16 banks from committed sources,
  verifies source-only ROM SHA-256, launches each ROM via externally supplied
  Emulicious.jar under Xvfb, and compares stable title-art pixels. Re-run after
  meaningful graphics, boot, mapper, or whole-cartridge changes.
- A WLA-DX `.exe` built for Windows is **not** a native Linux `wla-z80`. Never
  report fixture generation or non-executable binaries as independent assembly.
  Native assembler acceptance requires actual `wla-z80` + `wlalink` executions
  and the full bank/cart byte comparison, with build logs and versions.
- Keep proprietary ROMs, emulator JARs, third-party executable distributions,
  JVM runtimes, boot screenshots, and compiled bank files outside Git. Only
  test harnesses, expected digests, and reproducible reports belong in source.

## Independent Z80 assembler verification (M12)

Where user-provided `Emulicious.jar` is available, execute the built-in Z80
assembler through `Ys/tools/verify_emulicious_assembler_m12.py`. A real test
currently verifies 11,009 mnemonic instructions / 22,552 bytes from the 16
bank sources against the exact source-built ROM. The project encoder supplies
addressing/lengths only; it does **not** generate the external bytes. This is
an external opcode check, not an independent WLA-DX full linker build. The
`make verify EMULICIOUS_JAR=... ROM=...` gate includes this test. Without the
jar, only the recorded-evidence unit tests run; do not claim a fresh external
assembler pass. See `Ys/whole_system/M12_README.md`.
