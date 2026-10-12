# Phase 7 — Bank-1 control flow and bank-3 data reconnaissance

**ROM:** USA/Europe SMS, SHA-256 `02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`

## Result, with confidence levels

| Type | New ROM bytes | Status |
|---|---:|---|
| Bank-1 Z80 | 763 | **ROM instruction bytes verified**, 376 instruction starts; *runtime mapping conditional* |
| Bank-3 non-padding payload | 14,541 | **ROM bytes digest-verified**, *non-code status and internal encoding provisional* |
| **Total new candidate region coverage** | **15,304** | All distinct, non-overlapping with Phases 1–6 |
| Previously classified | 21,523 | Phase 6 checkpoint retained |
| **Combined candidate coverage** | **36,827 / 262,144 (14.05%)** | Not percentage of decoded behavior or matching assembly |

For comparison, Phase 6 added 14,521 bytes. Phase 7 adds **15,304 bytes**, about **1.054×** Phase 6, while explicitly distinguishing **14,541 still-opaque data bytes** from 763 analyzed code bytes. The rise in covered bytes does not imply an equivalent improvement in reconstructed game logic.

## Bank 1 `$4000–$7FFF`: six independently grounded roots

The reset path sets slot-1 mapper register `$FFFE` to bank 1 and slot-2 mapper register `$FFFF` to bank 2. Prior fixed-bank code contains direct calls or jumps to six potential bank-1 targets:

| Target | Fixed-bank reference(s) | Status |
|---|---|---|
| `$42BA` | `$1D74` | Statically decoded; active bank at call unproven |
| `$476C` | `$0DCC` | Statically decoded; writes `$FFFF` to change slot-2 bank |
| `$60B5` | `$0DCF` | Statically decoded; current mapping unproven |
| `$61AE` | `$27A0`, `$2FFE` | Statically decoded; multiple callers |
| `$6215` | `$0E20` | Statically decoded; current mapping unproven |
| `$64CD` | `$0E7F` | Statically decoded; current mapping unproven |

The recursive walker follows additional branch/call targets only within the *physical* bank-1 code window. The walker intentionally does not assign a physical bank to three encountered calls to CPU `$807C` (at bank-1 offsets `$47C2`, `$486C`, `$48DF`). Changing `$FFFF` along these paths makes that especially important.

`code.lst` contains the exact byte sequence of every classified instruction, including its ROM offset and nominal CPU address, and `coverage.json` records the six roots and three unresolved slot-2 edges. This is not a verified list of complete functions: it is the reachable static subset from explicit prior call references.

## Bank 3 `$C000–$FFFF`: avoiding padding inflation

Physical bank 3 begins with repeated structured-looking byte sequences and later contains pattern- and symbol-like data. Internal structures are **not decoded** and labels below are only investigative:

| Physical ROM region | Bytes | Status |
|---|---:|---|
| `$C000–$CFFF` | 4,096 | Repeated four-byte motifs; opaque |
| `$D000–$D5FF` | 1,536 | Packed/pattern-like bytes; opaque |
| `$D600–$DEFF` | 2,304 | Mixed payload; opaque |
| `$DF00–$F8CC` | 6,605 | Symbol/command-like stream; opaque |
| `$F8CD–$FFFF` | 1,843 | All `$FF`, **excluded** as padding |

All four provisional payload regions have separate SHA-256 digests and descriptive, format-neutral metrics in `coverage.json`. The all-`$FF` tail is found by scanning backward from the bank end, *not* by assuming that every bank byte is useful content. A future parsing pass must use code references, bank-state traces or a recognizable stream grammar before raising the confidence of these regions.

## Files

- `code.lst`: 376 ROM-backed Z80 instructions (no embedded commercial opaque data payloads)
- `coverage.json`: root provenance, segment digests, uncertainty and candidate coverage
- `../tools/z80_bank1_phase7.py`: deterministic previous-phase-root CFG plus bank-3 padding survey
- `../tests_phase7.py`: independent ROM-byte comparisons, region checks and mutation rejection

## Reproduction

```sh
cd Ys
ROM='/path/to/Ys - The Vanished Omens (USA, Europe).sms'
python tools/verify.py "$ROM"
python tools/z80_bank1_phase7.py "$ROM" --check
python tests_phase7.py "$ROM"
```

All Phase 1–7 test scripts passed on the matching uploaded ROM. These checks **do not** establish complete instruction reachability, audio command grammar, valid bank mappings at runtime, or assembler-produced binary identity.

## Follow-on priorities

1. Instrument mapper writes in an emulator to resolve slot-1 and slot-2 bank identities at the six rooted calls and the three `$807C` edges.
2. Decode the bank-3 payload structurally instead of treating its 14,541 provisional bytes as fully understood data.
3. Assemble and byte-compare one bounded reconstructed Z80 routine with an actual Z80 assembler; the existing mnemonic comparison is not a build-equivalence test.
4. Continue bank-aware CFG expansion only from grounded call sites, tables or runtime traces.
