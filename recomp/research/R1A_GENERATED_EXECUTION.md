# R1a — genuine generated-C execution and first divergence

## Actual original-cartridge source path

Original source: exact 262,144-byte Ys: The Vanished Omens (USA/Europe)
image reconstructed from **all 16 committed source banks** without ROM
fallback, SHA-256
`02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.

- Upstream SMS/GG compiler: `mstan/smsggrecomp` pinned at
  `224d5bb2c150a2c295033d35dec629ef9ee42940`, with shared
  `z80-recomp-core` submodule `0e6606a41245d54c5fd0c3dc322ef9d6890d3923`.
- Our verified codegen adapter now preserves all four output files, including
  mandatory `ys_sms_funcs.h`. They are private, ignored, and SHA-hashed.
- All source C was compiled/linked using upstream's real headless
  `runner/main.c`, `runner/glue.c`, VDP, PSG and Z80 fallback C, plus the
  four original-game generated files. External sources were checked out
  temporarily by CI, never committed or redistributed.
- [First successful original generated-C CI run
  38992946897](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38992946897)
  reached **one actual frame** of Ys execution, 59,749 guest cycles,
  **zero fallback calls** and **zero dispatch misses**. A one-frame
  run exercises only a small initialization prefix, with zero recognized
  IRQs and zero sampled game-I/O operations.

## Strict original versus interpreter comparison

[First 60-frame differential run
38993078687](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38993078687)
**failed the strict gate**, despite both paths exiting at 60 frames.

The compiled path: 3 recognized IRQs, 26 hybrid/interpreter calls,
8 distinct dispatch misses (including bank-dependent entries at
`$8883, $8067, $8080, $80C0, $81D9, $01B4, $00FC, $0C4A`).
Its instrumentation reports **97.133% static guest cycles** within its
measured execution (11,753 interpreted of 409,915 measured).

The upstream superzazu reference interpreter ended at 60 frames with
zero generated-function dispatch misses (as expected for the interpreter
path). At frame 1 the first strict difference was:

- **Guest SP: translated `$DFEE`, interpreter `$DFF0`**.

The bounded same-runner frame trace includes VRAM/CRAM/register/WRAM
fingerprints, selected video registers and the current Z80 stack pointer.
This evidence does **not** prove equivalent frame states; even equal
video fingerprints alone could hide different internal CPU instructions,
IRQ timing, stack entries, or unobserved inputs. It is also not an
independent Mesen/Genesis Plus GX hardware check.

The strict `recomp/verify_vdp_parity.py` comparer remains unchanged
in what it requires: **all** recorded fields must match for **every**
requested frame. Failure remains a CI failure; no golden fingerprints
are rewritten, no SP tolerance is introduced, and no game state or PC
is forced. The [second 60-frame diagnostic run
38993200809](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38993200809)
returned the same initial SP discrepancy and strict CI failure.
The all-frame mismatch histogram was:

| Frame fingerprint field | Nonmatching frames (of 60) |
| --- | ---: |
| VRAM | 0 |
| CRAM | 0 |
| VDP register array | 0 |
| Full WRAM | **1** |
| VDP R8/R9/R0/R1 | 0 for each |
| Z80 stack pointer | **57** |

These are checksums, not byte-level CPU-state equivalence. The identity
of the one WRAM-divergent frame and the first differing byte remain to
be established. There is no verified explanation yet for the SP
difference. This strict mismatch **must not** be waived to promote R1.

## Status

- **R1a output provenance + actual generated C compile/link:** verified.
- **R1a one-frame native execution:** verified, diagnostic only.
- **R1b 60-frame differential CPU/VDP/WRAM/SP parity:** **FAILED**.
- **R1c accurate original gameplay, equivalent controller/audio/video,
  and Alpha release gates:** **NOT VERIFIED**.

Investigation should first determine whether the frame-1 two-byte SP
discrepancy comes from an instruction timing boundary, a generated
CALL/RET/interrupt implementation, or a different execution path.
Do not assume which. Next check exact compiled-vs-reference Z80 CPU/stack
state around the first divergence before modifying any evaluator,
reference image, or generated instructions.
