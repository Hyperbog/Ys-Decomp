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
    make recomp-verify ROM=/path/to/owned/Ys.sms SMS_RECOMP=/path/to/SmsRecomp
    make recomp-tests

Preflight validates ROM size and SHA-256, and independently checks CRC-32
if supplied by the manifest and/or game.toml. The upstream tool only
**warns** about configured CRC mismatches; the adapter **rejects** them.

After code generation, `recomp-verify` re-hashes all three output files
and checks the evidence report against the exact ROM, config and external
tool binary. This catches tampered files and obsolete generated C even
when the filenames are unchanged. Successful verification proves only
**generated-file provenance**, not that the output compiles or runs.

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

## Original-cartridge integration check (M39)

The [tagged M39 source-ROM CI run](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38443152403)
reconstructed the complete 16-bank Ys cartridge **without using
an owned binary as fallback**, then invoked this adapter's
`--preflight` mode against that actual 256 KiB image and checked-in
`Ys/manifest.json` / `Ys/recomp/game.toml`. It passed SHA-256
`02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`
and CRC-32 `B33E2827`. The independent
[adapter CI](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38424674348)
also passed all **9/9 synthetic tests**.

This confirms the Ys configuration and source-ROM identity **only**.
There is no tested upstream `SmsRecomp` binary invocation or
generated C build in CI, no verified recompiled CPU/VDP/PSG ABI,
no branch-dispatch coverage profile, and no executable native Ys
game derived from static recompilation yet. Set
`runtime_verified` only after comparing generated-code execution
with the source-ROM reference traces using the same hardware
state and frame-clock schedule.

## M41 provenance hardening

[SMS/GG adapter CI 38462981399](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38462981399)
passed **14/14** synthetic tests. The adapter now rejects generated
C or provenance reports supplied as symbolic links, rejects
symlinked generated output directories and Boolean ROM lengths,
and creates uniquely named temporary source/report files before
atomic replacement to avoid clobbering existing `.tmp` symbolic
links. Exact input/tool hashes remain mandatory.

M41 also verified a 518-byte original Ys bank-5 compressed stream
and its 748-byte independent decompression result at source
`PC=$0C67`. It does not demonstrate compilation or runtime
correctness of actual upstream-generated C: that integration
remains a separate unverified milestone.

## M42 source-ROM versus static recompiler

[Adapter CI 38463864482](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38463864482)
passed 14/14 synthetic tests and `make -C Ys recomp-tests`.
This covers preflight identity, generated-file provenance and safe
artifact staging, **not compiled/generated-C execution**.
Separately, [source-ROM M42](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38470163784)
executed original Z80 opcodes to `$0C72` and verified the staged
resource. These are independent tracks until a real generated-C
runner and differential CPU/VDP/PSG timing tests exist.


## M43 original-ROM reference for future generated-C execution

The [gated source-ROM run](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38471475804)
executed 127,325 interpreted Z80 instructions through 1,536
real `OUTI` writes, ending at `PC=$0C7E`. This establishes
a reference CPU/VDP/mapper/timing boundary for **future**
static-recompiled code differential testing; it does **not**
mean any `SmsRecomp` generated code ran. Phase-1 only.


## M44 differential graphics reference for future recompiled code

[Source-ROM CI 38474627069](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38474627069)
verified 12,288 original interleaved VRAM graphics bytes at
source `PC=$0C87`, matching a separate host decoder after
382,973 Z80 instructions, 50 naturally accepted interrupts and
54 generated VBlanks. This provides strong future
CPU/mapper/VDP/timing reference evidence for native compilation
of `SmsRecomp` output. These results remain from the
**C11 Z80 interpreter**, not statically recompiled execution;
the external adapter is still Phase-1 only.

## M45 independently verified original execution boundary

[Source-ROM run 38478502672](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38478502672)
reached `PC=$0C92` after **430,886** original Z80
instructions, with **56** naturally accepted IM1 IRQs,
**60** VBlanks and an independently matched **5,344-byte**
four-column WRAM resource staging result consuming **4,425**
compressed source bytes. Source-only cartridge reconstruction
and this adapter's SHA-256/CRC-32 `--preflight` both passed.
The code and timing records form a future **reference target**
for executing output from an external SMS/GG Static Recomp tool;
they are **not** evidence that generated C compiles or runs yet.
See [M45 WRAM reference](../../native/research/M45_FOUR_COLUMN.md).
