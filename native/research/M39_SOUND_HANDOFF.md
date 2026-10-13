# M39 — Bank-2 sound entry and SMS/GG Recomp identity gate

## Source-backed native checkpoint

Following the verified M38 1,792-byte name-table clear, the
unaltered cartridge returns to the bank-0 state dispatcher at
`PC=$0C4D`. The next three original instructions in
`Ys/src/phase16/bank00_symbolic.asm` are:

```asm
$0C4D  LD A,$02
$0C4F  LD (MapperSlot2),A
$0C52  CALL $8803
$0C55  LD ($C02E),SP
```

The M39 timed runtime executes those first three source instructions,
stopping **before** the first opcode at bank-qualified CPU address
`$8803`. It verifies the Sega mapper selects physical ROM bank 2,
the Z80 CALL saves the real continuation `$0C55` on the source
stack, the fetched opcode corresponds to the correct bank-2 ROM
offset `$0803`, and the three instructions cost 37 nominal Z80
T-states. No host-provided IRQ, register modification, fake sound
update or disassembly patch is permitted.

A standalone ROM-free regression fixture deliberately maps a
different bank 7 first, then executes the byte-identical bank-0
opcodes and verifies that the mapper switches to bank 2 before
the `CALL $8803` fetch; it checks the stack return and cycles.

**This checkpoint is a sound-entry handoff, not an execution proof of
the bank-2 sound initialization routine or game audio output.**

## Independent SMS/GG Recomp integration validation

The separate Phase-1 integration lives in
`shared_decomp/smsgg_recomp.py` with
`Ys/recomp/game.toml` and Make targets
`recomp-preflight`, `recomp-generate`, `recomp-verify`,
and `recomp-tests`.

The adapter has nine successful **synthetic-fixture** tests, including
invalid SHA, CRC mismatch, tampered generated C, stale config
provenance and missing outputs. The upstream native
`SmsRecomp` binary is **not** vendored and is not invoked in
standard CI; actual generated C is unlinked and unexecuted.

M39 adds the following to the existing explicitly tagged
`[rom-check]` CI job, after all 16 banks are rebuilt
from Ys sources into the temporary runner's cartridge image:

```sh
python3 shared_decomp/smsgg_recomp.py \
  --rom "$RUNNER_TEMP/ys-native-boot.sms" \
  --manifest Ys/manifest.json \
  --config Ys/recomp/game.toml --preflight
```

This independently gates **the real Ys source-built ROM** against
both the original SHA-256/size in `Ys/manifest.json` and the
CRC32 `B33E2827` in `Ys/recomp/game.toml`. It does not
invoke the external generator, compile generated code, establish
static-to-interpreter equivalence or assert game playability.

## Next work and release gates

After verifying `$8803`, continue the actual bank-2 sound
routine with source-timing, PSG/FM interface tests and coverage
accounting; then proceed with the bank-5 graphics loading
at `$0C59`. The ROM-based static recompiler can only be
integrated into a **separate test runner** once its generated
code has a verified host ABI and can reproduce documented
game/VDP/audio state traces.

Do not promote Alpha, Beta or Final: no live title rendering,
gameplay loop, live input or native sound output exists yet.
The full ROM remains privately reconstructed only in tagged CI;
no original ROM or generated code is committed or released.
