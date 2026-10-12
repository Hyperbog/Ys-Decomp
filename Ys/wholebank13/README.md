# Bank 13 — indexed resource directory (partial semantics)

The final 100 bytes preceding this bank's 18-byte FF tail contain 50 little-endian pointers. Directory CPU span `$BF8A–$BFED`; every target is a **distinct address** inside the same bank's `$8000–$BF89` resource body. Their ordering is not monotonic. The pointer source is `wholebank13/source.json`; the generated `DW` assembly is in `src/wholebank13/bank13_complete.asm`.

This establishes a directory of valid in-bank addresses, **not** the record lengths, record formats, compression method, or consumer. Payload byte spans are currently unresolved and preserved as source-owned chunks. See `whole_system/M10_README.md`.
