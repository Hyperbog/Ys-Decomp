# Phase 17 — Source-backed graphics and full-image integration

Checkpoint: 2026-10-11. This phase upgrades **15,688 already identified bytes** to editable, regenerable graphics sources. **It adds no newly classified ROM bytes.**

## Source formats and byte provenance

| Physical region | Source structure | Data bytes | Proof |
| --- | --- | ---: | --- |
| Bank 3 `$0C000–$0D5FF` | 176 Mode-4-compatible 8×8, 4bpp tiles; each tile stored as eight 8-pixel hexadecimal rows | 5,632 | Independently reencoded with 4-bitplane interleave and matched Phase 8 block digests |
| Bank 7 `$1C877–$1EFBE` | 64 variable-length, 1bpp graphics records; each source byte stored as an eight-bit monochrome pixel row | 10,056 | All 64 individual digests matched Phase 13; pointer/length table; no gaps or overlaps |
| **Total** | **240 editable records/tiles** | **15,688** | Exact reference-ROM comparison and 13 negative/positive regression checks |

The bank-7 transfer routine at `$8180–$86C0` expands source bytes to `(byte, $00, $00, $00)` via one `OUTI` and three VDP data-port writes. The resulting **40,224 bytes** is total hypothetical transfer output if each of the 64 records is used once, **not** additional ROM bytes or observed VRAM occupancy. The existing bank-7 directory and transfer instructions are already independently source-backed: together with the newly reconstructed graphics and Phase 16 secondary records, the entire **13,631-byte interval `$1C000–$1F53E` is now source-backed**, with no original-ROM fallback in this interval.

`graphics.json` stores per-pixel data extracted from the user-provided copyrighted ROM. The generated `DB` sources embed the same bytes and should not be publicly shared without considering distribution rights. It is deliberately *not* a metadata-only project archive, although the commercial ROM image itself is excluded.

## Updated build provenance

| Component | Bytes |
| --- | ---: |
| Verified Z80 instruction sources | 14,025 |
| Phase 15 pointer tables/header | 678 |
| Phase 16 semantic records | 7,902 |
| **Phase 17 pixel sources** | **15,688** |
| **Source-backed total** | **38,293 (14.6076%)** |
| Original ROM fallback | 223,851 |
| Complete ROM | 262,144 |

The 58,133-byte (**22.18%**) candidate/classified ROM footprint is **unchanged**. Source-backed bytes are a subset with a stronger evidence standard. The full 256-KiB ROM SHA match still requires fallback bytes supplied from the user's original ROM; this is **not a source-only rebuild**.

## Reproduce

```sh
# Regenerate and verify assembly from committed pixel data; ROM is NOT read.
python Ys/tools/graphics_source_phase17.py --verify

# Full-image assembly-overlay comparison requires the original ROM separately.
python Ys/tools/build_phase17.py '/path/to/Ys.sms' --verify
python Ys/tests_phase17.py '/path/to/Ys.sms'

# Developer-only re-extraction from the exact original ROM (rewrites source):
python Ys/tools/graphics_source_phase17.py --capture '/path/to/Ys.sms'
```

All 13 Phase 17 tests must pass before committing. Rejects malformed rows, invalid indices, changed tile/record data, length drift, altered source text and the wrong ROM. The builder independently checks code/data ownership and exact assembled-byte positions.

## Runtime and external toolchain status

No emulator executable or third-party Z80 assembler was found in this environment at this checkpoint. No emulator event trace or third-party-assembler match is claimed. The graphics formats, pointer connections and prospective VDP transfer are **static ROM-supported findings only**. The next priority is to obtain a compatible emulator/assembler and verify actual mapper writes, VDP output, and complete source-only bank emission.
