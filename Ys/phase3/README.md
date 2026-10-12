# Phase 3 — banked update, interrupt subdispatch and SRAM bounds

**ROM:** `../manifest.json` SHA-256. All numeric addresses below are hexadecimal.
**Method:** anchored Z80 decoder and fixed-byte regression tests; no emulator trace or assembler binary round-trip is claimed.

## Confirmed code/data boundaries

| ROM offset / CPU address | Size | Classification | Evidence |
| --- | ---: | --- | --- |
| 001B4–001EA | 55 | four targets of the IM1 dispatch at 01AC | calls and bank selection in ROM |
| 001EB–001FC | 18 | nine little-endian words, **data**, not code | `01E2: LD HL,01EB; 01E5: RST 08` |
| 001FD–0025F | 99 | first target `RET`, then helper code | Z80 instruction scan |
| 003B8–00405 | 78 | interrupt-driven VDP output paths | writes to ports BF and BE |
| 005F2–00623 | 50 | bank-3 VDP transfer and bank restore | saves FFFC/FFFF before remapping |
| 08000–080F0 | 241 | bank-2 update entry and local helpers | fixed slot-2 mapping in calling path |

**Newly classified:** 523 instruction bytes and 18 table bytes, totaling **541**;
**cumulative distinct bytes:** 1,465 / 262,144 (about 0.56%).
This measures byte classification only, not percent of game logic understood.

## Dispatch and mapper ledger

- `$01D7` selects ROM bank 3 via `$FFFF` and loads `A` from RAM `$C105`.
  `RST $08` dispatches from the **base `$01EB`**, using `2*A` as the word offset.
  Table entries for `A=0..8`: `01FD, 01FE, 0288, 02B1, 02C2,
  032A, 0339, 035D, 0389`. Other values of `A` are **not validated**.
- `$01C6` selects bank 7 and jumps to `$8819`. **Calculated** ROM file
  offset for bank 7 in slot 2: `$1C819` (not yet decoded).
- `$05F2` temporarily selects bank 3, performs VDP data-port output, and
  restores both mapper registers at `$FFFC` and `$FFFF`.
- Bank 2 `$8000` calls `$8067`, `$8080`, `$80C0`, `$81D9` in sequence.
  `$DE60` selects one of two groups of 32-byte work records. `$8067`
  decrements `$DE61`; when it reaches zero, reloads it from `$DE62`
  and increments six record bytes beginning at `$DE79`, stride `$20`.
  **Supported interpretation:** timing/update work; precise gameplay or
  music meanings are **unverified**. Incomplete assembly in
  `../src/bank02_update.asm` covers `$8000–$808E`.

## Save-RAM reconstruction

At `$079A`, bit 3 of `$FFFC` is set, mapping cartridge SRAM into CPU
`$8000–$BFFF`. It compares a 24-byte marker at SRAM `$8010–$8027` with
ROM `$0782–$0799`: `Ancient Ys Vanished Omen`. On mismatch, instructions at
`$07B4–$07C0` clear `$8010` and execute `LDIR` of `$1FEE` zero bytes from
`$8010` to `$8011–$9FFE`. The signature is then copied to `$8010–$8027`.
On either path, `$FFFC` bit 3 is cleared before returning.

This demonstrates an initialization region of **8,175 bytes**, but does
**not** establish a save-slot format, checksum, battery presence, or the
meaning of the remaining SRAM bytes. Do not call it a fully decoded save.

## Reproduce

```sh
cd Ys
python tools/verify.py /path/to/Ys.sms
python tools/z80_regions.py /path/to/Ys.sms --phase 2 --check
python tools/z80_regions.py /path/to/Ys.sms --phase 3 --check
python tests_phase3.py /path/to/Ys.sms
```

Hardware reference: https://www.smspower.org/Development/Mappers
($FFFC bit 3 controls SRAM-in-slot-2; $FFFF selects ROM bank for slot 2).

**Next limited target:** trace `$81D9` and `$808F` within bank 2, then
identify producer and consumer accesses to `$DE60–$DEAF`; validate
save-slot hypothesis with actual emulator SRAM snapshots.
