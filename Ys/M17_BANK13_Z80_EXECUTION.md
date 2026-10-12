# Milestone 17 — direct Z80 execution of Bank 13 graphics transfers

This milestone independently executes *actual source-reconstructed Z80
instructions*, extending the M16 static source-signature/RLE replay audit.
It uses the ROM-independent 16-bank reconstruction with SHA-256
`02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
It does **not** use a commercial ROM or require a local REA MCP server.

## Bounded execution path

`tools/bank13_consumer_execution_m17.py` implements only the Z80 instructions
exercised by the Bank 0 `$3ACC` directory consumer and `$0695` four-plane
RLE->VDP writer. It models the real `RST $18` indexed pointer lookup and
`RST $28` VDP address-command helper, the Sega slot-2 mapper (preselected to
physical Bank 13), AF/AF' swapping and carry behavior, stack, and ports
`$BF`/`$BE`. Unsupported instructions and unexpected control-flow targets
raise errors rather than silently generating guessed output.

The harness seeds entry arguments and the bank mapper. It does not simulate
startup, actual input/UI decisions, interrupts, timing, or VDP rendering.

## Verified source-backed behavior

- 50 individual directory items at `$BF8A`, each producing exactly 288
  Mode 4 pattern bytes at VRAM `$0120`, match an independent packet decoder.
- The original 26-record caller (index 0, B=`$1A`) executes 154,675
  instructions and writes **7,488 VDP bytes**.
- The original 24-record caller (index 26, B=`$18`) executes 141,604
  instructions and writes **6,912 VDP bytes**.
- Both batch calls begin at VDP command `$4120`; these are *alternative
  uploads* to the same VRAM area, not 50 simultaneously resident icons.
- VDP writes reach every intended address exactly once per upload. Each
  decoded 4-plane resource is stored interleaved in four-byte tile rows.
- Independent extra graphics callers are now executed rather than only
  inspected statically:

| Bank 13 source | Compressed | Decoded | VDP write commands |
| --- | ---: | ---: | --- |
| `$A9A3–$ABB9` | 535 bytes | 4 × 160 = 640 bytes | `$5600`, `$7000` |
| `$BBF7–$BC22` | 44 bytes | 4 × 32 = 128 bytes | `$7600` |

The two streams account for **579** of the **5,607** bytes in Bank 13's
previously unexplained tail. The other **5,028 bytes** are not classified.
The 535-byte asset is used at two different VRAM destinations, and its
resulting 640 bytes have the same SHA-256 at both destinations.

## Reproduce

```sh
cd Ys
python3 tools/bank13_consumer_execution_m17.py --check
python3 -m unittest -v tests_bank13_consumer_execution_m17
python3 tools/build_system_m10.py --check
```

Eight additional negative and positive regression tests cover the original
batch grouping, VDP write and address counts, all 50 directory pointers,
three tail transfer cases, malformed RLE controls, invalid indices, and a
fail-closed opcode mutation. The deterministic per-case report is
`whole_system/bank13_consumer_execution_m17.json`.

The M16 static replay and M17 bounded execution intentionally remain
independent regression implementations. Neither claims independent third-party
hardware/emulator confirmation or palette mapping.

Next: trace the unknown `$ABBA–$BBF6` and `$BC23–$BF89` data, identify
palette selection and UI state, then expand source ownership and consumers
in Banks 05, 14, and 15. Commit future verified work to branch `Ys`.
