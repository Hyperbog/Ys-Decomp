# Whole-system Z80 evidence graph — first cross-bank inventory

**Status:** deterministic, ROM-checked *static evidence*, not a source-only ROM build and not a gameplay trace. Git baseline before this work: `adeed6b` on local `SMS` branch, no Git remote configured. The connected GitHub account has no SMS/NES decomp repo to pull from.

## Why this is a system milestone, not a byte-count phase

The inventory analyzes **every independently reconstructed Z80 instruction** in the current source modules and the newly recovered late bank-7 routines. Instructions are checked byte-for-byte against the original ROM before they enter the graph. The graph then partitions the verified instruction positions into maximal straight-line **basic blocks**, records branches and calls, and tracks mapper-dependent candidate targets and directly observable memory/port-access instructions.

| Evidence | Total | Meaning |
|---|---:|---|
| Verified Z80 instructions | **7,047** | Existing reconstructed instructions, not 7,047 newly discovered instructions |
| Verified Z80 instruction bytes | **14,198** | Previous 14,025 + previously recovered 173 late-bank-7 bytes; **no new ROM coverage** |
| Basic blocks | **1,765** | Static graph partitions of verified instruction spans |
| Directed edges / exit markers | **8,155** | Includes 6,665 contiguous fallthroughs and 279 non-static exits |
| Fixed-bank-0 branch/call targets | **770** | CPU `$0000–$3FFF`, physically fixed bank 0 |
| Same-image mapper-slot candidates | **412** | Syntactically local to a source bank, **not runtime bank proof** |
| Static mapper-write bank candidates | **12** | From prior tightly bounded constant-write evidence |
| Unresolved mapper-slot branches/calls | **17** | Explicitly unassigned, not assigned an invented bank |
| Memory/I/O effect instruction sites | **1,645** | Immediate port accesses, register-C ports, and absolute-address reads/writes; not complete data flow |

Source-bytes remain **53,249 / 262,144**, with **208,895 fallback bytes**. The two byte-complete source banks are still **3 and 7**. Re-running the original-ROM overlay and graph tests does not establish runtime fidelity or third-party assembly.

## Whole-bank investigation queue

`frontier.json` records **five referenced, not-yet-source-backed bank-0 CPU locations**: `$0702`, `$07D5`, `$0718`, `$06E8`, `$0739` (seven references in all), plus the 17 unresolved mapper-slot control sites. These are evidence-backed *candidate entry points*, not classified Z80 instruction bytes. Validate their code/data context and exits before recovering another bank-0 segment; don't blindly disassemble arbitrary fallback bytes.

Bank 0 currently has **7,935 ROM-checked Z80 instruction bytes**, while its whole-system build report lists **8,242 total source-backed bytes** (including data); the remaining **8,142 bytes** depend on the original ROM. Bank 6 has **644 source-backed Z80 code bytes** and **7,192 total source-backed bytes**, with **9,192 fallback**. Subsystem execution evidence for sprite rendering is recorded separately in the Phase 19/20 reports; it is not replaced by this static graph.

## Reproduction

```sh
cd Ys
make system-graph ROM='/path/to/Ys - The Vanished Omens (USA, Europe).sms'
make system-graph-frontier
python tools/query_system_graph.py --bank 0 --cpu 0x0089 --radius 6
python tools/query_system_graph.py --bank 6 --cpu 0x9932 --limit 10
make whole-rom-verify ROM='/path/to/Ys - The Vanished Omens (USA, Europe).sms'
make whole-system-verify ROM='/path/to/Ys - The Vanished Omens (USA, Europe).sms'
```

* `evidence_graph.json`: structured instruction, block, control-flow, and memory/I/O evidence; generated from verified assembly, **does not embed commercial ROM bytes** (it contains authored/reconstructed mnemonics).
* `frontier.json`: unresolved control destinations for planned source recovery.
* `tools/build_system_graph.py`: checks each assembly instruction against ROM and independently checks decoder instruction length; rejects drift, source overlap, and malformed basic blocks.
* `tools/query_system_graph.py`: bounded, bank-aware context packets for AI-assisted reconstruction.
* `shared_decomp/evidence.py`: architecture-neutral structural validator reusable by 6502, compiled-code, or additional Z80 graph producers; it does **not** decode those architectures.
* `tests_system_graph.py`: 22 new corruption, identity, query, mapper, and provenance tests.

## Unresolved whole-system gates

1. Real `wla-z80` / `wlalink` run: **not available in this container**, so external assembly remains unverified.
2. Independent full-system emulator traces: **not available in this container**. Existing bounded CPU execution confirms only explicitly modeled routines and inputs.
3. Complete bank 0, bank 6, and the remaining banks' source-only reconstruction: **not achieved**.
4. Actual cross-routine register/flag data flow, indirect targets, compression formats, and text grammar: **not recovered** by this graph.

Next, work from the verified bank-0 target queue into bounded code/data recovery and from bank-6 sprite objects into whole-subsystem behavior, **without releasing a fake byte-complete bank obtained by dumping unknown bytes into DB statements**.
