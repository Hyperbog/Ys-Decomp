# Phase 2: startup, interrupts, cartridge SRAM, and bank-2 initialization

**Source:** SHA-256-identified USA/Europe `.sms` ROM (see `../manifest.json`).
Original copyrighted ROM is deliberately excluded. All offsets below are hex.

## Evidence-backed symbols

| CPU location | Bank / ROM file offset | Working name | Evidence |
|---|---|---|---|
| 0102 | bank 0 / 00102 | IM1 VDP interrupt normal path | `003F: JP 0102`; status, input, and banked call handling **SUPPORTED** |
| 0148 | bank 0 / 00148 | interrupt register-save and banked call path | preserves alternate registers, IX/IY, FFFC/FFFF **SUPPORTED** |
| 0540 | bank 0 / 00540 | indirect interrupt continuation | reads pointer from C022 and `JP (HL)` **VERIFIED code** |
| 0749 | bank 0 / 00749 | 11-register VDP setup | sends ROM 0768 table bytes to port BF **SUPPORTED** |
| 0773 | bank 0 / 00773 | active-high input and edge capture | `IN A,(DC)` and writes C01B/C01C **SUPPORTED** |
| 079A | bank 0 / 0079A | validate or initialize cart SRAM | bit 3 at FFFC; compare 24-byte signature to 8010 **SUPPORTED** |
| 0BC5 | bank 0 / 00BC5 | register-preserving VBlank wait wrapper | calls 0042 with A=01 **SUPPORTED** |
| 8803 | bank 2 / 08803 | DE63+ work-area initializer | fills DE63+; no RET at 8842 boundary **SUPPORTED** |
| 8842 | bank 2 / 08842 | shared PSG/hardware initializer | writes 11 bytes to port 7F via `OUTI` **SUPPORTED** |

`VERIFIED code` means original bytes and instruction boundaries are reproduced
by the bounded scanner; it does not prove full runtime semantics.

## RAM and hardware address ledger

| Address | ROM-derived usage | Confidence |
|---|---|---|
| C010–C01A | mirror of 11 VDP setup values from 0768 | SUPPORTED |
| C01B | current normalized controller bits (port DC) | SUPPORTED |
| C01C | rising edges: `(new XOR previous) AND new` | SUPPORTED |
| C01F | main dispatch selector; NMI also modifies it | SUPPORTED |
| C020 | NMI temporary previous selector | SUPPORTED |
| C021 | interrupt/wait request, cleared at 0140 | SUPPORTED |
| C022–C023 | little-endian indirect interrupt handler pointer | SUPPORTED |
| C031 | copied from C018 at main-loop entry, used at 0186 | SUPPORTED |
| C10F | interrupt path flag, set at 0191 / cleared at 0143 | SUPPORTED |
| DE63–DE68 | bank-2 initialization work area; DE68 receives E4 | SUPPORTED |
| FFFC | Sega RAM mapper control; bit 3 maps SRAM at 8000–BFFF | HARDWARE REFERENCE |
| FFFF | Sega ROM bank selector for CPU 8000–BFFF | HARDWARE REFERENCE |

## Key control/data flow

- From reset, `0089` calls SRAM checker `079A` **before** RAM clearing.
  `079A` temporarily sets mapper-control bit 3; it compares the 24-byte
  ROM signature `Ancient Ys Vanished Omen` (0782–0799) to SRAM at
  8010–8027. A mismatch initializes 8010–9FFE with zeroes and then
  copies the 24-byte signature. It clears bit 3 when complete.
  This identifies the code's intent, not proof that the cartridge has
  working battery-backed storage in an emulator.
- Initialization calls `8803` with bank 2 selected. Instructions at
  `883F–8841` pop three registers and immediately **fall through** to
  `8842`, which writes PSG bytes via `OUTI`. Another call site at `0052`
  calls `8842` directly.
- `0540` uses RAM C022 as a dispatch pointer. Verified writes form a
  continuation sequence `0545 → 0557 → 0575 → 0587 → 05A8 → 05BF →
  05D9 → 0545`, though exact display timing remains untraced.
- `0121` sets HL=01AA for `RST 08`: indices A=1..4 select word entries
  at 01AC–01B3 (targets 01B4, 01BA, 01D7, 03B8). A=0 would
  select the two instruction bytes at 01AA (`EI; RET`), so this is **not**
  a conventional zero-based dispatch table. Do not infer other indices.

## Scope and verification

`regions.json` marks **7 explicitly bounded code regions (612 bytes)**,
plus **54 anchored data bytes**, and no arbitrary guesses in the gaps.
`code.lst` is produced deterministically from the original ROM by
`tools/z80_regions.py`; it is **not assembled output**.

Run from the `Ys/` folder:

```sh
python tools/verify.py /path/to/Ys.sms
python tools/z80_regions.py /path/to/Ys.sms --check
python tests_phase2.py /path/to/Ys.sms
```

**Not yet established:** hardware execution trace, complete call graph,
all bank transitions, exact VDP timing, true source symbol names, assembler
compatibility, or binary-identical full ROM output.

Hardware references:
- https://www.smspower.org/Development/Mappers
- https://www.smspower.org/Development/MemoryMap
- https://www.smspower.org/Development/SMSOfficialDocs
