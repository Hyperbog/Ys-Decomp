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

## R1a — compile/link integration (experimental)

R1 introduces a fail-closed compiler driver at
[`compile_generated.py`](compile_generated.py). It verifies the *complete*
four-file `SmsRecomp` output (`*_full.c`, `*_dispatch.c`,
`*_layout.c`, `*_funcs.h`) through the canonical adapter's ROM SHA,
CRC, configuration and external-tool identity checks **before** compiling.
The generated functions header is mandatory; older adapter reports with
three files must be regenerated. The driver then compiles the generated
translation units and the **external** upstream headless runner source
against the original external shared Z80 ABI and writes an ignored
`recomp/build/compiled-report.json` (compile/link only, never claims parity).

A separately built external [smsggrecomp](https://github.com/mstan/smsggrecomp)
checkout with its nested submodules, and a legally owned Ys cartridge or
independent verified source-only cartridge build, are required. No external
source is vendored or redistributed here.

From repository root on Linux/macOS with GCC or Clang:

```sh
# Using the existing verified source-only ROM reconstruction:
python3 Ys/tools/build_system_m10.py --check --out /tmp/ys-source.sms
# Build the external tool separately, per upstream instructions.
python3 shared_decomp/smsgg_recomp.py --rom /tmp/ys-source.sms \
  --manifest Ys/manifest.json --config Ys/recomp/game.toml \
  --tool /path/to/smsggrecomp/recompiler/build/SmsRecomp \
  --output recomp/generated
mkdir -p recomp/build
python3 recomp/compile_generated.py --rom /tmp/ys-source.sms \
  --upstream /path/to/smsggrecomp \
  --tool /path/to/smsggrecomp/recompiler/build/SmsRecomp
# At this point compile/link only is checked; testing runtime is separate.
```

Independent fixture tests:
`python3 -m unittest discover -s recomp/tests -p test_compiled_runner.py -v`.
They actually compile, link and **execute synthetic C**, and verify corrupted
header/ABI/provenance/compile failures. They do *not* execute original Ys.

GitHub Actions `ys-r1-recomp.yml` has an explicit manual
`execute_original=true` experimental job that builds the upstream
compiler, reconstructs the original cartridge, compiles generated C,
and attempts a one-frame headless run. A passing one-frame run is still
**not** equivalent to validated gameplay. The historical CPU/VDP
differential gate must be developed and passed separately.

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
