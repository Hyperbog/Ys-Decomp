# M29 — First clock-generated VBlank in original Ys ROM

## Scope

The M28 clock counts nominal Z80 T-states for supported instructions. M29
joins it to *the actual* 256 KiB Ys Sega Master System ROM reconstructed
from decompilation source. The diagnostic starts from Z80 reset at PC=$0000
and stops at the original bank-0 interrupt service routine after its first
VDP status read at PC=$003B.

This is **not** title-screen initialization, a finished frame, audio playback
or interactive gameplay. It is also not a cycle-accurate VDP.

## Source evidence

`Ys/src/phase16/bank00_symbolic.asm`:

- `$0000`: `DI; IM 1; JP $0089`, authentic reset entry.
- `$00A5-$00B4`: DI and the 0x1E4F-byte block RAM initialization.
- `$00BB`: call bank-2 sound initializer `$8803`.
- `$00BE`: call bank-0 VDP initializer `$0749`.
- `$0749-$0767`: 11 initial VDP register writes, then `RST $28`;
  helper `$0028` uses DI / VDP control port writes / EI / RET.
- `$00C1`: startup calls its VBlank-wait bridge `$0BC5`.
- `$0038`: original IM1 handler starts `PUSH AF`, `IN A,($BF)`,
  `OR A` and jumps on status bit 7.
- `$0BC5`: preserves the primary and shadow CPU registers around the
  VBlank wait.
- `$0042-$004C`: wait flag setup, EI deferral, wait until IRQ clears flag.

The first interrupt can be recognized as soon as EI completes its
one-instruction deferral and VBlank status is pending; its return address
may lie within startup or the wait bridge, depending on accumulated CPU
time. **The test reads this return PC from the actual stack** and prints
it rather than substituting an invented return site.

## Acceptance

`native/trace_timed.c`:

1. Accepts **only a user-supplied 256 KiB cartridge image**, checks the
   `TMR SEGA` header, and allocates native mapper/VDP/sound/input devices.
2. Executes the actual reset vector through
   `ys_sms_runtime_step_auto`, accumulating nominal instruction T-states
   with NTSC 262×228 scanline timing. Nothing directly sets VBlank or
   calls `ys_z80_irq` from the trace.
3. Bounds execution to 1 million interpreter steps; any unsupported
   opcode or port fails closed with PC, T-state and scanline diagnostics.
4. Stops on **exactly the first accepted IM1 interrupt** with PC=$0038,
   VBlank status bit 7 set, VDP register 1 IRQ-enable bit 5 set,
   a valid RAM stack, and elapsed time after line 192.
5. Executes **source opcodes** `$0038 PUSH AF` and
   `$0039 IN A,($BF)`, confirms PC=$003B, bit 7 returned in A,
   pending VBlank status cleared, exactly one accepted IRQ.
6. Prints the interrupted PC taken from the real CPU stack. Does not
   claim completion of ISR, sound update, VRAM graphics or main loop.

`native/test_timing.c` has a ROM-free synthetic waiting program paired
with the original source-backed `PUSH AF / IN A,($BF) / OR A` ISR prefix.
This verifies natural frame IRQ recognition/acknowledgment and return-PC
stack behavior without a full ROM rebuild.

## Reconstruction policy

The fast six-device/timing suites and cross-platform packaging run without
rebuilding the ROM. **One meaningful source-backed ROM verification** is
requested for the new PC=$003B timed-VBlank checkpoint with `[rom-check]`.
The existing `ys-native-trace` still verifies its M25 manually injected
first VBlank and PC=$0B22 path, independently of the new mode.

Limitations: the VDP frame scheduler only models line-192 VBlank; CPU
nominal instruction T-states omit bus contention; no line interrupt,
NMIs, sound synthesis or physical display. The first timed interrupt
does not prove normal later-frame playability or an Alpha game build.

## Verified run — first timed source-ROM interrupt

Commit [733a6c702d88](https://github.com/Hyperbog/Ys-Decomp/commit/733a6c702d88c66eff4720483382ca0fba63611c)
executed the gated M10 source-ROM check in
[GitHub Actions run 38343836595](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38343836595):

```text
M10: 16/16 source-only banks, 262144 bytes; ROM fallback=0
SHA256=02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9
PASS timed actual Ys reset to first IM1: instructions=16379
T-states=338842 VBlank=5 IRQ=1 savedPC=$0764 PC=$003B SP=$DFE8
No injected IRQ; source ISR status acknowledgment verified.
```

**Significance:** the first accepted interrupt occurred at `$0764`,
right after the VDP register initialization's `RST $28` helper
(`$0763`, `$0028-$0030`). The prior DI/long memory initialization
had already consumed **five** scanline-clock VBlank events; the IRQ
became eligible when the helper's EI one-instruction delay ended.
The actual original ISR executed its `PUSH AF` and status-port read at
`$0038/$0039`, leaving `PC=$003B`, `SP=$DFE8`.
This differs from the existing manually injected M25 first wait IRQ
at `$0049`; **these are independent branches of the same authentic
startup** and should not be conflated.

All 13 strict native tests and the old M25 continuous trace
(`17,224` Z80 instructions, `PC=$0B22`) also passed.

**Next execution target:** continue from `$003B` through the
`$0102` handler, evaluate the zero-state branch to `$0148`,
and verify a full return to `$0764` without disturbing the
register snapshot. That requires further source-backed opcode coverage
and one new gated ROM check if the execution boundary advances.
