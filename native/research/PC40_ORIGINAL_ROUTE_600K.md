# PC-40 — original mapper-qualified sprite/control-flow route, 600k budget

## Purpose and evidence boundary

PC-39 established that, in the original source-ROM reset and 300,000
continued original-Z80 steps, the sprite-table WRAM region receives
192 zero-initialization stores at fixed bank-0 `$00B4`, one changed
store at `$0AA1`, and one **same-value** post-M45 `$0AA1` store.
The 27 full SAT VDP uploads are authentic Z80 instructions but are
**not** observed to be sourced from the bank-6 `$9932` producer.

PC-40 extends the original **opt-in experimental** input sequence
from verified M45 `$0C92` to **at most 600,000 continuation
iterations**. It uses exactly the PC-34 button-1 pulse armed at
original `$0CD1` and pressed/released at original `$0773`;
there is **no change** to the event schedule, CPU/mapper/WRAM,
clock, VDP or IRQ delivery.

At precisely iteration 300,000, it captures the authentic unmodified
CPU PC, mapper slots, `$C01F`, IRQ/VBlank counters, source collision
counter and five existing sprite-site counts. An independent check
compares those values against the existing **separately executed**
PC-34 experiment. If they differ, the route report is rejected.

At every natural CPU boundary, a read-only observer samples 12
source PC addresses, conditioned on physical mapped ROM bank:

| Physical bank | Observed candidate CPU PCs | Meaning / limitation |
| --- | --- | --- |
| 0 | `$26B6`, `$26DA`, `$26F3`, `$26F5`, `$2704` | Selector/caller region, previously researched in PC-15 |
| 0 | `$2BF2` | Separate candidate producer dispatch near the source `JP $9966` |
| 6 | `$9932`, `$9966` | Two candidate original bank-6 producer entry sites |
| 1 | `$4773`, `$47C2`, `$486C`, `$48DF` | Source collision-associated bank-1 code sites |

These are **physical-bank-qualified occurrences** rather than unqualified
CPU PC coincidences. A read-only watch does not imply a call occurred,
a sprite was drawn, collision logic was reached, or an actual player
was identified. The original-ROM source SHA is verified externally.

## Reproduction

Build the strict C11 native runtime and reconstruct the user's original
256-KiB Ys ROM with existing independent SHA-gated source tools:

```sh
./build-native/ys-native-timed-rom /tmp/ys-original.sms \
  --pc34-extended-postrelease \
  /tmp/pc34.json /tmp/pc35.json /tmp/pc36.json \
  /tmp/pc37.ppm /tmp/pc37.json /tmp/pc38.json /tmp/pc39.json

./build-native/ys-native-timed-rom /tmp/ys-original.sms \
  --pc40-source-route /tmp/pc40-source.json /tmp/pc40-route.json

python3 native/tools/verify_pc40_route.py /tmp/ys-original.sms \
  /tmp/pc40-source.json /tmp/pc40-route.json /tmp/pc34.json
```

The new read-only `native/pc40_route.{h,c}`, ROM-free
`native/test_pc40_route.c` and independent source-hash/prefix
verification guard this investigation. The expanded time window may
stop before 600k if the real source Z80 encounters an unsupported
instruction, a natural VBlank limit or mapped collision site.
Such outcomes must be reported as observed, not silently bypassed.

This is not independent emulator/hardware proof and does not meet
any of the original-game Alpha gates; the native PC window still
has a separate, synthetic two-room prototype. Keep all stacked
feature PRs draft; M45 is still the verified Development baseline.
