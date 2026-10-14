# Enhanced Ys PC port — native gameplay track

**Direction:** Build a standalone, maintainable, enhanced PC version of
*Ys: The Vanished Omens*. The original Sega Master System game is source
material for understanding maps, progression, assets and mechanics, **not**
a hardware-accuracy or instruction-execution requirement for the PC game.
Z80, VDP, timing, ROM reconstruction and SMS/GG recompiler diagnostics
remain available independently for investigation and comparison.

## PC-0: native playable-system prototype (not an Alpha)

This branch adds a **ROM-free, independent C11 gameplay core** and a native
SDL2 front end named `ys-native-game`:

- 60 Hz fixed-tick updates independent of render cadence
- Resizable native window, keyboard (arrows/WASD, Enter/Space, Esc) and
  optional SDL2 GameController buttons
- Placeholder 16 × 12 room, impassable walls and a locked room exit
- One stationary placeholder foe; deterministic bump interaction
- Health, defeat count, completion/restart states and status in window title
- Separate headless deterministic tests; dummy-SDL window smoke test in CI

**Content disclaimer:** The room layout, obstacle pattern, foe, protagonist
rectangle, graphic palette and combat numbers are **development
placeholders**, not extracted Ys maps, sprite art or verified mechanics.
This is an interactive architecture proof, not the actual opening
game, a recovered scene, complete game or an Alpha build.
Audio and save/load are not implemented. No commercial ROM or assets are
shipped or loaded. The five Alpha evidence gates stay false.

## PC-1 source graphics milestone

A new [bank-3 graphics research and runtime gallery](research/PC1_BANK3_TILE_GALLERY.md)
uses **176 original Mode-4 tiles** exported from the previously
source-verified physical ROM bank 3. The SDL2 game can display their
16×11 grayscale-index preview via `--tiles FILE`, switching between
gallery and placeholder gameplay with **F2**. The original palette,
tilemap arrangement and intended sprite usage are **not** established.
This does not yet turn the placeholder room into an authentic Ys map.

## PC-2 recovered map-object metadata

The [PC-2 bank-7 object-record ledger](research/PC2_BANK7_MAP_RECORDS.md)
adds 22 source-backed group pointers, 209 four-byte object records,
and 20 zero terminators. A fixed-bank selector at `$1B3C-$1B60`
and its source operand bytes are independently verified. The PC
renderer accepts an optional `--records FILE` and shows a **read-only
numeric field inspection view** (F3; PageUp/PageDown to change group).
It is not yet a decoded spatial tilemap, and the existing placeholder
gameplay is unchanged. The 16 bank-7 video/palette initialization
bytes at `$B9C3` are included as source bytes **without claiming
they are actual SMS CRAM colors**.

## PC-3 source object work-field projection

The [PC-3 source object work-field projection](research/PC3_OBJECT_WORK_PROJECTION.md)
now reconstructs the original bank-0 object initializer's
**16-slot, 48-byte-per-object work layout** for all 209 verified
bank-7 records. It conservatively fills only 11 explicitly supported
work bytes and computes two `8×`-scaled 16-bit values for each object;
unverified work bytes remain marked unknown. The diagnostic **F4**
view plots those two numeric fields, **not a recovered Ys map**.
No character movement, collision or scene geometry is inferred.

## PC-4 verified conditional object initialization

[PC-4 object parameter initialization](research/PC4_OBJECT_TYPE_INITIALIZER.md)
reconstructs both branches of original bank-0 `$1B9B` as native
object-data transforms: 36 standard entries receive fixed defaults,
and 173 table-indexed entries use one of 35 ten-byte parameter
records at original source `$1C05-$1D62`. The source-only exporter
creates a local, validated `--object-types FILE` package for
`ys-native-game --records FILE`. The native object projection
tracks exactly which work bytes are known, leaving other bytes
unknown. **This does not implement object AI or a playable game map.**

## Build and run

Install a C11 compiler, CMake 3.16+, and SDL2 development headers and
libraries. For example, Debian/Ubuntu:

```sh
sudo apt-get install cmake build-essential libsdl2-dev
cmake -S native -B build-native -DCMAKE_BUILD_TYPE=Debug
cmake --build build-native --parallel
ctest --test-dir build-native --output-on-failure
./build-native/ys-native-game
```

On Windows, configure with a compatible SDL2 development package, DLL
and CMake SDL2 target. If SDL2 is not discoverable, CMake continues
building the ROM-independent gameplay library and its tests, but
**does not** build `ys-native-game`. On macOS, provide SDL2 via the
local package manager or CMake package path.

To test the graphics executable without a physical desktop:

```sh
SDL_VIDEODRIVER=dummy SDL_RENDER_DRIVER=software \
    ./build-native/ys-native-game --smoke
```

The smoke flag runs and renders 12 simulation ticks, then exits;
it does not replace manual keyboard/controller playtesting.

## Next independently reviewed components

1. Replace placeholder tile map, actor graphics and transitions with
   ROM-derived, separately validated Ys map/sprite/resource converters.
2. Introduce modular world/actor definitions, camera, movement/collision
   and story-state interfaces, then test an authentic game region.
3. Implement enhanced keyboard/controller accessibility, renderer options,
   sound/music playback and save functionality.
4. Demonstrate actual Ys title → authentic interactive world → first
   reproducible combat/progression loop before considering Alpha.

**Release meaning:** A playable placeholder test room is not evidence
for the real-game `boot_to_title`, `interactive_gameplay` or other
Alpha criteria in `native/release/gates.json`. Fidelity to every SMS
instruction, pixel or cycle is not an enhanced-port release requirement.
