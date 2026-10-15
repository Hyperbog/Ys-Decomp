# Ys: The Vanished Omens — native PC modding profile

**Status:** PC-10 engineering profile; experimental in-memory scene API only.
This is a specialization of [the universal mod-forward methodology](../MOD_FORWARD_METHODOLOGY.md),
not an announcement of a public mod SDK, package loader, editor or authentic playable Ys area.

## Target and source of truth

- Target: Sega Master System *Ys: The Vanished Omens* (USA/Europe)
  as the historical gameplay/reference source; enhanced independent C11/SDL2
  PC runtime under `native/`.
- Verified original source-only cartridge SHA-256:
  `02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
  Source verification depends on the checked-in bank generators.
- Historical Z80, mapper, original SRAM, CRAM, VRAM, sprite
  diagnostics and source offsets remain **reference provenance** only.
  They are not the PC game's runtime, not a public mod namespace, and
  are not interpreted as automatically verified gameplay semantics.
- Native PC-0–PC-9 has a small interactive **placeholder** engine.
  It is not an authentic Ys opening room, original movement/AI or release Alpha.

## Actual extension points and status

| Subsystem | Currently supported | Not yet supported |
| --- | --- | --- |
| Scene data | **Implemented/tested (PC-10):** `YsPcSceneContent` C11 v1 in-memory model, validated 16×12 cells and two actor spawns | Authentic Ys map/scene, arbitrary sizes, serialized stage schema |
| Stable IDs | **Implemented/tested (PC-10):** namespaced symbolic IDs with strict validation; `prototype.scene.test_room`, `prototype.actor.player`, `prototype.actor.foe` | A public, frozen resource ID registry or modding API |
| Scene registration | **Implemented/tested (PC-10):** `ys_pc_catalog_apply`, explicit add/replace, sorted ID order, fail-closed conflicts and capacity | Loading mod archives, dependency graph, priorities, lockfile, filesystem discovery |
| Game runtime | **Implemented/tested (PC-10):** native PC engine copies one verified scene; original prototype defaults identical; scene drives walls, spawns, HP and move interval | Original Ys tile/actor art placement, real collision world, real NPC combat, progression |
| Source asset import | **Research-only (PC-1–9):** deterministic byte-level exporters with provenance and CRC, separate diagnostic views | Promoting unverified bank/VRAM numbers to canonical stage ID/tiles |
| Audio / video | Synthetic/research reference graphics and original VDP diagnostics | Native music/SFX buses, original scene graphics with verified palette and sprites |
| Menus | PC-0 title/restart and F-key diagnostic viewers | Menu/page registry, pause/actions/settings panel |
| Saves | **Unsupported** | Versioned game saves, content identity, migrations |
| Mods and editor | **Unsupported** | Filesystem mod resolver, data pack schema, editor import/round-trip |

**The prototype namespace is not the authentic game's `base.*` namespace.**
Do not assign final Ys NPC/map IDs based on candidate ROM addresses or
claim that symbolic prototype IDs already constitute an end-user compatibility contract.

## PC-10 canonical scene contract

- API: `native/pc_content.h`, `pc_content.c`, consumed by
  `pc_game.c` and `game_sdl.c`.
- C memory schema: `YS_PC_CONTENT_SCHEMA=1` (experimental, **not**
  an on-disk format); namespaced ASCII IDs use lowercase
  letters/digits/underscore/dash/dot, fit within 63 characters,
  and must be NUL-terminated and distinguish player/foe.
- One prototype 16×12 tile layer with WALL, FLOOR and GOAL cells.
  Require enclosing walls and one goal; player and foe start on
  distinct floor cells. Health 1–20, movement interval 1–60 ticks.
- `ys_pc_catalog_apply(catalog,scene,false)` registers an
  additional scene, rejecting duplicates. With `true`, replacement
  is explicit and rejects missing IDs; the catalog is sorted by
  symbolic ID so insertion order has no effect. Invalid operations
  do not mutate the catalog. Capacity is eight scenes.
- `ys_pc_game_reset_named_scene(game,catalog,scene_id)` first resolves
  a symbolic ID, rejecting missing/invalid references without changing
  game state. `ys_pc_game_reset_scene(game,scene)` validates before copying
  the scene into *owned game state*. The game does not hold pointers
  to an external catalog. Restart preserves the selected scene.
  The PC-0 `ys_pc_game_reset` and `ys_pc_game_tick` APIs still run
  the identical **placeholder** defaults when no replacement is supplied.
- This simple contract covers only scene-level replacement/addition
  **in application code**, not arbitrary entity additions or a
  user-authored filesystem/data mod.

## Distribution / security / compatibility

Original or generated commercial game ROM images, derived art/music,
private palette dumps and binary source captures are **not** committed
as mod packs. Local source checks and CI fixtures are independent.

No save-file, external resource package, JSON or API compatibility
version exists. `YS_PC_CONTENT_SCHEMA=1` labels in-memory data
only; it must not be treated as a stable versioned disk format.

The new tests verify default parity, rejected malformed entries,
deterministic sorted IDs, replacement/addition, scene-derived engine
state and restart behavior without any source ROM. All original
bounded Z80/VDP research regression checks remain separate.

## PC-11 source collision routing

[PC-11](research/PC11_BANK1_COLLISION_ROUTES.md) identifies
a conditional original bank-1 entry path that maps bank 4,
derives target bounds from original source descriptor records,
and calls the original collision predicate at three sites.
The validated native route enum and explicit byte-context
adapter are **internal research interfaces**, not scene-ID
collision geometry or an externally moddable actor system.
The canonical prototype room and its independent collision
rules remain unchanged.

## PC-12 original runtime observation boundary

[PC-12](research/PC12_RUNTIME_COLLISION_WATCH.md) adds a
bounded reference-Z80 tool to observe potential collision
caller runtime PCs and source mapper/IX/WRAM context.
It does **not** populate the canonical scene registry,
define authentic object/resource IDs, or grant support
for external mod packs, saves, editor or real gameplay.

## PC-13 experimental linked scenes

[PC-13](research/PC13_CAMPAIGN_VERTICAL_SLICE.md)
extends the native in-memory **prototype** scene contract
with a symbolic `next_scene_id` and adds deterministic,
validated campaign link traversal. All links and walkable
prototype encounter/goal positions are checked before play.
This is a **C11 internal prototype extension point**, not
an original Ys world map or an external serialized mod-pack
compatibility format. Official Alpha gates remain unpassed.

## PC-14 original sprite attribute producer

[PC-14](research/PC14_ORIGINAL_SPRITE_SAT.md) adds native
C11 source-only import of all **64 original bank-6 SAT
records** and deterministic Y/X/tile staging with a
192-case original Z80 output oracle. The record indices
remain **original source provenance**, not canonical
player/enemy IDs, nor a verified sprite-art or scene
resource in the modding interface. The F12 viewer is
diagnostic only; actual original sprite identities and
frame residency still require a live game-state trace.

## Next gates

1. Recover a verified authentic original Ys playable scene and
   its collision and actor relations; assign **new canonical IDs**
   only when the meanings are sourced.
2. Define a versioned, validated **serialized** canonical stage
   importer with round-trip tests before exposing external mod packs.
3. Implement deterministic mod set metadata, precedence, conflict/
   dependency rejection, cosmetic/gameplay isolation and lockfile
   **only when a real loader exists**.
4. Define save format/version and editor interfaces after the
   canonical native gameplay state is understood.

None of these gates, nor the Alpha release gates, are passed by PC-10.
