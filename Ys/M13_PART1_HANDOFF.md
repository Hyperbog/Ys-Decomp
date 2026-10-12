# Ys Decompilation — Part 1 to Part 2 handoff

This file preserves the final Part 1 conversation checkpoint alongside the
source-controlled M13 semantic-audit snapshot. The conversation reported
additional asset-recovery work **after** the repository's current M13 semantic
audit commit. Those later graphics changes are **not present in this archive**.
The observations below are historical reports, not tests rerun from this source.

## Source-controlled baseline in the supplied archive

- Branch: `SMS`
- Starting commit: `90b6e6c2cd15fef3d48249c2355ac733e4a5e3a8`
  (`Audit semantic debt across all 16 source-only banks`)
- 16 of 16 banks reconstruct a 256-KiB ROM without an original ROM template.
- Recorded ROM reference SHA-256:
  `02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`
- The M13 semantic-audit checkpoint predates the graphics work described below.

## Final Part 1 conversation: reported Milestone 13 work

1. Bank 13 includes a 50-entry pointer directory identifying RLE-compressed
   graphics resources.
2. Each resource reportedly decodes as four separately terminated blocks of
   72 bytes apiece, or 288 bytes per resource: 50 x 288 = 14,400 decoded
   bytes. Each block ends with a zero control byte.
3. The working interpretation is nine Sega Master System 8x8 tiles per
   bitplane, across four bitplanes, producing a 3x3 grid of 24x24-pixel icons.
4. Visual reconstruction reportedly produced recognizable inventory icons,
   including swords, shields, and rings.
5. The end of each stream was reported to coincide with the following
   resource pointer for 49 entries; additional data remains after entry 50.
6. The graphics source conversion was reported to replace 10,659 opaque
   compressed bytes with decoded blocks and reversible compression recipes.
   An unrelated 5,607-byte trailing area was not yet decoded.
7. Additional work reportedly covered Bank 05 RLE and exploratory/parser
   testing for Banks 14–15, with lossless decode/re-encode and pixel-bitplane
   round-trip regression checks, palette packaging, and asset inventories.
8. The previous conversation concluded with regression/build validation,
   documentation updates, a commit, and packaged source archive verification.
   **The commit SHA and the reported later source edits were not included in
   the M13 semantic-audit archive supplied to Part 2.**

## Safe resumption procedure

1. Preserve this source-controlled snapshot and its full Git history.
2. Obtain the newer Part 1 archive or exact commit, if available.
3. Compare before porting to avoid overwriting later changes.
4. If unrecoverable, reimplement RLE identification/decoding in small changes.
5. Require byte-for-byte ROM rebuild SHA-256 equivalence and resource-level
   decode/re-encode/pixel-bitplane round-trip tests before accepting changes.
6. Keep commercial ROMs, extracted copyrighted art previews, external tools,
   and transient outputs outside the Git repository.

## Provenance

The graphics observations above were transcribed from the user's Part 1
conversation excerpt supplied in Part 2 on 2026-10-12. They must not be
mistaken for verified source code in the attached M13 archive.
