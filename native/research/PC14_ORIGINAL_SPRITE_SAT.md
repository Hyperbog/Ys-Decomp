# PC-14 — Original bank-6 indexed sprite SAT records (not a player identity)

## Why this is the next original-content building block

The native PC-13 campaign can already drive a two-room placeholder
vertical slice, but the original game's **active scene, player sprite
identity, sprite graphics residency, collision geometry and
gameplay progression are still unknown**.

Earlier original source research independently established an
SMS **sprite-attribute-table (SAT) producer**:

- Physical bank 6 CPU `$8000–$807F`: **64 two-byte pointers**.
- CPU `$8080–$9931`: **6,322** contiguous count-prefixed source
  records. Each record is exactly `1 + 3×count` bytes,
  structured as a count, a count-length Y-delta group, and
  count pairs of X-delta plus literal tile-index bytes.
  All original source counts are between 27 and 38.
- Original bank-6 `$9932` producer uses `$C199` to select a
  record, `$C210/$C211` as Y/X accumulator origins, and
  writes the Y and X/tile SAT buffers to WRAM
  `$DD00/$DD40`.
- Fixed-bank `$26F3` explicitly maps physical bank 6,
  configures the staging pointers, calls `$9932`, then
  puts `$D0` at the end of the Y stream.
  Original fixed-bank `$0427` transfers **64 Y bytes**
  to VRAM `$3F00` and **128 X/tile bytes** to
  VRAM `$3F80`, exactly 192 bytes.
- The source project's original Z80 *bounded test oracle*
  at `Ys/phase19/execution_report.json` records
  **192 executions** (64 records × three synthetic
  origin pairs `(0,0)`, `(17,29)`, `(240,250)`),
  including 192 separate 192-byte SAT output SHA-256
  digests and an aggregate hash.

These are **verified source-code producer and bounded
synthetic execution behaviors**, not witnessed positions
during actual original gameplay. The record indexed by
`$C199` is **not** known to represent the protagonist
or a particular active game scene.

## PC-14 source-only export

`native/tools/export_pc_sprite_sat.py` rebuilds the
entire original 16-KiB physical bank 6 from checked-in
source via `Ys/tools/whole_bank06.py`, never consulting
the commercial ROM. The exporter checks:

1. All 64 distinct directory pointers, length/count,
   exact `$8080–$9931` non-overlapping record partition.
2. Source-bank SHA and the independent Phase-11B
   per-record hashes / source payload ledger.
3. Exact original Z80 source SAT output hashes for
   all 192 record/origin combinations from Phase 19,
   including the aggregate 36,864-byte digest.

The optional local **6,466-byte derived package** is:

```text
0–7      YSPC14S1 (8-byte magic/version)
8–9      uint16 LE number of source records = 64
10–11    uint16 LE data length = 6,450
12–15    uint32 LE CRC32 of directory + source payload
16–143   64 little-endian original CPU record pointers
144–6465 6,322 original count/delta/pair record bytes
```

No package file, ROM, screenshot, graphics or sprite
art binary is checked into Git.

## Independent native C11 transform

`native/pc_sprite_sat.h/.c` exposes a strictly validated
loader and `ys_pc_sprite_stage`, which:

- refuses wrong header/metadata/CRC, truncation, trailing
  bytes, duplicate/overlapping/out-of-bounds pointers,
  incomplete byte partition and missing/oversized records;
- takes an explicit *synthetic* pair of 8-bit Y/X
  origin values rather than guessing source player state;
- accumulates Y deltas into 64 Y-buffer bytes, leaving
  a `$D0` terminator; accumulates X deltas while copying
  the second byte of each pair as an uninterpreted
  SAT tile index into 128 X/tile-buffer bytes;
- preserves 8-bit wraparound and zero-initialized
  X/tile padding, and leaves output untouched for
  invalid requests.

The separate `ys-pc-sprite-sat-dump` replays **all
192 original-Z80 test input combinations** using this
C11 source decoder. CI compares its **complete
36,864-byte binary output SHA-256** to the independent
Phase-19 original-Z80 report. This is a byte-level
cross-implementation check, not a simulated display frame.

`native/test_pc_sprite_sat.c` additionally constructs
a completely synthetic, structurally valid 64-record
package and tests signed wrapping, independent reset,
SAT termination, bad metadata/pointers/CRC and 64-entry
source bounds.

## F12 native source viewer

`ys-native-game --sprite-records /tmp/ys-pc14-sprites.bin`
loads the strict source package and displays a **read-only
F12** SAT Y/X/tile-index marker inspector. PageUp and
PageDown browse all 64 original directory indices.
The marker positions are **diagnostic** and generated
from the explicit synthetic origin `(0,0)`.
Marker colors are artificial and merely distinguish
numeric indices; no sprite pattern/color pixels,
original player identity, map or onscreen game-scene
sprite residency is implied.

The F12 view is independent from the PC-13 prototype
campaign and all F2–F11 diagnostics. Without the
`--sprite-records` flag the existing native game remains
unchanged.

## Reproduction

```sh
python3 native/tools/export_pc_sprite_sat.py --out /tmp/ys-pc14-sprites.bin
python3 native/tools/export_pc_sprite_sat.py --verify /tmp/ys-pc14-sprites.bin

cmake -S native -B build-native -DCMAKE_BUILD_TYPE=Debug
cmake --build build-native --parallel
ctest --test-dir build-native --output-on-failure
./build-native/ys-pc-sprite-sat-tests /tmp/ys-pc14-sprites.bin
./build-native/ys-pc-sprite-sat-dump /tmp/ys-pc14-sprites.bin /tmp/ys-pc14-sat.bin

python3 -c 'import hashlib,json; p="/tmp/ys-pc14-sat.bin"; ref=json.load(open("Ys/phase19/execution_report.json"))["concat_sat_sha256"]; assert hashlib.sha256(open(p,"rb").read()).hexdigest()==ref'

./build-native/ys-native-game --sprite-records /tmp/ys-pc14-sprites.bin
```

## Remaining actual Ys Alpha blockers

- No observed original gameplay call of `$9932` with
  actual bank6 mapper state / real `$C199/$C210/$C211`.
- No player versus NPC sprite-record identity.
- No source-confirmed active sprite pattern VRAM,
  sprite palette, display-enabled game frame or
  mapping from sprite records to canonical scene IDs.
- No original Ys map geometry, collision/walkability,
  enemy behavior, or progression implemented natively.
- No external mod-loader or editor support.

Consequently **all five original-game Alpha gates
remain false**. This milestone recovers a reusable
source-backed sprite-position **producer** but does not
yet create an authentic Ys playable location.

PR #3 remains **draft, unmerged**.
