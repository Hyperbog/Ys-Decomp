# M46b — Original Ys VDP register-1 gate verified

## Continuation after M46a

Source: `Ys/phase5/code.lst`, `Ys/phase6/code.lst`, and fixed-bank
`Ys/src/phase16/bank00_symbolic.asm`. The M46a original-ROM execution
ends before `$0C9C`; the next `CALL $0AA7` enters:

```z80
$0C9C CALL $0AA7
$0AA7 LD A,($C011)
$0AAA LD E,A
$0AAB LD D,$81
$0AAD SET 5,E
$0AAF RST $0028
$0AB0 IN A,($BF)
$0AB2 CALL $0BC5     ; M46b stops BEFORE this instruction
```

The original `$0028` helper disables interrupts, writes E then D to
VDP control port `$BF`, reenables interrupts, and returns. With D=$81,
the command updates VDP register 1. The following status-port read
acknowledges/clears the latched VDP status.

## Implementation

- `native/z80.c` now implements the Z80 `CB SET b,r` and
  `SET b,(HL)` instructions with unchanged flags; existing timing
  assigns 8 T-states for registers and 15 for memory.
- `native/test_timing.c` checks register and memory SET encodings,
  flag preservation and cycles, then runs the original bounded
  `CALL` / `RST` / VDP-write / `IN` instruction sequence with a
  synthetic bus and sentinels.
- `native/trace_timed.c --m46b` replays the original cartridge from
  reset through M45 and M46a, validates the exact source opcodes,
  executes 14 further instructions, checks each destination PC and
  nominal timing (119 T-states), VDP command count, register 1,
  status-read-to-clear, mapper/PSG/VRAM/CRAM invariants, interrupt
  counts and all 8 KiB of WRAM. The temporary return-address bytes
  remain in the CPU stack because the outer CALL has not yet returned.
- M45 default and the opt-in M46a `--m46-prefix` checkpoint remain
  unchanged; the ordinary `--frame` mode still exports M45's static
  VDP snapshot. Neither new mode changes ROM, CPU or mapper state to
  force progress.

## Gated original-ROM results

[GitHub Actions run 38482882309](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38482882309)
passed all 13 native C11 tests, reconstructed 16/16 16-KiB ROM banks
without fallback and produced the original SHA-256
`02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.

```text
PASS M45: PC=$0C92, 430886 instructions, 3579261 T-states
PASS M46a: PC=$0C9C, four more instructions, 40 T-states
PASS M46b original $0AA7 VDP gate to $0AB2:
  instructions=430904 T-states=3579420
  VDP-R1=A0 status-read=00 IRQ=56 VBlank=60
```

**Scope limit:** This is still a bounded Z80-interpreter source trace,
not a compiled static-recompiler runner or an interactive Ys program.
Neither actual title rendering nor Alpha gameplay is verified.
The Development release baseline and its promotion gates remain M45
until the project separately approves a new milestone.

## Reproduce

```sh
cmake -S native -B build-native -DCMAKE_BUILD_TYPE=Debug
cmake --build build-native --parallel
ctest --test-dir build-native --output-on-failure
python3 Ys/tools/build_system_m10.py --check --out /tmp/ys-m46b.sms
./build-native/ys-native-timed-rom /tmp/ys-m46b.sms --m46b
```

The next independent scope is to execute through original `CALL $0BC5`
and verify the resulting natural frame wait, then advance toward real
VDP tile/palette updates without overriding game or hardware state.
