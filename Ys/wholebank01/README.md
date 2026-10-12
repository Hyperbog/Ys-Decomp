# Whole physical bank 01 — scene control and game-state code

## Byte-complete milestone, not semantic completion

Bank 1 (ROM physical `$04000–$07FFF`, CPU slot `$4000–$7FFF`) builds from the committed project sources **without opening the original game ROM**. All 16,384 bytes are independently emitted, and the result matches:

`SHA256 e91fa8fb9109dc13555967e208cb4650972d1965c2c9088be8d748ea177b4505`

This is one *whole-bank binary reconstruction*, **not** a complete system-control decompilation. The remaining unresolved spans include bytes that may be executable instructions. Do not describe the unresolved regions as decoded graphics, controls, or confidently identified data.

| Bank-1 ownership | Bytes | Confidence |
|---|---:|---|
| Previously ROM-matched Z80 assembly and SMS header | 779 | Established source-backed bytes |
| New disassembled Z80 candidate instructions | 1,717 | 875 mnemonic sites; byte-exact with the in-project encoder, but only statically analyzed |
| Two compact pointer directories | 20 | Ten pointer words, targets checked and bounded |
| Repetitive `$FF` bank filler | 340 | Exact length and byte value |
| Explicit unresolved spans | 13,528 | 71 bounded records; **not decoded**; includes possible additional Z80 instructions |
| **Total** | **16,384** | Entire physical bank builds without ROM fallback |

### Anchors and provenance

* Scene-related bank-1 instruction candidates are rooted in existing fixed-bank control-flow references and manually inspected entry points. Some bank-0 edges are **conditionally mapped**; the cartridge mapper state has not been independently established for every caller.
* `$4C03–$4C12`: eight little-endian handler pointers into `$4C13–$4C65`. An exact alias at the first two entries is retained. The directory is not a generalized proof of the scene-dispatch semantics.
* `$6028–$602B`: two scene setup pointers (`$602C`, `$6043`).
* `$7E9C–$7FEF`: 340 bytes of `$FF` padding; `$7FF0–$7FFF` retains the preexisting 16-byte SMS cartridge header.
* `wholebank01/source.json` owns the unresolved bytes as bounded, reversible data; it does not assert their format. `digests.json` pins source-owned code and data separately, and the complete bank image.
* `src/wholebank01/anchored_code.asm` contains **mnemonics**, not raw byte literals. The complete mixed source is `src/wholebank01/bank01_complete.asm`.

The analysis deliberately prefers recording unknown bytes over inventing a complete game-state machine. Accurate control-flow and cross-bank call mapping remain project tasks.

### Build / verification

```
cd Ys
make bank01-source
make six-bank-source
make bank01-verify ROM='/path/to/Ys - The Vanished Omens (USA, Europe).sms'
make six-bank-rom-verify ROM='/path/to/Ys - The Vanished Omens (USA, Europe).sms'
make system-m6-verify ROM='/path/to/Ys - The Vanished Omens (USA, Europe).sms'
make six-bank-wla-prepare
```

Normal `whole_bank01.py --verify-mixed` and the six standalone bank builds do **not** read a game ROM. The full 256-KiB build still requires the user-owned ROM as fallback in ten other banks. `whole_bank01.py --capture /path/to/original.sms` is the **explicit, fingerprint-checked, developer-only** source-generation path, not the usual build. Do not distribute a generated `.sms` or `.bin`.

`make six-bank-wla-verify` requires installed `wla-z80` and `wlalink`; generating WLA-DX fixtures is not evidence of successful independent assembly.

### Source-backed static system links

`tools/build_bank01_static_ledger.py --check` validates byte-exact instruction sites and captures direct control-flow references, memory mapper-write sites and hardware-port instructions. `wholebank01/static_control_links.json` is a reproducible, machine-readable **static** dependency ledger; slot-1 and slot-2 references remain conditional on the mapper state. This ledger adds no source-backed bytes and does not certify input processing or full-game scene execution.
