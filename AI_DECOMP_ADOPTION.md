# Review and adoption decisions: AI-assisted game decompilation research

Based on the supplied document **Game Decompilation Workflows and Standards for AI Integration** (2026-10-11 review). This assessment distinguishes the document's recommendations from independent verification and actual new implementation. It is applicable beyond Ys to SMS, NES/6502, and PC/C/C++ game reconstruction.

## Main findings / decisions

| Paper recommendation | Decision | Rationale / implemented status |
|---|---|---|
| Binary-exact full-build gate; enforce partition boundaries | **ADOPT, implemented** | Portable `shared_decomp/workflow.py audit` validates exhaustive, disjoint partitions, accounting and optionally SHA-256 for both entire image and its parts. This checks manifest consistency and ROM identity; real source-only build remains a separate must-pass gate. |
| Context-rich AI prompts (immediate callers, symbols, known examples) | **ADOPT, initial implementation** | Portable `context` reads bank-qualified symbol and static-reference ledgers; excludes ambiguous bank-dependent references. This is not yet a true CFG/SSA or similarity search. Add compiler-conditioned types/analogues later. |
| Protected targets + fail-fast AI loops | **ADOPT, implemented** | Local SHA-256-protected guard with reproducible attempt ledger; stops after **2** non-improving retries by default (this project's existing convention), rather than paper's 3. Matching score must come from independent evaluator. |
| CFG, basic blocks, IR/SSA, def-use chains | **ADOPT, planned high priority** | Crucial for Z80 flag-based branches and 6502 zero-page control flow and for C/PE recovery, but *not* implemented by the small context extractor; prioritize complete mapper-aware subsystem graph and verified instruction semantics first. |
| Declarative binary splitting (`splat`) | **ADAPT** | Manifest approach applicable to all file formats. `splat` upstream currently supports N64/PS1/PS2/PSP, not SMS/NES Z80/6502; use existing platform-specific extraction tools, do not promise direct compatibility. |
| `objdiff` and `decomp-permuter` | **CONDITIONAL** | Appropriate for supported compiled-language MIPS/PPC/ARM/x86 workflows, particularly later compiler tuning. They are not drop-in Z80/6502 matching tools. |
| Compiler fingerprinting and frozen toolchain flags | **ADOPT** | Pin compiler hashes, format/header, link scripts, build determinism for each target. Needed urgently for PE/Civ III and external WLA-DX/6502 assembly. No external WLA-DX binary has been executed yet. |
| Automated AST normalizations (C89 hoisting, typedef idioms) | **CONDITIONAL** | Useful for legacy C projects with known compiler rules, but **must not** silently change semantics; not relevant for native assembly projects. Run normalized source back through compiler/byte diff. |
| decomp.me API scratch automation and RAG | **CAUTION** | decomp.me's current FAQ explicitly asks users not to scrape or make repeated automated AI requests. Use local tooling and allowed/manual share workflows only. Optional embeddings can be tested privately with permission and quantified benefit. |
| A single optimal local LLM quantization (Q4_K_M) | **NOT ADOPTED** | Hardware/memory/model/performance dependent. Paper's numerical perplexity claims do not establish a cross-project policy; benchmark quality and end-to-end cost on representative functions first. |
| Zelda64Recomp as downstream proof of high-level decomp -> recomp | **CORRECTED** | Project explicitly documents that static recompilation **does not require** recovered decompiled source (though reverse-engineering symbols and code help). Distinguish matching reconstruction from native static translation. |
| Explicit role of agent policy files | **ADOPT, implemented** | Added root `AGENTS.md`, a portable task contract, fail-closed scripts and project adaptation instructions. |

## Independent primary references checked

- [splat official repository](https://github.com/ethteck/splat) — supported platforms currently N64/PS1/PS2/PSP.
- [objdiff official repository](https://github.com/encounter/objdiff) — ARM/ARM64/MIPS/PPC/SH/x86 object-level diff.
- [decomp-permuter official repository](https://github.com/simonlindholm/decomp-permuter) — C mutations for MIPS, PPC, ARM32.
- [Kappa extension description](https://marketplace.visualstudio.com/items?itemName=macabeus.kappa) — target-specific context, AST fixes and tool integration.
- [decomp.me FAQ](https://www.decomp.me/faq) — permitted scratch workflows, unsupported bulk uploads and automation policy.
- [Zelda64Recomp official README](https://github.com/Zelda64Recomp/Zelda64Recomp) — recompilation is distinct from matched-source decompilation.

## Adopt for every project (copyable checklist)

1. Identify original binary and toolchain with hashes/versions; version the partition layout, distinguish physical from runtime addresses.
2. Demand a complete partition ledger, source/fallback accounting and no overlaps before reporting coverage.
3. Build source-only parts without reading source binaries; compare byte digests; include protected negative tests.
4. Provide bank/section-specific symbol and cross-reference context to AI; list uncertainty rather than invent missing types.
5. Run a bounded compile/diff loop with locked targets and preserved failed-attempt diagnostics.
6. Independently verify assembly/compiler output, and separately emulate representative subsystem side effects.
7. Close whole-bank/whole-system milestones, not a running tally of tiny match percentages.
8. Preserve ROM/asset copyright restrictions and third-party service rate/automation policies.

## Architecture-specific priorities

**Ys / SMS Z80:** keep the two byte-complete banks (3 and 7), validate WLA-DX when installed, close fixed bank 0 and the bank-6 object subsystem; add mapper-state-aware CFG, two-bank verification and boot-to-gameplay emulator tracing. **No code coverage was added by this document review.**

**Castlevania III / NES 6502:** create a PRG/CHR ownership map based on iNES or NES 2.0 metadata and VRC6 banking, plus vectors, interrupts, PPU/APU/VRC6 writes, and source-only per-bank build targets. Do not generalize a Z80 fetch/window mapper model to a NES cartridge mapper.

**Civ III / PC compiled executable:** fingerprint the actual executable version, memory sections/relocations, original toolchain and debug/symbol availability; enable function-level CFG/IR/type analysis, compiler matching, `objdiff` where file format and toolchain work, then source-object-link/full-PE SHA gates. No toolchain or original binary is assumed verified.

## Next substantial engineering investment

The core accelerant beyond these guardrails is a **shared evidence graph** (functions, basic blocks, read/write effects, symbols, mapper/relocation state, trace witnesses and caller edges) feeding automated context packets and whole-system test generation. Design a portable data schema, then implement architecture plugins: Z80, 6502, and PE/C. Validate each against an independent disassembler or emulator before using it to drive source conversion. This is a proposed next project, not a completed integration.
