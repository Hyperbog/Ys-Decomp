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

## PC-5 independently verified source scene selectors

[PC-5 native scene routing](research/PC5_SCENE_SELECTORS.md)
preserves the original fixed-bank nine-entry `$C119` dispatch
table and the eight-entry bank-1 scene routine directory, including
source code that can write `$C181`, the independently verified
22-group object-record selector. The package `--scenes FILE`
adds an F5/F6/F7 **read-only pointer inspector**, not a
rendered location or a scene-to-object mapping. The actual
background name table, loaded palette, actor names, and authentic
opening scene are still unknown; the gameplay room is unchanged.

## PC-6 authentic initial name-table words (not a game map)

[PC-6 original VRAM name-table reconstruction](research/PC6_INITIAL_NAMETABLE.md)
adds a source-only bank-5 → intermediate WRAM → staged WRAM
decoder for the **1,536 authentic bytes** uploaded by original
Z80 helper `$06C1` to VRAM `$3900–$3EFF` during initialization.
The native `--nametable FILE` and F8 diagnostic view inspect
**768 name-table entries (32×24)** with tile indexes/attribute
bits, **not** actual original tile graphics or CRAM colors.
The top four name-table rows, later display-time tile residency
and active scene remain unverified. The placeholder gameplay
room is untouched.

## PC-7 source-backed graphics composition

[PC-7 pattern VRAM and name-table diagnostic preview](research/PC7_PATTERN_NAME_PREVIEW.md)
reconstructs the original M44 four-plane upload into **12,288
pattern bytes / 384 tiles**, and combines those with the earlier
M43 **768 name-table cells**. All 768 source name-table references
are within the 384 verified tiles. `--patterns FILE` together
with `--nametable FILE` adds an **F9 pixel-index composite**
with correct horizontal/vertical flips. Grayscale indices are
*not* original CRAM colors. The M43/M44 uploads are consecutive
original setup stages but their simultaneously resident display
state has **not** been verified. No collision, true scene or
authentic native Ys gameplay is claimed.

## PC-8 simultaneous original VDP state at M44

[PC-8 bounded source-execution snapshot](research/PC8_SIMULTANEOUS_VDP.md)
exports complete **simultaneous** VRAM (16 KiB), CRAM (32 bytes)
and VDP registers (16 bytes) from the **actual source-executed**
M44 `PC=$0C87` checkpoint. Native C11 compares its pattern
VRAM `$0000–$2FFF` and name-table bytes `$3900–$3EFF`
against the independent PC-6/PC-7 source exports, failing closed
on any mismatch. A new optional `--vdp-checkpoint FILE` and
**F10** diagnostic view renders captured palette/register state
using the existing SMS video research renderer. It remains
outside the native PC game loop and does **not** establish a
playable Ys scene, true camera/collision or original-game Alpha.

## PC-9 source-backed object collision predicate

[PC-9 collision source/semantics ledger](research/PC9_SOURCE_COLLISION.md)
introduces the original **31 bank-4 collision descriptors** and a
C11 equivalent of the original **$807C–$80A1 Z80 carry-returning
object-boundary predicate**. It uses the real source raw bytes and
tested 8-bit overflow/equality semantics. The three bank-1
candidate callers are statically verified, but their mapper state
in live gameplay remains unknown.

The native diagnostic `--collision FILE` uses **F11** to browse
the 31 descriptors and a 16×8 grid of the original synthetic
predicate-test cases. This is **not a recovered Ys area map**,
player-world coordinates, or replacement for the prototype's
placeholder collision. Real NPC identification, tile collision,
scene selection and gameplay progression still need proof.

## PC-10 experimental mod-forward content seam

[PC-10 canonical scene foundation](research/PC10_CANONICAL_CONTENT.md)
introduces an **experimental C11, in-memory** versioned scene
format with stable `prototype.*` IDs, strict validation and a
deterministic add/replace catalog with ID-based scene activation. The unchanged **placeholder**
PC-0 room, spawns and eight-tick movement are now supplied through
that content interface. Invalid scene registration/replacement
fails without mutating the catalog or runtime game state.

The [Ys-specific modding profile](YS_MODDING_PROFILE.md) records
**implemented vs proposed** support. There is no serialized
mod format, mod loader, editor, original playable Ys scene
or original-game parity claim in PC-10. Source bank addresses
remain private importer/provenance details rather than public IDs.

## PC-11 original bank-1 collision route and mapper evidence

[PC-11 source collision-call path](research/PC11_BANK1_COLLISION_ROUTES.md)
identifies the original **`$4773: LD ($FFFF),A` with `A=4`**
on the bank-1 `$476C` entry path, the source table at bank-4
`$8000`, and **three `CALL $807C` sites** using original
`IX+14`, `IX+14` and `IX+13`. A new native call-route
adapter independently constructs the source B/C/D/E byte bounds
from explicit WRAM context, then calls the verified PC-9
predicate. The adapter fails closed on wrong mapper or unverified
record indices.

**This is a conditional source control-flow result, not an actual
playable-area execution trace.** There is still no proven live
player/world geometry, authentic area, or scene-to-collision
relationship; PC-10's experimental placeholder room is unchanged.

## PC-12 bounded original-source runtime observation

[PC-12 collision-call source watch](research/PC12_RUNTIME_COLLISION_WATCH.md)
adds an **opt-in, nonmutating** original CPU/mapper/IX
observation after the independently verified M45 `$0C92`
checkpoint. It checks five original bank-1 PCs only when
physical bank 1 is actually mapped, and records real raw
WRAM/IX/mapper inputs if reached. Explicit bounded stop
reasons include unsupported instruction, step/VBlank
limit or an observed original call. **A blocked run is not
proof of any playable gameplay state.** The PC-10
placeholder remains untouched.

## PC-13 prototype campaign vertical-slice rehearsal (NOT authentic Ys)

[PC-13 end-to-end native campaign rehearsal](research/PC13_CAMPAIGN_VERTICAL_SLICE.md)
connects canonical `prototype.*` scene IDs to an actual
**two-room, source-free playable campaign**. A deterministic
input-driven test reaches an enemy in each room, defeats it,
crosses an unlocked door, retains HP/defeats between rooms,
completes the final room and restarts. Initialization rejects
missing/cyclic scene links and unreachable foes or exits.

To try it in SDL2: `./build-native/ys-native-game --prototype-campaign`.
The default command still opens the unchanged PC-0
one-room placeholder. This is **Alpha-path infrastructure,
NOT authentic Ys content or an Alpha promotion**; no
original scene/tiles, actor AI or gameplay transition is
claimed. The five Alpha gates stay false.

## PC-14 authentic original sprite SAT source (no player identity)

[PC-14 bank-6 sprite SAT reconstruction](research/PC14_ORIGINAL_SPRITE_SAT.md)
adds **64 original indexed sprite records** and the **source-verified
$9932 to $DD00/$DD40 to $3F00/$3F80** attribute-table producer
to native C11. A strict source-only exporter validates all
192 original-Z80 SAT outputs (three synthetic coordinate origins
per record); CI independently compares the complete 36,864-byte
C11 corpus against the frozen original-instruction SHA-256.

`ys-native-game --sprite-records FILE` opens an **F12**
read-only numeric sprite-placement inspector with PageUp/PageDown.
It uses synthetic origins, **not** actual original Ys player/NPC
art, sprite palettes or verified scene positions. The prototype
campaign and all five real-game Alpha gates remain unchanged.

## PC-15 original sprite selector and runtime event qualification

[PC-15 selector/source-run report](research/PC15_SPRITE_SELECTOR_WATCH.md)
links original fixed-bank `$26DA` **`$C199`** assignments
to a verified 8×8 conditional `$80–$BF` 64-record index
and original bank-6 `$9932` producer. The separate
`$275C` `$FF` assignment is rejected as an unsupported
directory index rather than silently masked.

`native/pc_sprite_selector.c` implements the conditional
source byte equation, tested over 4,096 combinations.
`ys-native-timed-rom --pc15-sprite-watch` passively
observes the original mapped bank6 call and raw selector/
origin/VDP state if actually reached from M45. A blocked
source trace **cannot** identify the player or an
authentic Ys area. Prototype gameplay and Alpha gates
are unchanged.

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
