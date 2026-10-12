# Phase 4 — Ys SMS audio command engine

**Source:** verified 256-KiB ROM (`../manifest.json`, SHA-256).
**Scope:** bounded Z80 code, anchored sound tables, symbol reconstruction and regression tests.
**Status:** ROM-consistent static analysis, *not* assembled or emulator-traced.
All addresses below are Z80 CPU hexadecimal addresses when bank 2 is mapped at `$8000`.

## Critical identification: these are audio routines

- `$8100–$810F` writes to I/O `$F0/$F1` (YM2413 FM register select/data).
- `$8112–$818C` initializes/mutes FM/PSG paths; `$7F` controls the SN76489 PSG.
- `$818D–$81B0` selects one of two 18-byte FM register-write streams.
- `$808F–$80BF` accepts high-bit commands in `$DE64–$DE66`, consults
  the priority byte array at `$8D02` (bounds **not** yet proven), and places
  a selected command in `$DE63`.
- `$81D9–$8328` processes queued commands and prepares audio work records.

Hardware references:
- Sega official hardware documentation: https://www.smspower.org/Development/SMSOfficialDocs
- YM2413: https://www.smspower.org/Development/YM2413
- FM audio control port: https://www.smspower.org/Development/AudioControlPort

## Confirmed code/data boundaries (bank 2, ROM file offsets == CPU addresses)

| Offset | Length | Type | Evidence |
| --- | ---: | --- | --- |
| `80F1–81B0` | 192 | code | continuation of previous bank-2 code; FM/PSG output and preset routine |
| `81B1–81D8` | 40 | data | words `81B5,81C7` followed by 2 × 18 FM register/value bytes |
| `81D9–8328` | 336 | code | queued-command decode, record initialization, pointer lookup |
| `8CFE–8D01` | 4 | data | two words `8112,814C`, used by `$BC/$BD` cases |
| `8D40–8D5E` | 31 | data | bytes indexed by `$81..$9F` commands and copied into `DE61/DE62` |

**New coverage:** 528 code bytes + 75 data bytes = **603 new distinct bytes**.
**Cumulative:** 2,068 / 262,144 bytes (**0.79%**); the number represents
classification, *not* the fraction of functionality recovered.

## ROM-proven command cases at `$81D9`

| Command (A / `DE63`) | Control-flow destination | Direct evidence |
| --- | --- | --- |
| `00–7F` | `$8803` | `BIT 7,A; JP Z,$8803` |
| `80` | `$8204`, then `RET M` | `SUB $81`, sets sign, returns |
| `81–9F` | `$8204` | reads `$8D40 + (A-$81)`; writes `DE61/DE62` |
| `A0–B7` | `$8235` | compares `A0/B8` and selects record paths |
| `B8–BB` | `$831A` | writes `$80` to `DE63` |
| `BC–BD` | indirect via `$8CFE` | jumps to `$8112` / `$814C` |
| `BE–FF` | `$8803` | `CP $BE; JP NC,$8803` |

`$81D9–$8203` also has an annotated assembly source:
`../src/bank02_sound_dispatch.asm`, cross-checked by
`../tools/check_phase4_asm.py` (22 instructions, two labels).

## Audio RAM evidence ledger (not a complete layout)

| Address / offset | ROM-supported operation | Working meaning |
| --- | --- | --- |
| `DE60` | controls 8-record vs 6-record loop and FM I/O path | audio mode flag; exact values unknown |
| `DE61`, `DE62` | timer counter and reload value | interval timing |
| `DE63` | sound command selected by `$808F`, consumed at `$81D9` | pending sound command |
| `DE64–DE66` | three bytes checked by `$808F`, each cleared when serviced | pending request slots |
| `DE67` | compared with table `$8D02`, updated on accepted priority | last/active priority byte |
| `DE6A–DE6C` | nested countdown/reload fields | audio sequence state |
| `DE6F + 20h*n` | 8-record pass when `DE60 != 0` (`n=0..7`) | channel work records |
| `DEAF + 20h*n` | 6-record pass when `DE60 == 0` (`n=0..5`) | alternate channel subset |
| record `+0` | bit 7 gates update routine; bit 5 read at `$8393` | flags (exact bit meanings unproven) |
| record `+3/+4` | loaded into `DE` as little-endian pointer at `$8351` | event-stream pointer |
| record `+8` | incremented at `$80E7` in five-record pass | state/step byte |
| record `+10/+11` | duration and elapsed-count comparison at `$8329` | timing bytes |
| record `+16` | sent to YM2413 register `$0E` at `$8339` | FM rhythm register byte |

At `$82D9–$8308`, the routine derives a repeat count from a source
byte's low nibble, executes nine `LDI` transfers into a selected record,
then initializes following record fields. This supports a fixed record
format, but **not** full decoding of the song/event bytes.

## FM preset table at `$81B1`

```
81B1: B5 81  C7 81     ; words pointing to presets at 81B5,81C7
81B5: 16 20 17 B0 18 01 26 05 27 01 28 01 36 00 37 40 38 51
81C7: 16 20 17 B0 18 FF 26 05 27 01 28 A5 36 04 37 30 38 F6
```

The two 18-byte streams consist of nine `(YM2413 register, value)`
pairs. `$818D` chooses the pointer using the source's upper nibble.
The permitted index range is not yet demonstrated; avoid generalizing
beyond these two ROM-grounded pointers.

## Reproducibility

```sh
cd Ys
ROM='/path/to/Ys - The Vanished Omens (USA, Europe).sms'
python tools/verify.py "$ROM"
python tools/z80_regions.py "$ROM" --phase 2 --check
python tools/z80_regions.py "$ROM" --phase 3 --check
python tools/z80_regions.py "$ROM" --phase 4 --check
python tools/check_partial_asm.py "$ROM"
python tools/check_phase4_asm.py "$ROM"
python tests_check.py "$ROM"
python tests_phase2.py "$ROM"
python tests_phase3.py "$ROM"
python tests_phase4.py "$ROM"
```

Phase 4 suite: **14/14 checks passed**, including deliberate data/listing/
source mutations that are correctly rejected. There is no ROM file in
this repository or its ZIP archive.

## Next checkpoint

1. Trace the per-channel event decoders `$837F`, `$8543`, `$85E9`,
   `$8472` (FM) and `$8A4B` (PSG), respecting RAM and bank identities.
2. Identify sources of queued commands `$DE64–$DE66` and producers of
   command `$DE63`; verify bounds of `$8D02` priority table.
3. Reconstruct a complete 32-byte record and attempt one isolated,
   assembler-generated byte-for-byte equivalence test.
4. Use emulator audio-port traces or known-good VGM recordings for
   **runtime** confirmation; static ROM inspection alone is insufficient.
