# Recompilation track — new, separately owned workspace

`recomp/` is the destination for **new** static-recompilation integration,
source-only reference/translated-execution comparisons, linker/ABI fixtures,
and independently audited runtime tests. It is separate from the historical
`Ys/` decompilation source and from `engine/` gameplay code.

Current verified state: the existing
[`../shared_decomp/smsgg_recomp.py`](../shared_decomp/smsgg_recomp.py)
provides opt-in generation and SHA/CRC provenance for an external SMS/GG
recompiler. Its legacy Ys-specific profile remains at
[`../Ys/recomp/game.toml`](../Ys/recomp/game.toml) for compatibility with
existing Makefile and adapter regression paths. **Actual upstream-generated C
has not yet been compiled, linked, executed or differentially validated.**
Do not describe current interpreted Z80 tests as recompiled execution.

## Source and output boundaries

| Category | Owner / location | Checked into Git? |
|---|---|---|
| Original recovered Z80 and banks | `Ys/` (decomp track) | Yes, source/metadata only |
| External SmsRecomp tool | User-provided external tool | No |
| Legacy generation profile | `Ys/recomp/game.toml` | Yes, compatibility only |
| New generated C, binaries and reports | `recomp/generated/` | **No** |
| Native game systems and mod contract | `engine/` | Yes, original-free code |
| Original ROM and extracted protected assets | Owner-controlled outside repository | **No** |

The original-game ROM identity is defined only by `Ys/manifest.json`;
do not create a second diverging digest authority. Generated output is
always ignored by Git, even if produced from the byte-exact source rebuild.
Do not import generated C into the semantic decompilation tree.

## Next execution milestone (not yet implemented)

1. Obtain a separately built and appropriately licensed upstream compiler.
2. Generate C from a locally rebuilt, hash-verified original cartridge.
3. Establish and compile an explicit generated-C/host ABI with a fail-closed
   dispatch implementation and SMS memory/VDP/input/interrupt adapters.
4. Execute identical bounded input schedules in the generated code and the
   verified native Z80 interpreter; compare CPU/WRAM/mapper/ports/clock and
   report the first divergence. No manual forced ROM states.
5. Only after independent parity tests, reuse this execution baseline to
   validate the original behavior of new `engine/` modules.

Upstream project licensing and redistribution require independent review.
Until verified, this track remains a **scaffold**, not a working recompilation.
