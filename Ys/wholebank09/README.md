# Bank 9 — Source-only / partial semantic decoding

16,384 bytes reconstructed independently from `source.json`, its verified Z80 region, and explicit FF fill; `digests.json` fingerprints the original bank. `$BEFB–$BF3B` is mnemonic code. `$BF3C–$BF4B` is a proven eight-word pointer directory to eight six-byte VDP data sequences at `$BF4C–$BF7B`. The remaining large language/resource span is explicitly unresolved. No fully decoded font or script grammar is claimed.

`tools/bank09_glyph_trace.py` executes the original instruction loop for all 8 entries × 3 seeded separator values (24 runs, 288 VDP bytes). VRAM address, mapper selection, initial HL and separator are initialized artificially. This is not a full-game emulator trace.
