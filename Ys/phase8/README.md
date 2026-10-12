# Phase 8 — Mapper-qualified Z80 roots and reversible Mode-4 tiles

**Source:** USA/Europe Ys SMS cartridge, SHA-256 in `../manifest.json`.
**Status:** ROM-byte verification complete; no emulator trace, build-equivalence claim, or complete image/text grammar.

## Incremental results, without counting the same bytes twice

| Classification | This phase | Evidence |
|---|---:|---|
| New rooted Z80 code | **797 bytes / 502 instructions** | Independent ROM-byte listing and physical-bank SHA-256 |
| New bank-4 indexed table | **124 bytes / 31 × 4-byte records** | `$807C–$8082` indexes `$8000 + 4*A`; table ends where function begins |
| **New distinct classified ROM bytes** | **921** | No overlap with preceding phase coverage |
| Previous opaque data *upgraded* to Mode-4-compatible tiles | **5,632 bytes / 176 tiles** | Full 4-bitplane decode and reverse encode, block digests, preview |
| Previous provisional bytes remaining without a validated grammar | **8,909** | 14,541 – 5,632; includes other bank-3 payload |
| **Cumulative candidate footprint** | **37,748 / 262,144 (14.40%)** | Prior 36,827 + 921; **not** game completion |

The last 5,632 bytes are **NOT newly covered ROM bytes**: they were in Phase 7's provisional bank-3 spans. This phase increases *structural understanding*, not the unique-byte coverage count for them. Mode-4 compatibility and visual coherence do not prove every tile is used or establish actual palette selection.

## Five newly rooted physical banks

| Mapper value written to `$FFFF` | CPU entry | Physical ROM offset | Classified bytes |
|---|---|---|---:|
| `$04` | `$807C` | `$1007C` | 38 |
| `$07` | `$86C1`, `$8819`, `$8856` | `$1C6C1`, `$1C819`, `$1C856` | 438 |
| `$08` | `$BEE8` | `$23EE8` | 138 |
| `$0A` | `$BEF7` | `$2BEF7` | 75 |
| `$0C` | `$9EFC` | `$31EFC` | 108 |

**Example of concrete prior uncertainty resolved:** fixed bank `$0DD5–$0DDA` is `LD A,$07; LD ($FFFF),A; CALL $86C1`, assigning the call to physical ROM offset `$1C6C1` *at this call site*. Previously calling it bank 2 was incorrect. Likewise `$0C4D–$0C52` and `$1D85–$1D8A` explicitly select bank 2 before `$8803`.

The bank-1 routine at `$476C` writes `$04` at `$4773`. Its three calls to CPU `$807C` (`$47C2/$486C/$48DF`) are therefore consistent with bank-4 physical `$1007C`, **provided the code is entered at `$476C` with the expected control flow**. We have not proven that condition through runtime tracing. Mapper values established before other mapped destinations are not silently extended across unknown calls or bank changes. There are **46 ROM-backed `$FFFF` writes** enumerated by the analyzer, including dynamic-value writes.

The bank-4 `$807C` function indexes a `$8000` lookup in groups of four bytes; its bounded 124-byte prefix comprises 31 complete indexed records before executable bytes at `$807C`. The field meanings and valid runtime indices are not established.

## Bank-3 tile reconstruction

Physical `$C000–$D5FF` has 176 complete 32-byte chunks matching the SMS Mode-4 organization: 8 pixel rows, each represented by four ordered bitplanes, with the most significant bit corresponding to the left pixel. The per-tile byte-preserving transformation is independently reversible:

- `$C000–$CFFF`: 128 chunks, **76 distinct raw tile patterns**.
- `$D000–$D5FF`: 48 chunks, **48 distinct raw tile patterns**.
- The preview renders 16 levels of *artificial grayscale* corresponding to palette indices 0–15, **not the game's colors**.
- Fixed-bank code `$0BA1–$0BB6` writes bank 3, then transfers bytes through VDP data port `$BE`; the source address is supplied by its caller, so this supports a VDP-data interpretation without proving which precise bank-3 bytes the loop uses.
- `$D600–$DEFF` and `$DF00–$F8CC` remain provisionally opaque; do not infer a graphic format or text decoder merely from appearance.

Hardware references: [SMS Power mapper](https://www.smspower.org/Development/Mappers), [SMS Power memory map](https://www.smspower.org/Development/MemoryMap), [SMS Power tile format](https://www.smspower.org/Development/Tiles).

## Artifacts and verification

- `banked_code.lst`: physically indexed code listing; no assembled binary.
- `mapper_audit.json`: all 46 statically seen slot-2 writes, explicit bank values where immediately available, root provenance and ambiguity.
- `tile_metadata.json`: per-range digests, tile/pixel counts, decoding status; *no raw ROM graphics*.
- `../tools/bank_trace_phase8.py`, `../tools/mode4_tiles_phase8.py`: deterministic reconstructions from independently supplied cartridge.
- `../tests_phase8.py`: **14 independent checks**, including mutation rejection.

```sh
cd Ys
ROM='/path/to/Ys - The Vanished Omens (USA, Europe).sms'
python tools/bank_trace_phase8.py "$ROM" --check
python tools/mode4_tiles_phase8.py "$ROM" --check
python tests_phase8.py "$ROM"
# Optional, not tracked in Git:
python tools/mode4_tiles_phase8.py "$ROM" --check --atlas /tmp/ys_tiles.png
```

**Still unresolved:** live mapper state under interrupts and nested calls, actual palette/VDP upload paths, bank-3 remaining opaque formats, text encoding, and byte-identical output from a genuine Z80 assembler. Do not report static instruction transcription as build equivalence.
