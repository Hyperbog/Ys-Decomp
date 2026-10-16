# PC-7 — Source-verified M44 pattern VRAM with M43 name-table words

**Status:** Source reconstruction + a native *diagnostic*, not an
original-color or fully observed game screen.

## Original instruction/data provenance

The source bank-0 code at `$0C7E–$0C86` selects `HL=$8000`
(original bank 5 remains mapped), `DE=$4000` (VRAM write start
`$0000`), then calls the original pattern expansion helper
`$0695–$06C0`. The helper reads **four** successive streams,
writes each output byte to the corresponding Mode-4 bitplane
position (destination byte offsets 0/1/2/3, stepping by four),
and returns when each stream reaches command 0.

Each source command's high bit chooses between a literal run and
a repeated byte; the low seven bits specify its length, and
`DJNZ` count zero means 256 iterations. The decoder enforces:
- Four streams terminated independently
- Contiguous exact coverage of VRAM `$0000–$2FFF`
- **12,288 written bytes = 384 32-byte tiles**, with no overlapping
  or missing byte; source/VRAM bounds checked
- The actual opcode bytes at `$0695–$06C0` and
  `$0C7E–$0C86` match `Ys/phase5/code.lst` and the
  independently source-rebuilt fixed bank 0
- Compressed input bytes come from reconstructed physical bank 5
  via `Ys/tools/whole_banks05_13_14_15.py` and its digest verification,
  with **no external commercial ROM loaded**

This is the same original program/source path whose **M44
cartridge-backed trace verified 12,288 pattern VRAM writes** at
`PC=$0C87` (see `native/research/M45_FOUR_COLUMN.md` and
`native/trace_timed.c`). PC-6 independently reconstructs the
preceding **M43 name-table upload** into VRAM
`$3900–$3EFF` (768 entries).

## What the composite viewer can substantiate

A native C11 validator imports **untracked**:
- `YSPC6N01` name-table package with 1,536 original M43 bytes
- `YSPC7P01` pattern package with a 16-byte header
  (start `$0000`, length `$3000`, CRC32) and 12,288
  original decoded M44 pattern bytes; total 12,304 bytes

The `ys_pc_patterns_preview` routine projects the 32×24
M43 name words through **only those 384 source-proven M44 tiles**.
For every word with tile index 0–383, it reads the corresponding
four source bitplanes to recover the exact 4-bit pixel indices,
applying the original name-word horizontal/vertical flip bits.
The source-only PC-7 run found that **all 768 name-table
references resolve** to indices 0–383 in the M44 pattern bank:
**768 matched; 0 missing**. The fallback path remains a required
error/diagnostic guard for future differently sourced resources.
For words referring to tile index 384–511, a separate
`255` **unresolved sentinel** is emitted. Tests enforce
that source pattern 0..383 never gets silently replaced by an
unrelated bank-3 tile, guessed image or placeholder.

The SDL2 F9 view renders recovered pixel **indices** as
artificial 16-level grayscale and unresolved references as
**magenta**. It reports matched/unresolved name-table cell
counts in the window title. These colors are *diagnostic*.
The original CRAM palette, source animation/sprites and
background palette selection are still unknown.

**Temporal limitation:** M43 and M44 are sequential verified
original initialization uploads. The existing M44 trace checks
the pattern bytes, but does not establish that all M43 name-table
words remained unchanged through all later VBlank ISR activity.
F9 is a controlled **cross-check of adjacent staged resources**,
NOT an independently observed simultaneously resident VDP frame,
complete title screen, or original gameplay scene.

**Spatial limitation:** PC-6's `$3900–$3EFF` word range is
the lower 24 rows of a conventional 32-wide Mode-4 name table.
The preceding `$3800–$38FF` four rows are absent from these
packages. F9 displays the recovered **24 contiguous rows only**,
re-indexed vertically starting at 0 for diagnostic inspection,
NOT as a claimed viewport origin, camera position or playable
map. No collision or scene/object-group correspondence is inferred.

## Files, native API and tests

- `native/tools/export_pc_patterns.py`: deterministic source-only
  four-bitplane decoder, original opcode check and package
  self-validation
- `native/pc_patterns.h/.c`: strict CRC/header/truncation/trailing
  byte validation; per-pixel bitplane reads and source-known masks
- `native/test_pc_patterns.c`: Mode-4 bitplane pixels, H/V flips,
  missing-pattern sentinel, full 768-cell composition, malformed
  asset rejection and an optional test of both source packages
- `native/game_sdl.c`: F9 read-only native SDL composite. F8
  original numeric name-table view and all other diagnostics remain
  separate from the placeholder game. F9 requires **both**
  `--nametable` and `--patterns`. Diagnostic modes disable
  controls on the hidden placeholder room.

## Run locally

```sh
python3 native/tools/export_pc_nametable.py --out /tmp/ys-pc-nt.bin
python3 native/tools/export_pc_patterns.py --out /tmp/ys-pc-patterns.bin
python3 native/tools/export_pc_patterns.py --verify /tmp/ys-pc-patterns.bin
cmake -S native -B build-native -DCMAKE_BUILD_TYPE=Debug
cmake --build build-native --parallel
ctest --test-dir build-native --output-on-failure
./build-native/ys-pc-patterns-tests \
  /tmp/ys-pc-patterns.bin /tmp/ys-pc-nt.bin
./build-native/ys-native-game \
  --nametable /tmp/ys-pc-nt.bin \
  --patterns /tmp/ys-pc-patterns.bin
```

The source package is not checked into Git; generate it locally.

## PC-8 follow-up

[PC-8](PC8_SIMULTANEOUS_VDP.md) tests an actual simultaneous
M44-source VDP checkpoint against these two separately
recovered resource packages, including the 32 CRAM colors and
16 VDP registers. **PC-7 by itself is only a resource composite.**

## Genuine game-content blockers

To call this an authentic *rendered original scene*, first verify
simultaneously resident **name-table + pattern VRAM + CRAM** at a
particular runtime checkpoint, including any interrupts and
pattern/map updates. To **play** a native Ys region, additionally
verify an actual game area, camera origin, player sprite, collision,
NPC AI and progression. PC-7 does not modify the placeholder
room, the original-ROM emulator, Draft PR's default branch, or
any Alpha/Beta/Final release gate.
