# M37 — First original Ys VRAM clear and VDP scroll setup

## Source provenance

The continuous source-ROM trace verified in M36 stops at original
bank-0 PC=$0A5E after the 16-byte bank-7 cartridge transfer,
VDP R0=$26/R1=$A0 and sprite-Y terminator $D0 write.

The *unaltered* listing in `Ys/src/phase16/bank00_symbolic.asm`
continues as follows:

| Source PC | Operation |
| --- | --- |
| `$0A5E` | `LD DE,$8800` — VDP register 8 write command |
| `$0A61` | `RST $28` — actual VDP control-port pair |
| `$0A62-$0A63` | `INC D; RST $28` — VDP register 9 |
| `$0A64-$0A6A` | `XOR A`, clear scroll fields `$C018` and `$C019` |
| `$0A6B-$0A73` | `HL=$0000`, `DE=$4000`, `BC=$0020` |
| `$0A74` | `CALL $06D4` — source 16-bit VRAM fill helper |
| `$06D4-$06E7` | `RST $28`, write zero low/high word to port `$BE`, increment VDP address and loop 32 words |
| `$0A77` | Return to original caller; next longer `$7800` name-table clear is NOT executed yet |

The source VDP command `$4000` selects VRAM data-write mode at
address zero. Exactly **32 source 16-bit writes** clear VRAM
`$0000-$003F` (64 bytes) and leave the VDP write pointer at
`$0040`. Register 8 and register 9 are written with zero
by authentic `RST $28` control-port commands.

## Native assertions

`native/trace_timed.c` resumes the **same** CPU/VDP/memory/clock
state as M36 and executes original ROM opcodes using
`ys_sms_runtime_step_auto`. It requires:

- PC returns naturally to `$0A77` within 800 CPU instructions.
- Exactly 64 additional VRAM writes, zero additional CRAM writes,
  two VDP register writes (R8=0, R9=0).
- Actual VRAM `$0000-$003F` contains 64 zero bytes; VDP code 1,
  address `$0040`; source scroll WRAM `$C018/$C019=0`.
- Source stack pointer, ROM bank mapping and natural IRQ/VBlank
  counters stay unchanged across the short VRAM routine.
- Any unsupported opcode/port, false stack/mapper state or
  unexpected IRQ fails closed. No state patching or artificial
  VBlank is permitted.
- Optional `--frame` exports a 256×192 P6 image from the actual
  VDP snapshot at `$0A77`, not a live game.

The ROM-free unit fixture uses byte-exact bank-0 opcodes at
`$0A5E-$0A76`, `$0028-$0030` and `$06D4-$06E7`.
Its synthetic VDP is initialized with nonzero VRAM data to
prove the original commands genuinely clear 64 bytes.
The full continuous original source-ROM trace is checked
separately and **only** with `[rom-check]`.

## Limitations

This first 64-byte pattern-memory clear is not the title image.
The source next writes `BC=$0380` (896 words) beginning at
`$7800`, which may overlap an authentic VBlank interrupt.
That larger initialization and its ISR/VDP addressing must
be verified as a separate milestone. No native game window,
live gameplay input or actual title art is established by M37.
All Alpha/Beta/Final release gates remain unpassed.
