# M41 — Bank-5 compressed resource and verified SMS/GG Recomp boundary

## Original execution path

M40's full-source, naturally timed Ys trace reaches bank-0 Z80
`PC=$0C55` after 105,009 instructions, 1,196,582 nominal
T-states, 16 accepted IM1 interrupts and 20 VBlanks. The source
then performs:

| PC | Original Ys bank-0 instruction |
| --- | --- |
| `$0C55` | `LD ($C02E),SP` (Z80 ED 73, 20 T-states) |
| `$0C59` | `LD A,$05` |
| `$0C5B` | `LD (MapperSlot2),A` |
| `$0C5E` | `LD HL,$B61A` |
| `$0C61` | `LD DE,$C600` |
| `$0C64` | `CALL $0C20` source decompressor |
| `$0C67` | First post-decompression staging instruction |

At `$0C20-$0C3D`, the original Z80 game decodes a
sentinel-terminated bank-5 stream:

- Command 0 ends the resource.
- Command with bit 7 set: literal stream, length `cmd & 0x7F`;
  an encoded zero count wraps DJNZ through 256 iterations.
- Positive command (1–127): one input value followed by
  `cmd` incrementing output values, using `INC A` and `DJNZ`.
- Source pointers, flags, and the live Sega ROM mapper remain
  authoritative; no HLE replacement is used to run the game.

## Native acceptance

- Implement ED 73 `LD (nn),SP` with little-endian bytes,
  no modified Z80 flags, wrap-safe writes and 20T timing.
- ROM-free fixture executes the source `$0C55–$0C67` startup
  and `$0C20` decompression routine against a synthetic bank-5
  compressed sequence with both literal and incremental commands.
- Gated original 16-bank source-ROM run executes the *real Z80
  instructions* through `PC=$0C67`. It independently decodes
  the physical source bank-5 bytes at offset `$361A` in
  bounded host code, checking every output byte, the encoded
  bytes consumed, output extent, original stack save, and bank-5
  mapper selection. No source CPU register or memory patches,
  injected IRQs or skipped opcodes.
- Limit expected output to a 4 KiB scratch buffer, and limit
  original CPU execution to 180,000 additional instructions.
  On overflow or unsupported source opcode, **fail**, do not
  synthesize or skip source code.

The resulting WRAM data is a decompressed resource, not a
verified title screen or a live Windows graphics mode. The
following original source stages and uploads these bytes; it
is a separate execution checkpoint.

## SMS/GG Recomp integration review

The opt-in `shared_decomp/smsgg_recomp.py` adapter and
`Ys/recomp/game.toml` follow the documented upstream
`SmsRecomp` interface, produce three ignored C artifacts,
and verify input/config/tool identity and generated-file SHA-256.
Added negative tests reject symbolic-link output directories,
symbolic-link source C, symbolic-link reports, Boolean ROM
sizes, and a dangerous pre-existing `.tmp` symlink.
Generated files use uniquely named temporary files before
atomic replacement. The corrected
[adapter CI](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38462981399)
passes 14 synthetic tests.

This is **Phase 1 codegen/provenance only**. The upstream
SmsRecomp executable is not built or executed in Ys CI.
Generated C is not compiled, linked, run, or differentially
verified against the game interpreter. No proprietary
ROM, output C or upstream source is vendored. The upstream
license and runtime interface require separate review before
a native game runner can be claimed.

## Gating

Keep the original 16-bank 262144-byte source-ROM digest
`02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
All Alpha, Beta, Final evidence flags remain false.
