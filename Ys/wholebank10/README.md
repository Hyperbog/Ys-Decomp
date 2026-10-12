# Bank 10 — Resource bank, text directory and number-to-VDP output

**Source-only:** 16,384 bytes, ROM independent in normal generation. SHA-256 `d8e67566e6b8ec634d346a88426fcbf6975ed8021037b74895d0aa0d6057f9db`.

| CPU range | Size | Source type | Confidence |
|---|---:|---|---|
| `$8000–$BE6F` | 15,984 | Explicit unresolved resource chunks | Binary-only; encoding unknown |
| `$BE70–$BE85` | 22 | Eleven little-endian words | Nine unique entries and two aliases |
| `$BE86–$BEF6` | 113 | Nine FF-terminated encoded strings | Record bounds verified, character map unresolved |
| `$BEF7–$BF41` | 75 | Existing canonical Z80 instruction source | Mnemonic and ROM exact |
| `$BF42–$BFFC` | 187 | Explicit unresolved trailing bytes | Binary only |
| `$BFFD–$BFFF` | 3 | FF padding | Exact fill |

Bank 0 includes mapper-select + jumps at `$38C4` to bank 10 `$BF16`, and `$3E86` to bank 10 `$BEF7`; these are static candidates rather than gameplay traces.

**Bounded execution:** The original instructions at `$BEF8–$BF41` are run for 265 inputs (0 through 65535 sampled plus decimal boundaries), with the `$BF35` print subroutine. The output contains 5 decimal glyph bytes (`'0'`-`'9'`) interleaved with five copies of RAM `$C026` at port `$BE` (10 bytes per run), compared against an independent formatting expectation. The preceding `RST $28` at `$BEF7`, VDP address state, and full game runtime remain unmodeled. See `tools/bank10_decimal_trace.py`.

Rebuild: `python tools/whole_banks08_10.py --verify-mixed`. Compare to original owner ROM using `--verify-rom /path/to/Ys.sms`.
