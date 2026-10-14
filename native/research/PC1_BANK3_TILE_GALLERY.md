# PC-1 — Source-verified bank-3 tile gallery

**Purpose:** Introduce actual `Ys: The Vanished Omens` tile *pixels* into
the native enhanced-PC renderer without implying we have established
their original colors, tilemap arrangement or gameplay context.

## Source and provenance

The source-only physical **bank 3** generator is
`Ys/tools/whole_bank03.py` (`full_bank()`). It rebuilds the
entire 16,384-byte bank without reading or copying a commercial ROM
at this step and checks SHA-256
`b9ade48d112c574b642f026fd770e78cb939bb717328e4c6a3fdc228cc7c2c15`
against `Ys/wholebank03/digests.json`.

This milestone exports exactly the **first 5,632 bytes** of that bank:
physical `$0C000–$0D5FF`, 176 complete 32-byte SMS Mode-4 tiles.

The two original blocks have independently recorded SHA-256 hashes
in `Ys/phase8/tile_metadata.json`:

- `$0C000–$0CFFF`: 128 tiles, 4,096 bytes,
  `ce7c073755a6382882ee518d16cf363e42354895f468e3eeac986b28c9469bea`.
- `$0D000–$0D5FF`: 48 tiles, 1,536 bytes,
  `527196d448c107535c8ab95cc71e0666acc0589c880c38af1bdc1b78bc98422e`.

Each tile has eight 8-pixel rows, with four bitplanes per row. The
index decoder reconstructs 4-bit pixel indices and independently
re-encodes them byte-for-byte before export. A PC asset package includes
magic/version `YSPC4T01`, tile count 176, two zero reserved bytes,
IEEE CRC-32 and exactly 5,632 data bytes. The PC loader rejects bad
headers, size, count and CRC.

**Visual limitation:** The 16×11 tile gallery shows the 16 pixel
indices as synthetic grayscale values `index*17`, not authentic SMS
palette colors. These 176 tile patterns are source-verified; their
runtime selection, intended tileset grouping, transparency and original
game placement have not been observed. A genuine game area/map should
not be synthesized by arbitrarily assigning these tiles.

## Build and view

The source conversion needs Python 3 and checked-in repository source;
**no Ys ROM is required**, and no derived binary is tracked:

```sh
python3 native/tools/export_pc_tiles.py --out /tmp/ys-pc-source-tiles.bin
python3 native/tools/export_pc_tiles.py --verify /tmp/ys-pc-source-tiles.bin
cmake -S native -B build-native -DCMAKE_BUILD_TYPE=Debug
cmake --build build-native --parallel
ctest --test-dir build-native --output-on-failure
./build-native/ys-native-game --tiles /tmp/ys-pc-source-tiles.bin
```

The tile gallery initially appears; **F2** toggles between the
authentic-source grayscale tile gallery and the PC-0 prototype room.
WASD/arrows, Enter/Space, optional GameController, and Esc continue
working in the prototype room. With no `--tiles` option, the gameplay
prototype works as before, including without an asset package.

CI runs the Python source-only exporter, re-verifies the created
package, compiles the strict C11 decoder/loader tests, starts SDL2
headlessly with the tile gallery and checks rejection of corrupted
packages. The SVG/SDL rectangles and game room are still placeholders.

## Remaining Alpha blockers

This phase **does not** implement a recovered Ys map, identify a
player/enemy sprite, import an original color palette, or demonstrate
real Yas/Adol game progression. The user-facing `ys-native-game`
remains an interactive architecture prototype, not an Alpha
version of the original game's content.

Next: link a runtime- or source-backed map index to specific graphics
tiles with independent source evidence, plus authentic palette/actor
identification, before replacing the placeholder room. Retain all
Alpha gates false pending real game progression and manual playtesting.
