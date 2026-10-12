# Ys: The Vanished Omens — SMS reverse-engineering workspace (Phases 1–4)

**Target:** uploaded USA/Europe Sega Master System cartridge ROM. This folder
contains no copy of the full commercial ROM; provide your own ROM to the verifier.

## Verify

```sh
python tools/verify.py "/path/to/Ys - The Vanished Omens (USA, Europe).sms"
```

The verifier checks the **SHA-256**, **CRC32**, **ROM length**, **Sega header**,
**SMS cartridge-header checksum**, and **every source byte in the annotated $0000–$0101 listing**.

## Contents

- `manifest.json` — ROM fingerprints and cartridge metadata.
- `src/bank00_boot.lst` — verified, ROM-offset-annotated Z80 instructions and data.
- `src/bank00_boot.asm` — readable assembly transcription of the listing (not yet
  validated by an assembler).
- `tools/verify.py` — reproducible checks of the uploaded ROM and listing bytes.

## Proven ROM observations

- 256 KiB with **16 × 16 KiB** physical banks, no 512-byte copier header.
- `TMR SEGA` signature at `$7FF0`; header region/size byte `$40` indicates
  export Master System, 256 KiB. Checksum **$5298**, calculated across ROM
  excluding the 16-byte header, matches.
- Reset vector `$0000`: `DI ; IM 1 ; JP $0089`.
- `$0089` initializes SP to `$DFF0`; writes **$80,$00,$01,$02** to the Sega
  mapper registers `$FFFC,$FFFD,$FFFE,$FFFF`.
- It clears RAM using `LDIR`, selects ROM bank 2 for `$8000–$BFFF`, calls
  `$8803`, `$0749`, `$0BC5`, then runs the main dispatch loop at `$00C4`.
- `$00D4` holds 20 little-endian dispatch targets selected by the byte at
  RAM `$C01F`; state identities remain unverified.
- `$0038` contains interrupt-mode-1 handler code; `$0066` contains NMI code.

## Addressing rules and limitations

The Sega mapper presents the CPU with slots `$0000–$3FFF`, `$4000–$7FFF`,
and `$8000–$BFFF`; the first 1 KiB at `$0000–$03FF` is unpaged. RAM is
`$C000–$DFFF`, mirrored at `$E000–$FFFF`. Thus the CPU address of a banked
routine **is not** its unique ROM file offset. The verified listing is in
ROM bank 0, whose CPU and file offsets match for the selected initial bank.

This is **not a complete decompilation** and no full binary-identical build is
claimed. Future phases should trace bank changes, distinguish code from data,
name RAM variables and verify an assembled source image against the ROM.

## Reference specifications

- SMS Power: https://www.smspower.org/Development/ROMHeader
- SMS Power: https://www.smspower.org/Development/MemoryMap
- SMS Power: https://www.smspower.org/Development/Mappers

## Phase 2 incremental analysis

- `phase2/README.md`: bank-aware Z80 function and RAM evidence ledger.
- `phase2/regions.json`: explicit code/data boundaries and binary anchors.
- `phase2/code.lst`: decoder-generated, ROM-backed opcode listing.
- `tools/z80_regions.py`: bounded Z80 scanner and checked snapshot.
- `tests_phase2.py`: seven Phase 2 regression checks.

```sh
python tools/z80_regions.py /path/to/Ys.sms --check
python tests_phase2.py /path/to/Ys.sms
```

Total independently classified offsets: 924 bytes, not a complete rebuild.

## Phase 3 incremental analysis

- `phase3/README.md`: ROM-bank execution and SRAM bounds with confidence marks.
- `phase3/regions.json` and `phase3/code.lst`: five bounded new code regions
  and nine-word dispatch table.
- `src/bank02_update.asm`: 67-instruction source reconstruction, checked
  against decoded mnemonics, not assembled yet.
- `tools/check_partial_asm.py`: validates partial source labels and operands.
- `tests_phase3.py`: 15 checks covering baseline, negative changes,
  mapper calls, SRAM boundaries, and overlap.

```sh
python tools/z80_regions.py /path/to/Ys.sms --phase 3 --check
python tools/check_partial_asm.py /path/to/Ys.sms
python tests_phase3.py /path/to/Ys.sms
```

Cumulative classified original-ROM offsets: **1,465 bytes (0.56%)**.
No full-ROM binary matching or emulator runtime interpretation is claimed.

## Phase 4: audio subsystem identification

- `phase4/README.md`: ROM-supported sound command ranges, FM/PSG ports,
  RAM work records and targeted future work.
- `phase4/regions.json`, `phase4/code.lst`: 528 verified code bytes
  and 75 verified data bytes in five disjoint regions.
- `src/bank02_sound_dispatch.asm`: 22-instruction annotated dispatcher.
- `tools/check_phase4_asm.py`, `tests_phase4.py`: fixed source and
  14-case regression suite, with deliberately corrupted inputs rejected.

```sh
python tools/z80_regions.py /path/to/Ys.sms --phase 4 --check
python tools/check_phase4_asm.py /path/to/Ys.sms
python tests_phase4.py /path/to/Ys.sms
```

Cumulative distinct classified bytes: **2,068 (0.79%)**. No complete
ROM build, assembled binary match, or emulator audio trace is claimed.

## Phase 5 — expanded byte coverage

`phase5/README.md` documents 4,934 new ROM-classified bytes in 2,055 decoded
Z80 instructions and six anchored table spans. `tools/z80_cfg_phase5.py`
reproduces the code listing and bank-qualified unresolved targets;
`tests_phase5.py` runs mutation/regression controls. Cumulative classification:
7,002 bytes (2.67% of this 256-KiB ROM). No assembler binary identity or
emulator-playback correctness is asserted.

## Phase 6 — fixed-bank dispatch and audio data typing

`phase6/README.md` documents **14,521 additional distinct bytes**, including
2,027 new fixed-bank Z80 instructions and bounded audio-data regions.
Use `tools/z80_cfg_phase6.py` and `tools/song_headers_phase6.py` with `--check`
to reproduce the reports and indexed audio-descriptor CSV. The descriptor
fields beyond the per-voice stream pointers are not yet named.
**Cumulative classified bytes: 21,523 (8.21% of ROM)**. No assembled
binary-match or runtime playback verification has been performed.

## Phase 7

See [`phase7/README.md`](phase7/README.md). Physical bank-1 CFG has 376
statically decoded instructions from six independently referenced targets;
physical bank-3 has 14,541 SHA-256-anchored **provisional** non-padding bytes.
The non-padding classification is not a decoded graphics or text format.

## Phase 8

See [`phase8/README.md`](phase8/README.md) for ROM-backed bank 4/7/8/10/12
paths (797 new code bytes), a new 124-byte indexed record prefix, and
reversible interpretation of 5,632 previously opaque bytes as SMS Mode-4
bitplane tiles. The 5,632 tile bytes are **not** added to cumulative unique
coverage a second time. Static mapper interpretation remains conditional.

```sh
python tools/bank_trace_phase8.py /path/to/Ys.sms --check
python tools/mode4_tiles_phase8.py /path/to/Ys.sms --check
python tests_phase8.py /path/to/Ys.sms
```

## Phase 9B

The four VDP-related Z80 routines in `src/phase9_vdp.asm` now emit **111
exactly ROM-identical bytes** through the restricted two-pass encoder in
`tools/z80_subset_asm_phase9.py`. The fixed `$06E4` branch regression has an
explicit negative test in `tests_phase9.py`. See `phase9/README.md` and
`phase9/assembly_report.json` for offsets, digests and remaining limitations.
The original ROM is still needed locally for all verification commands.

## Current status — Phase 21

See [`phase21/README.md`](phase21/README.md) for current code/data confidence, generated source and test results; the historical phase paragraphs above are not current project totals.

Reproducible ROM-backed source bytes: **46,349**, candidate classification **58,490**, original-ROM fallback **215,795**. Phase 21 adds 357 newly structured variable music-header bytes and converts 8,056 total bytes to ROM-independent source. See `tools/build_phase21.py`, `tools/phase21_semantic_sources.py`, and `tests_phase21.py`. All 24 suites have passed in the parallel runner. The full ROM is still template-assisted; WLA-DX was *prepared*, not independently run. Bank-3 glyph slots are not decoded dialogue.