# PC-15 — Original bank-6 sprite selector formula and genuine runtime watch

## Evidence boundary

PC-14 recovered **all 64** original bank-6 count/delta/pair
sprite-attribute layouts and reproduced the Phase-19 original
Z80 producer/SAT output in independent native C11 across
192 synthetic origin/record combinations. Those cases were
**controlled tests**, not actual active gameplay sprite selections.

PC-15 establishes a concrete original source link from fixed
bank-0 WRAM fields to the bank-6 record **directory index**,
adds a native equivalent with fail-closed unknowns, and adds
a **passive original CPU/VDP/mapper event watch** after the last
verified M45 checkpoint. **It does not assign a protagonist,
enemy or world-area identity to any index.**

## Source-backed conditional selector producer

At fixed-bank Z80 source `$26B6–$26DA`, verified against
`Ys/phase6/code.lst` and independently reconstructed
physical bank0 bytes:

1. `$26B6: LD A,($C198); OR A; JR Z,$270C`.
   The selector construction is bypassed when `$C198=0`.
2. `$26BC: LD A,($C011); AND $40; JR NZ,$270C`.
   It is bypassed when bit 6 of `$C011` is set.
3. `$26C3: LD BC,($C210)` fetches little-endian
   `C=$C210` and `B=$C211`.
4. `$26C7–$26D0` computes
   `(((($C184)+C)&7)<<3)` through three `RLCA`
   instructions and saves it in E.
5. `$26D1–$26DA` computes
   `(($C182+B)&7) | E | $80`, then writes the
   resulting byte to **`$C199`**.

Therefore the original conditional source formula is:

```text
row = ($C184 + $C210) & 7
col = ($C182 + $C211) & 7
$C199 = $80 | (row << 3) | col    # values $80–$BF only
directory_index = ($C199 * 2 modulo 256) / 2  # 0–63
```

At `$26DD–$2704`, on the preceding conditional entry
path, the original source maps bank 7 and calls its
helper, then **`$26F5: LD ($FFFF),A` with A=6**
maps physical bank6 and **`$2704: CALL $9932`**
enters the original source producer.
Bank6 `$9932` reads `($C199)`, executes
`ADD A,A; LD L,A; LD H,$80`, fetches a
pointer from the `$8000–$807F` 64-entry directory,
then `$9944/$9955` reads the two
origin bytes `$C210/$C211`.

**Important separate path:** fixed-bank
`$275A: LD A,$FF; $275C: LD ($C199),A`
writes `$FF` on another control path. Were
`$FF` fed directly to the `$9932` doubled-byte
directory operation, it would point to slot **127**,
outside the verified 64 entries. There is no evidence
that this invalid state reaches the producer; do
**not** silently mask `$FF` to index 63.

These instructions establish **conditional source
control flow and field relationships**, not that
an actual playable Ys scene took the path.

## PC-15 native independent selector

`native/pc_sprite_selector.h/.c` implements the exact
8×8 bitfield expression and entry preconditions with
explicit input values from original WRAM addresses.
It returns the original raw `$C199` value or
fails without mutating output if the source gate
bypasses construction. The directory decoder
accepts **only `$80–$BF`** and yields 0–63,
rejecting zero, `$C0`, `$FF`, unknown indices
and missing arguments. This is an **internal research
API**, not a public mod record namespace.

`native/test_pc_sprite_selector.c` verifies
**4,096 original-source bitfield combinations**
plus every unique 0–63 target, unsigned wrap,
skip paths, invalid values and immutable outputs.
`native/tools/verify_pc15_sprite_source.py`
checks all source opcode sites through the
original independently rebuilt bank0/bank6
and the original Phase-6 instruction listing.

## PC-15 passive original runtime watch

The separate `native/pc_sprite_watch.h/.c` is a
**read-only** observer of exact source CPU-PC hits:

| Original PC | Observation type |
| --- | --- |
| `$26F3` | fixed-bank sprite setup entry |
| `$26F5` | fixed-bank bank6 mapper write (pre-execution) |
| `$2704` | fixed-bank call to bank6 `$9932` (pre-execution) |
| `$9932` | bank6 producer entry **only if mapped slot2==6** |
| `$0427` | fixed-bank SAT upload entry (not scene-dependent) |

An opt-in `ys-native-timed-rom source.sms
--pc15-sprite-watch watch.json` starts from the
previously verified M45 original cartridge `PC=$0C92`
with natural source CPU stepping, mapper, RAM,
interrupt and VDP states. It **never** forces a
gameplay PC, mapped bank, scene byte, controller,
IRQ, palette or sprite record.

For the first genuine observation of each PC,
`ys-pc15-original-sprite-watch-v1` JSON records:
physical mapper slots, raw mapper selector,
`$C199/$C210/$C211/$C100`, original
`$C028/$C02A` staging-pointer words, IX,
VDP registers 0/1/5/6, display-enable bit,
VRAM/CRAM write counters, CPU instruction/IRQ/
VBlank counters. The bounded continuation
stops at first mapped bank6 `$9932` entry, an
unsupported original opcode, 150,000 steps or
90 additional naturally generated VBlank events.

`native/test_pc_sprite_watch.c` validates mapper
qualification, original source events, immutable
first-hit measurements, raw WRAM/VDP values,
and JSON serialization without a source ROM.
`native/tools/verify_pc15_sprite_watch.py`
checks the structured report and **separately
prints OBSERVED versus BLOCKED**. If no actual
source `$9932` call occurs, the report must
not claim a gameplay record was identified.

### Reference CPU blocker reduction

PC-12's authentic continuation stopped at
bank2 `$8204`. Original source Phase-4 listing
confirms this opcode is **`D6 81: SUB $81`**
followed by `F8: RET M` at `$8206`.
The bounded reference `native/z80.c` adds
the missing `SUB n` operation (all Z80
S/Z/H/PV/N/C flags, 7 T-states), with
`native/test_z80.c` tests for negative/zero,
signed overflow, positive/negative conditional
return and timing. This is **reference execution
tooling**, not the native PC gameplay runtime.

## Verify

```sh
python3 native/tools/verify_pc15_sprite_source.py
cmake -S native -B build-native -DCMAKE_BUILD_TYPE=Debug
cmake --build build-native --parallel
ctest --test-dir build-native --output-on-failure
python3 Ys/tools/build_system_m10.py --check --out /tmp/ys-source.sms
./build-native/ys-native-timed-rom /tmp/ys-source.sms \
    --pc15-sprite-watch /tmp/ys-pc15-watch.json
python3 native/tools/verify_pc15_sprite_watch.py \
    /tmp/ys-pc15-watch.json
```

The original Phase-19 exact SAT data oracle remains
a separate PC-14 regression; no source original
ROM image, original raw artwork or generated
sprite package is committed.

## Authentic Ys Alpha status

**All five authentic Ys Alpha gates remain false.**
No verified original gameplay scene, actual
selected sprite index for a playable frame,
player versus NPC identity, display-enabled
sprite pixel-pattern/palette residency, world
collision/walkability or native original encounter
has been proven. PC-13's two-room native playable
campaign still uses synthetic content.

PC-15 adds source-verified **selector linkage
and a measurement tool**; it does not turn a
source pointer or synthetic SAT test into
a real Ys player scene. PR #3 remains draft.
