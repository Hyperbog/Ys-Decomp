# PC-13 — Native campaign vertical-slice rehearsal (prototype, NOT Ys Alpha)

**Scope:** This is a deliberately source-free, **two-room prototype**
demonstrating an actual native PC game path from title to movement,
enemy defeat, door exit, another room, persistent HP, final completion
and full restart. The geometry, actors, movement cadence, combat,
palette and encounter placement are **not** original Ys content.
No scene is labeled `base.*` or assigned an original ROM address.

## Motivation and original-source boundary

The source-verified PC-6–PC-8 M43/M44 768 name-table entries and
384 patterns are real but correspond to a VDP initialization state
whose screen output was **disabled** with CRAM all zero. PC-9/PC-11
verified object-hitbox code and static call paths, but PC-12's
runtime watch stopped at bank-2 `$8204` sound dispatch with
**zero** actual collision calls observed. None of these proves
a traversable active original Ys map, player art or enemy AI.

Rather than invent a stage, PC-13 targets the **Alpha-critical
native campaign interface** so that independently verified original
content can later replace the prototype data without replacing the
whole game shell.

## Implemented native C11 changes

- `YsPcSceneContent` (experimental in-memory schema v1) gains
  an optional **symbolic `next_scene_id`**. Empty means terminal
  completion. Populated links must be valid namespaced ASCII
  scene IDs, different from the scene's own ID.
- `ys_pc_content_route_ok` performs a deterministic 4-neighbor
  BFS over a scene's floor/goal layout from the player starting
  position. It requires **both the foe and goal to be reachable**.
  The foe cell can be traversed after provisional combat succeeds.
  This prevents a "completable" prototype from containing
  isolated exits or inaccessible enemies. **Not original Ys
  tile-walkability.**
- `YsPcCampaign` contains an **owned copy** of a validated,
  ID-sorted `YsPcContentCatalog`, an owned `YsPcGame`,
  a namespaced entry-scene ID and a completed-scenes counter.
  Initialization resolves every link, rejects unsorted/invalid
  catalogs, dangling IDs, cycles and inaccessible encounters;
  failures do **not** mutate the destination campaign.
- `ys_pc_campaign_tick` delegates the actual movement/combat
  to the tested PC-0/PC-10 `ys_pc_game_tick` function.
  On defeating the foe and reaching the unlocked exit, it
  transitions to the linked scene directly in **PLAY** mode,
  preserving accumulated defeats and remaining player HP
  (capped by the next room's initial allowance).
  A terminal room reaches **CLEAR**. After CLEAR or DEAD,
  START resets to the campaign's original entry scene.
- `ys_pc_campaign_prototype_catalog` builds exactly two
  **ROM-free test rooms**: the historical PC-0 room and a
  slightly rearranged second room. No source ROM, exported
  game assets, CRAM colors, scene indices or bank selectors
  are involved.
- `ys-native-game --prototype-campaign` enables the
  opt-in multi-room flow with the same SDL2 window,
  60 Hz loop and keyboard/controller inputs. Window
  title labels the mode "**TWO-ROOM PROTOTYPE (NOT Ys)**"
  and shows scene progress and HP/defeats. Without this
  flag, **the historical one-room PC-0 behavior is unchanged**.
  Existing F2–F11 source-resource diagnostics still work
  independently and never drive the room geometry.
- The prototype demo is compiled from C11 literal data,
  **not** a serialized mod loader, stable external SDK,
  editor or authentic Ys scene.

## Verified complete gameplay replay

`native/test_pc_campaign.c` performs a deterministic
button-input equivalent of a real two-room run:

1. START from title; route from the initial player cell to
   the first foe; repeat movement/bump interactions until
   the foe is defeated.
2. Navigate to the now-unlocked exit; verify **automatic
   transition to room 2**, remaining HP, persistent
   defeat count, new foe and new movement interval.
3. Defeat the second room's foe, reach its final exit,
   and assert completed status. START then resets to
   room 1 with starting HP and no defeats.
4. Test a one-room catalog for **backward-compatible
   terminal CLEAR**.
5. Reject missing IDs, self-links, multi-room cycles,
   unsorted catalogs, unreachable goal and invalid
   replacement without corrupting an existing game.

This game-path test does not use synthetic internal Z80
registers or a forced PC. It runs exclusively through
native C11 game buttons and state transitions. CI also
launches SDL2 with `--prototype-campaign --smoke`
under the dummy video driver.

## Reproduce

```sh
cmake -S native -B build-native -DCMAKE_BUILD_TYPE=Debug
cmake --build build-native --parallel
ctest --test-dir build-native --output-on-failure

# Single original PC-0 placeholder room
./build-native/ys-native-game

# Opt-in two-room prototype, NOT authentic Ys:
./build-native/ys-native-game --prototype-campaign

# Deterministic end-to-end native gameplay rehearsal:
./build-native/ys-pc-campaign-tests
```

In the prototype window, press Enter to start; use WASD
or arrow keys to move and bump into each foe, then reach
the door. The next scene begins automatically when its
predecessor's exit is unlocked. Enter restarts after
completion or defeat.

## Alpha gate accounting

**No existing Alpha gate is promoted in this change.**
`native/release/gates.json` remains unchanged, with
`boot_to_title`, `automatic_frames`, `video_renderer`,
`live_controls` and `interactive_gameplay` still
`passed=false` for **authentic Ys**. A playable
prototype loop is valuable engineering evidence, but
not release-grade original-game gameplay evidence.

The next blocking research goal is to recover one
**actual original game area**, including a mapping from
verified scene selection to source graphics/CRAM,
player/avatar position, world collision/walkability and
a reproducible original encounter. Only once this data
is proven should it be assigned canonical `base.*`
IDs and substituted into the scene registry.

No original ROM, copyrighted asset payload or binary
reference capture is committed. PR #3 remains draft
and unmerged.
