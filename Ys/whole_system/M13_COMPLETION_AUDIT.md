# M13 — Completion assessment and semantic recovery queue

## Verified in this checkpoint

- All 16 physical 16-KiB bank images rebuild without reading an original ROM.
- The joined 262,144-byte ROM exactly matches the owner's SHA-256 `02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
- The **complete source listings**, rather than an inferred disassembler coverage estimate, contain **22,552 instruction-mnemonic bytes** and **239,592 bytes of `DB`/`DW` directives**. These categories cover every byte exactly once.
- Of these sources, **141,581 bytes** sit below names explicitly indicating unresolved, undecoded, opaque, candidate, or unknown material. This is a **lower bound on explicitly labeled semantic uncertainty**, not a measure of every unverified semantic fact. A `DB` area outside those labels is not automatically interpreted.
- The audit checks every instruction length, data literal, ORG, overlap and bank boundary. It is enforced with `make semantic-audit` and negative tests.

## What is *not* complete

1. A source-only exact byte copy is **not** evidence that all gameplay routines have been identified. All 16 banks contain bytes, but only ten have recovered mnemonic instructions in their current complete-bank sources.
2. Emulicious's independent opcode assembler previously matched the 22,552 recovered instruction bytes (M12); this is **not** an independent linking of the 16-bank cartridge.
3. The M11 Emulicious title-screen smoke test confirmed the game starts. It was not a frame-deterministic full-game equivalence or gameplay/audio trace.
4. Binary-level semantic debt includes data that is not literally labeled unresolved; the 141,581 figure must not be described as an exhaustive unknown-byte count.
5. The WLA-DX source toolchain remains unavailable in this offline Linux container, and the supplied v10.7 Win32/Win64 executables are PE binaries.

## Priorities, ordered by explicit uncertainty labels

| Bank | Explicitly uncertain bytes | Recovered mnemonic bytes | Target |
|---:|---:|---:|---|
| 15 | 16,380 | 0 | Identify resource consumers / compressed format |
| 14 | 16,342 | 0 | Identify resource consumers / compressed format |
| 13 | 16,266 | 0 | Trace 50-entry bank-end resource directory |
| 10 | 16,171 | 75 | Decode script/text records and decimal-output inputs |
| 4 | 16,150 | 38 | Confirm asset encoding and graphics transfer usage |
| 8 | 16,125 | 176 | Recover script and lookup semantics |
| 5 | 15,451 | 0 | Infer graphics/packed resource codec with consumer trace |
| 2 | 11,846 | 2,557 | Execute sound event interpreter; PSG/YM2413 log |
| 12 | 7,804 | 108 | Anchor reachable code and resource indexes |
| 1 | 5,788 | 2,480 | Expand control-flow traces and data ownership |
| 3 | 2,064 | 0 | Decode tile/text control grammar |
| 7 | 1,088 | 1,956 | Characterize remaining visual block |
| 9 | 106 | 65 | Decode glyph terminator/asset semantics |

The remaining banks (0, 6, 11) have zero *explicitly labeled* uncertain bytes; **that does not imply fully decoded semantics**. Bank 11 has no mnemonic assembly in the complete listing.

## Acceptance criteria for actual semantic completion

- Each game-data resource has a typed, reversible format with a traced consumer or independent ground truth.
- Every executable entry point is mapped to a physical ROM bank and carries reachability provenance; uncertain mapper states remain explicit.
- Emulator traces include fixed inputs and deterministic checkpoints of CPU, RAM, mapper, VRAM, and sound state across representative game paths.
- An independent Z80 assembler/linker builds the complete 256-KiB image from source, and its SHA-256 matches without original ROM fallback.
- Regression suites test both semantic behavior and exact source reconstruction, not just a final ROM hash.

M13 is a verified **planning and measurement checkpoint**. It does not claim the above semantic-completion criteria have been met.
