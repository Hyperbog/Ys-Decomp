# PC-41 — original Z80 carry-aware arithmetic and continued Ys trace

## Authentic source and previous checkpoint

PC-40's source-backed 300,000-iteration prefix, exact 525,358
original continuation boundary at **fixed bank 0 $1A0A**, and
mapped sprite/collision-adjacent site observation are preserved.
At that original boundary, the verified 256 KiB reconstructed ROM
has opcode **$88 = ADC A,B**; the older intentionally incomplete
native reference CPU stopped there as unsupported.

PC-41 adds the documented Z80 operations
`ADC A,r`/$88–$8F, `SBC A,r`/$98–$9F,
`ADC A,n`/$CE and `SBC A,n`/$DE.
These compute carry-in, half-carry/borrow, two's-complement signed
overflow, S/Z/3/5 and N/C from genuine CPU input values.
Register forms take 4 T-states, (HL) takes 7, and immediate forms
take 7. All reads use the existing mapped bus, without writing
ROM, controller state, VDP or other machine data.

The standalone native regression checks **all 256 × 256 × 2**
8-bit operand/carry combinations for both ADC A,B and SBC A,B:
**262,144** independently calculated register-state comparisons.
Additional (HL), A-self, and immediate operand tests exercise
signed overflow, wrap, half-carry, memory stability and documented
timing. The reference flags are computed by signed mathematical
result range checks and XOR-based nibble carries rather than
calling the implementation's flag helpers.

## Historical source-run invariant

The unchanged original ROM is executed from reset to M45, with
the same PC-34 opt-in original button-1 press/release schedule.
The longer existing PC-40 route audit still uses a maximum 600,000
post-M45 observation iterations, preserves its natural IRQ,
VBlank, mapper, RAM and controller changes and all bank-qualified
source-site observations.

At the EXACT pre-instruction continuation iteration **525,358**
(the former PC-40 unsupported stop), the new independent source
guard demands all previously observed CPU/program facts:

- Z80 PC $1A0A, IRQ 132, VBlank 136
- Mapper slot 1 = 1, slot 2 = 7; original $C01F = 6
- 40 bank0 $0427 uploader entry-site observations; other sprite watch counters 0
- One physical bank0 $26B6 entry and one bank1 $4773 entry
- No qualifying collision calls

The check is read-only. If any original state differs, the
source-only run FAILS; it never changes the CPU to satisfy it.
The original PC-40 golden checker remains usable independently;
the new `verify_pc41_route.py` checks the extended source run
using the same independently generated PC-34 prefix and verified
cartridge SHA. Its extended-run results will be golden-pinned
only after independent CI observation.

## Status and boundaries

This is original-source interpreter compatibility research;
it is **not** an independently confirmed emulator/hardware
trace, original-game native PC integration, verified player,
map traversal, animation or any original-game Alpha gate.
No original copyright ROM/media bytes are committed.
Development release M45 remains unchanged, and the PC-41 PR
must remain stacked, draft and unmerged pending all CI checks.
