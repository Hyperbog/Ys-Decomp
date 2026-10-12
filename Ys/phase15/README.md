# Phase 15 — Source-backed ROM tables and named cross-references

Checkpoint: 2026-10-11. **Scope is structural, not new code coverage.**

## What changed

Phase 14 rebuilt a complete 256-KiB image with 14,025 matched Z80 code
bytes and 248,119 copied fallback bytes. Phase 15 converts 678 already
identified data bytes into four independent `DB` / `DW` assembly modules.
The modules can be assembled from the committed sources **without reading
the ROM**. The original user-owned ROM is still required for the other
247,441 bytes and to validate the final result.

| Physical bank | CPU structures | Bytes |
| --- | --- | ---: |
| 0 | Game-state dispatch (41 pointers), scene dispatch (9 pointers) | 100 |
| 1 | Sega header at `$7FF0` | 16 |
| 6 | Sprite-record directory (64 pointers), work records (17), handlers (8) | 178 |
| 7 | Graphics directory (64 pointer pairs), secondary directory (64 pointers) | 384 |
| **Total** | **Source-backed structural data** | **678** |

All emitted bytes match the supplied reference ROM. No program ROM or raw
sprite/graphics payload is committed. Source tables are derived from the
existing Phase 6/11/12/13 metadata and cartridge manifest. Any unannounced
change in the metadata invalidates the committed source.

**Assembly-backed total:** 14,025 code + 678 new source-backed data =
**14,703** of 262,144 ROM bytes (5.6087%). **Fallback:** 247,441 bytes.
This does **not** increase the previous 58,133-byte candidate classification
footprint (22.18%). Phase 15 merely upgrades the provenance of bytes already
classified. The cartridge header is included for full source layout, not as
newly discovered ROM content.

## Symbol and reference index

`symbols.json` contains 23 deliberately named ROM/RAM symbols (20 ROM, 3 RAM),
and all 1,196 static control-flow references from Phase 14. Twelve previously
unresolved banked calls now receive **static candidate banks** from a verified
adjacent `LD A,n; LD ($FFFF),A; CALL ...` sequence. Each source offset is in
the ledger. The original `proven_target_bank=null` field remains unchanged:
this is not an emulator trace, nor a guarantee a path executes.

The tables have named labels, and RAM buffer names use the known SAT staging
addresses. Names are analyst-created and are *not* recovered original labels.

## Reproduce

Run from the repository root with Python 3:

```bash
python Ys/tools/source_tables_phase15.py --verify
python Ys/tools/symbols_phase15.py --verify
python Ys/tools/build_phase15.py '/path/to/your/Ys.sms' --verify
python Ys/tests_phase15.py
```

Optional full-image output (keep it outside Git):

```bash
python Ys/tools/build_phase15.py '/path/to/your/Ys.sms' --verify --out /tmp/ys-overlay.sms
```

`build_phase15.py` checks the supplied ROM fingerprint, reassembles code and
data, rejects source/ROM mismatches and overlapping output ranges, and writes
the complete image only when requested. `source_tables_phase15.py --sync`
regenerates the four data-source files if their upstream metadata changes.

## Remaining limits

- Full 256-KiB source-only ROM is **not** available; unknown ROM payload is copied.
- Existing Z80 instructions are matched by the project encoder, **not** SJAsmPlus or another external toolchain.
- No emulator execution trace verifies the static mapper-state candidates.
- Graphics/audio records still require semantic naming, not merely pointer bounds.

Next: move more already-reconstructed data out of fallback, validate a real
external assembler when available, and add emulator trace evidence.
