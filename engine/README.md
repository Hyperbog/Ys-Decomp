# Ys Expanded — native, mod-forward game engine

This directory owns new portable C11 engine systems and eventually canonical
content schemas, saves, display/audio interfaces and editor-facing data.
It must not require original cartridge offsets or embed commercial assets.
The recompiled original will serve as a **behavioral oracle**, not as the
permanent data model for added maps, quests, actors or mechanics.

## First implemented component: deterministic content binding registry

`content_registry.h/.c` provides a small, bounded prototype for resource
identity and conflict detection. All IDs and bindings are named, stable,
ASCII-lowercase dotted IDs; no ROM offsets or filesystem paths are accepted.
A content pack adds entries, or explicitly replaces a matching base entry;
multiple mods cannot silently override the same resource. Each successful
entry records the contributing pack's origin. Invalid/duplicate/conflicting
packs are rejected **atomically** without changing the registry.

This registry stores **symbolic bindings only**. It does not load content,
resolve filesystem assets, parse mod packages, implement dependency graphs,
run Ys mechanics, or offer a playable game. Limits (128 entries, 63 characters
per symbolic ID) are prototype constraints, not original cartridge limits.

Build and verify independently from decomp/recomp:

    cmake -S engine -B /tmp/ys-expanded-build -DCMAKE_BUILD_TYPE=Debug
    cmake --build /tmp/ys-expanded-build --parallel
    ctest --test-dir /tmp/ys-expanded-build --output-on-failure

The default base pack and provenance from the recovered original must be
validated before runtime import. Next steps are versioned external content
schemas, multi-mod dependency resolution, structured content import, and
an original-behavior gameplay vertical slice. No Alpha gates change here.
