# Phase 5 — 4,934 more Ys SMS ROM bytes classified

**Input:** `Ys - The Vanished Omens (USA, Europe).sms`, exact SHA-256 in `../manifest.json`.
**Scope:** fixed bank 0 (`$0000–$3FFF`) and bank 2 in CPU slot 2 (`$8000–$BFFF`) **when bank 2 is mapped**.
**Evidence:** original-ROM SHA-256 check, deterministic Z80 instruction-boundary listing,
non-overlap enforcement, independently hashed data tables, and regression mutation tests.
**Limitation:** This is **bounded static analysis**, not a functioning source build, emulator trace,
or complete sound engine. Functions and exact runtime bank identities may require further proof.

## Coverage

| Category | Newly classified bytes |
| --- | ---: |
| Fixed ROM bank 0, decoded reachable instruction regions | 2,499 |
| ROM bank 2, decoded reachable instruction regions | 1,655 |
| Explicit data tables, all bank 2 | 780 |
| **Phase 5 new, distinct** | **4,934** |
| **Phases 1–5 cumulative** | **7,002 / 262,144 (2.67%)** |

The new Z80 listing contains **2,055 instruction starts**. Classification is intentionally
not described as recovered source or game-functionality completion.

### Bounded instruction islands

The walker traces from known earlier code edges, explicit game-state entrypoints,
and 20 ROM-anchored dispatch targets. It stops at returns, indirect jumps,
unresolved mapper states, old classified bytes and anchored data. The resulting
occupied intervals are:

- **Fixed bank 0:** `0260–0287`, `0389–03B7`, `0406–053F`, `0624–06E7`,
  `0BEF–0C3D`, `0C4A–0FF6`, `19CC–1C04`, `1D63–1DA1`, `1DB2–1E14`,
  `1E3F–1EA7`, `1FD4–2001`.
- **Mapped bank 2:** `8329–837A`, `837F–85FB`, `8628–8802`,
  `8883–88D7`, `88DC–88E1`, `88E6–8A57`.

These are ranges containing instruction bytes, **not** a claim that each interval
is one function or that no as-yet-unseen data can occur on other paths.

### Anchored data, not Z80 instructions

| ROM file offsets | Bytes | ROM-supported interpretation |
| --- | ---: | --- |
| `8600–8627` | 40 | 20 little-endian event-handler entries used by `$85EF` |
| `8A58–8B7B` | 292 | Two address lookup arrays selected at `$85D6/$85DC` |
| `8B7C–8C2E` | 179 | Pointer/encoded audio modulation data; subformat incomplete |
| `8C2F–8C8E` | 96 | Five pointers and associated modulation bytes |
| `8C8F–8CFD` | 111 | `$80` marker followed by 55 pointer words |
| `8D02–8D3F` | 62 | Known prefix of indexed priority data; full bounds unproven |

The `$8600` event table points to: `868E`, `86EC`, `8628`, `863A`, `867B`,
`867B`, `873E`, `86AA`, `86E1`, `86C3`, `86E6`, `87EB`, `87BD`, `87D8`,
`868D`, `867B`, `873E`, `873E`, `8667`, `8646`.
All 20 destinations coincide with decoded instruction starts in this checkpoint.

## Mapper-sensitive gap caught during analysis

Fixed-bank code at **`0DDA`** contains a call to CPU **`86C1`**. That address
must **not** be interpreted automatically as bank 2 offset `86C1`: the mapped
bank at this particular call site is not proven. At bank-2 file offset `86C1`
there would also be a mid-instruction landing in a decoded routine. The
analyzer consequently logs `Unknown slot-2 bank` rather than adding false
code coverage. Other unresolved slot-2 calls and targets are recorded in
`coverage.json`. This is an explicit correction to the initial exploratory
scanner, which was too permissive across bank changes.

## Playback-relevant tracing

- The per-channel record step at `8329` reads record offsets `+10/+11` and
  calls `8351` on timing expiry.
- At `8351` and `84F1`, byte tests select event/parameter decoding paths,
  which eventually reach `85E9` for indirect command dispatch.
- The command dispatcher at `85EF` indexes the 20-word ROM table at `8600`.
- The FM path at `843E` and `8472` emits `$F0` register-select writes;
  other bank-2 routines emit `$F1` value writes and PSG `$7F` writes.

**These observations are instruction-level evidence, not confirmed music output.**

## Reproduce

```sh
cd Ys
ROM='/path/to/Ys - The Vanished Omens (USA, Europe).sms'
python tools/verify.py "$ROM"
for N in 2 3 4; do python tools/z80_regions.py "$ROM" --phase "$N" --check; done
python tools/check_partial_asm.py "$ROM"
python tools/check_phase4_asm.py "$ROM"
python tools/z80_cfg_phase5.py "$ROM" --check
for N in check phase2 phase3 phase4 phase5; do python "tests_${N}.py" "$ROM"; done
```

`phase5/code.lst` is a generated, committed **text snapshot**, and
`phase5/coverage.json` is its deterministic metrics/unresolved-edge record.
`phase5/regions.json` stores the typed table spans and their individual SHA-256
hashes. Test mutations must be rejected. No commercial ROM content is shipped
in the Git project archive.

## Next phase

1. Investigate slot-2 bank selection at `0DDA`, with mapper-state traces.
2. Determine the `$8D5F`-onward track/event data format and its true bounds.
3. Verify `$8A58/$8AEA` lookup roles by following consumers and audio events.
4. Assemble an isolated Z80 module and compare the produced machine code
   against the ROM; static listings alone cannot establish this.
