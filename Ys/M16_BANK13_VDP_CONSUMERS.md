# Milestone 16 — Bank 13 RLE consumer and VDP destination audit

Verified directly against **ROM-independent source-built Bank 0 and Bank 13**, using an explicit set of nine Z80 opcode signatures and an independent bounded RLE / VDP replay. These are source-backed, static findings, **not** a claim of live CPU/VDP emulation, exact palette rendering, or full gameplay validation.

## Indexed inventory icons — full fixed-bank producer path

| CPU address | Z80 evidence | Established effect |
| --- | --- | --- |
| `$0018` | `RST $18`: doubles A, adds HL, fetches little-endian word | A is the zero-based resource index into a `DW` table |
| `$0028` | `RST $28`: `OUT ($BF),E`, `OUT ($BF),D` | DE is submitted as the VDP control word |
| `$0695–$06C0` | `LD C,$04`, four zero-terminated packet streams, `OUT ($BE),A`, `DE+=4`, `INC DE` after each plane | RLE expands into **interleaved** Mode-4 graphics byte lanes, four planes per record |
| `$3ACC–$3AE2` | `LD HL,$BF8A`, `RST $18`, `CALL $0695`, `DE+=$0120`, `INC A`, `DJNZ` | Directory indexed by A; uploads consecutive graphics assets; advances VDP start by 288 bytes |
| `$38E2–$38FB` | select physical Bank 13, A=0, B=`$1A`, DE=`$4120`, call `$3ACC` | Uploads resource indices **0–25** to VRAM starting `$0120` |
| `$398C–$399A` | select physical Bank 13, A=`$1A`, B=`$18`, DE=`$4120`, call `$3ACC` | Uploads resource indices **26–49** to the same VRAM start |

Since each indexed resource has four decoded planes of 72 bytes, the writer outputs 288 **VDP bytes** per icon. Each Mode-4 tile is 8×8×4bpp = 32 bytes, so nine tiles = a **3×3 layout of 8×8 tiles**. The tile slot at VRAM `$0120` is tile index **9**; subsequent icons advance by nine tiles. The initial load fills 234 tiles (7,488 bytes, ending `$1E60`), and the alternate load fills 216 tiles (6,912 bytes, ending `$1C20`). Both start at the *same* address, so these pages represent alternative loads rather than two simultaneously resident banks of graphics.

This establishes the four-plane lane order written to VDP. It does **not** establish final CRAM palette selection, visual color values, or the gameplay circumstances activating each page.

## Additional RLE graphics recovered inside the 5,607-byte trailing region

The Bank 0 source also contains three **direct calls** to the same `$0695` RLE VDP writer with pointers inside the previously unresolved Bank 13 tail:

| Source range, end exclusive | Compressed | Decoded plane sizes | Unique VDP data | VDP command(s) | Code-site anchors |
| --- | ---: | ---: | ---: | --- | --- |
| `$A9A3–$ABBA` | **535** bytes | 4 × 160 | 640 bytes = 20 tiles | `$5600` and `$7000` | `$3CDE` and `$3E57` |
| `$BBF7–$BC23` | **44** bytes | 4 × 32 | 128 bytes = 4 tiles | `$7600` | `$38E7` |

These streams decode with the exact same RLE packet rules as the 50 inventory icons, but have *different plane sizes*. Both have valid zero terminators and independent endpoint checks. The `$A9A3` stream is loaded twice to different VRAM destinations.

**Accounting:** 579 of the original 5,607 trailing source bytes now have explicitly proven RLE-graphics ownership (10.3%). **5,028 trailing bytes remain unattributed**, including intermediate raw/table bytes not shown to be part of either new stream. Do not label this remaining region a single opaque asset or assume that its format is RLE. In particular, `$ABBA` and `$ACB2` are separately referenced through `$0BEF` and have not been classified here as four-plane graphics.

## Executable regression evidence

- `tools/bank13_vdp_consumer_m16.py --check` recreates the byte-for-byte-derived JSON inventory without an original ROM.
- `tests_bank13_vdp_consumer_m16.py` validates nine executable source-code anchors, both resource pages, nine-tile indexing and destinations, 50 source regions, four-plane VRAM layout, two tail stream boundaries, corrupt pointer rejection, malformed RLE rejection, source-bank hashes, and fixed page-output hashes.
- `whole_system/bank13_vdp_consumer_m16.json` records each icon's source pointer, end, VDP destination, tile slot, VDP-byte hash; page-wide hashes; and the two separately identified tail resource spans.
- The existing source-only ROM reconstruction and M13–M15 suites remain the parity and regression authority. The M16 audit reads source bytes without modifying them.

## Next

1. Extend static and bounded opcode execution validation of the `$0695` routine to distinguish inferred VDP writes from machine-level traced writes.
2. Map CRAM palette selection and which UI flows activate the two 26/24-item pages.
3. Investigate the `$ABBA–$BBF7` section and the remainder of the `$BC23–$BF89` tail via callsite references, while preserving byte-identical source and explicit unknowns.
4. Continue RLE format/consumer auditing in Banks 05, 14, and 15.

Every new verified milestone should be committed to the `Ys` Git branch and pass source-only CI.
