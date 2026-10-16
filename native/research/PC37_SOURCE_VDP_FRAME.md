# PC-37 — bounded original-source VDP snapshot at complete SAT upload

## Scope and evidence

PC-37 extends the **same**, already source-backed PC-34/35/36 original
Sega Master System Ys cartridge continuation. It adds **no controller
pulse, IRQ, clock tick, mapper write, RAM write, VDP write, new Z80
opcode, or additional interpreted instruction**.

At the **second** naturally executed fixed-bank `$053F` return after
`$0427`, PC-36 has verified that 64 Y bytes and 128 X/tile bytes
were copied from WRAM `$DD00/$DD40` into VRAM
`$3F00-$3F3F/$3F80-$3FFF`. PC-37 copies the full VDP register,
16-KiB VRAM and 32-byte CRAM state **at that exact CPU boundary**.

If one or more full SAT completions occur while Mode 4 and display
are enabled, the most recent eligible snapshot is selected. Otherwise
the most recent complete SAT snapshot is retained and explicitly
recorded as display-disabled. The existing native `ys_sms_video_render`
converts this static source state into one diagnostic **256×192 RGB
PPM** image; a JSON sidecar preserves the execution/mapper state,
register values, byte-level memory CRC32s, rendered RGB CRC32, and
native renderer overflow/collision-pixel counters. No ROM-derived image
is committed to Git or uploaded as a CI artifact.

This capture is **not** a raster-timed framebuffer trace; line-timing,
a hardware/independent-emulator oracle, actual visible presentation,
player identity, authentic gameplay location and original sprite
production remain unproven. The original bank-6 `$9932` producer and
original bank-1 collision path were still not seen during PC-36.

## Independently gated result

The first full source-ROM GitHub Actions run for PC-37 passed all three
existing workflows, including **31/31 native CTest cases**. The original
PC-34/35/36 input schedule remained unchanged and produced:

| Source-backed measurement | Value |
| --- | ---: |
| Completed 192-byte SAT uploads | 27 |
| Uploads at a Mode-4 display-enabled CPU boundary | **26** |
| Selected last display-enabled upload (steps after M45) | **162,573** |
| Native 256×192 RGB CRC32 | **`9FB8BB1E`** |
| Original bank6 `$9932` producer calls | 0 |
| Original bank1 collision calls | 0 |

The source bytes are protected by existing ROM SHA/listing checks;
the PC-37 checker also pins the observed 26/162,573/CRC fingerprint
so a self-consistent but changed native renderer cannot silently pass.
These values were observed in [native CI run 38850229114](
https://github.com/Hyperbog/Ys-Decomp/actions/runs/38850229114).
No third-party framebuffer comparison is claimed.

## Local reproduction

From the repository root after building the complete original ROM
from source using the existing SHA-gated toolchain:

```sh
./build-native/ys-native-timed-rom /tmp/ys-source.sms \
    --pc34-extended-postrelease \
    /tmp/pc34.json /tmp/pc35.json /tmp/pc36.json \
    /tmp/pc37-source.ppm /tmp/pc37-source.json

python3 native/tools/verify_pc34_extended_postrelease.py /tmp/pc34.json
python3 native/tools/verify_pc35_video_dispatch.py /tmp/pc35.json /tmp/pc34.json
python3 native/tools/verify_pc36_sat_upload.py /tmp/ys-source.sms /tmp/pc34.json /tmp/pc36.json
python3 native/tools/verify_pc37_source_frame.py \
    /tmp/pc37-source.ppm /tmp/pc37-source.json \
    /tmp/pc34.json /tmp/pc35.json /tmp/pc36.json
```

PC-37's validator independently checks an exact PPM header and
147,456 RGB bytes, the RGB CRC32, bounded typed JSON fields, and
identical PC-34/35/36 original run metadata. The original PC-36
golden result remains **27/27 complete original 192-byte transfers,
5,184 matching bytes and zero mismatches**. CI also verifies that a
deliberately truncated/corrupt PPM is rejected.

This is a **research checkpoint**, not a new M46 release or an
authentic-game Alpha gate. The user-provided `z80-recomp-core` runtime
archive is kept separate; its license and generated-code ABI require
an independent integration task. All five genuine-game Alpha gates
remain false until verified original interactive play exists.
