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
cartridge SHA. Its extended-run results were subsequently golden-pinned
against a separately observed, passing original-ROM CI trace.

## Verified original-cartridge results

The strict C11 ROM-backed source run at
[GitHub Actions run 38950586233](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38950586233)
completed successfully with **34/34 native CTest cases**, including
all new exhaustive ALU and indexed bit instruction fixtures. Every
original PC-34/35/36/37/38/39 provenance check remained passing.

The original controlled input schedule reached the **exact**
historical 525,358-iteration PC-40 pre-ADC state, and its new
observed continuation ended naturally at **531,478** iterations:

| Observation | PC-41 measured |
| --- | ---: |
| Continued interpreter iterations after verified M45 | **531,478** |
| Natural next unsupported opcode | Fixed bank0 **$141A** |
| Exact original bytes there | **ED 5F E6 0F** |
| Opcode | **LD A,R** followed by **AND $0F** |
| Accepted IRQ / VBlank | **133 / 137** |
| Mapper slot 1 / slot 2 | **1 / 7** |
| Final raw **$C01F** selector | **6** |
| Bank0 $26B6 source entry | **1** |
| **Mapped bank6 $9966** source entry | **1** |
| Mapped bank1 $4773 source entry | **2** |
| Mapped bank6 $9932 producer entry | **0** |
| Qualified original source collision calls | **0** |
| Bank0 $0427 SAT uploader **entry-site visits** | **41** |

These results are pinned against the full original-ROM SHA,
separately generated PC-34 prefix and read-only fixed PC-40
history. The independent new validator checks the *exact* stop,
mapper/IRQ/VBlank and every mapped source-site hit count, not
only internal JSON bookkeeping. CI rejects corrupted reports.

### What mapped $9966 establishes — and does not

The recovered original physical bank-6
`Ys/src/wholebank06/bank06_complete.asm` contains code immediately
after `ProduceSpriteBuffer` which loads `($C198)`, tests whether
it is zero, and conditionally calls **$9932**. PC-41 independently
observes one bank-qualified entry at **$9966**, but no $9932
entry. This demonstrates an original sprite-handler path was
*visited*, not that a sprite was generated or shown. The
value of $C198 at that exact source entry has **not yet been
independently observed**; we therefore do not assign a cause
to the skipped producer or identify a playable player sprite.

### Next stop: refresh-register correctness

The natural next opcode `ED 5F` (`LD A,R`) reads the Z80 **R
memory refresh register**, which the current bounded native
interpreter does **not** track. An arbitrary zero or current
instruction counter would be a gameplay-state fabrication.
The [Zilog Z80 CPU User Manual](https://www.zilog.com/docs/z80/um0080.pdf)
specifies a 9-T-state LD A,R instruction with flags
S/Z/3/5 from R, P/V from IFF2, H/N cleared and C preserved.
Proper R support requires counting M1 instruction/prefix
fetches, HALT refresh cycles, interrupt acknowledge cycles,
and preserving bit7 while incrementing the low seven bits.
The same manual specifies that maskable IRQ acceptance clears
**both** IFF1 and IFF2; the present interpreter does not yet
model that detail correctly.

That entire CPU behavior should be implemented with independent
R/interrupt tests and a new source-ROM milestone before
attempting to pass **$141A**. PC-41 intentionally stops at the
real unsupported opcode rather than inventing a refresh value.

## Status and boundaries

This is original-source interpreter compatibility research;
it is **not** an independently confirmed emulator/hardware
trace, original-game native PC integration, verified player,
map traversal, animation or any original-game Alpha gate.
No original copyright ROM/media bytes are committed.
Development release M45 remains unchanged, and the PC-41 PR
must remain stacked, draft and unmerged pending all CI checks.
