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

## Verified original-source result

The unmodified PC-34 experimental press/release sequence passed its
**300,000-iteration prefix comparison** against the existing
separately generated PC-34 source report. A longer bounded reference
Z80 run, with **no additional controller events or machine-state
forcing**, naturally reached:

| Observation | Verified PC-40 |
| --- | ---: |
| Continued iterations after M45 | **525,358** |
| Natural stop | Unsupported opcode at CPU `$1A0A` (`88`) |
| Accepted IRQ / VBlank at stop | **132 / 136** |
| Final mapper slot1 / slot2 | **1 / 7** |
| Final raw `$C01F` selector | **6** (300k prefix: 2) |
| Physical bank-0 `$26B6` selector-site hits | **1** |
| Physical bank-1 `$4773` collision-associated-site hits | **1** |
| Actual `$26DA` selector stores seen by route watch | **0** |
| Actual mapped bank-6 `$9932/$9966` route entries | **0** |
| Mapper-qualified original bank-1 collision calls | **0** |
| Naturally visited bank-0 `$0427` SAT upload entries | **40** |

The **first 27** `$0427` visits in the independent 300k PC-36
experiment were already proven to complete 64+128-byte source WRAM→VRAM
uploads. PC-40 does **not** independently compare full VRAM for the
13 additional `$0427` visits. Do not silently promote 40 uploader
entries to 40 verified full sprite uploads, animation frames, or
gameplay states.

The source path was initially blocked at fixed-bank `$267E`
(`ED 44`, `NEG`); after implementing original Z80 instruction
semantics it naturally progressed through additional graphics/caller
code and the mapper-selected sound/control code. The new native Z80
coverage is verified against the original source-ROM SHA and,
where available, the committed fixed-bank Phase6 instruction listing:

- `ED 44` `NEG` at `$267E` (complete Z80 flags, 8 T-states)
- `ED 52` `SBC HL,DE` at `$2693` (general rr forms, 15 T-states)
- `ED 4B 10 C2` `LD BC,($C210)` at `$26C3` (20 T-states)
- `ED A8` `LDD` at `$2AFE/$2B4B` (16 T-states, source/destination decrement)
- `DD 35 09` `DEC (IX+9)` in physical bank2 `$87C6`
  (signed displacement, carry-preserving flags, 23 T-states)
- `CB 3F` `SRL A` in physical bank1 `$61B1` (full flags)
- `ED 5B A1 C1` `LD DE,($C1A1)` in physical bank1 `$62DD`
  (mapped little-endian word read, 20 T-states).

Individual unit fixtures include zero/overflow/borrow flag edges,
memory mapper reads, signed IX/IY displacement, WRAM wrap,
ROM-write failure and documented timing. The fixed result is
**golden-pinned**, not inferred solely from a self-consistent trace.
No original ROM, music, tile or framebuffer bytes were committed.

This is important execution research, **not a gameplay breakthrough**.
No verified player, world traversal, actual bank-6 sprite production,
original collision or independently authenticated emulator frame has
been recovered. PC-40 cannot count as one of the five original-game
Alpha gates. The next unsupported CPU byte `88` at `$1A0A` must be
validated against the physical bank mapping before implementing
further Z80 instructions.

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
