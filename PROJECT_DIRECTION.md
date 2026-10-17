# Ys Expanded — separated development tracks

**Decision:** Preserve original *Ys: The Vanished Omens* behavior as a testable
baseline while building a native, data-driven engine designed for expanded
worlds, quests, enemies, visual/audio upgrades and modding.

This is a **single Git repository with logically isolated tracks** on the new
`feature/ys-expanded-foundation` branch, not two independent remotes or Git
histories. Separate future repositories can be extracted once the recomp ABI
and dependency contract are proven. No existing commit history is rewritten.

- **Decomp (`Ys/` + `decomp/README.md`)** owns original-bank sources, disassembly,
  binary verification and authentic execution evidence. Preserve existing
  paths and frozen oracles; the stable `Ys` branch remains unchanged.
- **Recomp (`recomp/`)** owns *new* generated-C integration, native execution
  bridge, parity traces and tests. `Ys/recomp` is a documented legacy
  compatibility path; no new codegen output is placed there.
- **Expanded engine (`engine/`)** owns new C11 simulation, canonical content
  contracts, mod resolution, save formats, renderer, audio and eventual tools.
- **Existing `native/`** remains the original Z80/hardware reference and
  diagnostic tools until an independently tested extraction is appropriate.

These are separate build/test ownership areas, not claimed independent Git
repositories. No original ROM, generated C, or protected asset blobs are
committed. The new C11 content registry is a validated engine foundation,
not playable Ys and not a working AOT runner.

## Milestone gates

1. **F0 — isolation and extensibility contract:** separate directories,
   ignored local recomp products, a buildable C11 registry and its tests.
2. **R1 — actual compiled recompilation:** original-ROM identity, external
   recompiler provenance, generated-C compilation/link, fail-closed ABI,
   and original-vs-recomp differential execution.
3. **G1 — authentic vertical slice:** at least one source-confirmed interactive
   area, graphics, input and audio; regression comparisons against the
   original reference, not guessed gameplay.
4. **E1 — expansion:** stable external content schemas, controlled overrides,
   mod dependency resolution, source-content import and editor reuse.
5. **Release:** staged Alpha/Beta/Final gates from `native/release/gates.json`;
   mark only independently demonstrated abilities as passed.

The unmerged original PC-44 and PC-45 draft research branches remain
untouched for later selective integration. Preserve original evidence;
never alter a golden to make native code appear equivalent.
