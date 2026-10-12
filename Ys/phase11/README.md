# Phase 11A — Extended sparse reconstruction (partial regression checkpoint)

## ROM and build evidence

The Phase 11 generator completed successfully against the private 262,144-byte SMS ROM with SHA-256 `02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.

- **6,158 decoded Z80 instructions / 12,439 assembled, ROM-identical instruction bytes** (unique physical offsets). This adds 1,198 instructions / 2,251 assembled bytes over the Phase 10B subset; 50 of these bytes were already matched in Phase 9B, so the cumulative all-phase assembly total rises from 10,238 to 12,439 (+2,201 distinct bytes).
- 97 first-bank boot instructions (185 bytes) extracted from the previously verified Phase 1 annotated listing. Entries marked `DB`/`DW` are not misclassified as code.
- 342 Phase 2 instructions (612 bytes), 257 Phase 3 instructions (523 bytes), and 274 Phase 4 instructions (528 bytes), reconstructed from bounded, audited ranges.
- 228 newly traced bank-6 instructions (403 bytes), rooted at CPU `$9932` and `$9966`, following explicit fixed-bank writes of `$06` to mapper port `$FFFF`. **These are static path-local interpretations, not emulator-confirmed execution.**
- 64 two-byte entries (128 new classified ROM bytes) in physical bank 6, `$18000–$1807F`, with distinct destinations in CPU `$8000–$9931`. The ROM routine at `$9932` doubles its input index and reads from `$8000 + 2 × index`; the directory's valid runtime index range and pointed-to payloads are not yet established.
- 176 × 32-byte tile blocks (5,632 previously counted ROM bytes) reversibly reencoded using the earlier Mode-4-compatible bitplane transform. The Phase 9 uploader expands certain source spans into VRAM format at runtime; these tile-grouping results **do not prove native on-screen tile usage**.

### Accounting (non-overlapping physical ROM offsets)

| Metric | Bytes | Interpretation |
|---|---:|---|
| Phase 10B assembly-matched union | 10,238 | Previously verified project encoder output |
| Phase 11 additional assembly-matched offsets | 2,201 | Includes the newly traced bank-6 code |
| **Cumulative assembly-matched code** | **12,439** | Project encoder; no external assembler |
| Independently reencoded tile data | 5,632 | Counted as provisional data in Phase 7 |
| Bank-6 indexed pointer table | 128 | Newly classified structured ROM data |
| **Combined code + reversible data footprint** | **18,199** | 6.94% of ROM; distinct offsets |
| New candidate classified offsets | 531 | 403 bank-6 code + 128 pointer bytes |
| **Cumulative candidate ROM footprint** | **38,279** | 14.60% of ROM, *not* functionality completion |

## Source artifacts

- `../src/phase11_roundtrip/bankNN.asm`: sparse source for physical banks `00`, `01`, `02`, `04`, `06`, `07`, `08`, `10`, `12`. Each `org` and comment retains CPU and physical ROM provenance; gaps are not filled with guessed opcodes.
- `../tools/rebuild_phase11.py`: strict SHA-256 gate, legacy-region reconstruction, mapped bank-6 trace, independent mnemonic encoding, per-bank `assemble()` comparison, tile pixel-encoding and pointer-structure checks. `--write` generated the verified source and JSON report.
- `report.json`: deterministic per-bank counters and hashes, confidence notes and data/accounting methodology.
- `../tests_phase11.py`: **experimental test runner; not passing in this checkpoint** because legacy imports are not package-relative.

## Verification results

1. Phase 11 generator ran with `--write` and reported `PASS Phase11: 6158 assembled instructions / 12439 code bytes; 5760 reversible data bytes; 18199 combined unique bytes`.
2. All **10 preexisting regression suites**, Phases 1–10B, were rerun as individual processes and returned exit code zero.
3. The new Phase 11 test runner **has NOT completed**, and Phase 11 is **not promoted as a fully regression-verified checkpoint**. After two correction attempts, testing was stopped per project policy.

### Blocking traceback (the latest attempt)

```text
Traceback (most recent call last):
  File "Ys/tests_phase11.py", line 9, in <module>
    from tools import rebuild_phase11 as build
  File "Ys/tools/rebuild_phase11.py", line 17, in <module>
    from .bank_trace_phase8 import walk_bank
  File "Ys/tools/bank_trace_phase8.py", line 14, in <module>
    from z80_regions import decode
ModuleNotFoundError: No module named 'z80_regions'
```

**Proposed next repair:** Make `bank_trace_phase8.py` (and its legacy imports, if necessary) safely importable as part of the `tools` package, or arrange for `Ys/tools` to be on `sys.path` in `tests_phase11.py` before importing `tools.rebuild_phase11`. This repair has **not** been tested or claimed in Phase 11A. Subsequently run `tests_phase11.py` and `rebuild_phase11.py --check`, including mutation gates.

No commercial ROM or reencoded graphic payload is committed. A matching complete ROM image, independent external Z80 assembler, and emulator-verified runtime are not claimed. Repository branch `SMS` remains local.
