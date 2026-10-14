# PC-8 — Simultaneously resident M44 VRAM/CRAM/registers

**Purpose:** Establish what an *actual simultaneously resident* original Ys
VDP looked like at one precise source-execution checkpoint, without making
the PC game execute Z80 or falsely calling this a playable scene.

## Original evidence boundary

The original source-only 16-bank Ys cartridge is generated with
`Ys/tools/build_system_m10.py --check`. The existing independent
`ys-native-timed-rom` diagnostic then executes actual bank-0/bank-5
source Z80 instructions, with natural frame timing/IRQs and no injected
VDP writes or patched registers, through the previously verified M44
checkpoint **PC=$0C87**.

**PC-8 adds observation, not emulation opcodes:** immediately after
the real M44 four-plane pattern upload completes, it writes a bounded,
raw source-checkpoint snapshot of exactly:
- **16,384 simultaneous VRAM bytes**
- **32 simultaneous CRAM bytes**
- **16 simultaneous VDP register values**

These are read from the **same original executing VDP instance** at the
same source-PC boundary. This checkpoint is **after** the M43
`$3900–$3EFF` name-table upload and M44 `$0000–$2FFF`
pattern upload, **before** the subsequently verified M45
four-column WRAM-resource staging. The trace continues to M45 without
using the captured values as replacements.

## Snapshot format

An untracked local **16,448-byte** file:

```text
offset  bytes   meaning
0         8     ASCII YSPC8V01 version/magic
8         2     LE original source PC = $0C87
10        2     LE payload length = 16,432
12        4     CRC32 of exactly the 16,432-byte payload
16     16384    Original simultaneous VRAM[$0000..$3FFF]
16400     32    Original simultaneous CRAM[0..31]
16432     16    Original simultaneous VDP registers 0..15
```

The native `ys_pc_vdp_checkpoint_load` rejects truncation,
trailing bytes, invalid format/PC/length and CRC errors.
`ys_pc_vdp_checkpoint_matches` independently enforces that the
capture's original VRAM bytes at `$0000–$2FFF` are byte-identical
to PC-7's source-only M44 pattern export **and** at
`$3900–$3EFF` are byte-identical to PC-6's source-only M43
name-table export. A well-formed CRC alone does **not** imply the
snapshot is the verified original source.

This second comparison is important because natural IRQs or other
writes could, in principle, mutate VRAM between adjacent source
uploads. A mismatch must fail PC-8 rather than drawing a
fabricated combination.

## Native inspection, not a shipping game-runtime dependency

- `native/pc_vdp_checkpoint.{h,c}`: format, writer, strict
  loader and independent M43/M44 source-byte identity check
- `native/trace_timed.c`: opt-in
  `--vdp-at-m44 /path/to/snapshot.vdp`, a read-only capture
  inserted at the existing exact `PC=$0C87` milestone
- `native/pc_vdp_probe.c`: validates capture against the original
  source pattern and name-table packages; prints the *actual*
  VDP R0/R1 display-enable state and all 32 CRAM bytes. Can
  render an optional P6 diagnostic PPM using the existing
  SMS Mode-4 VDP renderer
- `native/game_sdl.c`: optional **F10** diagnostic source
  framebuffer via `--vdp-checkpoint FILE`, which requires
  **both** `--patterns FILE` and `--nametable FILE` for a
  source-identity guard. Displays the palette defined by
  captured source CRAM, not arbitrary grayscale. The original
  display-enable registers are honored: a blank screen can be
  the *correct original checkpoint frame*.
- `native/test_pc_vdp_checkpoint.c`: synthetic but strict
  format + CRC + source-byte comparisons; independently
  checks validly checksummed nonmatching VRAM is rejected

The native PC gameplay room, input, physics and provisional combat
are **not** replaced or driven by this diagnostic snapshot.

## Reproduce source-only

```sh
cmake -S native -B build-native -DCMAKE_BUILD_TYPE=Debug
cmake --build build-native --parallel
ctest --test-dir build-native --output-on-failure

python3 native/tools/export_pc_nametable.py --out /tmp/pc8-nt.bin
python3 native/tools/export_pc_patterns.py --out /tmp/pc8-patterns.bin
python3 Ys/tools/build_system_m10.py --check --out /tmp/pc8-source.sms

./build-native/ys-native-timed-rom /tmp/pc8-source.sms \
  --vdp-at-m44 /tmp/pc8-m44.vdp

./build-native/ys-pc-vdp-probe /tmp/pc8-m44.vdp \
  /tmp/pc8-patterns.bin /tmp/pc8-nt.bin /tmp/pc8-m44.ppm

./build-native/ys-native-game \
  --nametable /tmp/pc8-nt.bin \
  --patterns /tmp/pc8-patterns.bin \
  --vdp-checkpoint /tmp/pc8-m44.vdp
```

F10 opens/closes the actual checkpoint RGB view. F9 retains the
earlier **index-grayscale combination** for comparison; these are
distinct evidence levels. CI creates all assets in its temporary
directory, checks full source identity and file sizes, launches SDL2
headlessly, and tests deliberate corruption rejection.

## What this does not establish

Even a byte-exact M44 snapshot does **not** demonstrate an authentic
**playable** Ys scene: original content may be in setup/blanked
state, and object/camera/collision/progression for an active
gameplay location remain unresolved. Rendering fidelity of the
existing SMS diagnostic layer is not independently pixel-audited
against an external physical-hardware capture at this source
checkpoint. **The original CRAM/register state is authentic
to this bounded trace; whether it constitutes a finished display
palette/scene depends on the original register and runtime state.**

No original ROM, generated ROM, rendered snapshot, or proprietary
asset binary is committed. This remains draft research support
for an enhanced standalone native PC port, not a return to
instruction-for-instruction runtime emulation. Alpha gates stay
unpassed.
