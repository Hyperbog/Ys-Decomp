# Fixed bank 0 — standalone byte-complete source reconstruction

The **entire $0000–$3FFF physical bank** can be emitted without the commercial
ROM, through `tools/whole_bank00.py`, using committed Z80 mnemonics and
reversible records. Reassembly passes byte-for-byte against the supplied
256-KiB reference and is independently checked against the frozen bank SHA256
`3bc23bce4f0bdcf88669187f949c7a89dea9341a9653fb21025fe704e8ce872b`.
This is **binary closure**, not full behavioral or data-format understanding.

| Bank0 source owner | Bytes | Confidence/limitations |
|---|---:|---|
| Previously assembled Z80 and source records | 8,242 | Retained from Phases 11–21 |
| Newly transcribed Z80 mnemonic spans | 6,518 | 35 disjoint manually inspected spans; decoder- and encoder-matched; partial CFG evidence, not all traced |
| Newly typed pointer tables, ASCII title, and `$FF` padding | 463 | Constrained by counts and selected pointer bounds; pointer interpretation remains partly unknown |
| Newly reversible, semantically unresolved data | 1,161 | Explicit unresolved byte arrays; not counted as decoded game mechanics |
| **Complete fixed bank** | **16,384** | **No bank0 original-ROM fallback** |

Selected anchored recoveries:

* `$0288–$0388`: VDP-related code, including RAM pointer and mapper-control sequences.
* `$06E8–$0748`: fixed-bank graphics transfer support.
* `$07D5–$0800`: byte stream/decompression-related transfer routine (specific format still under investigation).
* `$0FFD–$1987`: object/actor state instruction sequences, bounded before the 34-entry handler directory at `$1988`.
* `$1ED4–$1FD3`: graphics-load dispatch and Z80 data-transfer code, including VDP port `$BE` writes.
* `$28CE–$3C87`: multiple battle/scene/menu handlers and state transitions, split by known source regions and tables.
* `$3F70–$3FFE`: multiple late-game control handlers; intervening pointer tables remain separate data.

The single trailing `$3FFF` byte remains **unresolved**: it is the first byte
of an apparent conditional branch whose operand would lie beyond bank 0. It
must not be silently treated as a complete local instruction. Some newly
reconstructed linear spans can still contain undetected embedded data;
only verified control flow and bounded execution can establish their usage.

## Reproduce without ROM

```sh
cd Ys
python tools/whole_bank00.py --verify-mixed
python tools/build_system_m3.py --standalone-banks
```

## Reproduce with locally owned reference

```sh
python tools/whole_bank00.py --verify-rom '/path/to/Ys.sms' --verify-mixed
python tools/build_system_m3.py '/path/to/Ys.sms' --check
python tools/build_system_graph_m3.py '/path/to/Ys.sms' --check
python tests_whole_bank00.py '/path/to/Ys.sms'
python tools/run_system_m3_regressions.py '/path/to/Ys.sms' --jobs 4
```

* Normal builds read `src/wholebank00/new_code.asm`, `wholebank00/source.json`,
  and checked-in existing sources; they **do not** read the original ROM.
* `--capture /path/to/Ys.sms` is a one-time ROM-to-editable-source conversion,
  never part of normal builds or CI.
* `src/wholebank00/bank00_complete.asm` is generated mixed Z80/`DB`/`DW`
  source. Both the sparse code source and the mixed source reassemble under
  the project's restricted native encoder.
* `tools/wla_system_m3.py --prepare` prepares external WLA-DX fixtures for
  banks 0/3/7. `--run` needs real binaries and is **not yet verified**.

Graph follow-up: three potential overlapping entry points (`$1033`, `$1036`,
`$1681`) remain unresolved in `whole_system/frontier_m3.json`. These are
concrete reasons that **byte-complete bank0 != fully deciphered bank0**.
