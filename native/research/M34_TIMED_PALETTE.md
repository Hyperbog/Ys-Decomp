# M34 — Timed Ys dispatcher and initial palette-nibble processing

## Original source path

After M33's first frame-wait completes naturally at `PC=$00C4`
(23,583 Z80 instructions, three accepted maskable interrupts),
the original startup's state dispatcher executes the following
bank-0 code in `Ys/src/phase16/bank00_symbolic.asm`:

| Original Z80 PC | Source behavior |
| --- | --- |
| `$00C4-$00D0` | Read `$C018`/`$C01F`, dispatch through original `RST $08` table |
| `$00FC-$0101` | First dispatcher state sets `$C01F=1` and returns |
| `$0C4A` | Second dispatcher state begins `CALL $0A5B` |
| `$0A5B` | Begin video, palette and sound initialization |
| `$0A80` / `$0AE8` | Initial palette setup, including staging callback `CALL $0B10` |
| `$0B10-$0B21` | Copy 32 source bytes from WRAM `$C160` to `$C530` using `LDI` |
| `$0B22-$0B4D` | Transform 32 packed palette bytes using the authentic Z80 `RLD`, `SUB C`, `RRCA`, `RLCA`, and `DJNZ` loop |
| `$0AEF-$0AF4` | Set `$C02C=1`, load `B=3` for initialization delays |
| `$0AF6` | First palette-init `CALL $0BC5` wait, intentionally **not yet executed** |

The timed interpreter extends only the verified Z80 subset:
`SUB r` opcodes `$90-$97` (correct SZ53/H/PV/N/C flags),
`RLCA` (`$07`) and `RRCA` (`$0F`) with 4 T-states,
documented carry behavior and S/Z/PV preservation. Existing `RLD`
timing remains 18 T-states and byte writes go through the mapper.

## Acceptance tests

`native/test_timing.c` tests subtract with borrow, signed overflow
without borrow, rotations with F3/F5 and carry, and executes a
**byte-identical** ROM-free `$0B22-$0B4D` 32-iteration nibble loop
over synthetic WRAM. Tests require the loop to return naturally
to `$0AEF`, preserve `AF`, advance HL by 32, exhaust B, and
avoid writes outside `$C160-$C17F`.

`native/trace_timed.c` continues the actual 256 KiB cartridge
**from the identical M33 CPU/VDP/sound/mapper state**, with no
patched PC, stack, CRAM, controller input or clock. It asserts:

1. Original startup transitions from state 0 to 1 and selects
   `$0C4A`, with `$C01F=1`, `SP=$DFEE` and slot-2 ROM bank 2.
2. The first palette staging call returns to `PC=$0B22`, with
   `HL=$C180`, `SP=$DFE6`, `BC=0`, and the saved 32 bytes
   duplicated at `$C530-$C54F`.
3. The actual `RLD/SUB/rotate` loop finishes at `PC=$0AF6`
   with `B=3`, `HL=$C02C`, `$C02C=1`, wait flag `$C021=0`
   and no unplanned extra IRQ.
4. The optional `--frame` image exports the authentic VDP state
   from this **bounded initialization checkpoint**; it is not
   a rendered title or live game frame.
5. Any unsupported opcode/port, wrong timing, unexpected source
   return or budget exhaustion fails the gated acceptance run.

## Build and stage policy

One `[rom-check]` commit triggers reconstruction of all 16
source-only banks (256 KiB, no ROM fallback), M25's separate
legacy injected-VBlank trace, and the continuous M29-M34 timed
trace. Expected unchanged ROM digest:

`02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`

No `Ys/**` sources or original ROM bytes change here.
Windows `START_HERE.cmd` retains the persistent synthetic test
viewer and real-ROM static PPM option. All gameplay promotion
gates stay false: the next significant work is to run the
source's `$0AF6` palette-delay waits and actual title-graphics
loading with input and video connected to live frame presentation.

## Verified continuous ROM execution

Commit [af5ab13b120d](https://github.com/Hyperbog/Ys-Decomp/commit/af5ab13b120dcb9226e890e4af74c80aa78d2fa9)
passed the gated full-source reconstruction in
[GitHub Actions run 38348967643](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38348967643).
The original 256 KiB ROM remained source-only, with no fallback and
the established SHA-256:

```text
M10: 16/16 source-only banks, 262144 bytes; ROM fallback=0
SHA256=02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9
PASS original Ys frame-wait completed to $00C4: steps=23583 T-states=409651 IRQ=3 VBlank=7 VRAMwrites=192 PSGwrites=44
PASS timed Ys state 0 -> 1 dispatch: PC=$0C4A steps=23615 SP=$DFEE C01F=01 IRQ=3
PASS timed Ys palette staging: PC=$0B22 steps=23755 T-states=411212 SP=$DFE6
PASS timed Ys first palette nibble transform: PC=$0AF6 steps=24468 T-states=416854 palette_steps=713 IRQ=3 VBlank=7
Stop BEFORE $0AF6 CALL $0BC5 palette delay; no title/gameplay.
PASS authentic timed VDP image: 147471 bytes
```

The native C11 suite passed 13/13 tests. The Windows Release
build passed 14/14 native tests and 8/8 Python packaging tests;
the Linux and macOS Development archives also passed 13/13
native tests and 8/8 packaging tests. Full cross-platform builds:
[run 38348967882](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38348967882).

**Next target:** advance actual `$0AF6 CALL $0BC5` and
its subsequent palette-init wait iterations, then reach the
source VRAM/title pattern transfer, and finally drive the
Windows surface with a continuous true game frame sequence.
Until then, all Alpha promotion gates remain blocked.
