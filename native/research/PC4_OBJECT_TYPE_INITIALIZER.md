# PC-4 — Source-backed conditional object parameter initialization

**Scope:** Import a verified portion of the original `Ys` object
initializer into standalone native C11 data transformations. This is
**not** hardware emulation, object AI, world collision, or a playable Ys
scene. The original ROM is not used at runtime or by the exporter.

## Fixed-bank original source evidence

At `$1B5D–$1B64`, the bank-0 object-record reader copies
`record[1]` to work byte `IX+$20` and calls `$1B9B` with that
same source byte in `A`. The source routine `$1B9B–$1C04`
contains 55 decoded Z80 instructions totaling 106 bytes; the new
Python exporter verifies these original opcode bytes against the
independent `Ys/phase5/code.lst` and source-only rebuilt bank 0.

The routine executes `ADD A,A`, followed by `JR C,$1BB6`:
- **Bit 7 clear:** applies fixed defaults at work offsets
  `+1=$20`, `+33=$04`, `+18=$01`, `+13=$0A`, `+14=$0A`.
- **Bit 7 set:** `A` now contains twice `record[1]&$7F`;
  multiplication by five indexes ten-byte records starting at
  `$1C05`. Table bytes are written in the following exact order:

| Source table byte | Work-slot byte |
| --- | --- |
| 0 | +33 |
| 1 | +34 and +42 |
| 2–7 | +35 through +40 |
| 8 | +23 |
| 9 | +24 |

The high-bit branch then writes `+18=$01`, `+1=$20`,
`+14=$01`. It does **not** write `+13`; that offset remains
unknown in this branch unless another identified routine writes it.

The source `$1C05–$1D62` comprises exactly **35 ten-byte
entries (350 bytes)**. The 209 source-backed bank-7 object records
contain **36 standard** and **173 indexed** initializers; observed
high-bit indices are exactly `0–34` (all 35 entries used).
The native projection rejects any high-bit index beyond 34,
rather than reading outside the source table.

## Native implementation

- `native/tools/export_pc_object_types.py` reconstructs fixed
  bank 0 without ROM input, validates the 55 instructions and source
  table, then generates an untracked 366-byte package:
  `YSPC4O01`, LE `count=35`, LE `stride=10`, CRC32 of the
  350-byte original table, then exactly those 350 bytes
- `native/pc_object_types.h/.c`: strict bounds, identity, count,
  stride and CRC checks; rejects extra/truncated/corrupted files
- `native/pc_objects.c`:
  `ys_pc_project_objects_typed` extends the existing native
  record projection with the two proven conditional branches and
  maintains the per-byte **known mask**. The PC-3 entry point
  `ys_pc_project_objects` remains unchanged for callers lacking
  the verified source table.
- `native/test_pc_object_types.c`: both branches, exact write
  offsets, untouched fields, CRC/size/metadata rejection, type
  boundary indices 34 vs 35, and legacy compatibility
- `native/test_pc_objects.c`: optional source-derived bank-7
  record package **plus** source-derived bank-0 type table; verifies
  all 209 records and cross-table indices
- `native/game_sdl.c`: optional `--object-types FILE` for
  the read-only F4 diagnostic object-work projection.
  Marker coloration distinguishes table-indexed and default
  branches; axes are normalized diagnostic values **not** world
  coordinates, and this does not change gameplay physics.

No derived `*.bin` game graphics, commercial ROM, or complete
source object tables are checked in as new binaries.

## Reproduce

```sh
python3 native/tools/export_pc_records.py --out /tmp/ys-pc-records.bin
python3 native/tools/export_pc_object_types.py --out /tmp/ys-pc-types.bin
python3 native/tools/export_pc_object_types.py --verify /tmp/ys-pc-types.bin
cmake -S native -B build-native -DCMAKE_BUILD_TYPE=Debug
cmake --build build-native --parallel
ctest --test-dir build-native --output-on-failure
./build-native/ys-pc-objects-tests /tmp/ys-pc-records.bin /tmp/ys-pc-types.bin
./build-native/ys-native-game --records /tmp/ys-pc-records.bin \
    --object-types /tmp/ys-pc-types.bin
```

In the SDL2 native viewer, **F4** switches from source byte
inspection to a normalized plot of source-derived object fields;
**PageUp/PageDown** change group, and **F3** returns to the
placeholder game room.

## Unresolved and release boundary

The actual value of source WRAM `$C181` for an opening playable
scene has **not** been validated in gameplay, so the active group
and full scene are unknown. Table values are raw game data and
not yet given invented enemy/NPC class names. Camera transforms,
map/name-table tile placement, collision flags, sprite tile identity,
true SMS palettes, encounter behavior and story progression remain
open. The native executable is an enhanced-PC **prototype**, not a
verified Ys Alpha. No release gates have been modified.

The next useful task is to trace the active scene/group index and
a background-name-table consumer, using real original-source
evidence rather than drawing an arbitrary map from the records.
