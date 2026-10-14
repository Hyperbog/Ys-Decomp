# PC-12 — Bounded original-source gameplay collision watch

## The question addressed

PC-11 proved a **conditional original-source** bank-1 entry at
`$476C` that maps bank 4 at `$4773` and can call the verified
bank-4 collision routine from `$47C2`, `$486C` or `$48DF`.
That did **not** prove any authentic game-state execution of the
entry path, or that a specific IX object is the Ys player.

PC-12 introduces a **passive runtime observation experiment**
starting at the last independently verified bounded original
cartridge checkpoint, **M45 PC=$0C92**. It does not force any
unobserved instructions, gameplay states or map values.

## How the opt-in experiment works

`ys-native-timed-rom locally-built-original.sms --pc12-watch out.json`

- Rebuilds the original SMS cartridge using existing source-only
  tools when run in CI. No commercial ROM/generator output is
  committed. Before the new observation, the existing M25–M45
  checks execute the original CPU, bus/mapper, VDP/CRAM,
  PSG/FM port observer and automatically timed NTSC VBlank IRQs.
- Starts at the **already live** `$0C92` CPU and uses
  `ys_sms_runtime_step_auto` **without resetting, forcing PC,
  synthesizing VBlank, changing mapped banks, writing RAM,
  altering IX, sending artificial game inputs or loading a
  claimed gameplay room**.
- Bounded to at most **150,000 instruction/refresh steps** and
  **90 additional naturally timed VBlank events**. Stops early
  on unsupported instruction/bus/port execution.
- Observes original CPU PC **before** execution of source
  `$476C`, `$4773`, `$47C2`, `$486C`, `$48DF`;
  *only* treats them as original bank-1 instructions if
  **physical bank 1 is actually mapped to CPU slot 1**.
- For each first observed event, copies the real mapper
  selector and effective bank, PC, IX, WRAM `$C100`,
  `$C119`, `$C181`, `$C20D/E`, `$C210/211`,
  and four `(IX+d)` bytes (13/14/16/17).
  It also records observed CPU instruction-step, IRQ, and
  VBlank counters. These are **original runtime raw bytes**,
  not interpreted world coordinates/actors.
- Stops at the **first** observed original mapped bank-1
  collision call *before executing it*, if one occurs.
  Thus the report **cannot claim the predicate was executed**
  or a game area was entered based solely on a PC match.
- Emits versioned **JSON diagnostic metadata** only
  (`ys-pc12-source-watch-v1`), no ROM bytes/art/palette
  dump or scene content. All five first-hit objects have
  `seen`, `count` and optional raw register/mapper fields.
  A separate Python validator checks event qualification,
  counters and bounded termination.

**Blocked status is not a failure of the research test:** if the
native opcode subset halts on an unsupported instruction, or the
search budget expires without a matching call, the report
states `unsupported`, `budget`, or `vblank_limit`.
It reports **zero** original collision calls. This must
not be relabeled as a successful gameplay collision trace.
CI verifies the observation report's internal consistency
in either case, not a fabricated scene transition.

## Files and tests

- `native/pc_source_watch.h/.c`: passive mapper-qualified
  observer and strictly bounded JSON serializer.
- `native/test_pc_source_watch.c`: ROM-free synthetic
  fixture verifies original-PC address qualification,
  effective bank-1 filtering, preservation of the first
  real value, WRAM/IX copying, event-count output and
  JSON serialization without manipulating the CPU.
- `native/trace_timed.c`: optional `--pc12-watch`;
  existing `--frame`, `--vdp-at-m44` and normal M45
  checkpoint behavior unchanged.
- `native/tools/verify_pc12_watch.py`: checks
  schema, event list, mapper qualification and
  observed-vs-blocked result semantics.
- Source-regression, PC-0–PC-11 C11 and SDL2
  diagnostics remain in CI unchanged.

## Reproduce

```sh
cmake -S native -B build-native -DCMAKE_BUILD_TYPE=Debug
cmake --build build-native --parallel
ctest --test-dir build-native --output-on-failure
python3 Ys/tools/build_system_m10.py --check --out /tmp/ys-source.sms
./build-native/ys-native-timed-rom /tmp/ys-source.sms \
  --pc12-watch /tmp/ys-pc12-watch.json
python3 native/tools/verify_pc12_watch.py /tmp/ys-pc12-watch.json
```

The default trace setup initializes controller input to its
ordinary **unpressed** condition. This is not a human-authored
button sequence or a confirmed path from the title to a
live gameplay encounter. A blocked source execution is a
starting point for tracing required original controls and
unimplemented Z80 instructions, not license to fake them.

## Release and implementation boundary

The native PC content registry still contains only the
verified **placeholder** room and optional synthetic C
scenes. PC-12 introduces no collision link into its
playable map, no source player or NPC identity, no
serialized mod files, and no promotion of Alpha gates.
The feature PR stays draft and unmerged. A full
authentic gameplay location requires an *observed*
display-enabled/palette-populated area, active scene
selection, player/actor source identity, world map/
collision semantics and progression, none of which
can be inferred merely from this diagnostic watch.
