# PC-10 — Canonical scene-content foundation for native Ys

## Why this milestone exists

Default branch `Ys` added the repository-wide
[mod-forward standard](../../MOD_FORWARD_METHODOLOGY.md).
The current enhanced PC-9 branch had a hardcoded `pc_game.c`
prototype map. Before implementing a real Ys area, this milestone
creates a small **replaceable, engine-owned data contract**, aligned
with the project's evidence-first and mod-forward requirements.
There is **no guessed original Ys geometry** in this milestone.

The base reference for this change is the PC-9 draft branch
`5b51e276eba428cd17a74979dcac7e1f0eb2890b`.
The verified commercial cartridge SHA is
`02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
No ROM, actual extracted textures or reference fixtures were altered.

## Changes and implemented contract

- `native/pc_content.h/.c` specifies **experimental C11 schema v1**:
  `YsPcSceneContent` with namespaced 63-character symbolic
  scene/player/foe IDs, exact 16×12 tile cells, actor spawn
  coordinates and HP, and a movement-tick interval.
- The original PC-0 **placeholder** map `# . G` moves from
  `pc_game.c` into a single content default function; it retains
  the original start coordinates (2,2), stationary foe (9,7),
  starting HP 5/3, eight-tick movement, room walls, one locked goal,
  bump combat and restart behavior.
- Engine exposes a symbolic-ID resolver (`ys_pc_game_reset_named_scene`)
  that selects a catalog entry before validating and copying the scene;
  missing IDs leave the current state intact.
- Engine now validates and copies `YsPcSceneContent` into
  `YsPcGame` at reset. `ys_pc_game_tick` and `game_sdl`
  read from this owned content snapshot, not from a hardcoded
  global map pointer. F2–F11 reference-data viewers remain independent.
- The experimental `YsPcContentCatalog` has capacity 8, supports
  deterministic lexicographic symbolic-ID registration, explicit
  add or replace, duplicate and missing-ID errors, size/version
  bounds, and no mutation on invalid updates.
- No untrusted file/archive loader was introduced. No stable mod
  pack, save format, resolver, editor or user-facing override CLI
  is implied. Original ROM bank addresses stay as separate
  provenance in the existing PC-1–PC-9 diagnostics.

## Validation gates

`native/test_pc_content.c` (independent C11/ROM-free fixture):
- byte-equal state after identical baseline prototype input
  sequences through the original and canonical reset APIs;
- symbolic ID validation, bounded tile chars, enclosing walls,
  one goal, safe spawn/HP/timing values and schema-version rejection;
- order-independent registration, conflict/missing/full behavior,
  nonmutating invalid updates and intentional scene replacement;
- alternative in-memory scene proving wall, movement, HP, restart
  and owned content copy semantics while default gameplay remains
  unchanged.

`native/test_pc_game.c` remains the historical PC-0 deterministic
baseline. Existing source-only graphics, Z80/mapper/collision and
SDL dummy-driver smoke checks remain in GitHub Actions.

## What PC-10 does NOT prove

It does not recover original Ys map data, authentic player graphics,
enemy movement, collision walkability, content serialization,
actual mods or editor workflows. Using `prototype.*` IDs does
**not** turn the original source bank indices into public mods.
No Alpha/Beta/Final release gate is promoted and the draft PR
remains unmerged.
