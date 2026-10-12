# Portable decompilation evidence and AI workflow controls

This package is **independent of CPU, console, compiler, and AI provider**. Standard-library Python 3.9+ only. Copy `shared_decomp/` and `AGENTS.md` into another decompilation repository, then provide a project-specific partition manifest. It is not a decompiler, assembler, binary splitter or full-system emulator.

## Concrete features

1. **Whole-binary manifest audit** (`workflow.py audit`): verifies contiguous, disjoint coverage of the entire target file; complete source-versus-original fallback ownership; per-partition digests and whole-binary digest if the user's original image is provided. Tracks *source-backed*, *semantic*, *independent assembly* and *runtime evidence* separately. The manifest is a claim, not proof the source will build. Real build/recompiler tests must run in addition to this audit.
2. **Bounded context packets** (`workflow.py context`): retrieves known bank-qualified symbols, proven incoming references and instructions' direct outgoing references from existing JSON ledgers; rejects ambiguous mapper edges as proven callers. The output is bounded by `--limit` to avoid dumping the whole codebase into the LLM. Does not invent signatures or claim full CFG ownership.
3. **Protected matching attempts** (`workflow.py guard-init`, `guard-record`): locks the original assembly and build/test targets by SHA-256, records an **externally supplied** matching score, and stops after two consecutive non-improving attempts by default. This project-specific policy is stricter than the paper's suggested three. It cannot and does not compile or infer the score. Match percentages are not byte-equivalence proof.

## Commands — Ys (SMS) example

From the repository root:

```sh
python shared_decomp/workflow.py audit \
  --manifest shared_decomp/examples/ys_sms_manifest.json \
  --binary '/path/to/your/Ys - The Vanished Omens (USA, Europe).sms' \
  --output /tmp/ys_partition_audit.json

python shared_decomp/workflow.py context \
  --manifest shared_decomp/examples/ys_sms_manifest.json \
  --bank 6 --address 0x9932 --limit 10

python shared_decomp/workflow.py guard-init \
  --state /tmp/ys_sprite_guard.json \
  --lock Ys/src/phase11/bank06_sprite.asm \
  --lock Ys/Makefile
# Adjust --lock paths to the source files used by the actual task.
# After a separate compiler/diff script has supplied a percentage 0..100:
python shared_decomp/workflow.py guard-record \
  --state /tmp/ys_sprite_guard.json --score 88.5 --label attempt-1
```

The third non-improving attempt (initial match + two failed improvements) exits with status **3** and records `STOP`; treat this as a handoff to a human/diagnostic task. A changed locked reference fails with status **2** and does not register an attempt. Never reset the state file to get more attempts on the same problem without recording a review and a new plan. The guard treats a *larger* score as better, so convert low-is-better mismatch values to a consistent increasing score externally; document the conversion.

Run the toolkit tests:

```sh
python -m unittest discover -s shared_decomp/tests -v
```

## Manifest schema (`decomp-project-v1`)

```json
{
  "schema": "decomp-project-v1",
  "project": "Any reverse engineering target",
  "binary": {"size": 262144, "sha256": "...64 lowercase hex digits..."},
  "partitions": [
    {"name": "physical_bank_00", "offset": 0, "length": 16384,
     "source_backed_bytes": 0, "fallback_bytes": 16384,
     "source_only_complete": false, "semantic_status": "unresolved",
     "external_assembler_verified": false, "runtime_verified": false,
     "sha256": "...optional per-partition hex digest..."}
  ],
  "context_sources": {"symbols": "path/to/symbols.json", "references": "path/to/crossrefs.json"}
}
```

All partitions must cover the target exactly once (including headers, resource data, archives, gaps and padding). A partition could be a physical SMS bank, NES PRG/CHR bank, PE section, executable overlay, or any exhaustive and disjoint byte span. Do **not** equate physical completeness, semantic understanding, and a source-only reproduction. Avoid source paths to copyrighted assets in published repos.

The **Ys manifest is a snapshot** derived from `Ys/whole_system/build_report_m4.json` in Milestone 4. Reconcile it whenever its authoritative report changes. The toolkit's Ys integration tests detect drift in the ledger. In the current manifest, `semantic_status=partial` for banks 0, 3, 6 and 7, despite byte-complete source; other banks are conservatively marked unresolved. Runtime_verified is false for all partitions because no full-system emulator has corroborated complete-bank behavior.

## Project-family adaptation

| Family | Layout | Matching evaluation | Most valuable next work |
|---|---|---|---|
| SMS Z80 (Ys, future games) | Cartridge physical banks + mapper slots | Native WLA-DX vs ROM, VDP/PSG traces | Independent assembler, boot-to-play trace, code/data discovery |
| NES 6502 (CVIII) | iNES/NES2 header, PRG banks, CHR banks, mapper bank-state | 6502 assembler against PRG, audio/PPU/APU traces | Function CFG, mapper-aware callers, source-only PRG/CHR |
| PC compiled code (e.g., Civ III) | PE executable sections, code, read-only and mutable data | Compiler+linker, object/symbol diff, full PE checksum | Toolchain fingerprint, CFG/IR/type recovery, objdiff where supported |

Do not apply `m2c`, C89 syntax normalizers, splat or C permuters to handwritten 6502/Z80 assembly merely because the tools work elsewhere. Keep the C-specific workflow optional and compiler-conditioned.

## Portable review contract

See `TASK_CONTRACT_TEMPLATE.json` and the repository-root `AGENTS.md`. A whole-bank or whole-system milestone is accepted only after its **actual build/test** succeeds; partition accounting by itself cannot close a bank.

## Portable evidence-graph contract (added after AI workflow adoption)

`shared_decomp/evidence.py` provides `validate_graph(instructions, blocks, edges, image_size)` and is architecture neutral. Producers must supply physical byte-offset instruction nodes (`id`, `offset`, `size`), straight-line blocks (`id`, `offset`, `byte_count`, `instruction_count`), and edges (`from`, `to_instruction` or `null`, `from_block`, `to_block` or `null`). Its return value includes `valid`, `errors`, and audited counts. It rejects overlapping nodes/blocks, gaps in claimed basic blocks, bad spans, and broken edges. It **does not** certify CPU decoding, correct function boundaries, mapper state, semantic types, or runtime execution. A CPU-specific producer must verify opcode length/bytes separately.

Working Z80 producer and query examples: `Ys/tools/build_system_graph.py`, `Ys/tools/query_system_graph.py`; usage and confidence limitations are in `Ys/whole_system/EVIDENCE_GRAPH.md`. Future NES 6502/Civ III ports should keep instruction decoding and mapping separate from the reusable validator, rather than apply Z80 assumptions to those architectures.
