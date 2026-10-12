# Phase 11B — Bank-6's indexed record payloads

**Status:** byte-accurate, reversible ROM-data reconstruction and repaired
Phase 11A regression runner. The original 256-KiB SMS ROM is required to
regenerate the analysis and is not stored here.

## Evidence

1. In physical ROM bank 6, Z80 routine CPU `$9932` (file `$19932`) loads
   `$C199`, doubles it, and uses the result as an offset into a 64-word
   little-endian table starting at CPU `$8000` (file `$18000`).
2. The table has 64 distinct CPU pointers. Their sorted destinations begin
   at `$8080` and each record occupies exactly `1 + 3*n` bytes, where `n`
   is the first source byte. Every one ends exactly where the next begins;
   the last ends at `$9932`, the first byte of the consuming routine.
3. Across 64 records, there are 2,086 counted elements and **6,322 data
   bytes**. Size range: 82–115 bytes/record; element counts 27–38.
4. Instructions at `$993D–$9965` preserve the count in B/C and use two
   sequential loops, copying a running-sum first stream to RAM through the
   `$C028` pointer, then a running-sum/literal interleaved stream through
   `$C02A`. The starting sums are read from RAM `$C210` and `$C211`.
   Both accumulators are loaded *outside* their respective loops.

## Recovered record grammar

```text
n:          u8                   // element count
first:      u8[n]                // cumulative-sum delta stream
second:     tuple<u8,u8>[n]      // cumulative delta, copied literal
size:       1 + 3*n              // verified for all 64 records

first_output[i]  = (initial_C210 + sum(first[0..i])) & 0xFF
second_output[2*i] = (initial_C211 + sum(second[j][0] for j<=i)) & 0xFF
second_output[2*i+1] = second[i][1]
```

The descriptions above are structural. The code does **not** establish that
these bytes represent a specific map coordinate, character, sprite, or
other gameplay object. No emulator execution trace has been collected.

## Coverage accounting

| Category | Phase 11A | Phase 11B | Newly covered |
|---|---:|---:|---:|
| Project-assembler-matched Z80 code | 12,439 | 12,439 | 0 |
| Reversible tile data (previously surveyed) | 5,632 | 5,632 | 0 |
| Bank-6 pointer table | 128 | 128 | 0 |
| Bank-6 variable-length payload records | 0 | 6,322 | 6,322 |
| **Code + reversible data union** | **18,199** | **24,521** | **6,322** |
| **Candidate ROM-byte footprint** | **38,279** | **44,601** | **6,322** |

The candidate footprint is **17.01%** of the ROM. The code+reversible-data
union is **9.35%**. Neither figure is a measure of recovered gameplay logic;
all Z80 byte matching still uses the project's restricted assembler.

## Validation and how to reproduce

From repository root, with the ROM supplied externally:

```sh
python Ys/tests_phase11.py "/path/to/Ys.sms"
python Ys/tools/recover_bank6_records_phase11b.py "/path/to/Ys.sms" --check
python Ys/tests_phase11b.py "/path/to/Ys.sms"
python Ys/tools/rebuild_phase11.py "/path/to/Ys.sms" --check
```

`phase11/bank6_records.json` contains table metadata, source ROM digests,
all 64 record boundaries and lengths, and hashes of reconstructed zero-origin
output buffers. It contains **no raw record payloads**. The Phase 11B tests
reconstruct every record, compare every source byte, independently recompute
running-sum effects at three origins, and deliberately corrupt record sizes,
pointers, metadata, and ROM payloads.

## Next steps

- Observe this routine dynamically, especially values of RAM `$C199`,
  `$C210/$C211` and the destination pointers `$C028/$C02A`.
- Seek callers/consumers of those RAM buffers before assigning domain labels.
- Expand independent assembler verification and support a first complete
  bank-level rebuild only when fill and data boundaries are justified.
