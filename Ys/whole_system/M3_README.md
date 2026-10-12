# Whole-system Milestone 3 — Source-only banks 0, 3, and 7

Original ROM size: 262,144 bytes (16 physical banks × 16 KiB).
Original SHA-256: `02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.

| Metric | M2 | M3 |
|---|---:|---:|
| Complete independent source-only banks | 2 (3,7) | **3 (0,3,7)** |
| Whole-bank source-independent bytes | 32,768 | **49,152** |
| Total source-backed ROM | 53,249 | **61,391 (23.42%)** |
| Remaining input-ROM fallback | 208,895 | **200,753 (76.58%)** |
| Newly encoded Z80 instructions (bank0) | — | **6,518 bytes** |
| Newly typed bank0 metadata and padding | — | **463 bytes** |
| Newly preserved, unresolved bank0 bytes | — | **1,161 bytes** |
| Cross-bank instruction bytes in evidence graph | 14,198 | **20,716** |

### Requirements for binary bank closure

1. Every one of the 16,384 physical bank bytes has a non-overlapping project
   source owner; no original-ROM fallback inside banks 0, 3, or 7.
2. Normal bank builds read no game ROM and reproduce both a cryptographic
   bank digest and the user-supplied ROM's corresponding 16-KiB span.
3. Mixed-source Z80/DB/DW listings reassemble using the in-project assembler.
4. Source mutations and mapping conflicts are rejected.
5. The **full ROM build still requires fallback for all other banks**.

All 16 physical banks are individually reported in `build_report_m3.json`.
The updated `evidence_graph_m3.json` includes the new fixed-bank Z80 code and
preserves mapper uncertainty. Its extra static edges are not runtime execution.

### Remaining whole-system gates

* 13 banks still retain input-ROM fallback; full source-only ROM not achieved.
* New fixed-bank instruction ranges have not all been exercised in an emulator;
  linear disassembly can mistake embedded data for opcodes.
* 1,161 new fixed-bank bytes are still opaque, plus undecoded spans in banks 3/7.
* WLA-DX independent external assembly was prepared but **not run**;
  no `wla-z80` or `wlalink` executable installed locally.
* Comprehensive full-game execution, audio and text semantics remain open.

**Next closure target:** physical bank 6 and its sprite/object subsystem, where
7,192 bytes are already independent sources and record-to-VDP bounded execution
has been tested. Do not count generated DB blobs as semantically complete work.

### Updated fixed-bank CFG frontier

All five M2 missing fixed-bank target **addresses** are now source-backed.
The expanded graph identifies three new instruction-boundary conflicts at
`$1033`, `$1036`, and `$1681`. They remain unverified alternate-entry
candidates; some appear to land within linear-decoded operand bytes.
See `frontier_m3.json`. Do **not** count them as newly established functions,
and do not infer that byte-exact linear decoding proves unambiguous code/data
separation.
