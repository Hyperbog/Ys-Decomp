# SMS/GG Recomp integration (opt-in)

This directory enables upstream [SMS/GG Recomp](https://github.com/mstan/smsggrecomp)
as a **separate, experimental native Z80 code-generation track** for Ys. It does
not replace the exact WLA-DX source reconstruction or the existing native C11
CPU/VDP runtime. The shared adapter is portable to future SMS games.

## Requirements

- Python 3.11+ (for the standard-library TOML parser)
- Your own legally obtained SMS ROM, matching Ys/manifest.json
- A separately installed and built SMS/GG Recomp executable (with its
  z80-recomp-core submodule), using upstream's build instructions
- Appropriate rights for using the upstream project and its dependencies

The upstream SMS/GG Recomp repository currently declares **no overall license**;
z80-recomp-core uses PolyForm Noncommercial 1.0.0. No upstream source,
generated C, original ROM, or engine binary is vendored here.

## Generate C

From the root of this repository, build upstream SMS/GG Recomp separately,
then invoke:

    python3 shared_decomp/smsgg_recomp.py \
      --rom /path/to/owned/Ys.sms \
      --manifest Ys/manifest.json \
      --config Ys/recomp/game.toml \
      --tool /path/to/smsggrecomp/recompiler/build/SmsRecomp

Or from the Ys directory:

    make recomp-preflight ROM=/path/to/owned/Ys.sms
    make recomp-generate ROM=/path/to/owned/Ys.sms SMS_RECOMP=/path/to/SmsRecomp
    make recomp-tests

The adapter first verifies exact SHA-256 and ROM size, stages upstream
generation in a temporary directory, then writes three files to the ignored
Ys/recomp/generated/ directory:

- ys_sms_full.c
- ys_sms_dispatch.c
- ys_sms_layout.c

A local report.json holds input/tool identity and generated-file hashes.
Its runtime_verified flag remains false until a separately tested runner
has executed the generated code against hardware-accurate reference traces.
Generated C is **not** decompilation-semantic or gameplay proof.

## Portability contract for other SMS games

Copy the TOML configuration into each game's recomp/ directory; update
output_prefix, ROM CRC, mapper and *verified* function/jump-table seeds.
Point the same adapter at that game's identity manifest and owned ROM.
The adapter accepts root-level sha256 + rom_bytes, or binary.sha256
+ binary.size. Generated C must remain ignored and private.

Phase 1 covers deterministic code generation, not compiling/linking the
per-game native runner, dispatch-miss profiling, cycle accuracy or gameplay
verification. Those are separate reviewed milestones.
