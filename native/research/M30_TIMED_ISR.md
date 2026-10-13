# M30 — First naturally timed Ys VBlank ISR return

## Source-backed target

Starting from cold original Ys SMS cartridge reset in the M29
`ys-native-timed-rom` diagnostic, preserve all CPU, mapper, VDP,
sound and clock state after the automatically generated first VBlank.
Continue through the **actual source bank-0 interrupt service routine**
until its first return to the interrupted PC `$0764`.

Source of control flow: `Ys/src/phase16/bank00_symbolic.asm`.

| Source address | Effect |
|---|---|
| `$0763` / `$0028-$0030` | Initial VDP setup invokes RST $28 to write control ports; EI returns with no pending interrupt yet accepted |
| `$0764` | Source PC suspended by the first automatically accepted IM1 interrupt |
| `$0038-$003B` | PUSH AF, read VDP status via IN A,($BF), OR A |
| `$003C-$003F` | Signed/status selection uses JP P,$0540 versus JP $0102; a latched VBlank selects $0102 |
| `$0102-$0106` | Load `$C021`, OR A, and JR Z,$0148 because first setup has not begun the `$0042` wait |
| `$0148-$015C` | Preserve primary and alternate general registers, IX/IY, mapper-bank and mapper-control selectors |
| `$015D-$0166` | Set temporary ROM mapper bank 2 and invoke actual bank-2 `$8000` audio-frame handler |
| `$0169-$018F` | Inspect initialized VDP flags, potentially adjust video-control register writes |
| `$018F-$0199` | Write `$C10F=1` and restore prior ROM mapper control and slot-2 bank |
| `$019C-$01A9` | Restore every saved primary and alternate general register plus IX/IY |
| `$01AA-$01AB` | EI, RET to interrupted `$0764` |

## Strict acceptance conditions

This routine executes under automatic T-state-based VBlank generation.
No direct IRQ injection, no manual VDP status changes, no hardcoded
jump, no stack rewriting and no CPU/VDP timing reset are permitted.

The new source-ROM trace stops **before executing** `$0764`:
- Exactly one accepted IM1 IRQ; first interrupt originally returns to
  `$0764` (as established by M29).
- All primary/alternate AF, BC, DE, HL and IX/IY registers equal the
  snapshot taken immediately after the first IRQ was accepted.
- SP restored to the snapshot interrupt stack pointer **plus 2** (the
  hardware-pushed PC is removed by source RET).
- Mapper control and selected physical ROM slot-2 bank unchanged from
  the interrupt snapshot.
- `$C021=0`, `$C10F=1` after the zero-state branch.
- VDP status was acknowledged, without a second IRQ or any synthetic
  status-port event; clock reports five generated VBlank entries.
- Bound source ISR execution to 4,000 instructions, fail closed on
  unexpected opcode/port/status or mismatched state.

## Regression tests

`native/test_timing.c` encodes the source `$003B-$0041` branch,
the `$0102-$0107` zero-state check and the save/map/sound-call
prologue `$0148-$0168`. It asserts that the expected `$8000`
call was reached, the stack contains the correct `$0169`
return address and saved mapper selectors, and the mapper switches
into the required bank. This fixture is ROM-free and does **not**
execute the actual bank-2 sound code.

The single gated M10 reconstruction plus two continuous source-ROM
traces is invoked only by a commit message marked `[rom-check]`
or explicit `rom_trace=true` workflow dispatch. The original
ROM digest must remain
`02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.

## Limitations

A return to `$0764` is the first initial VDP interrupt only. The
rest of VDP initialization at `$0764`, the startup wait at `$0042`,
subsequent automatic VBlank events and the state dispatch/title
screen are **not** yet verified under the timed ROM. A completed
ISR is not yet a playable PC build. Alpha/Beta/Final release gates
remain unpassed.
