# PC-42 — authentic Z80 R-refresh and maskable IRQ fidelity

## Original source reason for this milestone

The source-only original Ys reference Z80 path passed the exact
independent PC-41 original 531,478-iteration checkpoint and stopped
before executing fixed-bank0 **$141A**: **ED 5F**, `LD A,R`,
followed by `E6 0F`, `AND $0F`. This path cannot be executed
authentically by inventing the value of Z80 R.

PC-42 adds explicit `r` state to the native Z80 CPU. Each M1
opcode fetch increments **only the low 7 bits**, preserving bit7:
normal opcodes increment once, ED/CB/DD/FD prefixed opcodes increment
again for the second opcode fetch, and DD/FD CB d operation bytes
and displacement bytes are data reads, not extra refresh M1.
HALT's repeated 4-T-state refresh cycles each increment R,
**before** runtime clock advance may accept an IRQ. IM1 interrupt
acknowledge increments R once. The interrupt acceptance clears
**both IFF1 and IFF2**, while RETN and RETI continue to be
handled distinctly. The prior tests expecting an IFF2-preserving
maskable IRQ are corrected to the documented Z80 behavior.

Original `ED 5F LD A,R` takes 9 baseline T-states, copies the
post-fetch R into A, sets S/Z/3/5 from A and P/V from IFF2,
preserves C and clears H/N. This is the native reference
interpreter's documented timing model, without physical wait
states or assertions of hardware-exact cycle simulation.

## Authenticity and regression barriers

New independent test fixtures enumerate **256 × 2 LD A,R**
initial R/IFF2 combinations, prove refresh bit7 and low7 wrap,
execute ordinary, CB, DD, and DD CB prefixed opcodes, HALT
refresh without extra completed instructions, IM1 M1 and both
IFF clears, and RETN following a maskable interrupt.

The original source run remains exactly the existing opt-in
PC-34 button-1 schedule, at most **600,000 iterations** from
the M45 source checkpoint. PC-42 adds a second read-only
history assertion at **iteration 531,478**, in addition to
PC-41's 525,358 and PC-34's 300,000 historical guards.
It checks the original pre-LD A,R PC, physical mapper banks,
IRQ/VBlank events, source-selector values, sprite/collision
counters, and mapped source-site event totals. No CPU, R,
controller, RAM, mapper, VDP or IRQ state is forced or
modified to satisfy these checks.

The independent Python verifier checks original ROM SHA,
source opcode bytes, same PC-34 prefix, bank-qualified route
and an **exact golden measured in original-ROM CI**.

## Verified bounded original-ROM continuation

[Original-ROM CI run 38961300656](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38961300656)
passed the entire **600,000-iteration post-M45 continuation budget**.
All 34 native CTest cases, source-only PC-34 through PC-41
regressions and the exact pre-CPU-ADC/pre-LD A,R history guards
passed. The source reached original fixed-bank `$13F5` with
`EE 80` (`XOR $80`) and then fixed-bank `$1A77` `3F`
(`CCF`). Those documented Z80 operations were implemented with
exactly 7 and 4 T-states, respectively, original ROM opcode
byte verification, a further **65,536** exhaustive XOR immediate
vectors and **65,536** exhaustive CCF flag combinations.

The final source trace, independently golden-pinned, is:

| Observation | Recorded value |
| --- | ---: |
| Source controller continuation iterations | **600,000 / 600,000** |
| Natural stop | **Budget** — no unsupported opcode |
| Final CPU PC | **$0046** |
| IRQ acknowledgements | **144** |
| Original SMS VBlank events | **148** |
| Physical mapper slot1 / slot2 | **1 / 6** |
| Visible $C01F selector | **6** |
| Fixed-bank0 $26B6 selector entry | **1** |
| Physical bank6 $9966 handler entry | **13** |
| Physical bank1 $4773 route entry | **13** |
| Physical bank6 $9932 sprite producer | **0** |
| Qualified collision calls | **0** |
| Fixed-bank0 $0427 SAT uploader **entries** | **52** |

The extra 25 SAT uploader entry-site visits after PC-34 are
**not** independently proven to be 192-byte-complete SAT
transfers. PC-36 verified completion for 27 earlier uploads.
Do not convert 52 uploader entries into 52 frames or animated
sprites.

The bank6 $9966 location is in a recovered sprite handler
which conditionally calls $9932 based on $C198. Its **13
natural visits** do not demonstrate that conditional call was
taken, or a sprite was drawn. The original game is not yet
authenticated on external SMS hardware or independent emulator.

A verified continuation of the whole **600k bounded input
experiment** is an important original source execution
milestone. It is not world traversal, player movement,
an independently confirmed framebuffer, or one of the five
original-game Alpha gates.

## Authentic game limitations

This is **original-cartridge Z80 execution research** rather
than independently confirmed hardware/emulator equivalence.
A mapped source sprite-handler `$9966` hit is not proof
of player identity or sprite generation; the original
bank6 `$9932` producer has not been observed. The native
PC game window still contains a synthetic two-room demo.
No original-game Alpha gate is promoted, and the
`Ys` M45 release branch remains unchanged.
