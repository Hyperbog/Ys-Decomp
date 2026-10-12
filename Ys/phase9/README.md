# Phase 9A — ROM-to-VDP data provenance (partial checkpoint)

**Source:** original Ys SMS ROM, SHA-256 `02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
**Status:** Four upload-source spans and static VDP byte transformations independently reconstructed. **Restricted assembler binary match is NOT verified.**

## Verified uploader

- At fixed-bank `$0BA1`: `LD A,$03; LD ($FFFF),A; RST $28` switches in physical ROM bank 3 and writes the VDP address using `$BF`.
- `$0BA7–$0BB6` loops `C` times, with 16 source bytes per iteration. Each ROM byte written to `$BE` is immediately followed by zero. Hence `16*C` ROM bytes become `32*C` VDP bytes, i.e. one Mode-4-shaped 32-byte tile per iteration.
- Four immediate-argument sequences ending in `CALL $0BA1` are checked against their actual opcodes; the ROM bank is chosen *inside* `$0BA1`, not guessed from prior callers.
- The 4 sites access 3,248 ROM bytes (including repeats), producing 6,496 VDP bytes. The source union is **1,184 distinct bytes**, physical `$0D14A–$0D5E9`. These bytes are *already* included in prior Phase 7–8 candidate coverage.

| Caller | Bank 3 source physical | Source bytes | VDP destination | Emitted bytes |
|---|---|---:|---|---:|
| `$1DC8` | `$0D14A–$0D529` | 992 | VRAM `$1400–$1BBF` | 1,984 |
| `$3C9C` | `$0D1EA–$0D5E9` | 1,024 | VRAM `$2820–$301F` | 2,048 |
| `$3CA7` | `$0D14A–$0D219` | 208 | VRAM `$2600–$279F` | 416 |
| `$3D97` | `$0D14A–$0D549` | 1,024 | VRAM `$2C00–$33FF` | 2,048 |

**Interpretation correction:** The Phase 8 method of grouping `$C000–$D5FF` as native 32-byte Mode-4 tile images is mathematically reversible but does *not* demonstrate that all bytes are uploaded as raw 4bpp tiles. The four demonstrated source ranges are consumed as **16-byte/tile source streams**, expanded into 32-byte Mode-4-compatible VDP output. Both interpretations of those bytes cannot be presented as equivalent runtime semantics. Do not double-count the 1,184 source bytes as newly covered data.

## Binary-equivalence attempt: checkpoint, not pass

A separate custom two-pass restricted Z80 assembler is drafted at `../tools/z80_subset_asm_phase9.py` with source `../src/phase9_vdp.asm`. It has *not* yet passed its generated-vs-ROM check. The last encoder comparison produced:

```
FAIL Phase9 assembler: Assembler mismatch at $06E4: built $F6, source $F5
```

The Z80 branch opcode `JR NZ` at `$06E3` should target `$06DA` (`LD A,L`) rather than `$06DB` (`OUT ($BE),A`). In the draft assembly, move the `.WordLoop` label from immediately before `out ($BE),a` to immediately before `ld a,l`, then re-run the comparison and new negative tests. The custom encoder is *not* a third-party assembler and is not a completed full Z80 assembler. Under the project's two-retry policy no further automated repair attempt was made this phase.

## Reproduce verified part

```sh
cd Ys
ROM='/path/to/Ys - The Vanished Omens (USA, Europe).sms'
python tools/vdp_upload_phase9.py "$ROM" --check
```

Metadata `vdp_uploads.json` is reproducible without committing raw game data. Actual VDP timing, mapper state during interrupts, game palette contents, external assembler matching and full ROM rebuild remain unverified.

**Next:** resolve the draft label offset; independently verify assembled output; add mutation tests; trace the conditional graphic upload call path and song stream grammar. This phase is a **partial checkpoint**, not a completed Phase 9.

## Phase 9B — First verified restricted-assembler round-trip

**Status:** PASS for four disjoint selected Z80 routines; no matching full-ROM
build, external full-Z80 assembler run, emulator trace, or graphics timing proof.

The Phase 9A failure at physical `$06E4` was caused by a misplaced local
`.WordLoop` symbol. Both original branches (`JR NZ` at `$06E3`, `DJNZ`
at `$06E5`) target `$06DA`, the `LD A,L` instruction. The draft had set
`.WordLoop` to `$06DB` and produced `$F6` instead of ROM `$F5` at `$06E4`.
Moving `.WordLoop` immediately ahead of `LD A,L` yields a verified exact
byte match for all four independently emitted assembly sections:

| Fixed-bank ROM interval | Assembled bytes | SHA-256 of bytes |
|---|---:|---|
| `$05F2–$0623` | 50 | `fdf4fc15d846cac2c782a8fa8f6df518deeef8ed4e6799c75f2c718bdc28afb0` |
| `$06C1–$06D3` | 19 | `cb9dbd1119c143698dcfac5a4c774ae5c157dfa10eec35eac9cf4db099a0f125` |
| `$06D4–$06E7` | 20 | `81f2fe18b6c2caad6e0bce486af9d267fe69c4475b7e43a6eefccf51c6368dc8` |
| `$0BA1–$0BB6` | 22 | `a2acb58c74700864082c4cfee35543a6cf4268d8ce3f61079a01207ee29925ec` |
| **Total** | **111** | See `assembly_report.json` |

The assembler (`tools/z80_subset_asm_phase9.py`) is an intentionally restricted,
separate two-pass opcode encoder; it does not read the ROM to emit code. The ROM
is only used *after* emission for fingerprint and byte comparison. It cannot
assemble arbitrary Z80 source or the entire game. An independent Z80 decoder
checks ROM instruction boundaries against emitted source spans.

`tests_phase9.py` covers ROM identity, both VDP uploader and assembly metadata,
instruction lengths, key branch destinations, rejected bad source, and mutations
of source labels, opcode encodings, reports, and original ROM bytes. The Phase 1–8
suites each passed; Phase 9B passed on a separate invocation following a combined
suite timeout. No meaningful byte coverage increase is claimed: all 111 assembled
bytes were already among previously classified addresses; cumulative candidate
footprint remains **37,748 of 262,144 (14.40%)**.

Reproduction:

```sh
cd Ys
ROM='/path/to/Ys - The Vanished Omens (USA, Europe).sms'
python tools/z80_subset_asm_phase9.py "$ROM" --check
python tools/vdp_upload_phase9.py "$ROM" --check
python tests_phase9.py "$ROM"
```

**Next:** make the restricted module buildable by a third-party Z80 assembler,
reconcile syntax differences, add bank-aware assembly modules without copy/paste
of raw ROM blocks, and test VDP transfers with reproducible emulator traces.
