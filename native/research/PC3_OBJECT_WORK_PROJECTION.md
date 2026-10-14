# PC-3 — Native projection of original object work fields

**Status:** Bounded native C11 source transformation. This is not a
gameplay/map reconstruction, not Z80 emulation, and not proof of screen
coordinates, object behavior, collision, or current location.

## New source-backed consumer relationships

Bank 0 source `Ys/phase5/code.lst` and
`Ys/src/wholebank00/bank00_complete.asm` contain the object
initialization loop `$1B3C-$1B9A`. The PC-2 bank-7 directory
at `$BA3B` supplies 22 groups, indexed by
`$C181 & $7F` and guarded by `< $16`.
Each group has up to 16 nonzero-first-byte, four-byte records.
A zero first byte marks the end of the current group.

The source initializes `IX=$C230`, advances by `$30` (48 bytes)
after each record, and writes the following **provable subset** of
each work slot, without interpreting its game meaning:

| Record byte or calculation | Source addresses | Work slot offsets |
| --- | --- | --- |
| `record[0]` | `$1B52-$1B5B` | `+0`, `+41` |
| `record[1]` | `$1B5C-$1B60` | `+32` |
| `value_a = record[2] × 8 + 8` | `$1B66-$1B7B` | LE 16-bit at `+6/+7`, `+43/+44` |
| `value_b = record[3] × 8` | `$1B7F-$1B90` | LE 16-bit at `+3/+4`, `+45/+46` |
| Advance to next 48-byte slot | `$1B91-$1B98` | Base `$C230 + 48×i` |

The listed `DD 75 d` and `DD 74 d` opcodes store the **ordinary L
and H register values** into `(IX+d)`, rather than the IX register
halves. This is the indexed-memory exception to usual DD-prefixed
H/L substitution, documented by
[Z80 opcode decoding](https://z80.info/decoding.htm)
and [Z88 developers' Z80 notes](https://cambridgez88.jira.com/wiki/spaces/DN/pages/9568467/The+Zilog+Z80+Undocumented+instructions).
Some repo-generated mnemonic listings call these source registers
`IXL/IXH`; the opcode bytes, indexed-memory rule, and the immediately
preceding HL arithmetic determine the actual values. PC-3 does not
modify or silently rewrite the original assembler listings.

These *are two 16-bit work values*, likely involved in object placement;
**their interpretation as world X/Y, sprite offsets, or gameplay
screen coordinates remains a hypothesis**. No authentic map
name-table, camera offset or collision layers are recovered here.

## Implementation

- `native/pc_objects.h/.c`: maps the exact 11 supported bytes within
  a 48-byte slot for up to 16 records, retains the original four raw
  record bytes and the two calculated work values, and uses a separate
  `known[48]` mask. All other work bytes are **unknown**, not zeros
  synthesized as if observed from the game.
- `native/tools/export_pc_records.py`: in addition to bank-7 source
  integrity, source-builds fixed physical bank 0 and checks exact
  original opcode bytes in the producer/consumer at
  `$1B3C-$1B60` and `$1B66-$1B98` before accepting the same
  1,000-byte PC-2 record package.
- `native/test_pc_objects.c`: checks exact 16-bit arithmetic,
  high-valued inputs (`255×8+8 = 2048`), duplicate work fields,
  offset masks, zero terminator refusal, empty group and capacity.
  An additional test using the **actual untracked source-derived**
  bank-7 package projects all **209 records** across 22 groups.
- `native/game_sdl.c`: **F4** switches between raw-source byte
  bars and a read-only diagnostic plot of those two *scaled work
  values*. The two numeric axes are normalized to the common
  `0–2048` work-value range; **this is not a spatial Ys map**.
  `F3` still switches to the placeholder room and `F2` displays
  PC-1's grayscale source tile gallery. The source plot is not
  connected to gameplay simulation, AI, collisions or drawing a
  reconstructed level.

The original initializer also calls `$1B9B`, performing additional
conditional object initialization with the second record byte
(`record[1]`) in A at the `CALL $1B9B` site. The first byte
(`record[0]`) controls the zero-terminator test and other stored fields. **Those writes are not modeled here**. A native object with
partially known work fields is not yet a valid in-world NPC/enemy
instance.

## Reproduce

From the project root, with SDL2 development headers installed:

```sh
python3 native/tools/export_pc_records.py --out /tmp/ys-pc-records.bin
python3 native/tools/export_pc_records.py --verify /tmp/ys-pc-records.bin
cmake -S native -B build-native -DCMAKE_BUILD_TYPE=Debug
cmake --build build-native --parallel
ctest --test-dir build-native --output-on-failure
./build-native/ys-pc-objects-tests /tmp/ys-pc-records.bin
./build-native/ys-native-game --records /tmp/ys-pc-records.bin
```

CI runs the above deterministic C11 checks as well as headless
SDL2 smoke tests for both PC-2 and the new PC-3 F4 diagnostic mode.

## Remaining gating work

Recover `$1B9B` object's conditional setup and actual map/screen
selection, tile/name-table placement, camera transform and palettes.
Validate the derived work values against an authentic scene or
reference emulator trace before treating them as PC game coordinates.
The existing `ys-native-game` room remains a **placeholder**.
The Development branch/Alpha gates remain unchanged.
