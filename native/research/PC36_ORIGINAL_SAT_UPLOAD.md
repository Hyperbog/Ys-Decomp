# PC-36 — whole original 192-byte SAT upload verification

## Evidence boundary

The original physical bank-0 source listing `Ys/phase5/code.lst`
contains the entire fixed-bank Z80 sprite attribute table (SAT)
upload routine at CPU `$0427-$053F`. PC-36 uses **unchanged,
source-verified Z80 execution**, not replacement C gameplay logic.

The previous PC-34 and PC-35 original controller experiment reached
`$0427` **27** times over a bounded 300,000-step continuation
from independently verified M45 `$0C92`. Those visits proved only
a sprite *upload routine* was reached, not that the upload data
matched staging memory. PC-36 closes this concrete data-flow gap.

The original source is a two-phase subroutine:

1. At `$0427`, write the VDP port `$BF` control pair
   `$00,$7F`, setting the VRAM write address to `$3F00`.
   Set HL to source WRAM `$DD00`, then `CALL $04BF`.
2. The first execution from `$04BF` through `$053D`
   contains exactly **64** contiguous `ED A3` (`OUTI`)
   instructions; its `RET` at `$053F` returns to
   `$0436`. These write the 64 Y bytes to VRAM
   `$3F00-$3F3F`.
3. At `$0436-$043C`, set the VRAM control address pair to
   `$80,$7F` (destination `$3F80`) and set HL to
   WRAM `$DD40`. Execution from `$043F` through
   `$053D` contains exactly **128** consecutive `OUTI`
   instructions. The **second** visit to `$053F` completes
   the 128 X/tile bytes at VRAM `$3F80-$3FFF`, then returns
   to the original caller.

Counting only the first `$053F` as a finished transfer would
be incorrect. The PC-36 observer tracks both distinct natural
returns before judging a whole upload.

## Implementation

- `native/pc_sprite_upload_watch.h/.c` is an optional passive
  observer. It snapshots the exact **64 + 128** work-RAM bytes
  at the naturally executed `$0427` entry, then compares all
  **192 bytes** against the true VDP VRAM `$3F00/$3F80`
  ranges only on the **second** `$053F` visit. It measures
  complete/abandoned/mismatched transfers, source and VDP CRC32s,
  first mismatching byte, total compared bytes and write delta.
- `native/test_pc_sprite_upload_watch.c` independently checks
  both `RET` phases, bytewise identity, a deliberately mismatched
  tile byte, CRC mismatch, duplicate sample idempotence, observer
  input validation and abandoned transfer tracking.
- Existing `--pc34-extended-postrelease` gains an **optional
  sixth path**, `PC36.json`, alongside unchanged PC-34/35
  JSON reports. No new controller input, CPU step, VBlank,
  mapper or machine state is imposed.
- `native/tools/verify_pc36_sat_upload.py` independently
  validates cartridge **SHA-256**, each of the **128** contiguous
  bank-0 `OUTI` source instructions (including the 64-byte
  CALL suffix) and listing rows, and checks PC-36 entry/exit
  counts and run metadata against independent PC-34 watch output.

## CI-verified result

The PC-36 code/checker branch HEAD
[`f9d5163`](https://github.com/Hyperbog/Ys-Decomp/commit/f9d5163fa80748dbd791695debfe2155170ad0f6)
passed all three workflows:

- [Native original-ROM execution](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38846524399):
  **31/31 CTest passed**, complete original 192-byte
  source-to-VDP comparisons passed.
- [M13–M17 source integrity](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38846524351):
  PASS on the original reconstructed ROM.
- [SMS/GG adapter](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38846524357):
  PASS.

| Entire source-backed PC-34/36 observation | Measured |
| --- | ---: |
| CPU continuation budget after verified M45 | 300,000 |
| Original `$0427` entries | **27** |
| First `$053F` visits (finished 64-byte Y helper) | **27** |
| Second `$053F` visits (finished 128-byte X/tile phase) | **27** |
| Complete 192-byte transfers matching source WRAM | **27** |
| Abandoned, pending, or mismatched transfers | **0** |
| Total compared bytes | **5,184** |
| Different bytes | **0** |
| VDP VRAM writes during final full upload | **192** |
| Physical bank-6 `$9932` producer entries | **0** |
| Mapper-qualified original bank-1 collision calls | **0** |

The previous PC-35 active-display, VRAM/CRAM activity, mapper
transitions and `$C01F` dispatch-selector change are preserved.

## Reproduce

Given the user-owned cartridge reconstructed and independently
SHA-verified using existing repository tooling:

```sh
./build-native/ys-native-timed-rom /tmp/ys-source.sms \
    --pc34-extended-postrelease \
    /tmp/pc34.json /tmp/pc35.json /tmp/pc36.json
python3 native/tools/verify_pc34_extended_postrelease.py /tmp/pc34.json
python3 native/tools/verify_pc35_video_dispatch.py /tmp/pc35.json /tmp/pc34.json
python3 native/tools/verify_pc36_sat_upload.py \
    /tmp/ys-source.sms /tmp/pc34.json /tmp/pc36.json
```

No original ROM, generated ROM data or extracted sprite assets
are stored in Git. The controller press/release is still an
**opt-in experiment**, not independently matched to a hardware
or trusted emulator input trace. These 27 real SAT transfers do
**not** prove that the physical bank-6 `$9932` sprite
*producer*, original player collision, world traversal or an
authenticated Ys gameplay frame ran. M45 stays the source
Development checkpoint, all five original-game Alpha gates
remain false, PR #3 remains draft, and the separate PC game
window still uses synthetic gameplay.
