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
and strict bounded stop. Real results must be observed
separately in CI before pinning a final golden.

## Authentic game limitations

This is **original-cartridge Z80 execution research** rather
than independently confirmed hardware/emulator equivalence.
A mapped source sprite-handler `$9966` hit is not proof
of player identity or sprite generation; the original
bank6 `$9932` producer has not been observed. The native
PC game window still contains a synthetic two-room demo.
No original-game Alpha gate is promoted, and the
`Ys` M45 release branch remains unchanged.
