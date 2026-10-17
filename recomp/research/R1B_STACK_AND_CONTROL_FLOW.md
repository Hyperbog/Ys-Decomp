# R1b — original Z80 stack and control-flow diagnostic

**Status: investigation complete for the first failure boundary; original
execution parity remains BLOCKED.** Separate draft
[PR #16](https://github.com/Hyperbog/Ys-Decomp/pull/16), stacked above
R1a [PR #15](https://github.com/Hyperbog/Ys-Decomp/pull/15).
No changes to original Ys source ROM, decomp evidence, protected game data,
recompiled output or upstream permanent source are proposed here.

## Evidence and fixed inputs

- Cartridge: 16 source-only banks, 262,144 bytes; original exact SHA-256
  `02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
- Upstream original runtime/compiler pinned to SMS/GG Recomp
  `224d5bb2c150a2c295033d35dec629ef9ee42940`;
  shared Z80 core `0e6606a41245d54c5fd0c3dc322ef9d6890d3923`.
- Upstream `runner/glue.c` Git blob SHA
  `264be88e214ffc32e162bcf581113363b00c9191`.
- Same ROM, no scripted input and 60 requested frames for both compiled-C
  and upstream superzazu `--interp` execution. Upstream runner/hardware is
  shared between these paths; this is **not** an independent emulator oracle.

## Root problem 1: frame SP trace compared different CPU state objects

The upstream `glue_run_interp()` executes Z80 instructions in private
`g_hz`, without synchronizing the corresponding live CPU register state
into `g_z80` each frame. Yet `frame_completed()` uses `g_z80.sp` for
both interpreter and generated-C frame-trace rows. This makes R1a's
initial `$DFEE` versus `$DFF0` sample an **invalid comparison**;
it cannot alone identify a translated stack-instruction bug.

`recomp/diagnostics/live_sp_overlay.py` verifies the exact pinned upstream
commit and blob plus unique source anchors, then temporarily substitutes
live `g_hz.sp` for **interpreter diagnostic sampling only**. Recompiled
sampling remains `g_z80.sp`. This temporary diagnostic does **not** alter
the original tracked evidence, recompiled generated output, or the
unchanged R1a strict parity comparator.

Original vs corrected 60-frame samples:
- Unmodified: SP mismatched **57** frames, WRAM mismatched **1** frame.
- Corrected live-SP diagnostic: SP mismatched **54** frames,
  first observed SP differences begin at **frame 7**. WRAM still
  differs **only on frame 6**. Every compared VRAM, CRAM, video-register
  and R8/R9/R0/R1 fingerprint matched in both runs.

**Do not interpret the remaining 54 frame-SP differences as 54 proven
individual CPU bugs.** Per-frame callbacks can sample different guest
instruction boundaries. An instruction-aligned comparison is needed.

## Root problem 2: real program execution paths diverge

The byte-level WRAM snapshot check reran the genuine 60-frame path with
`--dump-frame 6` in external temporary storage. Its **first unequal byte**
was CPU address **`$DFC6`** (the upper WRAM/CPU stack region):

| Frame | CPU address | Generated C | Interpreter |
| --- | --- | --- | --- |
| 6 | `$DFC6` | `0x83` | `0x72` |

There may be additional unequal bytes at that frame; this report records
the first, not a claim that it is the only one. No extracted memory dump
is committed or uploaded.

The pinned upstream function-level same-start-state, VDP-frozen internal
differential harness reported:
- `$079A` **ok** (frame 0)
- `$8803` **ok** (frame 5)
- `$0749` **ok** (frame 5)
- `$0BC5` **skipped** (did not return within the bounded diagnostic)

Function-level equivalence with frozen VDP **does not prove** that different
interrupt/mapper/synchronization histories enter a function from the same
runtime state.

An independent exact-PC watchpoint comparison (live Z80 registers, cycles
and SP at the **same guest instruction address**) reported over 60 frames:

| Guest PC | Compiled path | Interpreter | Interpretation |
| --- | ---: | ---: | --- |
| `$079A` | 1 hit | 1 hit | All 16 sampled fields matched |
| `$8803` | 1 hit | 58 hits | Different program progression |
| `$0038` (IM1 vector) | 3 hits | 56 hits | Different interrupt execution frequency |
| `$0749` | first hit seen | first hit seen | At least refresh register R differed |
| `$0BC5` | 1 hit | 14 hits | Different resource/staging control-flow frequency |

On the first sampled visit to each listed PC, **all other sampled
registers and the accumulated cycle count matched**; the recorded
Z80 refresh register **R** was the first difference at `$8803`,
`$0038`, `$0749` and `$0BC5`. The instruction-entry comparator
subsequently recorded all first-hit differences (not only the first
field) in
[run 38999671281](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38999671281).

The **first source-identified CPU-model inconsistency** is HALT refresh:

- Upstream `runner/external/superzazu/z80.c` executes another
  `exec_opcode(0x00)` on each halted `z80_step()`, and that opcode
  calls `inc_r()`. Its halted Z80 therefore increments R through
  repeated 4-cycle cycles of execution.
- Upstream native `runner/glue.c::sms_halt()` instead fast-forwards
  `g_z80.cyc` to the next synchronization deadline and calls
  `sms_sync()`, **without incrementing R** during the elapsed
  halted time.

This is a documented semantic difference in **R accounting** for
halted execution. It is **not yet proven** to be the sole or main cause
of the execution-frequency divergence, stack changes or IRQ discrepancy.
No HALT candidate patch has been incorporated into the acceptance gate
or original source.

This is **stronger evidence of genuine execution divergence** than a
frame-end SP mismatch. An earlier compiled path logged 26 hybrid
interpreter calls and 8 unique computed-dispatch misses by frame 60.
Merely reaching 60 frame callbacks does not imply executing the same
number of guest Z80 instructions or interrupts.

## Reproducibility and gates

- Baseline genuine 60-frame strict run:
  [38993078687](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38993078687) — **failed**.
- Root-cause diagnostic: [38999166326](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38999166326)
  — temporary SP oracle fix ran, **strict gate failed**.
- Instruction-entry differential:
  [38999279959](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38999279959)
  — three selected frozen-state functions passed, `$0BC5` skipped;
  **strict gate failed**.
- Exact-PC watchpoint run:
  [38999504891](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38999504891)
  — authentic rebuilt source ROM, compiled real generated C, and
  independent CPU-watch comparisons ran; **strict gate failed**.
- `recomp/tests/test_r1b_diagnostics.py` covers fail-closed pinned
  source anchors, CRLF preservation, PC and frame parsing, misaligned
  records, and first byte/CPU-address mapping.

The temporary overlay must be reviewed as a **diagnostic infrastructure
change**, not retroactively substituted into the R1a evaluator. All
strict SP/WRAM/VDP comparison requirements remain in place.

## Next corrective investigation

1. Independently test a **candidate HALT-refresh/time-step correction**
   that advances the native CPU in 4-cycle HALT intervals, incrementing
   R and sampling IRQ at the instruction boundary as the interpreter
   does. Validate against original full-ROM traces; do not change the
   historical original or the evaluator to make it pass.
2. Locate the **first difference in actual IRQ count, mapper slot bank,
   or identical-PC cycle history**, not merely the first frame snapshot
   difference. Prioritize the first naturally accepted IM1 and banked
   dispatch around frames 5–6.
3. Check whether generated `sms_tick/sms_sync`, `sms_halt`, and
   hybrid-interpreter handoff sample a pending IRQ at the same
   instruction boundary as superzazu. This is a hypothesis, not a proven
   bug location.
4. Check the live mapping, stack push/pop and continuation semantics of
   `$8883` and other banked computed-dispatch misses. Compare matched
   guest PC and mapper state before changing emitter or runner logic.
5. Apply any corrected implementation in its own reviewed code change,
   without relaxing the original strict gate; independently repeat
   source-ROM 60-frame and longer controller/VDP/audio checks.

**No Alpha/Beta/Final release gate is promoted.**
