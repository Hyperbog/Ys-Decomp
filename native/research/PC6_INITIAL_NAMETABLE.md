# PC-6 — Authentic initial VRAM name-table upload, without invented game scene

**Evidence status:** The original Ys SMS game **writes real, verified
source data to the VDP name-table region**. It is an initialization
checkpoint, not an observed first playable map or a complete graphical
frame. This port reconstructs the exact underlying word values in
native C11 without executing Z80 code or requiring a ROM file.

## Proven original source control flow

Three already verified source-ROM checkpoints establish the chain:

1. **M41:** Physical bank 5 source at CPU `$B61A`, through the original
   decompressor `$0C20`, consumes **518 encoded bytes** and emits
   **748 intermediate command bytes** to WRAM `$C600`.
   The compressed language has literal blocks and incremental runs.
2. **M42:** Original code `$0C67–$0C6F` uses the interleaved
   two-column decoder at `$0BEF–$0C1F`. Exactly 1,536 destination
   bytes are staged starting at WRAM `$D600`. Each column advances
   two bytes at a time and uses its own command terminator.
3. **M43:** Original `$0C72–$0C7B` selects `HL=$D600`,
   `DE=$7900` (VDP VRAM write command for **$3900**) and
   `BC=$0600`. Original helper `$06C1` executes **1,536 OUTI**
   instructions writing the staged bytes to **VRAM $3900–$3EFF**.

[Passing original-cartridge M43 trace](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38471475804)
verified byte-by-byte identity of the upload in the continuous
automatically timed original Z80 execution, including natural IRQs,
with **no host-injected VRAM, PC, registers, game state or interrupts**.

PC-6 independently reconstructs exactly those 1,536 bytes using
source-only physical bank-5 content and the two decoded resource
languages. It additionally verifies the original Z80 instruction
bytes at `$0C20–$0C3D`, `$0C55–$0C7D` and `$06C1–$06D3`
against the Phase-5 opcode listing and the independently
reconstructed source-only fixed bank 0.

## What the data means, and what it does not

The Master System mode-4 name-table entries are 16-bit words.
VRAM $3900–$3EFF contains exactly **768 entries**, arranged as
**32 columns × 24 rows**. On a normal 32-cell-wide VDP name table
the range begins after the first 128 entries (4 rows), at VRAM
$3900. Those first four rows **$3800–$38FF are omitted from the
PC-6 package**, and no current-state bytes for them are guessed.

The native decoder extracts each word's 9-bit tile-pattern index,
horizontal flip, vertical flip, palette-select and priority
flags. These are authentic decoded **name-table words**, but their
initialization state does not establish any of the following:

- Which exact pattern tiles are resident in VDP VRAM when an actual
  scene is displayed (M44 and subsequent routines can modify them)
- Authentic CRAM colors, camera location, scene composition,
  actual NPC placement, and collision
- Which current `$C119` scene or `$C181` bank-7 object group
  should be paired with these entries
- That the initialization data is a visible playable screen,
  a title graphic or the opening game's tilemap

Consequently **the placeholder PC room is not replaced**, and the
PC-6 view is diagnostic rather than claiming a faithful rendered
game level.

## Native artifact, verification and user control

`native/tools/export_pc_nametable.py` reconstructs physical
bank 5 from checked-in source, separately validates the original
source instruction identities from fixed bank 0, independently
decodes the two command layers and emits an **untracked 1,552-byte
file**:

```text
offset  size  field
0       8     ASCII YSPC6N01
8       2     LE VRAM base = $3900
10      2     LE byte count = $0600
12      4     IEEE CRC-32 of the next 1,536 bytes
16      1536  Exact original M43 VDP write payload
```

`native/pc_nametable.h/.c` exposes a strict native C11 file
validator and `ys_pc_nametable_cell` for indexed 32×24 reads.
Truncated files, trailing bytes, malformed metadata and incorrect
CRC are rejected. The original data's tile indices are preserved
without adding palette/sprite art.

`native/game_sdl.c` adds **`--nametable FILE`** and a
read-only **F8** gallery of the 32×24 name-table words. Its grayscale
comes **only from the numeric tile ID**, with diagnostic
annotations for palette/priority bits. This is **not a visual
reconstruction of the original tiles or original colors**.
F8 switches back; the existing F2/F3/F4/F5 inspection modes and
placeholder gameplay remain independent. Opening any gallery
stops player input to the hidden placeholder prototype.

### Reproduce

```sh
python3 native/tools/export_pc_nametable.py --out /tmp/ys-pc-nt.bin
python3 native/tools/export_pc_nametable.py --verify /tmp/ys-pc-nt.bin
cmake -S native -B build-native -DCMAKE_BUILD_TYPE=Debug
cmake --build build-native --parallel
ctest --test-dir build-native --output-on-failure
./build-native/ys-pc-nametable-tests /tmp/ys-pc-nt.bin
./build-native/ys-native-game --nametable /tmp/ys-pc-nt.bin
```

CI must pass strict C11 tests, source-only export/reverification,
the real derived-package input, native SDL2 headless viewer startup
and deliberate corrupt file rejection. The bank-5 bytes are
reconstructed for local inspection, not committed as a packaged
ROM or gameplay asset.

## Next bounded steps

Connect **proven original VRAM pattern uploads, tile residency
and CRAM palette state** to one specific name-table state,
preferably backed by a genuine source-ROM running checkpoint or
external emulator capture. Only after a *scene-selected* source
tilemap and collision data are independently established should
the PC room use authentic Ys environment content.

Release/Alpha gates remain false; Draft PR #3 is not a release.
