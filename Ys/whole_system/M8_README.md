# Whole-System Milestone 8 — nine complete source-only SMS banks

Two additional physical banks, **8 and 10**, now regenerate without reading the user-owned ROM in the normal build. The project has **9/16 complete 16-KiB banks**: `[0,1,2,3,4,6,7,8,10]`, or 147,456 bytes in nine complete bank images. Another 108 bytes of previously covered bank 12 remain source-backed (not a complete bank).

**Total source-backed** = **147,564 / 262,144 bytes (56.2912%)**. **Original ROM fallback** = **114,580 bytes** in seven incomplete banks `[5,9,11,12,13,14,15]`.

**This milestone's increment:** 32,555 source-backed bytes, including 38 new mnemonic Z80 instruction bytes (bank8 `$BFB6–$BFDB`) and 32,517 new explicit data source bytes. The existing 138 bank8 and 75 bank10 instruction bytes were source-backed before M8 and must not be counted twice.

More structural evidence: bank 8 holds 11 five-byte lookup records at `$BF7F`, accessed by five-byte index arithmetic; bank 10 holds a directory of 11 pointers to nine FF-terminated strings, with two aliases. Neither large main resource data stream is semantically decoded. The independently modeled bank-10 numeric output routine executes 265 selected input cases and checks 10 PSG-independent **VDP data-port** output bytes per case. It does not model earlier `RST $28` setup, VDP address state or actual gameplay.

## Reproduction

```sh
cd Ys
python tools/build_system_m8.py --standalone-banks
python tools/whole_banks08_10.py --verify-mixed
python tools/bank10_decimal_trace.py --check
python tools/bank08_10_crossbank.py --check
python tools/build_system_m8.py /path/to/your/Ys.sms --check
python tools/run_system_m8_regressions.py /path/to/your/Ys.sms --jobs 4 --timeout 240
python tools/wla_system_m8.py --prepare
```

`build_system_m8.py` builds nine physical banks entirely from sources and falls back to the user's ROM for the other seven. The full 256-KiB overlay is byte-identical, but is **not a source-only full-ROM build**.

WLA-DX fixture preparation is included. **Independent WLA-DX assembler/linker is not installed or verified**, and no full-system emulator execution is verified. The source files contain original-derived encoded data; none of the ROM binaries are distributed.
