# M28 — Per-instruction T-states and automatic VBlank integration

**Development milestone, not a playable Alpha.** The emulator now knows
the nominal T-state count for its supported Z80 instructions and can
advance the SMS scanline clock at *each instruction boundary*. This is
a source-independent hardware-subsystem improvement; original Ys ROM
execution is still verified only through M25 at PC `$0B22` with an
explicitly injected VBlank event.

## CPU timing contract

- `ys_z80_step` updates `last_tstates` and `total_tstates` for
  successful instructions. Failed/unimplemented opcodes contribute **zero**
  time and retain a fail-closed status.
- `sms_runtime_step_auto` uses that measured duration to advance the
  NTSC/PAL scanline clock and automatically recognize enabled VBlank
  interrupts, respecting `IFF1`, interrupt mode and `EI` deferral.
- An acknowledged IM1 interrupt consumes **13 T-states** in addition to
  the completed opcode and pushes the interrupted PC. The VBlank status
  remains latched until the game reads the VDP status port.
- A halted CPU consumes **4 T-states per refresh step**, without executing
  instructions, until an eligible VBlank IRQ wakes it.
- Conditional `JR`, `DJNZ`, `CALL cc`, `RET cc`, and repeating `LDIR`
  have taken/not-taken or repeat/final timings. The supported `CB`,
  `DD/FD`, `ED`, I/O, register and memory instruction classes are
  covered. New interpreter opcodes require an explicit timing assignment.
- The existing `ys_sms_runtime_step(rt, tstates)` continues to accept
  caller-provided durations for M27 fixtures and external test harnesses;
  use `ys_sms_runtime_step_auto` for M28 CPU-derived timing.

This is *nominal* Z80 instruction timing. No VDP contention, scanline
counter readback, memory refresh quirks, line interrupts, or FM/PSG
synthesis has been modeled. Interrupt recognition is performed at the
completed instruction boundary.

## User-testable Development executable

After building or extracting a Development ZIP:

```sh
bin/ys-native-timing --check
```

The executable constructs a **synthetic ROM-free NOP/EI program**,
runs Z80 instructions against the automatically advanced NTSC frame clock,
confirms the first VBlank interrupt reaches `$0038`, and verifies the
status read clears the frame-pending bit. It requires no copyrighted ROM.
The existing `ys-native-frames` outputs synthetic animated PPM frames;
the optional SDL2 viewer continues to display synthetic patterns.

## CI and promotion

`native/test_timing.c` asserts exact cycles for arithmetic, indexed BIT,
RLD, memory access, conditional branches/calls/returns, LDIR repetitions,
unsupported-opcode failure, HALT refresh, EI deferral and IM1 entry.
`native/test_clock.c` continues validating the manually timed runtime.
The phase packager adds `ys-native-timing` on Windows, Linux and macOS.
All Alpha/Beta/Final promotion gates remain blocked.

**ROM reconstruction policy:** No `[rom-check]` is requested here;
no new original-ROM path is claimed. Full source rebuild and realistic
gameplay timing comparison should occur only when the timed execution
path reaches a new meaningful source-backed boundary and its exact
expected PC, stack and VDP state have been established.
