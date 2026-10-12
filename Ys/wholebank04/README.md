# Whole physical bank 04 — collision descriptors, collision predicate, and unresolved patterned data

## Binary reconstruction is complete; graphical semantics are not

Bank 4 (physical ROM `$10000–$13FFF`, CPU slot `$8000–$BFFF`) builds from project sources alone. All **16,384 bytes** reassemble to the original bank SHA-256:

`bd2e9c90792a9f462a3f8ff42763c676ffc9568d9913227e3460c592beb42354`

| Provenance | Bytes | Interpretation |
|---|---:|---|
| Existing source-backed rectangle table `$8000–$807B` | 124 | 31 four-field descriptors, actually read by `$807C` |
| Existing source-backed Z80 `$807C–$80A1` | 38 | Carry-returning collision/bounds predicate |
| New four-byte lane groups `$80A2–$BF61` | 16,064 | 502 groups × 8 rows × 4 bytes; **organizational grouping only; pixel format unproved** |
| New undecoded trailer `$BF62–$BFB7` | 86 | Unresolved bytes; do not assign asset semantics |
| New `$FF` padding `$BFB8–$BFFF` | 72 | Verified constant fill |
| **Bank total** | **16,384** | Entire bank ROM-free source-backed |

All records are explicit bytes or source fields in `wholebank04/source.json`; no original ROM is opened during `whole_bank04.py --verify-mixed` or `build_system_m7.py --standalone-banks`. `whole_bank04.py --capture original.sms` is an explicitly separate ROM-fingerprint-validated source-generation operation. The mixed assembly source `src/wholebank04/bank04_complete.asm` retains original Z80 mnemonics at `$807C`.

The 502 groups are intentionally **not claimed to be 502 graphics tiles**. 32-byte grouping is reversible and happens to cover the chosen interval; it does not establish actual game asset, rendering, or compression boundaries. The source-only bank image is therefore a strict byte-identity milestone rather than a fully semantically decoded subsystem.

## Executed collision predicate

`tools/bank04_collision_trace.py` executes the *original ROM opcodes* at `$807C` with synthetic A/BC/DE/IX state against a separate direct arithmetic predicate. It checks **3,968 cases** (31 records × 16 coordinate seeds × 8 boundary variants), tests both carry outcomes, and verifies all descriptor reads stay in `$8000–$807B`. This is **bounded execution**, not a real-game trace, boot test, or full-system emulator.

The ROM-independent `tools/bank04_crossbank_ledger.py` verifies three bank-1 call instructions to `$807C`, at CPU `$47C2`, `$486C`, and `$48DF`; preceding load uses `(IX+14)` for the first two and `(IX+13)` for the third. The bank-4 target is a **static bank candidate**, not proven active mapper state at those call sites. The caller consumes the returned carry flag to branch.

## Reproduce

From `Ys/`, with a legally obtained owner ROM for comparisons:

```
make bank04-source
make seven-bank-source
make seven-bank-rom-verify ROM='/path/to/Ys.sms'
make bank04-collision-verify ROM='/path/to/Ys.sms'
make bank04-crossbank-verify
make system-m7-verify ROM='/path/to/Ys.sms'
make seven-bank-wla-prepare
```

WLA-DX **fixture preparation is not independent assembly verification**. `seven-bank-wla-verify` deliberately fails closed if external `wla-z80`/`wlalink` binaries are unavailable.
