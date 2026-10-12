# Phase 18 — Bounded Z80 execution and VDP/mapper trace

This checkpoint adds **actual execution of selected ROM instructions** within a
restricted, fail-closed Z80 interpreter. It improves on earlier static analysis,
but **is not an SMS emulator, automatic gameplay trace, or cycle-accurate proof**.
All register states and the SAT's RAM contents are explicitly initialized.

## Reproduced executions

| Path | Execution setup | VDP bytes verified | Checks |
| --- | --- | ---: | --- |
| Bank-3 `$0BA1`, 4 fixed-bank call sites | Execute original `LD HL`, `LD DE`, `LD C`, `CALL`; original routine writes bank 3 to `$FFFF`; execute `RST $28` and loops | 6,496 | Four mapper writes, `$BF` commands, `$BE` streams and output SHA-256 digests match Phase 9 static analysis |
| SAT upload at fixed-bank `$0427` | RAM `$DD00/$DD40` seeded from the existing decoded bank-6 record #7 and padded | 192 | Two `$BF` commands (`$7F00`, `$7F80`), 64 Y and 128 X/tile bytes written to the expected VRAM ranges |
| Bank-7 unrolled transfer code, 64 indexed entries | Bank slot 2 set to 7, A=0, C=`$BE`, HL set to recorded source pointer, `$7420` sent to `$BF` | 40,224 | Execute the original `OUTI; OUT ($BE),A` code and return; verify each stream byte against separately expanded ROM-source records |
| **Total** | 69 bounded executions; repeated use of ROM data is expected | **46,912** | All byte streams/destinations verified; results contain hashes only |

The 40,224 bank-7 bytes are a **sum across 64 separate executions**, each
starting at the same VRAM address. They are **not 40,224 simultaneous VRAM bytes**.
Similarly, the 6,496 bank-3 bytes include overlapping/repeated ROM source data.
These are **output bytes** and must not be added to ROM classification totals.

### Supported interpreter instructions

The test runner implements only opcodes exercised by these paths: `LD` immediate
and memory, `CALL`, `RET`, `RST $28`, `OUT`, `OUTI`, `INC`, `DEC`, `JR NZ`, `DJNZ`,
`XOR A`, `NOP`, `DI`, and `EI`. Memory accesses resolve selected ROM banks and
RAM addresses; `$FFFF` writes select physical bank 2's mapping slot. The VDP
port model uses `$BF` control-word pairs and `$BE` sequential VRAM writes.
Unsupported opcodes, unexpected ports, illegal VRAM commands and overlong runs
fail closed. No Z80 cycles, interrupts, VDP registers/rendering, audio, input,
DMA or frame state are modeled. The code is an **isolated subroutine harness**;
it does not boot the game or prove any real game state executed a transfer.

### Reproduce

```sh
python Ys/tools/phase18_z80_trace.py '/path/to/Ys.sms' --check
python Ys/tests_phase18.py '/path/to/Ys.sms'
python Ys/tools/build_phase17.py '/path/to/Ys.sms' --verify
```

Expected: matching reference-ROM SHA-256, four bank-3 traces, 64 bank-7 traces,
192 SAT bytes, 15 positive/negative tests passing, and unchanged 38,293-byte
source-backed ROM build. `execution_report.json` contains CPU addresses, sizes,
mapper register values and SHA-256 output digests, **not extracted pixels**.

## Honest progress accounting

| Metric | Phase 17 | Phase 18 |
| --- | ---: | ---: |
| Source-backed bytes | 38,293 | 38,293 |
| Remaining ROM-template bytes | 223,851 | 223,851 |
| Classified/candidate distinct ROM bytes | 58,133 | 58,133 |
| Independently installed Z80 assembler | No | No |
| Complete-game emulator trace | No | No |
| Restricted instruction-level transfer trace | No | **Yes, 69 cases** |

Next: obtain or build a *separate* open-source emulator with full CPU/VDP
register support; use recorded breakpoint conditions at `$0BA1`, `$0427`, and
bank 7 `$8856` and compare its events with this isolated harness. Never call
synthetic test setup a real gameplay capture.
