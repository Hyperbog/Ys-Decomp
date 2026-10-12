# Ys native C11 runtime — Phase 3: SRAM startup + bounded VDP I/O

**This is not a playable native port.** The original Z80/Python source-only
cartridge reconstruction (M10–M17) is untouched and remains authoritative.
No commercial ROM bytes, assets or executable binaries are committed.

## Configure, compile and verify

```sh
cmake -S native -B /tmp/ys-native-build -DCMAKE_BUILD_TYPE=Debug
cmake --build /tmp/ys-native-build --parallel
ctest --test-dir /tmp/ys-native-build --output-on-failure

python3 Ys/tools/build_system_m10.py --check --out /tmp/ys-source-built.sms
/tmp/ys-native-build/ys-native-trace /tmp/ys-source-built.sms
```

The source builder validates SHA-256
`02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
The native tracer checks image length/header, *not* the ROM hash. Always feed
it the independently source-built, SHA-verified image.

## Continuous reset checkpoint

From actual Ys reset vector `$0000`, execute through `$079A`, the SRAM
setup/check routine, its return at `$00A5`, and the WRAM-clear loop.
Stop at `$00BB`, **before** the banked subroutine `CALL $8803`.
Check that bank 0 has initialized mapper slots 0/1/2, restored control `$80`,
copied the 24-byte ROM identifier `$0782-$0799` to SRAM `$8010-$8027`,
cleared the rest of the observed SRAM/WRAM regions, and set expected stack
and RAM values. This executes both long Z80 LDIR loops instead of treating
them as startup shortcuts.

## Separately seeded VDP initializer

The source-backed `$0749` routine is the *next available isolated hardware
test*, not a claim that continuous execution reaches it yet. With a seeded
return address on the stack, run real `$0749-$0767` ROM opcodes through the
Bank 0 RST `$28` VDP helper. Check that 11 VDP registers receive the 11-byte
table at `$0768`, the same values appear at console RAM `$C010`, 24
control-port bytes were written, and one CRAM byte at `$10` was set to zero.

`native/sms_vdp.c` implements a register/VRAM/CRAM port model, not rendering:
- Two-byte low-first command latch and control read latch reset.
- VDP command modes 0 (VRAM read/prefetch), 1 (VRAM write),
  2 (VDP register), 3 (CRAM write); mirrored ports `$80-$BF`.
- 16 KiB VRAM, 32-byte SMS CRAM, 16 register storage locations.
- Data-port address increment/wrap and basic read-ahead buffer.
- Read-to-clear VDP status; no VBlank/IRQ generation or timing.

The base behavior follows SMS Power's Control Port and I/O Port Map:
https://www.smspower.org/Development/ControlPort
https://www.smspower.org/Development/IOPortMap

## Known limitations

The Z80 interpreter is an intentionally fail-closed partial implementation.
Its supported instructions are extended with `DJNZ`, `LD (DE),A`,
`LD A,(DE)`, `OR n`, `AND n`, `CP (HL)`, `RST $28` and VDP
`OUT (n),A` / `IN A,(n)`. The other instructions from Phase 2 remain.
Ports other than VDP fail closed; neither PSG/FM sound, controllers, port
`$3E`, nor CPU I/O by `(C)` is implemented. The full Z80 prefix, interrupt,
alternate-register, undocumented flag and cycle sets are unfinished; EI
interrupt deferral and LDIR's undocumented flag bits are approximate.
VDP frame timing, sprite status generation, H/V counters, palette rendering,
tile renderer, IRQ delivery, CPU cycles, and SDL3 frontend are absent.

The Sega mapper assumptions inherited from Phase 1 remain in place; ROM
write-enable, SRAM persistence, and full mapper-revision behavior are not
validated. The next trace must cover the banked `$8803` initializer before
we can call `$0749` part of a *continuously observed* boot.

## Regression gates

`ctest` now covers independent bus, VDP, and Z80 unit suites. GitHub
Actions compiles with strict warnings, runs all three, reconstructs the full
source ROM using M10 and invokes `ys-native-trace` with that ROM. Existing
M13–M17 CI continues independently.
