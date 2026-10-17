# Decompilation track — preserved historical reference

**Canonical source tree: [`../Ys/`](../Ys/)**. The legacy path is intentionally
retained: moving its thousands of source/build references would invalidate
existing relative paths and tests. This is a track boundary, **not yet an
independent Git repository or a renamed source tree**.

Owns original Ys ROM identity (`Ys/manifest.json`), complete 16-bank
source reconstruction, disassembly, provenance, verification oracles, and
source-derived classification reports. The original ROM is not committed.

The baseline is the stable `Ys` branch's M45 source-only 262,144-byte cartridge:
SHA-256 `02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
This value is a historical original-byte identity, **not a gameplay certificate**.

New work in this track belongs in `Ys/` and its existing test workflows.
Do not put AOT-generated C, native engine rules, player-made maps, or mod
packages in this track. `Ys/recomp/` is a **legacy Phase-1 configuration and
documentation path**, not the destination for future recompilation code.

Existing unmerged PC-series research remains in its own draft branches;
this project-direction branch does not rewrite, cherry-pick, or merge it.
