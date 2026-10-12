# Reference study: StarFoxSNESRecomp static recompilation strategy

Reviewed 2026-10-12 (read-only inspection of upstream default branches).

## Authoritative project sources

- Game project: https://github.com/mstan/StarFoxSNESRecomp (README.md; tools/regen.sh; recomp/bank03.cfg; src/starfox_rtl.c; docs/REFERENCE_SOURCES.md)
- Recompiler framework (moved from mstan): https://github.com/RetroPortingToolKit/snesrecomp (README.md)
- Disassembly used as reference for addresses and comments: https://github.com/SpyderTL/StarFoxDisassembly (pinned reference described in StarFoxSNESRecomp/docs/REFERENCE_SOURCES.md)
- Reference renderer and symbol source: https://github.com/kandowontu/starfox-enhanced (pinned submodule described in .gitmodules and docs)

## Mechanism documented by StarFoxSNESRecomp

1. Validate the exact user's own unheadered 1 MiB Star Fox USA v1.2 ROM by hash. Neither the ROM nor generated ROM-derived C is committed.
2. Run `tools/regen.sh` to build snesrecomp's native analyzer (Python reference backend optional), import annotations as non-promoting `symbol` entries in `recomp/bank*.cfg`, and invoke `snesrecomp/tools/v2_emit.py --cfg-roots --no-host-root-scan`. Code is written into ignored `src/gen/`.
3. The framework follows 65C816 control flow (including processor M/X register widths), emits statically recognized code as portable C, and retains interpreter fallback for unresolved/dynamically reached instructions. Game behavior still comes from original machine code rather than hand-rewritten algorithms.
4. Build native C with CMake, a pinned `snesrecomp` framework, `recomp-ui` launcher, game-specific integration, and a shared emulated SNES PPU/APU/DMA/cartridge/Super FX runtime.
5. Star Fox title glue owns the game scheduler, input, presentation, Super FX interaction, and save-state continuation. Low-level execution remains authoritative; narrowly scoped HLE optimizations can be bypassed.
6. The opt-in widescreen renderer and some mods are adapted from the *separate* Star Fox Enhanced decomp/native renderer. Widescreen is not an inherent result of static recompilation.

The Star Fox README expressly calls this a development-reference preview: title/attract, menus, route selection, training, and basic gameplay have had interactive tests. Longer routes, full rendering/effects parity, save-state behavior, and other platforms remain validation work. GitHub's manual CI compiles and tests ROM-free host code; it does NOT establish reproducible playable ROM-derived code, which users generate locally.

## Specific use of reference symbol data

The StarFox Enhanced reference exported 13,633 symbols; 7,947 are ROM names. The ingest tool adds them as non-promoting `symbol` entries, **not** function roots. The source explicitly warns that automatically treating all names as `func` declarations would accidentally compile tables, labels, and asset headers as code. For example, `recomp/bank03.cfg` explicitly declares `func LoadAudio b109 end:b269` and an optional HLE hook. This preserves the boundary between established code and merely annotated bytes.

## Applicability to SMS Ys

Our verified 16/16 physical ROM bank rebuild is an exact source-reconstruction milestone, **not** yet ahead-of-time recompilation to a native host executable. SNESRecomp targets 65C816 and SNES hardware; it cannot directly compile Ys's Z80 machine code or emulate the SMS Sega mapper, VDP, PSG, or optional FM audio.

Most useful transferable steps:

1. Establish a Z80 code/data/indirect-jump and bank-switch-aware control-flow graph, promoting only proven code entries to compilable roots; keep merely symbolic addresses as names.
2. Emit a portable C/native implementation for proven Z80 blocks, coupled to an authoritative SMS hardware layer (VDP, input, mapper, RAM, PSG/FM as applicable).
3. Preserve a small validated Z80 interpreter fallback for dynamically reached or unresolved code. Bounded execution audits are evidence, not already a general emulator.
4. Use an exact owned ROM identity at runtime without checking the commercial game ROM or ROM-derived generated output into the public repository.
5. Keep the 256-KiB source build/hash and existing source-only M13–M17 tests as independent regression gates; add differential state/VDP/audio traces for every converted block.
6. Leave separate native graphics enhancements until the authentic SMS behavior is proved, as Star Fox did with its opt-in renderer.

M17 project-specific note: our latest repository documents 50 Bank 13 icons and 3 extra tail transfer cases executed through a bounded Z80 emulator, with 579 tail bytes attributed to RLE graphics and 5,028 bytes still unclassified. This is an excellent seed for a Z80 CFG+interpreted/native hybrid but is NOT a complete gameplay recompiler.

**No evidence in the inspected StarFoxSNESRecomp source makes REA (Reverse Engineer Anything) a required part of this pipeline.** The project explicitly names snesrecomp, not REA, as its primary recompiler.
