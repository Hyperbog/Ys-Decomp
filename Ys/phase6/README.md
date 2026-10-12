# Phase 6 — Doubled target, fixed-bank dispatch and audio descriptor structure

**Target:** >= 9,868 additional distinct classified ROM bytes (twice Phase 5).
**Result:** **14,521 additional bytes**, 2.94× Phase 5; cumulative
**21,523 / 262,144 (8.21%)**. Input ROM fingerprint: `../manifest.json`.

## Coverage with scope and limitations

| Classification | Additional bytes | Evidence/meaning |
|---|---:|---|
| Fixed bank 0 statically decoded code | 4,474 | 2,027 instruction starts; explicit CFG seeds; per-instruction ROM byte checks |
| Bounded data and table spans | 10,047 | SHA-256 on each span; structure known only for pointer directories and regular descriptors |
| **Total new** | **14,521** | Disjoint from earlier Phase 1–5 byte sets |

This measures **ROM bytes assigned to bounded static code or data regions**,
not matching rebuilt assembly, verified functions, played audio, or executable
coverage. Some music event stream ranges are *opaque*: their bytes and placement
are verified; the precise internal format and reachability of every byte are
not. The optional `B319–B6ED` region was investigated but deliberately **not**
included because its upper boundary and mixed data layout remain uncertain.

## Main discoveries

- Fixed bank 0 `$205A–$20AB` is a **41-word game-state jump table**, used by
  the `$2055` dispatcher. All 41 target values point to decoded instruction
  starts in this snapshot. Repeated targets are meaningful; do not invent
  distinct game states for duplicate entries.
- Fixed bank 0 `$2C24–$2C35` is a **nine-word scene dispatcher**. The nine
  pointers are `2C36`, `2D9D`, `2F2A`, `3014`, `3194`, `329C`, `333B`, `3415`,
  and `3519`, all instruction starts in the checked listing.
- Fixed bank 0 `$2533–$2584` contains **41 little-endian references** to
  **23 distinct nine-byte records** at `$2585–$2653`. The entries are
  aligned with `$2585 + 9n`; record fields are not fully identified.
- The known bank-2 song directory `$8C90–$8CFD` has **55 pointer entries,
  45 unique destinations**. Its first 21 destinations are evenly spaced
  `$25` bytes, beginning at `$AA77`.
- Each of these **21 regular audio descriptors** starts with `$04` and has
  four nine-byte channel records. In each channel record, bytes `+3/+4`
  form a little-endian stream pointer. This yields **84 pointer references
  to 77 unique addresses**, all bounded in `$8D40–$B318`.

**Important address overlap:** one descriptor references `$8D57`, which
belongs to a previously classified Phase 4 lookup span. We retain the
previous classification and log the shared pointer rather than double-counting
or pretending the address has a single proven runtime role.

## New files and verification

- `regions.json` — individual table/opaque-data bounds, checksums and
  confidence levels.
- `code.lst` — fixed-bank Z80 listing; includes code bytes, but **does not
  embed raw music-event payloads**.
- `coverage.json` — deterministic byte totals, branch uncertainty ledger,
  dispatch target listings and digests.
- `audio_descriptors.csv` — 84 indexed channel records represented by
  pointers and SHA-256 digests; not a dump of the game's audio streams.
- `../tools/z80_cfg_phase6.py` — bank-limited CFG walker and snapshot checker.
- `../tools/song_headers_phase6.py` — 21×4 descriptor extractor.
- `../tests_phase6.py` — independent byte-level checks, structural assertions,
  and deliberate corruption tests.

```sh
cd Ys
ROM='/path/to/Ys - The Vanished Omens (USA, Europe).sms'
python tools/verify.py "$ROM"
python tools/z80_cfg_phase5.py "$ROM" --check
python tools/z80_cfg_phase6.py "$ROM" --check
python tools/song_headers_phase6.py "$ROM" --check
for N in check phase2 phase3 phase4 phase5 phase6; do
    python "tests_${N}.py" "$ROM"
done
```

## Unresolved, not silently assigned

1. Mapper state for fixed-bank jumps/calls into `$4000–$BFFF`, especially
   `$0DDA -> $86C1` and new edges recorded in `coverage.json`.
2. Detailed format of embedded music stream commands and per-voice timing.
3. Runtime behavior and the semantic meaning of nine-byte resource records.
4. Remaining later audio descriptors beginning at `$B319` and any graphics
   payload beyond them.
5. Independent assembler-produced binary equivalence; this phase provides
   disassembly/metadata, **not** a binary-matching compiled ROM.

**Next checkpoint:** decode bounded music stream opcodes into typed events,
then reconstruct and assemble a small Z80 routine for byte-identical output.
