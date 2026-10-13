# Native C11 M24 — First VBlank sound update and context restoration

## Scope

This milestone extends the prior source-backed continuous execution from
`$8000` (bank-2 first-frame sound update) to `$00C4` (the first instruction
after the bank-0 `CALL $0BC5` VBlank bridge). The event is **one explicitly
injected IM 1 interrupt**, not video-timed automatic VBlank generation.

## Source-backed execution path

All instructions below are read from committed decompilation sources in
`Ys/src/phase11_roundtrip/bank02.asm` and
`Ys/src/phase16/bank00_symbolic.asm`.

| PC | What the original code does |
|---|---|
| `$8000` | Switch register banks, inspect sound mode `$DE60`, call `$8067`, `$8080`, `$80C0`, `$81D9` |
| `$8067` | If timer `$DE61` is zero, return without changing channels |
| `$8080` | Inspect three command slots at `$DE64-$DE66`; idle slots have bit 7 clear |
| `$80C0` | With timer `$DE6A=0`, return |
| `$81D9` | With command `$DE63=0`, jump to `$8803` for PSG/FM re-initialization |
| `$8016-$8042` | Inspect mode `$DE60=0` and select six-channel FM path |
| `$8042-$8066` | Scan six inactive IX-relative channel entries at `$DEAF`, step by `$20`, skip callbacks when bit 7 is clear |
| `$0138` | Test second input port `$DD`; for default unpressed state `$FF`, clear `$C021` and `$C10F`, pop AF and return from IRQ |
| `$0049-$004C` | Re-check the cleared VBlank wait variable and return to `$0BDC` |
| `$0BDC-$0BEE` | Restore mapper bank 2, IX/IY, alternate and main register sets, return to `$00C4` |

This execution path assumes the **actual reset state already verified**
through M23; no audio channel state or game mode is hand-seeded in the
continuous ROM run. The input device supplies idle-high `$DC/$DD=FF`
snapshots. No PSG/FM sample synthesis is implemented.

## New interpreter coverage

`native/z80.c` adds:
- `CB BIT b,r` for registers or `(HL)`, preserving carry and setting the
  usual Z/PV/H/S flags, with 3/5 from the tested operand.
- `DD/FD CB d BIT b,(IX/IY+d)`, including signed displacement and
  undocumented flag bits sourced from effective address high.
- `LD IX/IY,nn` and `ADD IX/IY,BC/DE/IX(or IY)/SP`, with 16-bit flags.
- `CP r` and conditional `CALL cc,nn` using the standard eight conditions.

Invalid or unimplemented indexed rotates/other prefixes fail closed. The
native CPU remains a partial interpreter; cycle counts and general hardware
timing are not modeled.

## Acceptance tests

1. Fast native CTest (six suites) covers zero-state scan at `$8042`,
   IX-relative memory BIT, carry preservation, signed displacement and
   conditional call behavior without rebuilding the cartridge.
2. The explicit ROM checkpoint traces from original source-built reset
   through sound update return `$0138`, controller test `$0049` and
   startup resume `$00C4`. The checkpoint compares every main and alternate
   Z80 general register plus IX/IY and SP with a snapshot before `$0BC5`.
3. Existing M10 source-only bank rebuild and SHA-256 check is invoked only
   when the native workflow is dispatched with `rom_trace=true` or the commit
   message includes `[rom-check]`. **Routine native commits do not rebuild.**

## Deliberate stop

The next opcode `$00C4` has **not** been executed in this milestone.
Although the initial VBlank IRQ and sound-update calls return, there is no
emulated frame scheduler, native display rendering, controller polling,
PSG/FM synthesis, or playable title screen. Continue from `$00C4` and
its RST $08 state dispatcher using fail-closed instruction expansion.
