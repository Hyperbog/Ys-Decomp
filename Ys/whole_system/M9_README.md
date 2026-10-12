# Whole-System M9 — Twelve independent 16-KiB banks (75% ROM)

**M9 complete ROM-independent banks**: `0,1,2,3,4,6,7,8,9,10,11,12`.
Source-backed bytes: **196,608 / 262,144 (75.00%)**. Four banks (`5,13,14,15`) remain original-ROM assisted (65,536 bytes).
M9 adds **49,044** source bytes, comprising 65 Z80 mnemonic bytes from bank 9 and 48,979 explicitly represented data bytes. Bank 12's previously matched 108 bytes are not counted again.

## Bank-9 VDP glyph output path

The 65-byte executable region `$BEFB–$BF3B` contains a conditional selector and a six-byte VDP-data-port transfer loop (`LD B,$06`, `LD C,$BE`, `OUTI`, `OUT (C),A`, `JR NZ`). The directory at `$BF3C–$BF4B` contains eight two-byte pointers. The eight pointed-to **six-byte byte sequences** occupy `$BF4C–$BF7B`, in this index order: `$BF52,$BF5E,$BF58,$BF64,$BF6A,$BF70,$BF76,$BF4C`. That is a demonstrable indexed six-byte transfer structure, not yet a decoded font or complete gameplay trace. The actual ROM loop at `$BF2C` was also executed in **24 bounded runs** (8 records × 3 separators), verifying 288 VDP data-port bytes against separately reconstructed record fields. The mapper, initial HL, separator RAM value and VRAM address are seeded.

Bank 11 is source-backed as bounded but predominantly unresolved resource data. Bank 12 contains a 128-byte candidate waveform/curve (`$8000–$807F`), preserved resource spans, previously verified 108 Z80 instruction bytes at `$9EFC–$9F67`, and verified FF tail padding. The consumer/semantics of its candidate curve remain unknown. Any project-wide claim of fully decoded language, graphics, or behavior would be incorrect.

## Reproduce

```sh
cd Ys
python tools/build_system_m9.py --standalone-banks    # ROM-independent, all 12 banks
python tools/whole_banks09_11_12.py --verify-mixed    # mixed assembler round trips
python tools/build_system_m9.py /path/to/Ys.sms --check   # strict full-ROM comparison
python tests_whole_banks09_11_12.py /path/to/Ys.sms
python tools/run_system_m9_regressions.py /path/to/Ys.sms --jobs 4 --timeout 600
python tools/bank09_glyph_trace.py /path/to/Ys.sms --check
python tools/wla_system_m9.py --prepare  # not an independent compiler result
```

**Limitations:** This is **not yet** source-only full-cartridge reconstruction. The majority of newly represented bank9/11/12 bytes preserve unresolved proprietary resource encodings. Only 65 *new* mnemonic instruction bytes are recovered. WLA-DX external assembly and a full SMS emulator trace are not verified. This milestone expands source-controlled binary coverage, but semantic reconstruction is substantially incomplete.
