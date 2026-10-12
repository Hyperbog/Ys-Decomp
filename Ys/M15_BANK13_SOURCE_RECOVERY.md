# Milestone 15 — Bank 13 source-owned RLE graphics

The verified Milestone 14 Bank 13 RLE format has been promoted from an external
report to **typed, reproducible source records** in `Ys/wholebank13/source.json`.
This is a source migration, not a claim that Bank 13's entire graphics system
has been semantically understood.

## What changed

- New `ys-bank13-source-v2` schema holds **50 ordered graphics resources** and
  **200 separate 72-byte decoded bitplanes**, each with the original RLE
  *packet control sequence* as its re-encoding recipe.
- Each `decoded_hex` block contains source-owned pixel-plane data. The recipe
  references those decoded bytes to regenerate the exact original packets;
  duplicated compressed payload literals are **not** preserved as opaque hex.
- The 50 pointers remain in their original (unsorted) 100-byte directory; records
  are laid out in physical ROM order and checked against every adjacent boundary.
- The **10,659 resource bytes** are recreated exactly; **5,607 trailing bytes**
  remain opaque and are separately stored as bounded source chunks.
- The source-only Bank 13 binary still has SHA-256
  `00227b5f7b913280a53e60ad90743371b82381a30c8514aa4d92a287e062b39e`.
- The **256 KiB** source-only cartridge must retain SHA-256
  `02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.

## Verification

```
cd Ys
python3 tools/bank13_semantic_source_m15.py --check
python3 -m unittest -v tests_bank13_semantic_source_m15
python3 tools/bank13_rle_m14.py --check
python3 -m unittest -v tests_bank13_rle_m14 tests_semantic_debt_m13
python3 tools/build_system_m10.py --check
```

The migration was performed **once** with
`python3 tools/bank13_semantic_source_m15.py --migrate`. The converter refuses
subsequent overwrite of an already migrated source. The full bank remains
completely reproducible, and the old v1 format remains supported for an
explicit authoring/capture path in `whole_banks05_13_14_15.py`.

The M10 build report remains a legacy conservative classification of final-four
bank data. It is *not* a live semantic-coverage measurement; use this document
and the M14 RLE inventory for the recovered Bank 13 graphics ownership.

## Still unresolved

Bitplane/palette ordering on actual SMS hardware, precise game-code consumers,
5,607 bytes after indexed resources, and analogous resource types in Banks 05,
14, and 15. Do not report these as solved.
