# M38 — Original Ys 1792-byte name-table VRAM initialization

## Verified source instruction path

This is a bounded continuation from M37's original cartridge
`PC=$0A77`. In `Ys/src/phase16/bank00_symbolic.asm`:

| Bank-0 CPU PC | Original code | Meaning |
| --- | --- | --- |
| `$0A77` | `LD DE,$7800` | VDP VRAM data port at address `$3800` |
| `$0A7A` | `LD BC,$0380` | 896 zero words |
| `$0A7D` | `JP $06D4` | **Tail jump**, not a CALL |
| `$06D4` | `RST $28` | Original two-byte VDP control command |
| `$06D5-$06E7` | `LD A,C / OR A / INC B / ... / OUT($BE),A ... DJNZ / RET` | Write two zero bytes per word |
| `$0C4D` | `LD A,$02` | Resume the original `$0C4A CALL $0A5B` caller |

`$0A80` is physically adjacent but **not** the execution return
address: `$0A7D` performs a tail `JP` into the shared VRAM writer
and its RET returns to the saved `$0C4D` stack address.

The `$06D4` loop uses one partial inner loop for C=$80 plus
three full C=$100 cycles from the original B=$03 upper count,
resulting in **896 complete words / 1792 byte output writes**,
nominally filling VRAM `$3800-$3EFF`.

## ROM-free unit acceptance

The `native/test_timing.c` test
`test_m38_source_name_table_clear_tail_return` executes exact
source instructions in a synthetic bank-0 ROM and a real VDP
port state:
- Makes source bank-0 `$0A77` tail jump to `$06D4`.
- Sets a genuine saved return `$0C4D` on the Z80 stack.
- Requires exactly 896 writes at each of the two `OUT ($BE)`
  opcode sites, VDP byte-write count 1792, VRAM `$3800-$3EFF`
  all zeroed, and the final VDP pointer `$3F00`.
- Asserts BC=0, DE=$7800, SP unwinds by 2, with natural return
  `PC=$0C4D`.
- No synthetic IRQ is necessary in the unit test (frame IRQ
  disabled); this isolates the source helper and its own timing.

## Gated source-ROM continuation

`ys-native-timed-rom` starts at cold reset and preserves all M25
and M29–M37 checks. The M38 addition steps through the same
`$0A77` source routine to original `$0C4D` under the
emulated 228-T-state scanline clock. If VBlank arrives:
- The game's real IM1 `$0038` ISR is executed normally.
- No manual VBlank injection, PC change, mapper reset or SRAM
  write is permitted.
- Every accepted IRQ is verified at its actual status-bit and
  entry PC, and its suspended source PC is logged.
- The two original `OUT` opcode sites must be visited exactly
  896 times each even if interrupts interleave.
- Require at least 1792 new VDP data writes, no unexpected
  CRAM writes, mapper preservation and source stack unwind.
  An ISR may perform additional VDP/sprite writes and modify
  the shared VDP address; those effects are NOT overwritten
  to fake a perfect contiguous `$3800-$3EFF` fill.
- Optional `--frame` captures the authentic VDP state on
  return at `$0C4D`.

The expensive source-only ROM rebuild is gated by an explicit
`[rom-check]` commit; native C11 fast and package CI run for
ordinary code changes. Expected 16-bank 256 KiB SHA-256 remains
`02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.

This remains a ROM-free Development diagnostic package and a
bounded real-ROM trace, not a playable Ys game or a rendered
title. The optional separate SMS/GG Recomp adapter now merged
into the repository performs only generated-C provenance checks;
it does not yet link or execute a statically recompiled runner.
All Alpha/Beta/Final release gates remain false.

## Authentic ROM checkpoint achieved

[Full source-ROM CI run 38425466962](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38425466962)
verified the unchanged 16-bank, 262,144-byte ROM and all
13 strict native test suites:

```text
SHA256=02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9
PASS original Ys first VRAM clear to $0A77: zero_bytes=64 R8=$00 R9=$00 steps=97144 T-states=1129966 IRQ=15 VBlank=19 VRAMwrites=2561
PASS original Ys name-table clear natural IRQ: savedPC=$06DE IRQ=16 VBlank=20 written=727/726
PASS original Ys 1792-byte name-table VRAM clear: PC=$0C4D words=896 steps=104746 T-states=1194146 IRQ=16 VBlank=20 VRAMwrites=4353
PASS authentic timed VDP image: 147471 bytes
```

The IRQ arrived between the original low/high byte writes.
The native runtime kept the resulting VDP address state and
allowed the source loop to complete without artificially
reprogramming the VDP. A return to `$0C4D` is still early
initialization, not a title or playable game.
