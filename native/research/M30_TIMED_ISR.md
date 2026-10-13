# M30 — Timed Ys zero-state ISR with pending VBlank re-entry

## Source-backed path

Start from the real 256 KiB reconstructed Sega Master System Ys cartridge,
cold CPU reset at `$0000`. At M29 the first **clock-generated** IM1
interrupt was accepted with interrupted return PC `$0764`; the authentic
ISR `$0038 PUSH AF / $0039 IN A,($BF)` cleared VBlank. M30 continues
from the same CPU, VDP, clock, mapper and sound state, without any injected
IRQ or modified data.

Source: `Ys/src/phase16/bank00_symbolic.asm`.

| PC | Recovered original Z80 behavior |
|---|---|
| `$003B-$003F` | OR A / JP P,$0540 / JP $0102; VBlank bit 7 selects $0102 |
| `$0102-$0106` | Read `$C021=0`, select the early zero-state branch at `$0148` |
| `$0148-$015C` | Save main and alternate BC/DE/HL/AF, IX/IY, mapper bank and control |
| `$015D-$0166` | Temporarily map ROM bank 2, CALL `$8000` actual audio frame update |
| `$0169-$018F` | Check VDP initialization flags and optionally update VDP control registers |
| `$018F-$0199` | Set `$C10F=1`; restore mapper control and bank |
| `$019C-$01A9` | Restore all original primary and alternate registers |
| `$01AA-$01AB` | EI; RET to the interrupted PC `$0764` |

## Discovery from first gated execution

In [run 38344348713](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38344348713),
the 16 source-only ROM banks rebuilt correctly and the previous M25
and M29 checkpoints passed. The initial new M30 assertion correctly
detected an **additional** naturally generated VBlank instead of a
stable return after the first ISR:

```text
steps=16791 PC=$0038 SP=$DFEA status=running
totalT=342823 line=193 hpos=139 frames=5
VBlank=6 IRQ=2 VDPstatus=80 reg1=A0
```

The sixth VBlank arrived while the first source ISR's bank-2 audio
routine was running. When `$01AA EI` and `$01AB RET` finished, the
pending interrupt was recognized *at the RET boundary* and IM1
re-entered `$0038`, pushing the same return PC `$0764`. This behavior
is preserved. **Do not clear VBlank artificially or disable IRQs to
force an immediate stop at `$0764`.**

## Revised M30 acceptance checks

1. Complete the first zero-state ISR and recognize a pending second
   IRQ: `PC=$0038`, `IRQ=2`, `VBlank=6`, real saved PC `$0764`.
2. At the IRQ re-entry boundary, compare **all primary and alternate
   registers and IX/IY** with the original M29 interrupted snapshot.
   Verify mapper control and selected bank 2 restored, `$C021=0`,
   `$C10F=1`, and second IRQ status bit 7 pending.
3. Continue the second authentic source ISR through its VDP status
   read, zero-state bank-2 sound update and `EI; RET`. Now assert
   **stable `PC=$0764`**, before executing its `POP AF`.
4. Verify SP equals the first interrupt snapshot's SP **plus 2**,
   all general and alternate registers are preserved, mapper restored,
   `C021=0`, `C10F=1`, status bit 7 cleared,
   `IRQ=2`, `VBlank=6`, `IFF1/IFF2` enabled and EI deferral cleared.
5. Fail closed on any unsupported opcode, port, stack mismatch or
   instruction budget overrun; bound each handler to 4,000 instructions.

The revised `native/test_timing.c` adds a ROM-free fixture for original
`EI; RET` at `$01AA-$01AB` with a pending frame interrupt, verifying
that the Z80 runtime vectors again to `$0038` and saves PC `$0764`.
The previous source-encoded `$0102 -> $0148 -> CALL $8000` prologue
test remains in place.

## Reconstruction and release policy

The single source-dependent acceptance test runs only with
`[rom-check]` or explicit `rom_trace=true`, and also rechecks the
earlier M25 manually injected checkpoint. The established ROM SHA-256
is `02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.

This is a bounded execution checkpoint, not a true game-frame loop,
title screen or playable PC build. No native video window with Ys game
content, live input or sound synthesis has been established. Alpha,
Beta and Final release gates remain unpassed.


## Verified completion

[Gated GitHub Actions run 38344640720](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38344640720)
passed the two source-ROM acceptance boundaries and all 13 strict native
test suites (no ROM fallback; 16/16 source-only banks, 262144 bytes):

```text
PASS timed actual Ys reset to first IM1: instructions=16379 T-states=338842 VBlank=5 IRQ=1 savedPC=$0764 PC=$003B SP=$DFE8
PASS natural second VBlank re-entry after $01AB RET: PC=$0038 savedPC=$0764 VBlank=6 IRQ=2 handler_steps=412
PASS timed Ys second zero-state ISR stable return to $0764: first_steps=412 second_steps=414 total_steps=17205 T-states=346813 SP=$DFEC mapper=80 bank2=2 IRQ=2
Stop BEFORE executing $0764 POP AF; normal startup not yet resumed.
```

This completion did **not** establish any additional timed startup
state transition. The next meaningful checkpoint is execution of
`$0764 POP AF`, return to `$00C1` and subsequent automatic
VBlank wait handling. One new gated reconstruction should be run only
after that path and its hardware assumptions are source verified.
