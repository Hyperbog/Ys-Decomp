# Decompilation workflow research — 2026-10-11

Source scope: [decomp.dev](https://decomp.dev/) and its [public implementation](https://github.com/encounter/decomp.dev), [decomp.me FAQ](https://www.decomp.me/faq), [objdiff](https://github.com/encounter/objdiff), [decompedia](https://decomp.wiki/), and [splat](https://github.com/ethteck/splat).

## What the tools actually do

- **decomp.dev** publishes and tracks project progress using reports and GitHub automation. Its public repository describes it as a progress website and bot; `objdiff` supplies detailed progress reporting. It is *not* an automatic game decompiler.
- **decomp.me** provides small shareable function-matching workspaces: target assembly + proposed C/C++ + shared definitions + compiler preset, with automatic compile/disassembly/diff. It cannot upload and automatically decompile a complete binary. Its FAQ explicitly asks developers not to scrape or automate repeated requests.
- **objdiff** automates rebuilding and comparing functions and object files, with per-function reporting. Its published supported CPUs do **not** include Z80, and its object-file workflow cannot be assumed to work on SMS ROM segments.
- **splat** is an example of a reproducible binary splitter. The general idea of segment manifests applies to SMS; a MIPS-specific configuration or scripts should not be transplanted unchanged.
- **decompedia** explains a key platform distinction: much of the 5th-generation-and-newer work is recovering matching C/C++ built with original compiler versions. For 8-bit Z80 games, reconstructing symbolic assembly and the original bank/data structure may be the more appropriate goal. No source establishes which language Ys was originally authored in.

## Why sophisticated projects can appear to move faster

1. A prebuilt ROM/binary splitter establishes trusted code/data boundaries so everyone avoids repeated triage.
2. A known compiler, assembler and flags make function matching mechanical after the initial compiler-research investment.
3. Feedback arrives per function immediately, with highlighted first differences rather than one opaque failure at build time.
4. Shared type/symbol databases and repeatable contexts prevent rediscovery of RAM fields, function signatures and asset formats.
5. Distributed contributors work on disjoint units and integrate independently matched results.
6. Dashboards track *actual matching* separately from work-in-progress and make regressions visible.

These are documented workflow characteristics, **not evidence that other teams routinely finish entire complex games quickly**; published completion percentages and screenshots alone do not establish person-hours or comparable scope.

## Adopted now in SMS / Ys

**Offline function-level matching:** `Ys/tools/scratch_compare.py` accepts an original local ROM, one sparse Z80 assembly source, and an explicit physical bank. It emits first-difference diagnostics and optional JSON without embedding ROM payload. It checks the pinned ROM SHA-256 and enforces physical-bank/CPU-slot mapping. This brings the *tight iteration idea* of decomp.me into our existing restricted assembler.

**Regression tests:** `Ys/tests_scratch_workflow.py` proves that an existing 1,345-byte bank-7 routine matches and that a changed mnemonic, wrong ROM, impossible bank mapping or empty source is rejected.

**Source distinction:** This check proves bytes emitted by **our own** assembler match the supplied ROM. It does not independently validate those bytes with a third-party assembler, prove runtime execution, or rebuild the whole ROM. It does not increase ROM-byte coverage.

**Quick start:**

```sh
python Ys/tools/scratch_compare.py /path/to/owned/Ys.sms \
  --source Ys/src/phase13/bank07_unrolled_vdp.asm --bank 7 \
  --json /tmp/ys_bank7_match.json
python Ys/tests_scratch_workflow.py /path/to/owned/Ys.sms
```

## Highest-value next upgrades (not yet implemented)

1. **Independent Z80 assembler + deterministic full-ROM linker:** choose and verify a third-party assembler, provide bank-aware placement, and compare a complete reconstructed ROM with the original. Do not claim this is available yet.
2. **Unified interval ownership:** one machine-readable manifest partitioning all 16 banks into code, structured data, padding, provisional data and unknown. Fail on overlaps or unexpected gaps; automatically calculate category-specific progress.
3. **Symbol and cross-reference database:** `(physical_bank, CPU_address, mapper_state)` identifiers, incoming/outgoing edges, RAM fields, confidence level, and evidence paths. Never assign a bank just from CPU address alone.
4. **Function queues:** small, self-contained unmatched regions ranked by proven inbound references, stable bank context and low ambiguity; keep provisional data separate from code work.
5. **Runtime capture:** VDP writes, mapper registers `$FFFC-$FFFF`, PC and frame counters; correlate traces to static labels and test game behavior.
6. **CI and progress history:** run inexpensive unit tests per change and deeper ROM-dependent tests only where the user supplies the ROM locally/privately; publish digest-and-offset-only progress reports (never commercial bytes).

## Guardrails

- The visible Z80/SMS platform is **not listed** by decomp.me or objdiff as supported; do not claim integration.
- Do not send the user's ROM or bulk snippets to external services. Respect decomp.me's no-repeated-automated-requests instruction.
- Do not confuse a 100% *sparse source match* with 100% ROM recovery or meaningful reverse engineering.
- Match progress must count unique physical ROM offsets; refined data interpretations never add already counted bytes again.
