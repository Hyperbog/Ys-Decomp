# Phase 14 — Source-overlay ROM build and cross-reference infrastructure

**Status:** Tested local tooling; not a complete source-only decompilation.

## Reproducible build

The overlay builder reads an original, user-supplied 256-KiB ROM, verifies its
SHA-256, independently encodes source modules using the project's restricted Z80
encoder, checks every emitted byte at its physical ROM address, and overlays
these bytes onto a copy of the input ROM. It fails closed on wrong ROM bytes,
unsupported source instructions, duplicate byte ownership and bad bank slots.
The output's full-image SHA-256 must match the original.

```
python Ys/tools/build_sms_phase14.py '/path/to/Ys - The Vanished Omens (USA, Europe).sms' \
  --out /tmp/Ys_overlay_rebuild.sms \
  --report /tmp/Ys_overlay_report.json \
  --references /tmp/Ys_crossrefs.json
```

`--out` writes a commercial-ROM-derived image; do not add it to version control
or package it for redistribution. The project ZIP includes only source,
metadata, tests and history. The input ROM is not embedded.

### Direct-source status

- Original full image: 262,144 bytes / 16 physical banks.
- Restricted-assembler verified code: **14,025 distinct bytes** across 11 ASM
  modules and 9 physical banks (5.35% of total ROM).
- Template fallback: **248,119 bytes** (94.65%), untouched and sourced from the
  user-supplied original ROM. Many of these have data-format knowledge from
  earlier phases, but they are not represented in this builder's ASM coverage.
- Exact output image SHA-256: `02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
- 1,196 syntactic control-flow references indexed. 770 have fixed-bank-0
  destinations; 426 have unproven dynamic cartridge slot mappings.
- Candidate ROM classification remains at the previously reported 58,133 bytes.
  Neither template fallback nor existing ASM has been counted as newly decoded.

`build_report.json` contains per-bank coverage and module ownership information;
`crossrefs.json` lists the source bank, instruction CPU address, mnemonic,
referenced CPU address, and **mapper certainty**. It does not claim function
names, mapper state, or executed control flow that has not been established.

## Optional independent assembler

SJAsmPlus is a genuine external Z80 assembler with a documented `--raw` output
flag (see https://github.com/z00m128/sjasmplus). When it is installed locally,
run:

```
python Ys/tools/build_sms_phase14.py '/path/to/original.sms' \
  --sjasmplus sjasmplus --report /tmp/external_build_report.json
```

This optional check uses an **independent executable** to assemble the contiguous
bank-7 `$8180–$86C0` module and compares all 1,345 emitted bytes against ROM.
It never uses the source ROM as assembler input. It fails if the assembler is
missing or emits different bytes. This environment has **not** run that
independent check because SJAsmPlus is unavailable and GitHub cannot be reached
from the container. The default build report therefore explicitly states
`external_assembler_verified: false`.

## Verification

`python Ys/tests_phase14.py` runs nine automated checks, including negative
cases for a one-byte-modified ROM, an assembly mutation, invalid physical bank
mapping, and a duplicate module. The previously implemented Phase 11B, 12, 13
and offline-scratch suites also pass separately in this environment.

## Next stage

1. Run and verify independent SJAsmPlus on a machine where it is installed.
2. Replace original-ROM fallback regions one at a time with reproducible source
   code or reversible data declarations, tracking a distinct `source_only_bytes`
   metric and never double-counting classified regions.
3. Enrich the cross-reference index with ROM-grounded symbolic names, and add
   emulator trace provenance before promoting banked targets to resolved.
4. Keep the template build stable as a control against which source-only
   reconstruction can be tested incrementally.

### Extended regression checkpoint

In the Phase 14 session the individual Phase 1–14 suites (including separate
Phase 11A and 11B) and the offline-scratch workflow **all passed**. A combined
sequential command exceeded its runtime limit after Phase 8; the remaining
suites were then run separately, including the long-running Phase 9 suite.
This is not an emulator-playability certification.
