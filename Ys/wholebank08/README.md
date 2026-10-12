# Bank 8 — Script/resource bank with indexed state tables

**Source-only:** 16,384 bytes, ROM independent in normal generation. SHA-256 `3ef67b48f3b9e55adc980894ab1a4bfc932556f9f3e1a315204eb7456d4f53fa`.

| CPU range (inclusive) | Size | Source type | Confidence |
|---|---:|---|---|
| `$8000–$BEE7` | 16,104 | Explicit reversible unresolved script/resource chunks | Unknown grammar; binary only |
| `$BEE8–$BF71` | 138 | Canonical existing Z80 source (not newly discovered) | Mnemonic byte exact |
| `$BF72–$BFB5` | 68 | Two six-byte offset tables, one byte, eleven five-byte records | Pointer/index arithmetic backed by `$BF0C` |
| `$BFB6–$BFDB` | 38 | New Z80 mnemonic source, including RAM `$C120` read and state table | Decoder + encoder exact; runtime unverified |
| `$BFDC–$BFF0` | 21 | Unresolved trailing bytes | Binary only |
| `$BFF1–$BFFF` | 15 | FF padding | Exact fill |

Fixed bank 0 `$0FB1` contains `LD A,$08; LD ($FFFF),A; CALL $BEE8`. This is static evidence of a bank-8 entry point; it does not certify the call ran during gameplay. The bank-8 state routine indexes `$BF7F` in five-byte strides; the table is partitioned at that exact boundary. The main 16,104-byte stream is **not decoded** merely because it is stored in project source.

Rebuild: `python tools/whole_banks08_10.py --verify-mixed`. Compare against locally owned ROM using `--verify-rom /path/to/Ys.sms`. See `tools/build_system_m8.py` for nine-bank standalone build.
