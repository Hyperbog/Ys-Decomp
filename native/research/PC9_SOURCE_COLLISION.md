# PC-9 — Original bank-4 collision predicate, NOT an original playable area

## Evidence and boundaries

The repository already has source-byte and execution evidence for one
particular original Ys object-boundary subsystem:

- Physical bank 4 (mapper slot $8000–$BFFF) contains **31 four-byte
  descriptors** at original CPU **$8000–$807B**.
  Each descriptor consists of unsigned source fields
  **Y offset, Y extent, X offset, X extent**.
- Original **38-byte Z80 routine $807C–$80A1** indexes these records
  using input A multiplied by four. It reads IX+17 (Y origin),
  IX+16 (X origin), and incoming C/B/E/D register bounds, returning
  its predicate result in the CPU **carry flag**.
- Source-only bank-1 instructions at **$47C2, $486C, $48DF** call
  CPU $807C after loading the candidate index from respectively
  **(IX+14), (IX+14), (IX+13)**. The caller tests carry.
  **Actual mapping of physical bank 4 at these calls was not
  established in a live game-state trace.** These are *candidate*
  cross-bank links; not proven gameplay encounters.
- The previous source bank-4 bounded execution oracle
  (`Ys/tools/bank04_collision_trace.py`) executed original
  Z80 opcode bytes for **3,968 synthetic cases**
  (31 descriptors × 16 origin seeds × 8 boundary variations):
  **3,033 carry-positive, 935 carry-negative**, checked against a
  separate direct arithmetic reference. The outcome ledger's
  source report SHA-256 is
  `4290475a0305428d1fe857ba5b3bdafa2ba787fc63af15cf8d9d6a520a28d977`.

The original bank-4 502 candidate 32-byte groups beyond $80A2
remain **unresolved patterned bytes**, not confirmed tiles
or world-collision grid content. PC-9 does not use them.

## What native C11 now does

`native/tools/export_pc_collision.py` reconstructs physical banks
1 and 4 from checked-in source and asserts their original
byte-for-byte source digests, collision routine's full 38-byte
opcode identity and the three candidate caller instruction
prefixes and destinations. It also checks the repository's
previous original-Z80 collision execution report. It creates
one untracked local **140-byte** diagnostic package, not a
shipped commercial ROM or original game map:

```text
offset  length   contents
0         8      ASCII YSPC9C01
8         2      little-endian descriptor count 31
10        2      little-endian stride 4
12        4      CRC32 of the following 124 source descriptor bytes
16      124      31 original Y-offset/Y-extent/X-offset/X-extent records
```

`native/pc_collision.h/.c` has a strict package loader and
`ys_pc_collision_eval` with explicit original register inputs,
object origin bytes and descriptor index 0–30. It calculates
Z80 unsigned **8-bit overflow/carry and boundary equality exactly**:

1. Source Y offset + IX+17 must overflow 255, or return no carry.
2. If wrapped Y equals input C, pass this Y check; otherwise Y
   must be below C, and Y + extent must avoid overflow and meet B.
3. Source X offset + IX+16 must overflow 255, or return no carry.
4. If wrapped X equals E, return carry. Otherwise X must be below
   E, and X + extent must avoid overflow and meet D.

The native API's boolean return reports **valid input/data**;
the separate output boolean reports the original predicate carry.
This avoids silently conflating invalid indexes with ordinary
missed collisions.

`native/test_pc_collision.c` verifies load/truncation/header/count/
stride/CRC rejection and distinct equal/overflow/boundary routes.
When passed the source-derived package it reproduces the previous
original-Z80 oracle's entire 3,968-case corpus, expecting precisely
3,033 positive and 935 negative results.

The CI run **also directly re-executes the original 3,968 Z80
instruction cases** against the source-rebuilt cartridge via
`bank04_collision_trace.py --check`, and validates the bank1→bank4
source ledger via `bank04_crossbank_ledger.py --check`.
No native host fabricated a playable map or character.

## Native diagnostic view (separate from the game)

`ys-native-game --collision path/to/ys-collision.bin` opens a
**read-only F11 collision predicate case view**. PageUp/PageDown
cycle 31 original descriptors. Each of the 128 cells in its
16×8 matrix is a deterministic seed/variant predicate input
from the bounded original opcode-test corpus. Green shows
carry; gray shows no carry. The four source descriptor byte
values are separately displayed as bars.

The matrix axes are **synthetic test indices, NOT Ys area
coordinates**, and the colors are **diagnostic**, not original
game art. Source data can be inspected alongside F2–F10
without changing the placeholder room or its simplified
movement/combat. Hidden-room input remains disabled during
the view. No original player sprite, AI, collision-map
walkability or room geometry was inferred.

### Source-only reproduction

```sh
python3 native/tools/export_pc_collision.py --out /tmp/ys-collision.bin
python3 native/tools/export_pc_collision.py --verify /tmp/ys-collision.bin
cmake -S native -B build-native -DCMAKE_BUILD_TYPE=Debug
cmake --build build-native --parallel
ctest --test-dir build-native --output-on-failure
./build-native/ys-pc-collision-tests /tmp/ys-collision.bin
./build-native/ys-native-game --collision /tmp/ys-collision.bin
```

To verify the original instruction oracle as well:

```sh
python3 Ys/tools/build_system_m10.py --check --out /tmp/ys-source.sms
python3 Ys/tools/bank04_collision_trace.py /tmp/ys-source.sms --check
python3 Ys/tools/bank04_crossbank_ledger.py --check
```

## Unresolved original Ys gameplay

The essential missing evidence is how a verified **active** gameplay
scene selects background map tiles, player graphics, collision
geometry, and source actor IX coordinates. The three bank-1
CALLs are not a substitute for a real mapper/game-state trace,
and an object hitbox predicate does **not** establish a
walkable world tilemap. PC-9 is a verified native collision
building block, not an authentic playable Ys location and not
Alpha-ready. Draft PR #3 remains unmerged, and release
gates must remain false until actual gameplay is recovered.
