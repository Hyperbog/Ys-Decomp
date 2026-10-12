# Phase 13 — Bank-7 grid graphics directory and VDP expansion engine

**Source:** User-supplied USA/Europe SMS ROM, 262,144 bytes, SHA-256 recorded in `../manifest.json`.
**Status:** Static bank-7 mapper-context trace, deterministic instruction source and independent ROM-byte assembly check, data layouts recovered; not emulator-traced, not externally assembled, not a complete ROM rebuild.

## Overview and bank mapping

Bank 7 is explicitly mapped to the `$8000–$BFFF` CPU slot by the fixed-bank writes at `$01C8` and `$0DD7`, followed immediately by CPU calls to `$8819` and `$86C1`, respectively (Phase 8). The previously recovered bank-7 code at `$86C1–$8876` forms a continuous 438-byte interval. That code references two directories at `$8000` and `$8100` and performs VDP port `$BE/$BF` output.

Newly reconstructed bank-7 assets and executable transfer code fill the regions on either side. **The entire 13,631-byte physical ROM interval `$1C000–$1F53E` is now accounted for**, using nonoverlapping code and data classes. Only 13,193 bytes are new this phase because the existing 438-byte code is not double-counted.

| Component | Physical ROM interval | CPU interval | Byte count | Evidence |
|---|---|---|---:|---|
| 64 graphics/code pairs | `1C000–1C0FF` | `$8000–$80FF` | 256 | `$8856` derives `4*index`, fetches first/second pointer words |
| 64 secondary-record pointers | `1C100–1C17F` | `$8100–$817F` | 128 | `$871C` loads `H=$81`, `L=2*index` |
| Unrolled VDP transfer code | `1C180–1C6C0` | `$8180–$86C0` | 1,345 | 168 times `(OUTI; OUT ($BE),A ×3)` followed by `RET`; separately assembler matched |
| Prior bank-7 game routine | `1C6C1–1C876` | `$86C1–$8876` | 438 | Phase 8 ROM-checked control-flow graph |
| 64 variable graphics records | `1C877–1EFBE` | `$8877–$AFBE` | 10,056 | 64 second-directory words, variable length tied to selected code entry |
| 64 secondary 22-byte records | `1EFBF–1F53E` | `$AFBF–$B53E` | 1,408 | 64 consecutive pointers at exactly 22-byte stride; 11-iteration two-byte fetch loop |
| **Complete union** | `1C000–1F53E` | `$8000–$B53E` | **13,631** | No gap or overlap |

### Graphics transfer mechanism

The producer at `$86C1` derives a 6-bit index from two three-bit subcoordinates and sets bit 7 of `$C199` as an update flag. The transfer routine at `$8856` clears the pending flag, uses the index to load a pair of words at `$8000+4*index`, initializes VRAM control via port `$BF`, and places the corresponding data pointer into `HL`. It enters the chosen unrolled instruction sequence through **`PUSH DE; RET`**. This is deliberate indirect code dispatch, not an ordinary return from the caller.

The instruction interval `$8180–$86BF` has **168 identical eight-byte instruction groups**, each containing `OUTI` (one source byte to port `C=$BE`) and three `OUT ($BE),A` writes. `$8856` clears `A` first, so the resulting bytes are `(source, 0, 0, 0)`. A final `RET` at `$86C0` terminates the transfer.

The table chooses one of seven entrypoints between `$8180` and `$8300`, thereby executing **15–21 eight-row tiles** (120–168 source bytes). All 64 second words point to source spans that precisely abut when sorted by address, from `$8877` to `$AFBF`. Reversing the interleave extracts the original input bytes, for all 64 records. The full ROM source footprint is 10,056 bytes; **40,224 bytes** is the summed VDP write volume if all 64 entries are executed once, **not** unique VRAM occupancy or a trace of gameplay.

The secondary directory at `$8100` has 64 little-endian pointers, from `$AFBF` up to `$B529`, each increasing by 22. `$871C` dereferences these pointers and the loop starting `$8729` reads two source bytes per iteration, 11 times, exactly the 22 bytes per record. The semantic meaning of these bits and their map-coordinate effects is not yet runtime confirmed.

### Size distribution

| Source bytes / record | Record count | Mode-4-compatible 8×8 tiles / record |
|---:|---:|---:|
| 120 | 1 | 15 |
| 128 | 3 | 16 |
| 136 | 1 | 17 |
| 144 | 8 | 18 |
| 152 | 12 | 19 |
| 160 | 14 | 20 |
| 168 | 25 | 21 |
| **Total** | **64** | **1,257 tile instances** |

The *Mode-4-compatible* designation describes the one-plane-to-four-plane output byte ordering only, not the complete game's palette/tile selection or actual frame presentation.

## Verification and coverage

- The new `src/phase13/bank07_unrolled_vdp.asm` uses Z80 mnemonics and sparse `org`, not copied opcode blobs. Project assembler emits all **1,345 original ROM bytes**, checked instruction-by-instruction with a separate ROM decoder. This adds **673 instruction boundaries**.
- `phase13/graphics_directory.json` contains per-record offsets, lengths, hashes, and aggregate metrics, not source payloads.
- The structural analysis tests all 64 code/data pointer pairs, nonoverlapping sorted record spans, 64 × 22-byte records, reversibility of the output byte stream, and zero gaps in the 13,631-byte classified interval.
- The phase-13 tests mutate directory entries, the first unrolled opcode, source assembly, and coverage metadata. The ROM mutation cases temporarily substitute the altered-input fingerprint to demonstrate that the **structural validation**, not merely the ROM SHA check, rejects the invalid entries.

| Cumulative metric | Phase 12 | Phase 13 | New distinct bytes |
|---|---:|---:|---:|
| In-project assembler-matched Z80 instructions | 12,680 | 14,025 | +1,345 |
| Reversibly structured data | 12,180 | 24,028 | +11,848 |
| Stronger code/data union | 24,860 | 38,053 | +13,193 |
| Candidate/classified ROM footprint | 44,940 | 58,133 | +13,193 |
| ROM percentage (candidate footprint) | 17.14% | **22.18%** | +5.03 percentage points |

The candidate/classified metric includes earlier provisional opaque regions and is *not* the fraction of game behavior reconstructed. No independent external assembler, emulator graphics trace, or binary-identical full-ROM build is claimed.

## Reproduce

```sh
python Ys/tools/phase13_bank7_graphics.py '/path/to/Ys.sms' --check
python Ys/tests_phase13.py '/path/to/Ys.sms'
```

The original ROM must be supplied separately and is deliberately excluded from Git and the distributable archive.

## Next steps

1. Run bank 7 under an emulator and capture mapper writes `$FFFF`, VDP control writes `$BF`, and graphics/data writes `$BE` to confirm index selection and final displayed tile positions.
2. Trace the secondary 22-byte record's `$87E5` bit logic to identify map-cell flags and coordinate updates, not just per-record boundaries.
3. Continue from bank-7 `$B53F` with evidence-based code/data entrypoints, and test mnemonic output with a third-party assembler.
