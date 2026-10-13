# M36 — Source bank-7 data transfer and VDP setup

## Original ROM program

The M35 continuous timed trace stops at bank-0 `PC=$0B00`.
The next original instructions from
`Ys/src/phase16/bank00_symbolic.asm` select
`MapperSlot2=7`, load `HL=$B9C3`, `DE=$C170`, `BC=$0010`,
and jump to the shared `$0B19-$0B21` LDI loop. The source copies
16 bytes of actual bank-7 cartridge data to `$C170-$C17F` and
returns to `$0A83` from the existing `$0A80 CALL $0AE8`.

At `$0A83-$0AA4`, original Ys then clears bits 4 and 6 in
VDP registers 0 and 1 respectively, writes both registers with
`RST $28`, updates `$C010/$C011`, prepares the sprite-Y
terminator data `$D0`, and tail-jumps to the original
`$0762 PUSH AF / RST $28 / POP AF / OUT ($BE),A / RET` helper.
The expected caller continuation is `$0A5E`, before subsequent
graphics initialization.

## Native acceptance

The `ys-native-timed-rom` diagnostic must execute naturally from
reset through the prior M29–M35 checks and:

1. Verify physical source bank 7 is mapped to CPU `$8000-$BFFF`;
   compare each of the 16 target RAM bytes to
   `rom[7*$4000+$39C3+i]`. Count exactly 16 original `LDI`
   iterations, with `HL=$B9D3`, `DE=$C180`, `BC=0`,
   source return `$0A83`, and correct stack unwind.
2. Continue the same CPU, RAM, mapper, VDP, interrupt and clock
   state through VDP registers 0/1 and the sprite marker write.
   Verify register values against WRAM `$C010/$C011`,
   VRAM `$3F00=$D0`, exactly one additional VDP data write,
   original return to `$0A5E`, and no unexpected IRQ.
3. Optionally export the **authentic VDP snapshot** at `$0A5E`.
   A P6 256×192 RGB image is not evidence of a title screen.
4. Reject unexpected opcode, port, mapper, stack or timer behavior;
   do not patch the game, inject interrupts or skip source routines.

The ROM-free timing suite includes a byte-accurate synthetic
bank-0 LDI sequence, a bank-7 cartridge data fixture, sentinel
checks, and tests for mapper selection and AF restoration.

## Constraints

No `Ys/**` source files were edited. The original ROM remains
256 KiB from all 16 source-only banks and has SHA-256
`02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
Source reconstruction remains gated with `[rom-check]`.

This is still a Development diagnostic, not live game graphics,
an interactive title screen, sound playback, or playable Ys.
The Windows GUI remains a synthetic test and static PPM viewer.
All Alpha/Beta/Final promotion gates remain false.
