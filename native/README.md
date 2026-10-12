# Ys — native C11 runtime, foundation checkpoint

This is a **separate, non-playable native runtime** alongside the ROM-identical
Z80/Python decompilation. It does not replace the cartridge build or alter any
existing M10–M17 tests, signatures, or golden source data.

## Build and test

```sh
cmake -S native -B /tmp/ys-native-build
cmake --build /tmp/ys-native-build
ctest --test-dir /tmp/ys-native-build --output-on-failure
cd Ys && python3 tools/build_system_m10.py --check --out /tmp/ys-source-built.sms
/tmp/ys-native-build/ys-native-probe /tmp/ys-source-built.sms
```

The `ys-native-probe` command checks file size and Sega header only; it is **not**
a cryptographic ROM validator or CPU emulator. The existing M10 builder verifies
SHA-256 `02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
No ROM or extracted game asset is committed here.

## Implemented boundary

- Immutable caller-owned 256 KiB ROM, initial slots 0/1/2.
- Fixed bank-0 `$0000–$03FF`; banked slot 0 `$0400–$3FFF`, slot 1
  `$4000–$7FFF`, and slot 2 `$8000–$BFFF`.
- 8 KiB console RAM mirrored at `$E000–$FFFF`.
- Sega mapper writes `$FFFC–$FFFF`, including visible RAM write-through,
  slot-2 cartridge RAM bank selection, optional `$C000–$FFFF` cartridge RAM,
  and delayed bank-shift behavior.
- The 32 KiB cartridge RAM is volatile and zero-initialized for testing;
  persistence and hardware detection are not yet implemented.

### Deliberate limitations

No instruction execution, interrupt/timing implementation, CPU ports, VDP,
PSG/FM, controller support, BIOS emulation, ROM-write hardware, cartridge RAM
saves, or graphics display. The initial bank layout is a documented assumption
matching the Ys startup mapping setup; mapper revision reset states vary.
The unusual `$FFFC` bit-4 cartridge RAM mode is represented as a simple map;
real hardware also requires bus control through port `$3E`. Bank shifting on
256 KiB ROMs is modeled with the 16-bank wrap; actual shifted-bank behavior
is mapper-revision dependent.

The next checkpoint is a fail-closed Z80 CPU core with reset, register/flag,
stack and memory operation support; test instruction and mapper traces against
the original M13–M17 evidence before adding VDP and SDL3.
