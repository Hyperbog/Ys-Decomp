# Whole-system Milestone 6 — six independently source-backed banks

**Physical banks:** 0, 1, 2, 3, 6, 7 — each exactly 16 KiB from project sources with no original ROM fallback. Bank 1 is newly closed in this milestone. Each generated image passes its original-ROM SHA-256 check; the combined six-bank image comprises 98,304 independently built bytes.

| Metric | M5 | M6 |
|---|---:|---:|
| Complete physical 16-KiB banks | 5 | **6** |
| Source-backed bytes in 256-KiB ROM | 83,182 | **98,787** (37.6842%) |
| Bytes still from owner ROM | 178,962 | **163,357** (62.3158%) |
| Newly source-backed | — | **15,605** |
| Newly captured candidate mnemonic code | — | 1,717 bytes |
| Newly source-backed data | — | 13,888 bytes |

The 13,888 new data bytes consist of two typed directories (20 bytes), 340 `$FF` filler bytes, and **13,528 unresolved bytes**. The latter may include unexamined code. Candidate mnemonic code is byte-identical but not fully runtime-validated. Therefore this is **binary source closure, not semantic closure of the entire game control system**.

`tools/build_system_m6.py` requires the user's validated original ROM for the other ten banks, compares the entire output to it, and rejects mismatch. The bank-1 source-only path uses no ROM. `tools/run_system_m6_regressions.py` preserves all M5 suites and adds full bank-1, six-bank, and WLA preparation checks. `tools/wla_system_m6.py --run` fails closed when external binaries are unavailable.

This checkpoint does **not** report full-game emulator verification, third-party assembler verification, or source-only completion of the entire cartridge. Current mandatory next steps are whole-bank closure of bank 4 and linking source fragments to real runtime mapper/VDP/audio traces; incrementing byte coverage alone does not constitute game-system understanding.

## Static system graph supplement

`wholebank01/static_control_links.json` records **1,251 source-backed instruction sites**, **217 direct control-flow references**, **2 I/O-port instruction sites**, and **10 mapper-register write sites**. These counts are static; no mapper-state trace or new game execution is claimed. The reproducible check is `make bank01-static-links`.
