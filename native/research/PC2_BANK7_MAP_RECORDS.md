# PC-2 — Recovered bank-7 map-object tuples; geometry unresolved

## Evidence level

**Source-byte and boundary verified; map semantics NOT verified.**

The original Ys SMS fixed-bank source and bank-7 source builder establish a
22-entry pointer directory at CPU `$BA3B-$BA66`. Each pointer
indexes a compact group of 4-byte records at `$BA67-$BDBE`.
Source `Ys/wholebank07/source.json` reconstructs:
- **22 strictly ordered group pointers** (44 bytes).
- **209 four-byte tuple records** (836 bytes).
- **20 zero-byte group terminators** (20 bytes).
- **856 bytes** in the full group region, without gaps or overlaps.
- One legitimately **empty, terminator-only group** (group index 4).

Physical bank 7 is built without reading a game ROM by
`Ys/tools/whole_bank07.py:full_bank()` and checked against its
original digest in `Ys/wholebank07/digests.json`. The portable
PC-2 exporter independently checks that all source pointer bytes,
record bytes, and terminator bytes equal this assembled bank.

**A group is not proven to be a tilemap/screen/level.** Four tuple
fields have not been linked to tile IDs, map x/y coordinates, actor
IDs, collision bits, or selection under real gameplay. The gallery
therefore depicts 4 source BYTE VALUES per column, **not spatial
positions** or a reconstructed location.

## Additional 16-byte source transfer

M36 original-code execution established that bank 7 `$B9C3-$B9D2`
is copied to work RAM `$C170-$C17F` as part of video/palette-state
initialization. PC-2 includes those exact 16 source bytes as a
separate diagnostic lane at the bottom of its tuple viewer.

They are **not** a verified CRAM palette: source-side palette
transformation, eventual CRAM use, and colors remain unverified.
PC-1's 176 tiles remain displayed using synthetic grayscale, not
those 16 bytes.

## PC data format and checks

`native/tools/export_pc_records.py` emits one **untracked 1,000-byte**
derived file, from source-only bank 7. Layout:

```text
bytes  0-7:  YSPC7M01 (magic/version)
bytes  8-9:  22 (little-endian)
bytes 10-11: 209 (little-endian)
bytes 12-15: CRC-32 of the remaining 984 bytes
bytes 16-147: 22 records (u16 source_pc, u16 count, u8 terminator, u8 reserved)
bytes 148-983: 209 original 4-byte source records
bytes 984-999: 16 copied source bytes from bank 7 $B9C3
```

The strict C11 loader rejects mismatched size, magic, counts,
CRC, group pointer boundary, group length, invalid terminators,
unaccounted padding/overlap and bad end addresses. Native tests
cover normal decoding, an empty group, boundary checks and
mutated files even after updating CRC.

Use the package to **inspect, not drive gameplay state**:

```sh
python3 native/tools/export_pc_records.py --out /tmp/ys-pc-records.bin
python3 native/tools/export_pc_records.py --verify /tmp/ys-pc-records.bin
cmake -S native -B build-native
cmake --build build-native --parallel
ctest --test-dir build-native --output-on-failure
./build-native/ys-native-game --records /tmp/ys-pc-records.bin
```

Controls when viewing record diagnostics: **PageUp/PageDown**
to choose a group, **F3** to return to the placeholder room.
If the PC-1 tile package is also provided via `--tiles`, **F2**
switches to the separate grayscale tile gallery; **F3** accesses
record inspection. The prototype room does not interpret any
group as a traversable level. Records and graphics do not silently
change the prototype's collision or combat.

## What is still required for a genuine Ys world

1. Trace which code consumes the 22 group pointers and how each
   tuple is interpreted at runtime.
2. Trace map cells through actual name-table / VDP writes and
   match tile IDs to source graphics without inventing placement.
3. Trace actor sprite indexing, palettes and CRAM upload, ideally
   against gameplay-state evidence.
4. Convert evidence to native typed scene data with independent
   input/movement/collision playtests.

The current `ys-native-game` remains a standalone enhanced **engine
prototype** with a placeholder room. No authenticated Ys playable
area has been built and the five Alpha gates remain false.
