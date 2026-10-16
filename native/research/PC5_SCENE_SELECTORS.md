# PC-5 — Independent scene dispatchers and object-group selector

**Scope:** Preserve original Ys source *routing metadata* in native C11,
not decode a background map or choose the authentic opening scene.

## What the source actually proves

### Fixed-bank scene dispatcher (separate index `$C119`)

Original bank-0 source near `$2C1B` contains:
```
LD A,($C119)
LD HL,$2C24
JP $0008
```
The 9 original pointer words at `$2C24-$2C35` have destinations
`$2C36,$2D9D,$2F2A,$3014,$3194,$329C,$333B,$3415,$3519`.
The source-only exporter checks both the dispatcher instruction bytes
and all nine words against the independently reconstructed physical
bank 0. These are **dispatch target addresses**, not nine confirmed
playable maps or nine confirmed background tilesets.

### Bank-1 scene routines and separate `$C181` writer

Source-rebuilt physical bank 1 includes an eight-word subroutine
directory at `$4C03-$4C12` and original code at `$4C26-$4C30`
that can write `A` into `$C181`. One path at `$4C1C` supplies
`A=1` and jumps to the store at `$4C2B`. Other paths can
supply different values. Opcode and source table bytes are verified
against the reconstructed physical bank 1; **their execution and
timing in an authentic gameplay state have not been verified.**

The PC-2/PC-3 original bank-0 object initializer independently
reads `$C181`, masks it with `$7F` and accepts indices `0–21`
for the 22 bank-7 object-record groups. The high bit is retained
separately; out-of-range values do **not** select arbitrary groups.

These are **two independent state variables**:
`$C119` for the nine-entry fixed-bank dispatcher and
`$C181` for the 22-group object selector. No source-backed
one-to-one relationship, initial playable-scene value, or
scene-to-tilemap data link is claimed.

### Background screen data is still blocked

Earlier M37–M38 source-timed traces establish initial VDP VRAM
clears and a name-table-region clear, not a populated map. The
Phase-13 bank-7 graphics engine and tile streams establish actual
VDP transfer *structure* but not a validated mapping from this
scene index or the object-group index to background name-table
tile IDs, palette bits, camera origin, or collision. No tile data
is newly placed into the PC-0 gameplay room in PC-5.

## New native interfaces

- `native/tools/export_pc_scenes.py` verifies both source-only
  physical banks 0 and 1 and original dispatcher/store opcode
  sequences, then emits a **50-byte untracked source package**:
  `YSPC5S01`, LE `9` + LE `8`, CRC32 and the original
  9 + 8 little-endian pointer words
- `native/pc_scenes.h/.c`: strict file loader, independent
  `ys_pc_scene_select` API that accepts **explicit caller
  supplied** `$C119` and `$C181` values, returns a fixed-bank
  handler and an optional valid object-group index, and keeps
  the `$C181` high bit. It does not fetch a hidden state or
  infer a live game scene.
- `native/test_pc_scenes.c`: verified pointer values,
  no scene index `>=9`, group boundary `21/22`, masking and
  high-bit preservation, invalid size/magic/CRC/metadata and
  semantically bad pointer rejection; accepts an actual
  source-derived package for a second independent check.
- `native/game_sdl.c`: optional `--scenes FILE` opens a
  **read-only pointer index visualization** (F5).
  F6 cycles the nine fixed-bank entries; F7 cycles the eight
  bank-1 entries. The bars encode pointer values, **not map
  geometry**. F2/F3/F4 reference views remain independent.
  Gallery mode never drives movement, collision or combat.

## Run without original ROM

```sh
python3 native/tools/export_pc_scenes.py --out /tmp/ys-pc-scenes.bin
python3 native/tools/export_pc_scenes.py --verify /tmp/ys-pc-scenes.bin
cmake -S native -B build-native -DCMAKE_BUILD_TYPE=Debug
cmake --build build-native --parallel
ctest --test-dir build-native --output-on-failure
./build-native/ys-pc-scenes-tests /tmp/ys-pc-scenes.bin
./build-native/ys-native-game --scenes /tmp/ys-pc-scenes.bin
```

All existing PC-0 to PC-4 source asset options remain separate.
The game window does not load original Ys map assets or original
CRAM palette colors.

## Remaining blockers and next bounded investigation

Recover a **source-to-VDP background name-table writer with tile-ID
data and an actual runtime-selected scene/index**, then validate
its tile placement and palette selection before importing an
authentic PC gameplay location. If runtime-state evidence
remains absent, label the scene linkage blocked instead of using
an arbitrary group and calling it an Ys area.

This checkpoint does not meet any Alpha release gate, does not
import a commercial ROM, and does not touch the separate M46
original-Z80 diagnostic work.
