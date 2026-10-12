# Ys SMS physical bank 6: standalone source-only build

**Binary closure:** 16,384 / 16,384 bytes, SHA-256
`cd64e2820b24ee57c2d909b9edf871246d37fc5e9e6dc889c0d58116a92524eb`.

* `$8000–$9C17` — previously reconstructed 7,192 bytes: sprite count/pointer
  directory, sprite records, producer code at `$9932`, object handlers,
  offset and dispatch tables. These retain their original canonical assembly
  and typed record sources.
* `$9C18–$B907` — **7,408 bytes** of visual data grouped into 926 8-byte
  lanes. The source grouping is lossless, **not proof** of 1bpp, 2bpp or 4bpp
  encoding. Fixed bank 0 includes a ROM-matched `LD HL,$9C18` instruction in
  its graphics transfer path, but the runtime mapper state is unverified.
* `$B908–$B9C7` — 192 tile-index bytes grouped into 24 eight-byte rows.
* `$B9C8–$B9CF` — four little-endian layout pointers, including an explicit
  alias to `$B9F8`: `$B9D0`, `$B9F8`, `$BA23`, `$B9F8`.
* `$B9D0–$BA4A` — three count-prefixed layouts of 13, 14 and 13 triplets
  respectively. All records have `1 + 3 × count` length.
* `$BA4B–$BA5A` — 16 additional tile-index bytes.
* `$BA5B–$BA62` — second four-pointer layout directory (`$BA63`, `$BA7C`,
  `$BA9B`, `$BABA`), referenced by a byte-matched fixed-bank `LD HL,$BA5B`.
* `$BA63–$BAD8` — four additional count-prefixed layouts, with 8, 10, 10,
  and 10 triplets, totaling **78 triplets across all seven layouts**.
* `$BAD9–$BFF8` — 1,312 tile-index bytes in 164 eight-byte rows.
* `$BFF9–$BFFF` — seven `FF` fill bytes.

**Meaning not yet demonstrated:** exact visual compression/bitplane semantics;
field meanings of each triplet; runtime active cartridge bank at all call
sites; complete game behavior. These are not reclassified as understood by
virtue of byte-exact reproduction. The sprite record producer and SAT upload
were previously exercised with a bounded Z80 interpreter (Phases 19–20), not a
full-system emulator.

## Build

```sh
cd Ys
python tools/whole_bank06.py --verify-mixed
python tools/build_sprite_asset_ledger_m4.py --check
python tools/build_system_m4.py --standalone-banks
python tests_whole_bank06.py '/path/to/Ys - The Vanished Omens (USA, Europe).sms'
python tools/build_system_m4.py '/path/to/Ys - The Vanished Omens (USA, Europe).sms' --check
python tools/wla_system_m4.py --prepare  # preparation only, not verification
python tools/wla_system_m4.py --run      # needs installed wla-z80 and wlalink
```

`--capture` is a one-time, explicit source-data extraction requiring the
original owner-supplied ROM. Normal builds use only the committed project files.
The full-ROM overlay still uses the original ROM for the other twelve banks.
Original ROM binaries are intentionally excluded from the repository.

The two bank-0 references are tracked as **static literal evidence only** in
`asset_ledger.json`; they do not imply executed bank-select sequence proof.
