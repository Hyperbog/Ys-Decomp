# M25 — Source-backed state-table dispatch and staging buffer copy

The native C11 interpreter's *next* acceptance target is PC=$0B22, before
executing the first palette/tile nibble-processing routine. This is not a
title-screen or gameplay milestone.

## Original control flow

Recovered instruction and table source:
- `Ys/src/wholebank00/bank00_complete.asm`: bank 0 dispatch table at
  physical `$00D4`, whose first two little-endian words are
  `$00FC` and `$0C4A`.
- `Ys/src/phase16/bank00_symbolic.asm`: address-annotated Z80 instructions
  used below.

| PC | Source behavior |
| --- | --- |
| `$00C4` | Copy `$C018` into `$C031`, load state `$C01F`, dispatch with `RST $08` |
| `$0008` | Index 16-bit ROM table at HL by A*2, then `JP (HL)`; `RST` pushed `$00D1` |
| `$00FC` | In startup state 0, write `1` to `$C01F`, then `RET` |
| `$00D1` | Jump back to `$00C4` |
| `$0C4A` | State 1 calls `$0A5B` (start of initial scene preparation) |
| `$0A5B` | Calls `$0A80` |
| `$0A80` | Calls `$0AE8` |
| `$0AE8` | Calls work-RAM staging copy `$0B10`, then XOR A and call `$0B22` |
| `$0B10` | Copy 32 bytes `$C160-$C17F` to `$C530-$C54F` with 32 `LDI` iterations and register-preserving loop |
| `$0B22` | **Stop before executing** nibble-processing code containing Z80 `RLD` |

## C11 changes

`native/z80.c` implements `ED 6F` Z80 `RLD` with fail-closed writes
to ROM and the documented result flags: carry is preserved; sign, zero,
parity and undocumented 3/5 are derived from the new accumulator; H/N clear.
This instruction is a prerequisite for executing `$0B22`, but that routine
is not included in the M25 real-ROM acceptance boundary.

`native/test_z80.c` uses source-encoded, non-cartridge fixtures of
`$00C4`, `$0008`, `$00D4`, `$00FC`, `$0C4A`, `$0A5B`,
`$0A80`, `$0AE8` and `$0B10`. The fixture feeds **nonzero** source
bytes into `$C160`, checks all 32 copied bytes, state `$C01F`,
dispatch return addresses and the stack shape at `$0B22`. Separate
`RLD` tests cover nibble rotation, carry/overflow flags and ROM write
rejection. The unit tests require no source reconstruction.

`native/trace_boot.c` exercises those same dispatches using the 256 KiB
ROM rebuilt from *committed source*, following one deliberately injected
IM 1 VBlank event and the first complete ISR return (M24). No handler,
bytes, state, input or Z80 stack are modified to bypass game code.
Expected endpoint: `PC=$0B22`, `SP=$DFE6`, `C01F=1`.

## Verification policy

Fast six-suite CMake/CTest runs on routine native-only changes. The
ROM-dependent check is explicitly gated behind manual
`workflow_dispatch` with `rom_trace=true` or a commit message marked
`[rom-check]`. The established original ROM digest is
`02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
Neither the original ROM assets nor original decompilation files are committed
or modified by this milestone.

## Remaining work

`$0B22` nibble transformation, subsequent VBlank events and scene loading,
actual VDP frame generation, sound synthesis, live inputs and a playable
frontend are not implemented. The *dispatcher has started*, but normal
title-screen rendering and main-loop operation have not been shown.
