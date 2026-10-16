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

## Measured source-only original ROM result

[Passing native original-ROM run 38855605003](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38855605003)
executed the unchanged cartridge from reset, then continued the
same controlled PC-34 input sequence. Native C11 passed **33/33
CTest cases**, the complete original ROM rebuild and PC-34/35/36/37/38
regressions. The three bank-qualified observed sites are:

| Source opcode site | Phase | Successful WRAM stores | Same-value | Changed-value |
| --- | --- | ---: | ---: | ---: |
| Fixed bank 0 `$00B4` — `LDIR` | Reset → M45 | 192 | 192 | 0 |
| Fixed bank 0 `$0AA1` — `LD ($DD00),A` | Reset → M45 | 1 | 0 | 1 |
| Fixed bank 0 `$0AA1` — `LD ($DD00),A` | Post-M45 | 1 | 1 | 0 |

All 192 source byte offsets are written during initialization.
The initial boot phase records **193 total writes**: 65 to the Y
region and 128 to the X/tile region, 192 identical-to-existing
values and one changed value. The post-M45 300k-iteration run
records **one same-value store** to the Y region; no X/tile
store or changed value. **No physical WRAM mirror alias or IRQ
stack write** targeted the SAT source during either observed phase.

This specifically resolves PC-38's blind spot: the post-M45
SAT source buffer was rewritten once *without* changing value.
All 27 SAT uploads remain byte-identical. The full original
`$00B4` `LDIR` initialization is NOT an animated sprite
producer: its source context is `LD HL,$C010`,
`LD DE,$C011`, `LD BC,$1E4F`, `LD (HL),$00`,
then `LDIR`. The subsequent `$0AA1` source opcode is
`32 00 DD` = `LD ($DD00),A`. The independent PC-39 checker
now verifies the original **262,144-byte ROM SHA-256**, fixed
bank-0 opcode bytes, the independently committed Phase6 listing,
and the bank-0 assembly source before asserting these three
site/count golden values.

Nothing in this trace establishes original player animation,
world movement, map traversal, or the source bank-6 `$9932`
producer. A trusted independent emulator/hardware execution
remains necessary to authenticate a playable original Ys frame.

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
    /tmp/ys-source.sms /tmp/pc39.json /tmp/pc34.json /tmp/pc36.json \
    /tmp/pc37.json /tmp/pc38.json
```

The result is evidence of what the existing bounded interpreter
executed, **not** an independently confirmed hardware or emulator
trace, recovered original player, controllable game area or
original-game Alpha milestone. Do not force a bank-6 `$9932`
sprite producer call or synthesize collision/gameplay state.
