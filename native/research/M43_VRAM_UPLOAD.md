# M43 — Original Ys staged tile resource to VDP name-table upload

## Exact source-ROM sequence

The verified M42 continuous Z80 trace reaches `PC=$0C72`, after 748
bytes of source bank-5 compressed resource were independently decoded
and 1,536 writes staged in original WRAM (`$D600-$DFBF` excluding
the live IRQ stack at `$DFC0-$DFFF`). From
`Ys/src/phase16/bank00_symbolic.asm`:

```asm
$0C72  LD HL,$D600
$0C75  LD DE,$7900   ; VDP write command: VRAM $3900
$0C78  LD BC,$0600   ; six 256-byte pages = 1536 bytes
$0C7B  CALL $06C1
$0C7E  LD HL,$8000   ; next source pattern graphics step, not yet run

$06C1  RST $0028     ; original VDP control port setup
$06C2  LD A,C
$06C3  OR A
$06C4  JR Z,$06C7
$06C6  INC B
$06C7  LD A,B
$06C8  LD B,C
$06C9  LD C,$BE
$06CB  OUTI          ; original Z80 I/O opcode, not a memory-copy stand-in
$06CD  NOP
$06CE  JR NZ,$06CB
$06D0  DEC A
$06D1  JR NZ,$06CB
$06D3  RET
```

The source sends 1536 staged bytes from `$D600-$DBFF` to
`VRAM[$3900-$3EFF]`. This prepares game graphics/name-table data but
does not establish a visible, animated title screen.

## M43 test contract

`native/test_timing.c` adds a ROM-free, **byte-identical**
Z80 fixture for `$0C72-$0C7D`, `$06C1-$06D3` and the
`$0028` VDP control helper, plus deterministic 1536-byte WRAM content.
It verifies 1536 OUTI instructions, the unchanged VRAM sentinel
bytes on either side of the transfer, correct mapper/stack/HL/BC
results, the final VRAM write address and complete byte-for-byte
match. The fixture runs through the normal instruction-granular VBlank
clock without an invented game image.

`native/trace_timed.c` preserves all M29–M42 checkpoints, snapshots
the authentic staged WRAM source prior to upload, then executes the
real `$0C72 -> $06C1 -> $0C7E` call path using
`ys_sms_runtime_step_auto`. It counts actual source `$06CB OUTI`
steps and checks each resulting VRAM byte at `$3900-$3EFF` against
its independent original WRAM snapshot. It also validates:

- Original `$0028` control path sets VRAM write mode/address
  `$3900`; after 1536 writes it ends at `$3F00`.
- CPU returns to `PC=$0C7E` with `HL=$DC00`, `DE=$7900`,
  `BC=$00BE`, and restored stack pointer.
- 1536 authentic source OUTI opcodes were executed; no test-supplied
  byte copies, PC manipulation or interrupt injection.
- All natural IRQ/VBlank events remain permitted inside a bounded
  source code execution window, while unexpected CRAM writes, wrong
  mapper/stack state or mismatched VRAM bytes fail the checkpoint.
- Optional `--frame` emits a real-cartridge VDP screenshot from this
  later point, not a live native game frame.

## Static recompiler integration boundary

`shared_decomp/smsgg_recomp.py` and `Ys/recomp/game.toml` are
opt-in **SMS/GG Recomp Phase 1** integration. The adapter verifies
ROM SHA-256/CRC/size, calls an **external** `SmsRecomp` binary
if provided, and audits generated C provenance. Its adapter CI passed
14/14 tests, including safe output handling, but neither compiles
upstream-generated C nor executes a static-recompiled Z80 dispatcher.

**M43's CPU steps run the existing C11 interpreter**, not generated
C. A future static-recompiler execution milestone must compile/link
generated code and compare CPU, mapper, VDP and PSG state to the
verified source-ROM trace, including the M43 VRAM byte ledger.
Do not advertise runtime fidelity or gameplay until those checks exist.

## Distribution and stage policy

No `Ys/**` ROM sources, generated proprietary C, original ROM
assets or upstream SMS/GG Recomp executable are vendored. The original
256 KiB 16-bank ROM digest must remain

`02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.

A single tagged `[rom-check]` CI run reconstructs the ROM and checks
the extended trace. Windows GUI remains a diagnostic/static-PPM viewer,
not a playable game. Alpha/Beta/Final gates stay blocked.


## Passing cartridge-backed M43 verification

[CI 38471475804](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38471475804)
passed with 16/16 source-only banks (262,144 bytes, no fallback),
SHA-256 `02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`
and 13/13 CTest:

```text
PASS authentic Ys two-row staged resource to $0C72: source_used=748 staged_writes=1536 steps=122272 T-states=1323179 IRQ=18 VBlank=22
PASS original Ys staged tile bytes uploaded to VDP at $0C7E: bytes=1536 OUTI=1536 steps=127325 T-states=1376546 IRQ=19 VBlank=23 VRAMwrites=5889
PASS authentic timed VDP image: 147471 bytes
```

The original VBlank ISR ran naturally during the byte-matched
transfer. Actual tile pattern upload and title/gameplay remain
outside this checkpoint.
