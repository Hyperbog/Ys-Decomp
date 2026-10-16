# PC-20–PC-25 — original Ys sound-path execution and bounded research handoff

**Classification:** evidence-backed native/reference Z80 interpreter research;
not a completed original Ys PC port, original gameplay, playable stage,
sound-output authentication or new original-game release.

## Locked original evidence

- Target: Sega Master System original Ys source-only unheadered 16×16KiB
  cartridge, 262,144 bytes, SHA-256
  `02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
- Baseline: verified M45 original CPU PC `$0C92`; the native timed-ROM
  executor preserves source Z80/mapper/VDP/WRAM/IRQ and unpressed controller
  state during the read-only passive watches.
- Sound paths: original physical bank 2, independent `Ys/phase5/code.lst`
  and source-only ROM matching; fixed-bank pointer path `$0D9F-$0DCC`
  independently listed in the same Phase 5 ledger.
- No original ROM or separately extracted commercial game assets committed.

## Completed implementation milestones

| Milestone | Interpreter-only source-backed capability | Implementation SHA |
| --- | --- | --- |
| PC-20 | `DD/FD 86 d`, indexed `ADD A,(IX/IY+d)`, 19T and full Z80 arithmetic flags | `d49a80c` (test adjustment `b5942f5`) |
| PC-21 | `DD/FD 70-73,77 d` indexed B/C/D/E/A stores and `46/4E d` indexed B/C reads, 19T | `4a9d47f` (timing test fix `5de885d`) |
| PC-22 | `DD/FD 66/6E d` indexed ordinary H/L loads, `74/75 d` ordinary H/L stores, 19T | `7793ee6` (superseded-test fix `260bd83`) |
| PC-23 | `DD/FD 36 d n` indexed immediate memory store, 19T | `f90f900` |
| PC-24 | `DD/FD 23/2B` 16-bit `INC/DEC IX/IY`, 10T and flags unchanged | `831487c` |
| PC-25 | **Separate** opt-in 300k-step passive source collision research mode, preserving legacy 150k tests and original input | `d4db4fd` |

Tests include isolated original-opcode fixtures, signed IX/IY offsets,
ROM-write rejection, live SMS mapped bank reads, 16-bit wrap,
unchanged flags/registers where required, cycle accounting, exact source
bytes, SHA-256 and independent listing ledger matches. All successful
implementation run workflows passed **30/30 CTest**.

The Phase 5 listing uses historical `ixl/ixh` register names at
`$89D1/$89D4` and `$8587/$858A`. The **hardware** meaning of
`DD 6E/66 d` and `DD 75/74 d` when memory `(IX+d)` is also
accessed uses the ordinary L/H registers, leaving IX unchanged.
The reference CPU implements and independently tests this behavior,
rather than editing or trusting the ambiguous golden listing label.
Hardware rule reference: Zilog Z80 CPU User Manual,
https://www.zilog.com/docs/z80/z80cpu_um.pdf
and indexed-prefix decoding,
https://z80.info/decoding.htm.

## Actual passive original-source continuation

| Research checkpoint | Steps after M45 | Stop PC | Stop cause | Accepted IRQs | VBlanks |
| --- | ---: | --- | --- | ---: | ---: |
| PC-19 | 6,027 | `$85D3` | unsupported indexed ADD | 57 | 61 |
| PC-20 | 6,038 | `$8510` | unsupported indexed A store | 57 | 61 |
| PC-21 | 6,114 | `$89D1` | unsupported indexed L load | 57 | 61 |
| PC-22 | 6,533 | `$88FF` | unsupported indexed immediate store | 57 | 61 |
| PC-23 | 78,197 | `$0DB2` | unsupported INC IY | 69 | 73 |
| PC-24, legacy bounded watch | 150,000 | `$84A1` | **instruction budget** | 81 | 85 |
| PC-25, opt-in extended collision watch | 300,000 | `$81E1` | **instruction budget** | 106 | 110 |

**Neither budget stop is an unsupported opcode.** At the PC-24
150k limit, the original mapper has slot1=physical bank1 and
slot2=physical bank2; the PC-25 300k limit has the same mapping.
There were **zero mapper-qualified original bank-1 collision CALL
events** in both windows, despite natural IRQ and VBlank progress.

The **bank-6 `$9932` sprite producer** was watched only in the
legacy PC-15 window of 150,000 steps, where it was not reached.
PC-25 extends collision research only; it **does not** establish
absence of sprite production beyond 150,000 steps.

The source listing at fixed bank `$0DCC` contains
`CALL $476C`, the candidate bank-1 collision setup.
That is a *static disassembly fact*, not evidence of entry or
a live player, since neither passive watch observes it.

## Reproducibility / CI evidence

On the PC-25 implementation SHA `d4db4fd`:

- [Native C11 startup/VDP/sound CI](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38829100821):
  **30/30 CTest**, PC-12 legacy watch (150k), PC-15 sprite watch
  (150k), PC-25 collision watch (300k), all source checkers pass.
- [Source integrity](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38829100806):
  PASS.
- [SMS/GG adapter](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38829100835):
  PASS.

PC-25 invocation (with locally rebuilt ROM; never ship it):

```sh
python3 Ys/tools/build_system_m10.py --check --out /tmp/ys-pc25.sms
cmake -S native -B build-native -DCMAKE_BUILD_TYPE=Debug
cmake --build build-native --parallel
ctest --test-dir build-native --output-on-failure
./build-native/ys-native-timed-rom /tmp/ys-pc25.sms \
  --pc25-collision-watch /tmp/ys-pc25-source.json
python3 native/tools/verify_pc25_collision_watch.py \
  /tmp/ys-pc25-source.json
```

The original `--pc12-watch` and `--pc15-sprite-watch` remain
unchanged at 150k/90-extra-VBlank ceilings with their own unchanged
validators. PC-25 is an opt-in **separate 300k/120-extra-VBlank**
research horizon, not a relaxed release test or gameplay claim.

## Stop decision / concrete next evidence needed

The validated interpreter is no longer blocking the sampled source
continuation with an unimplemented opcode. Increasing unpressed-input
budgets again without a hypothesis or independent oracle would not
authenticate gameplay and may simply sample more of the same timed
sound/intro loop.

The next independently justified task needs **one** of:

1. A hardware or trusted-emulator trace of the authentic cartridge
   through title-to-gameplay, including actual controller/pause inputs,
   mapper bank snapshots and Z80 PC/IRQ timing for comparison; or
2. Independently derived and verified original title/controls dispatch
   context that identifies a legitimate progression event. Input
   replay can then be defined as an explicit sourced test rather
   than silently injecting a fabricated scene or player state.

Until that evidence is available, **do not** force a source PC, map
bank6, insert collision calls or synthesize controller activity
to make an Alpha gate appear to pass.

**M45 is still the verified Development release.** All five
original-game Alpha gates remain false, including live controls
and interactive gameplay. Feature PR #3 remains draft/unmerged;
the native PC prototype is synthetic and does not authenticate
the original Ys game.

