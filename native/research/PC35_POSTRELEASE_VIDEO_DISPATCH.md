# PC-35 — same-run original source VDP and dispatch audit

## Distinct evidence and scope

PC-35 attaches an **optional read-only JSON sidecar** to the already
source-proven, opt-in original cartridge PC-34 300,000-step
`--pc34-extended-postrelease` controller experiment. It **does not**
create a second replay, extend its instruction/VBlank budget, inject
a source Z80 PC, seed RAM/mapper/VDP, fake an IRQ, or add another
controller press. The only controller event remains the PC-27/33
**explicit experimental active-low button-1 sample**, armed by the
naturally reached `$0CD1` source edge check, executed at
`$0773` and then genuinely released at the next source port read.
This controller schedule is **not independently validated** against
hardware or trusted emulator input timing.

The PC-35 implementation
[commit a59e69f](https://github.com/Hyperbog/Ys-Decomp/commit/a59e69f0b674d1887ceb81bfea52a8fa0e63699e)
adds a fifth optional path to the PC-34 command and samples:

- Z80-derived $C01F dispatch selector transitions (not mode labels);
- VDP register 1 bit 6 display-enable sampled on real CPU step boundaries;
- additional existing VDP VRAM/CRAM write counters relative to the same
  M45-start reference state;
- actual slot-2 mapped physical bank transitions;
- existing mapper-qualified sprite-upload, bank-6 producer and
  bank-1 original collision observation counters.

Separate `native/tools/verify_pc35_video_dispatch.py` checks typed
fields, monotonically bounded counters, and shared run identifiers,
stops, IRQ/VBlank values, sprite/mapper/collision counters against
the original PC-34 report. No frame, tilemap or source player
identity is inferred. A command-line grouping compile fix is
[commit 1e3ec28](https://github.com/Hyperbog/Ys-Decomp/commit/1e3ec28a5505ad4c13a66cb3c6368dd623affcfa).

## Verified GitHub Actions run

On the corrected PC-35 SHA **1e3ec28**, all three workflows PASS:

- [Native C11](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38841837333):
  **30/30 tests passed**, PC-33 and PC-34 original source
  watchers passed, PC-35 independent same-run audit passed.
- [M13–M17 original source integrity](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38841837263): PASS.
- [SMS/GG adapter](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38841837280): PASS.

Original PC-34 source run (after verified M45 $0C92), with one
explicitly experimental button sample and source-observed release:

| Observation | PC-35 read-only value |
| --- | ---: |
| Post-M45 CPU continuation steps | 300,000 |
| Original stop PC / cause | `$0030` / budget |
| Accepted IRQs / VBlanks | 100 / 104 |
| Selector $C01F transitions | **1** ($01→$02) |
| Display-enable-active sampled steps | **156,411** |
| Display-enable transitions | **2** |
| VRAM writes (additional) | **15,592** |
| CRAM writes (additional) | **288** |
| Slot-2 mapped bank transitions | **99** |
| Actual $0427 source sprite upload routine visits | **27** |
| Mapper-qualified physical bank-6 $9932 sprite producer | **0** |
| Mapper-qualified bank-1 collision calls | **0** |

PC-34 independently records the exact same PC, event horizon,
sprite and collision values. Its final slot2 physical ROM bank
is **11**.

## What is and is not proven

These source-proven observations show that original code executed
under the controlled input schedule does toggle display-enable,
write VRAM/CRAM, switch mapper slot 2, and invoke the original
$0427 sprite *upload* code. This is more than sound-loop idling,
but no authenticated rendered gameplay frame, player identity,
world map, title-to-play input schedule, sprite-production path
or actual collision route follows from these counts alone.

In particular, the PC-34/35 **27 uploads** do not establish
execution of the physical bank-6 $9932 **producer**. The
five original-game Alpha gates remain false; the native gameplay
window still contains a separate synthetic room. PR #3 remains
draft and M45 is still the verified Development checkpoint.

The next independently justified investigation should compare
a **trusted emulator or hardware trace** at a matched source
controller pulse, timing, mapper, VDP register state and an
actual captured frame. The read-only counters can guide that
comparison but are not a substitute for it.

## Reproduce with locally reconstructed source ROM

```sh
./build-native/ys-native-timed-rom /tmp/ys-original.sms \
  --pc34-extended-postrelease \
  /tmp/ys-pc34-postrelease.json \
  /tmp/ys-pc35-video.json
python3 native/tools/verify_pc34_extended_postrelease.py \
  /tmp/ys-pc34-postrelease.json
python3 native/tools/verify_pc35_video_dispatch.py \
  /tmp/ys-pc35-video.json /tmp/ys-pc34-postrelease.json
```

Build/reconstruct the user-provided source ROM using existing
SHA-gated repository scripts. Never commit or redistribute it.
