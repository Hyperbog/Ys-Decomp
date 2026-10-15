# Ys SMS — Full ROM assembly and data reference

**Canonical master file:** [MASTER_ROM_LISTING.txt](MASTER_ROM_LISTING.txt)  
**Verified original-cartridge footprint:** 262,144 bytes = **16 × 16 KiB**.  
**Source-original SHA-256:** `02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.

This is the complete **persistent, searchable reference** for the original
Sega Master System *Ys: The Vanished Omens* USA/Europe ROM used by this repository.
The master contains **all 16 physical-bank source listings in a single 27,999-line
text file**, preserving known Z80 mnemonics, labels, original data literals,
and explicit unresolved regions. You **do not need to disassemble the ROM again**
to consult its existing bytes and supported instruction boundaries.

**Confidence boundary:** The source reconstructs **100% of the original ROM's
bytes**, but it is **not a fully semantically decompiled executable**. Only
**22,552 bytes** currently appear as recovered Z80 mnemonics; the other
**239,592 bytes** are byte-preserving `DB`/`DW` data directives,
some of which may eventually be demonstrated to contain executable code.
A minimum **141,581 bytes** are explicitly labeled uncertain;
unlabeled data is *not automatically understood*. See
[M13 semantic audit](M13_COMPLETION_AUDIT.md).

## Bank-by-bank navigation

| Physical bank / canonical assembly | ROM offset | Mapper-visible CPU address | Z80 mnemonic bytes | DB/DW bytes | Current known focus |
|---|---|---|---:|---:|---|
| [00](../src/wholebank00/bank00_complete.asm) | `$00000–$03FFF` | `$0000–$3FFF` | 14,453 | 1,931 | Boot/reset, interrupts, fixed-bank dispatch |
| [01](../src/wholebank01/bank01_complete.asm) | `$04000–$07FFF` | `$4000–$7FFF` | 2,480 | 13,904 | Scene / object control; bank-4 caller path |
| [02](../src/wholebank02/bank02_complete.asm) | `$08000–$0BFFF` | `$8000–$BFFF` | 2,557 | 13,827 | Sound command and FM/PSG handlers |
| [03](../src/wholebank03/bank03_complete.asm) | `$0C000–$0FFFF` | `$8000–$BFFF` | 0 | 16,384 | Mode-4 patterns and visual/control resources |
| [04](../src/wholebank04/bank04_complete.asm) | `$10000–$13FFF` | `$8000–$BFFF` | 38 | 16,346 | Collision descriptor records; residual assets |
| [05](../src/wholebank05/bank05_complete.asm) | `$14000–$17FFF` | `$8000–$BFFF` | 0 | 16,384 | Source-owned packed graphics/resource bytes |
| [06](../src/wholebank06/bank06_complete.asm) | `$18000–$1BFFF` | `$8000–$BFFF` | 644 | 15,740 | Sprite SAT records and original producer |
| [07](../src/wholebank07/bank07_complete.asm) | `$1C000–$1FFFF` | `$8000–$BFFF` | 1,956 | 14,428 | Graphics dispatch and object records |
| [08](../src/wholebank08/bank08_complete.asm) | `$20000–$23FFF` | `$8000–$BFFF` | 176 | 16,208 | Partly recovered script/resource data |
| [09](../src/wholebank09/bank09_complete.asm) | `$24000–$27FFF` | `$8000–$BFFF` | 65 | 16,319 | Glyph / numeric text resources |
| [10](../src/wholebank10/bank10_complete.asm) | `$28000–$2BFFF` | `$8000–$BFFF` | 75 | 16,309 | Script/text and numeric resources |
| [11](../src/wholebank11/bank11_complete.asm) | `$2C000–$2FFFF` | `$8000–$BFFF` | 0 | 16,384 | Source-owned data; meaning not fully established |
| [12](../src/wholebank12/bank12_complete.asm) | `$30000–$33FFF` | `$8000–$BFFF` | 108 | 16,276 | Resource indexes and related data |
| [13](../src/wholebank13/bank13_complete.asm) | `$34000–$37FFF` | `$8000–$BFFF` | 0 | 16,384 | Asset bytes, 50-word resource pointer directory |
| [14](../src/wholebank14/bank14_complete.asm) | `$38000–$3BFFF` | `$8000–$BFFF` | 0 | 16,384 | Unresolved resources |
| [15](../src/wholebank15/bank15_complete.asm) | `$3C000–$3FFFF` | `$8000–$BFFF` | 0 | 16,384 | Unresolved resources |
| **TOTAL** | `$00000–$3FFFF` | Mapper-dependent | **22,552** | **239,592** | Complete byte ownership; incomplete semantics |

**Addressing:** CPU `$0000–$3FFF` is bank 0's initial slot (the first
1 KiB is fixed/unpaged), `$4000–$7FFF` is the bank-1 slot on the
referenced source configuration, and **banks 2–15 share**
the mapper-controlled CPU `$8000–$BFFF` window. A bare
`$8204` address does **not** uniquely identify a physical ROM bank;
use **physical-bank number + CPU address** (or the absolute ROM offset).
`$8204` in physical bank 2 corresponds to ROM offset `$08204`.

## How to use this instead of repeated disassembly

- **Find instructions/data:** Search [the one-file master](MASTER_ROM_LISTING.txt)
  for a label or address, or navigate directly to a bank's
  `bankXX_complete.asm` file in the table above.
- **Identify a bank:** The master has a physical-bank heading,
  original ROM-offset span, mapped CPU-address span and source-file
  SHA-256 before each bank's complete listing.
- **Check whether bytes are established code:** Only trust explicit
  mnemonics where current source and independent instruction
  evidence support them. An undecoded span shown as `DB` is
  preserved original data, **not proven code**. Do not blindly
  linear-disassemble banks 3, 5, or 13–15 and invent execution paths.
- **Re-generate this reference only when assembly sources change:**
  the generator **copies the verified bank sources**, not re-decompiles
  the ROM, and checks source instruction/data coverage against the
  committed M13 audit.

From the **repository root**:

```sh
# No commercial ROM required; verify that the master still matches
# all 16 authoritative per-bank source listings.
python3 Ys/tools/build_master_rom_listing.py --check

# Only if the canonical sources were intentionally changed and
# independently reverified:
python3 Ys/tools/build_master_rom_listing.py

# Optional: create another local searchable copy elsewhere.
python3 Ys/tools/build_master_rom_listing.py --out /tmp/ys-master.txt

# Quick terminal lookup. Multiple banks can use the same CPU address.
rg -n '^(SoundFrameUpdate|SpriteRecordPointers|CollisionBox|SceneControlEntry):|\$8204' \
  Ys/whole_system/MASTER_ROM_LISTING.txt
```

To independently verify the **byte-exact cartridge reconstruction** as well,
the existing source-only builder remains available:

```sh
python3 Ys/tools/semantic_debt_m13.py --check
python3 Ys/tools/build_system_m10.py --check
```

These are **verification commands**, not prerequisites for reading the
committed master reference. No original ROM image is needed in the
repository and no ROM binary is committed. The master listing is a
**human-readable research document**, not an assemblable single translation
unit (bank 2 onward reuses the same mapped Z80 addresses). The
separate canonical bank files remain the authoritative assembly inputs.

## Maintenance requirements

1. Update the appropriate `Ys/src/wholebankXX/bankXX_complete.asm`
   only with source-backed instruction/data evidence, preserving
   exact bank byte coverage.
2. Re-run and review the [M13 semantic audit](M13_COMPLETION_AUDIT.md)
   and ROM identity checks. Do not relabel previously opaque bytes
   as executable solely based on a guessed opcode decoder.
3. Regenerate the master and require `--check` in CI.
4. Keep game-meaning assertions and Z80 runtime observations in
   separate research reports: a full listing **does not** automatically
   establish which stage, actor, or collision routine runs in gameplay.

**Existing complete reconstruction:** [M10 source-only build](M10_README.md).
**Current semantic limitations:** [M13 semantic audit](M13_COMPLETION_AUDIT.md).
