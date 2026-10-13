# M23 source-backed first VBlank sprite and controller checkpoint

## Evidence and boundaries

This note records the ROM-derived *execution goal*, not an assertion that the
full title screen, rendering, or frame scheduler already works.

Sources from this repository, all under `Ys/src/phase16/bank00_symbolic.asm`:

| Z80 PC | Source opcode path | Expected behavior |
|---|---|---|
| `$01B4` | `CALL $0427` | First state-handler sprite-attribute transfer |
| `$0427-$043E` | VDP control writes, `CALL $04BF`, second VRAM command | Set VRAM writes to `$3F00` then `$3F80` |
| `$04BF-$053E` | 64 literal `OUTI` opcodes | Copy `$DD00-$DD3F` to `$3F00-$3F3F` |
| `$043F-$053E` | 128 literal `OUTI` opcodes | Copy `$DD40-$DDBF` to `$3F80-$3FFF` |
| `$053F` | `RET` | Finish the unrolled block |
| `$01B7` | `JP $03E8` | Evaluate work-RAM sprite update flag |
| `$03E8-$03EC` | `LD A,($C02C); OR A; RET Z` | First reset state: zero flag, return to `$0125` |
| `$0125-$012F` | `EI`, state comparison, `CALL $0773` | Reenable IRQ, sample controller |
| `$0773-$0781` | `IN A,($DC)` + active-low processing | Idle-high input `$FF` stores zeros to `$C01B/$C01C` |
| `$0130-$0137` | Map bank 2 and `CALL $8000` | Stop **before** Bank 2 sound-frame update |

### Test fixtures

`native/test_irq.c` uses a synthetic source-encoding fixture for the 192
unrolled `OUTI` operations with nonzero test-pattern sprite bytes. It asserts
both regions of VDP VRAM, command/address state, returns and stack depth.
The source-backed `$0773` fixture checks both a pressed controller bit and
an unpressed controller, via the `sms_input.c` active-low port snapshots.
`native/test_input.c` checks default input state and port validation.

`native/trace_boot.c` executes the **source-built actual cartridge** when
explicitly invoked. Starting from reset, its existing checkpoints pass through
the bank-2 sound initializer, initial VDP programming and first manually
injected IM 1 VBlank interrupt, then add the 192 sprite data bytes and the
idle controller sample. A pass requires the 192 VDP write bytes to match the
original WRAM sprite buffers and PC to be `$8000`, with stack holding
`$0138` as the return address.

### Reconstruction policy

Routine CMake and CTest verification **does not rebuild the cartridge**.
Only explicit `rom_trace=true` workflow invocation or commit marker
`[rom-check]` runs the M10 source reconstruction and the complete native trace.
The check is warranted once for this new ROM-dependent execution boundary.
Do not commit binary ROM contents, source-extracted proprietary assets, or
speculative playability statements.

### Deliberate limitations

No automatic frame/IRQ scheduler, actual game input polling, rendering,
sound synthesis, SDL3 frontend, or completed main-loop execution exists.
`$8000` is explicitly unexecuted. The controller model supplies a fixed
snapshot and does not emulate the entire SMS port map.
