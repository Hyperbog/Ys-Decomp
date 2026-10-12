# Phase 10A — Assembly expansion experiment (paused)

**Branch:** `SMS`  
**Source:** original USA/Europe Ys SMS ROM (SHA-256 recorded in `../manifest.json`).  
**Status:** EXPERIMENTAL; unverified encoder. The known-good Phase 9B 111-byte matching assembly is unchanged.

## Work accomplished

Inspected the ROM, current Git history, the fixed and banked opcode listings, the Phase 9B source, and available assembler binaries. Existing decoded candidate instruction inventory:

| Prior classification | Starts | Instruction bytes |
|---|---:|---:|
| Phase 5 | 2,055 | 4,154 |
| Phase 6 | 2,027 | 4,474 |
| Phase 7 | 376 | 763 |
| Phase 8 | 502 | 797 |
| **Total candidate inputs** | **4,960** | **10,188** |

These numbers summarize existing analysis, NOT newly covered ROM bytes or assembler-built matches. Code/data labels and mapper assignments remain subject to the confidence markings in the original listings.

Draft `experimental_z80_roundtrip.py` creates opcode encodings from a standalone table rather than reading source-ROM bytes at emission. Design includes unprefixed, ED, CB, and DD/FD indexed families, relative displacement checks and `org`/label parsing. This draft is intentionally stored under `phase10/`, not production `tools/`, because **it currently does not import or run**.

## Blocking error — two correction attempts used, no further retries

First attempted run showed incorrect handling of negative relative displacement and indexed CB opcode selection; e.g. `DJNZ $06DA` at `$06E3` was incorrectly rejected, and `BIT 2,(IY-2)` emitted `FD CB FE 50` instead of canonical `FD CB FE 56`.

Following a correction attempt, the next invocation failed with exactly:

```text
Sorry: IndentationError: unindent does not match any outer indentation level (z80_roundtrip_phase10.py, line 168)
Traceback (most recent call last):
  File "<stdin>", line 2, in <module>
  File "/mnt/data/SMS-NES-Decomp/Ys/tools/z80_roundtrip_phase10.py", line 168
    return bytes(value)
                       ^
IndentationError: unindent does not match any outer indentation level
```

**Proposed repair (not applied or retested):** Lines 166–168 should be a `for ... else` body with both statements consistently indented, guarded by `if ddcb`:

```python
        else:
            if ddcb:
                value.append(opbytes[-1])
            return bytes(value)
```

This is a *syntax* repair only. Once applied, validate opcode encoding using independent expected outputs for: `JR NZ,$06DA` at `$06E3` → `20 F5`; `DJNZ $06DA` at `$06E5` → `10 F3`; `BIT 2,(IY-2)` → `FD CB FE 56`; `RST $0028` → `EF`; `LD A,(IX+17)` → `DD 7E 11`. Then verify all generated code byte-by-byte against fingerprint-validated ROM, explicitly reject altered operands and corrupted ROM input, and ensure branch targets/bank assignments are independently checked. Do not claim a pass on any of these until run.

No external Z80 assembler (`z80asm`, `sjasmplus`, `pasmo`, `sdasz80`) was found installed in this environment. Direct download attempts failed DNS resolution, so independent external assembler validation remains outstanding.

## Preservation

The Phase 9B restricted-assembler source and verification reports were not edited. The draft's nonworking status must not be mistaken for a regression in the prior production checks. Actual emulator execution and a complete byte-identical ROM build are still unverified.

**[PAUSED: Ready to continue with Phase 10B — repair experimental encoder, add tests, then expand matching bytes]**

## Phase 10B — verified continuation

**The Phase 10A encoder blocker was repaired and tested.** The production subset
now lives at `../tools/z80_roundtrip_phase10.py`. For full verification
results, precise limits and reproducible commands, see [PHASE10B.md](PHASE10B.md).
**4,960 independently assembled mnemonic instructions / 10,188 matched bytes**
from the previously classified regions, with **10,238 distinct assembler-
matched bytes across Phases 9B+10B after 61 overlapping bytes are deducted**.
All prior suites plus Phase 10B pass; neither external toolchain nor emulator
execution equivalence has yet been established.
