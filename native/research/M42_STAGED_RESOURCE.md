# M42 — Source bank-5 staged resource and static-recompiler boundary

## Original source control flow

The fully reconstructed 16-bank 256 KiB Ys cartridge is already verified
through **bank-0 PC=$0C67** at M41:
109,081 interpreted Z80 instructions, 1,226,741 nominal T-states,
16 accepted IM1 interrupts and 20 clock-generated VBlank events.
The original bank-5 RLE stream (518 bytes) has produced 748 bytes
of resource data in WRAM starting at $C600.

Original `Ys/src/phase16/bank00_symbolic.asm` then executes:

| Original PC | Instruction/action |
|---|---|
| `$0C67` | `LD HL,$C600` |
| `$0C6A` | `LD DE,$D600` |
| `$0C6D` | `LD C,$02` |
| `$0C6F` | `CALL $0BEF` |
| `$0BEF-$0BF1` | Set row count to 2, save DE and BC |
| `$0BF2-$0C1F` | Decode commands into two interleaved rows, advancing destination by 2 each byte |
| `$0C72` | Return to original graphics upload sequence (not executed here) |

For each row, source command `0` terminates; negative commands copy
a length of literal bytes, while positive commands repeat one value.
A literal length whose seven low bits are zero runs 256 Z80 DJNZ
iterations. At each row end the source restores DE and increments by
one, so row 0 targets the even address offsets and row 1 the odd
offsets. This is **resource staging in WRAM**, not video presentation.

## Independent reference and native verification

`native/trace_timed.c` extends the existing full source-ROM trace
without changing CPU registers, the instruction clock, RAM or hardware
ports. A separate bounded C decoder models the source commands over
the already validated $C600 resource and updates an expected copy of
the pre-existing non-stack $D600-$DFBF WRAM workspace.

The original Z80 CPU independently runs the source `$0BEF` routine.
The acceptance gate checks:

- Natural return at **PC=$0C72**, through the source routine.
- Exact byte-for-byte agreement for all $9C0 bytes of non-stack
  destination WRAM ($D600-$DFBF), including untouched locations;
  require exactly 1,536 staged writes from all 748 resource bytes.
  The remaining $DFC0-$DFFF bytes are live Z80/IM1 stack scratch
  and MUST NOT be compared to their pre-trace contents; doing so
  falsely rejects authentic interrupt stack pushes.
  No synthetic graphics or CPU state are inserted.
- Source pointer and final DE derived from independent row lengths,
  restored stack pointer, B=0 and unchanged C=2.
- Slot-2 ROM mapper preserved; allow clock-generated IM1 IRQs to
  occur during the long routine. The first real gated run reached
  $0C72 after two additional IRQs and two VBlanks, so IRQ/audio/VDP
  counts are checked for monotonicity and a bounded window instead
  of being artificially held constant. No source-ROM edits or
  injected IRQs; a bounded instruction budget and explicit failure.
- Existing M25 and M29-M41 source-based CPU/VDP/sound checks remain
  mandatory, including independent M41 bank-5 decompression.
- Optional `--frame` P6 export remains a static **256×192** image
  of the actual VDP state at the new checkpoint. It may be blank.

A second ROM-free test executes byte-for-byte source opcodes for
`$0C67-$0C6F` and `$0BEF-$0C1F` with a synthetic two-row command
stream, checking literal and repeated values, interleaved offsets,
preserved sentinels and stack/mapper/IRQ behavior.

## SMS/GG Recomp integration review

[SMS/GG adapter CI 38463864482](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38463864482)
passed **14/14** synthetic tests and Ys Makefile integration.
The `shared_decomp/smsgg_recomp.py` adapter enforces exact ROM
size, SHA-256 and optional CRC-32, verifies the game config and
generated-output provenance, rejects unsafe symlinked generated
artifacts and stages writes via unique temporary files.

The documented upstream `SmsRecomp` executable is an **external
prerequisite**, not part of the current CI. No original game ROM,
ROM-derived generated C, or upstream runtime is included in the repo.
The integration is Phase 1 preflight/codegen/provenance, **not a
native static-recompiled execution engine**. Generated C remains
uncompiled and unlinked to the native game. No claim is made that
the static recompilation itself achieves $0C72, runs the game,
passes differential tests, or satisfies Alpha.

The source-only ROM checksum remains
`02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
All release-promotion gates stay false.

## Next boundary

The next original instructions `$0C72-$0C7B` call `$06C1`
for actual video data transfer. This likely needs a longer
VDP/interrupt-backed execution window, a bounded true VRAM write
ledger and a comparison with the staged WRAM resource.
Do not promote to playable/title-screen status without visible
live video and interactive control evidence.

## Initial full-ROM diagnostic

The first gated original-ROM run, [38469588594](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38469588594), reached the target `$0C72` in 122,272 instructions and 1,323,179 nominal T-states. It decoded all 748 bytes from `$C600`, performed 1,536 staged writes and naturally received two new frame interrupts (`IRQ=18`, `VBlank=22`). The original assertion incorrectly expected no IRQ during the 13,191-step routine. The corrected check allows natural interrupts and independently verifies every destination byte. Successful source-ROM validation of the corrected check is required before claiming M42 complete.

## Gated source-data vs. live-stack separation

The second tagged ROM run [38469858302](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38469858302) confirmed the complete 1,536 resource writes and all 748 consumed command bytes, two natural IRQs and normal CPU/mapper return. It found only **31** workspace comparison differences, beginning at `$DFC0`, which is **inside the original Z80 interrupt stack**, not the staged resource. The M42 acceptance scope is now precisely `$D600–$DFBF`, excluding the stack area `$DFC0–$DFFF`; any difference in the non-stack resource region remains a hard failure. No ROM/game-state edits, graphics fabrication or IRQ injection are used. A final gated check is required before declaring M42 verified.
