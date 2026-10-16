# PC-39 — actual original Z80 WRAM write strobes into the SAT buffers

## Source and scope

The previously verified original SMS Ys execution copies 192 source
bytes from CPU-visible WRAM `$DD00–$DDBF` to sprite attribute table
VRAM 27 times (PC-36). PC-38 detects **zero changed byte values**
in that WRAM range during the later bounded PC-34 controller run,
but cannot detect writes that store an unchanged value.

PC-39 closes that ambiguity using an **optional observer at the
successful SMS console-WRAM write primitive**. It runs from the
actual cartridge reset through the M45 `$0C92` checkpoint (the
initialization phase), then through the **unchanged PC-34
300,000-iteration source-controller experiment** (continuation).
The hook never suppresses, retries, injects, or modifies writes.

It filters the **physical 8-KiB console-WRAM offset**
`$1D00–$1DBF`, accepting both CPU-visible aliases
`$DD00–$DDBF` and `$FD00–$FDBF`. Writes to SRAM-mapped
`$C000–$FFFF` are excluded, even if the address looks like an
SAT source address. Writes into other RAM, or refused ROM writes,
are excluded. Exact *successful* bus strobes are counted even
when the new value equals the previous value.

Source attribution is recorded at the instruction's **latched
start address and physical ROM bank before operand fetch or mapper
side effects**, not the Z80 PC after fetching immediates. IM1
interrupt stack pushes are explicitly tagged `irq=true` and
attributed to vector `$0038`, not mislabeled as stores from the
interrupted instruction. The observer preserves per-phase totals,
same-value/changed-value counts, Y versus X/tile WRAM targets,
WRAM mirror aliases, touched-offset counts and bounded distinct
source sites.

## Implemented files

- `native/sms_bus.{h,c}`: optional synchronous read-only write
  observer invoked after successful physical console-WRAM writes.
  Unobserved default behavior remains unchanged.
- `native/z80.{h,c}`: latched original source opcode PC/bank
  and separately marked IM1 memory write context.
- `native/pc_sat_strobes.{h,c}`: fail-closed, two-phase
  physical-WRAM SAT write accounting and JSON evidence.
- `native/test_pc_sat_strobes.c`: actual synthetic Z80 instruction
  execution for normal stores, alias writes, bank-six site
  provenance and IM1 pushes, plus rejected-ROM and SRAM tests.
- `native/tools/verify_pc39_sat_strobes.py`: independent typed
  schema checks, per-source/phase arithmetic, IRQ/mapper
  invariants and exact PC-34/36/37/38 same-run provenance.
- Strict C11 build and full source integrity are verified by CI,
  without ever committing or uploading commercial ROM contents.

## Reproduce

Build `ys-native-timed-rom` and reconstruct the original source
ROM using the existing project SHA-verified ROM-independent tools:

```sh
./build-native/ys-native-timed-rom /tmp/ys-source.sms \
    --pc34-extended-postrelease \
    /tmp/pc34.json /tmp/pc35.json /tmp/pc36.json \
    /tmp/pc37.ppm /tmp/pc37.json /tmp/pc38.json /tmp/pc39.json
python3 native/tools/verify_pc39_sat_strobes.py \
    /tmp/pc39.json /tmp/pc34.json /tmp/pc36.json \
    /tmp/pc37.json /tmp/pc38.json
```

The result is evidence of what the existing bounded interpreter
executed, **not** an independently confirmed hardware or emulator
trace, recovered original player, controllable game area or
original-game Alpha milestone. Do not force a bank-6 `$9932`
sprite producer call or synthesize collision/gameplay state.
