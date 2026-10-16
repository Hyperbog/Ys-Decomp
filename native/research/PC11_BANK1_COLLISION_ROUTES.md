# PC-11 — Bank-1 collision callers mapped to bank-4 descriptors (bounded)

## Milestone outcome and status

PC-9 validated the original bank-4 `$807C–$80A1` predicate and
31 source records as an isolated native C11 object-boundary operation.
PC-11 recovers **its upstream bank-1 source routing**, showing
an explicit physical-bank-4 mapper write *on one bounded routine
entry path*, as well as the input bounds construction feeding
the three existing collision-call sites.

This is a source-backed **object hit-test subsystem**, not a verified
playable Ys world, tilemap walkability, source player identity, or a
particular gameplay invocation. There is no claimed scene/actor
identity in this milestone.

## Original instruction-level source evidence

The physical bank-1 byte-complete source reconstructs with original
SHA-256 `e91fa8fb9109dc13555967e208cb4650972d1965c2c9088be8d748ea177b4505`.
Original instruction bytes are independently cross-checked against
`Ys/phase7/code.lst` by `native/tools/verify_pc_collision_routes.py`.

The bounded source path starting at bank-1 CPU `$476C`:

1. `$476C`: `LD A,($C100)`; `$4770`: `RET NZ` (early exit).
2. `$4771: LD A,$04`; **`$4773: LD ($FFFF),A`** directly
   selects **physical bank 4 into CPU $8000–$BFFF** using the
   original Sega mapper. This is an exact source instruction,
   not an assumed game-state value.
3. `$4783–$479C`: `($C20D)` selects a four-byte record
   from **bank-4 $8000** (multiply index by four). Original
   `($C211)` and `($C210)` provide the byte origins used
   to form register pairs **B/C** and **D/E** by sequential,
   wrapping 8-bit additions of record offset and extent.
   The zero-doubled selector returns early.
4. Two calls to **`$807C`**, at `$47C2` and `$486C`,
   use `A=(IX+14)` as the tested object's descriptor index.
   Their object-work pointer advances by `$30` over up to 16 slots.
5. `$4780: JP C,$489F` is an alternate source branch.
   `$48A5–$48BE` uses **`($C20E)`**, with the same
   `($C211)`/`($C210)` offsets, to construct B/C/D/E.
   The subsequent **`$48DF: CALL $807C`** selects the tested
   object's index from `(IX+13)`.
6. This bounded instruction range has only the one direct
   `($FFFF)` mapper write at `$4773`, and exactly those
   three `CALL $807C` instructions. Its data/call addresses
   are jointly source-verified with the PC-9 bank-4 predicate.

**Confidence boundary:** for control paths entered at **`$476C`**
that pass the `$C100` early-return, the direct mapper write
precedes all three calls. It does **not** prove an actual frame
enters `$476C`, that no unknown other entry reaches the
call sites, or what bank and object-work bytes occur at a live
Ys gameplay moment. No original player coordinate or world
collision semantics are inferred.

## Native independent equivalent

- `native/pc_collision_routes.h/.c` adds three **native symbolic
  call-site enums**. Its input supplies explicit bank-2 mapper
  slot index, the original IX descriptor index fields and
  the original caller bounds. It selects `IX+14` for the
  first two calls, `IX+13` for the alternate, and executes
  the independently tested PC-9 `ys_pc_collision_eval`.
- `ys_pc_collision_route_frame` accepts **explicit**
  `C20D,C20E,C211,C210,IX+13,+14,+16,+17` byte values,
  independently reconstructs the original source target
  B/C/E/D register bounds using consecutive 8-bit additions,
  then invokes the native predicate. It reports a distinct
  `INACTIVE` status when the original zero selector would
  return, and **rejects indices outside 0–30** rather than
  reading unverified bank-4 instructions as collision boxes.
- The route adapter requires physical **bank 4** in the
  supplied slot. Wrong mapper value, unknown route, malformed
  index and missing input fail closed without mutating the
  result. Neither route is silently wired into the
  PC-10 placeholder map.
- `native/tools/verify_pc_collision_routes.py` source-only
  rebuilds bank1 + bank4, audits opcode sequence/branch/calls
  against the independent Phase-7 listing, asserts exactly
  one direct bank-4 slot selection in the bounded range,
  and checks the previously verified PC-9 descriptor/predicate.
- `native/test_pc_collision_routes.c` validates all three
  original call-site paths against **3,968** source-derived
  PC-9 probe cases each (**11,904 comparisons**) plus
  720 original-source target-bound preparations, equality/
  overflow, zero-selector, bank-state and invalid-index guards.
  The original Z80 opcode oracle remains a separate CI gate.

## Reproduce (no commercial ROM required)

```sh
python3 native/tools/verify_pc_collision_routes.py
python3 native/tools/export_pc_collision.py --out /tmp/ys-collision.bin
cmake -S native -B build-native -DCMAKE_BUILD_TYPE=Debug
cmake --build build-native --parallel
ctest --test-dir build-native --output-on-failure
./build-native/ys-pc-collision-routes-tests /tmp/ys-collision.bin
```

PC-10's experimental canonical `prototype.scene.test_room`
is unchanged. The source collision records are not inserted
as walls, player/foe positions, or a scene-specific collision
layer, and the namespaced native route enums are not a public
mod pack/API compatibility guarantee.

## Remaining PC-game integration gates

To replace the placeholder room, independently observe **an
active source gameplay frame** with bank1 routine entry,
mapper slot, `$C20D/$C20E`, `$C210/$C211`,
`IX=$C230+0x30*n`, player/actor source identification and
the real map name table/collision or physics semantics. Only
then attach source-proven meaning to canonical scene IDs and
reconstructed collision resources. **No Alpha release gate
changes at PC-11.**
