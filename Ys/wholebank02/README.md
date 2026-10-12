# Whole physical bank 02 — SMS sound code and data

**Binary milestone:** Entire 16-KiB physical bank 2 is emitted solely from
checked-in assembly and source records; no game ROM is opened in the normal
`whole_bank02.py` path. It matches SHA-256
`78b8ac016f2574ffece7f944f9b7680e873eb33f8481c31bbc0a480c4c74a4d8`.

## Source ownership

| Component | Bytes | Confidence |
|---|---:|---|
| Previously reconstructed sound Z80 code, song directory, and channel headers | 3,785 | ROM-matched source; not all routines runtime-traced |
| Newly recovered Z80 branch bridges | 16 | Mnemonics match original instructions; no gameplay trace |
| Newly source-backed, bounded sound data | 12,583 | Mix of mechanically typed and explicitly unresolved bytes |
| **Total** | **16,384** | **Byte-complete physical bank** |

Address ranges are CPU addresses relative to physical bank 2 in slot `$8000–$BFFF`.

* `$8A58–$8AE9`: 73 little-endian PSG periods, referenced by `LD HL,$8A58`.
* `$8AEA–$8B7B`: 73 little-endian FM register words, referenced by `LD HL,$8AEA`.
* `$8B7D–$8B9E`: 17-entry lookup pointer directory, anchoring records `$8B9F–$8C2E`.
* `$8C2F–$8C38`: five-entry secondary pointer directory with records through `$8C8F`.
* `$8C90–$8CFD`: 55 song directory words, reconstructed previously in Phase 21.
* `$AA77–$AD7F`: 21 regular four-channel descriptors, Phase 21.
* `$B319–$B6E7`: 24 one/two-channel variable song resources. Their previously established headers and new, individually bounded **618 bytes of event payloads** are separately sourced. Header fields remain partly uninterpreted.
* `$8CFE–$AA76`, `$AD80–$B318`, `$B6E8–$BE56`: **10,881 unresolved bytes** in preserved sound-data spans; exact spans are independently assembled, but this milestone does not decode their command grammar.
* `$BE57–$BFFF`: exactly 425 bytes of `$FF` tail padding.

The ROM-backed Z80 source links **5 sound-table references and 39 hardware write instruction sites** (see `static_sound_links.json`). The original Z80 code contains explicit `OUT ($F0),A`, `OUT ($F1),A`, and `OUT ($7F),A` instructions, confirming FM register/data and PSG port operations in the sound bank. These facts do **not** establish full music playback correctness.

## Build and verification

```
cd Ys
make bank02-source
make five-bank-source
make five-bank-rom-verify ROM='/path/to/Ys - The Vanished Omens (USA, Europe).sms'
make system-m5-verify ROM='/path/to/Ys - The Vanished Omens (USA, Europe).sms'
make five-bank-wla-prepare
```

`make five-bank-wla-verify` requires real external `wla-z80` and `wlalink`;
fixture preparation never masquerades as third-party verification.

### Semantics and evidence limits

* The preserved unknown event streams are **not** a decoded sheet-music score or source-level interpreter grammar.
* The in-project encoder assembles the mixed mnemonic/DB/DW source; independent WLA assembly is not yet proven.
* The game audio has **not** been exercised with a full-system emulator during this milestone.
* Normal independent bank build never needs a ROM. `--capture` is an explicit, fingerprint-checked, developer-only conversion from a user-owned copy.
