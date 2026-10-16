# PC-38 — original SAT source-buffer mutation provenance

## Source evidence and boundary

The previous PC-36 checks already prove that **27 complete** original
Z80 SAT uploads each copy **64 Y + 128 X/tile bytes** from CPU-visible
`$DD00–$DDBF` to VDP VRAM `$3F00/$3F80`. PC-37 captures an original
source-driven VDP snapshot and validates a frame rendered by the native
diagnostic. Neither milestone identifies a genuine player sprite.

PC-38 adds an **opt-in, read-only** byte-difference observer to exactly
the same PC-34, 300,000-instruction original source run. At each
pre-instruction boundary it reads all 192 visible source addresses.
Differences from the preceding boundary are counted separately for the
64 Y bytes and 128 X/tile bytes, and attributed to the **preceding**
Z80 instruction/IRQ boundary with its physical ROM bank. The observer
records each bank-qualified boundary site, number of changed bytes,
total unique byte offsets changed, and how many of the 27 sampled
source tables differ from their preceding upload.

These are **changed values**, not observed bus write strobes:
same-value stores are invisible; IRQ entry or bank switching can
occur between sampled boundaries; mapped cartridge RAM might alter
visibility. A listed PC is therefore a *candidate provenance boundary*,
not proof that its instruction is a game sprite producer. Exact
`$9932` invocation, player identity, map location and collision remain
separate unverified goals.

## Implementation and reproducibility

- `native/pc_sat_provenance.{h,c}`: bounded 192-byte source-memory
  diff scanner, bank-qualified source-boundary site registry (128 max;
  fails closed on overflow), per-upload comparisons and typed JSON
  exporter. The instrument does not write the emulated CPU, bus, RAM,
  VDP, mapper, controller or interrupt state.
- `native/test_pc_sat_provenance.c`: ROM-free C11 regression fixtures
  for independent Y/XT changes, mapped bank provenance, idempotency,
  identical/changed uploads, malformed requests and JSON checks.
- `native/tools/verify_pc38_sat_provenance.py`: strict JSON field and
  type checks, exact PC-34/36/37 same-run identities and internal
  per-site/total accounting. CI also rejects corrupted audit JSON.

```sh
./build-native/ys-native-timed-rom /tmp/ys-source.sms \
  --pc34-extended-postrelease \
  /tmp/pc34.json /tmp/pc35.json /tmp/pc36.json \
  /tmp/pc37.ppm /tmp/pc37.json /tmp/pc38.json
python3 native/tools/verify_pc38_sat_provenance.py \
  /tmp/pc38.json /tmp/pc34.json /tmp/pc36.json /tmp/pc37.json
```

Reconstruct and SHA-verify the original source-only ROM using
the existing project tooling; no ROM image, sprite image or new
commercial asset is committed. PC-38 does **not** widen the instruction
budget, synthesize controls, promote the M45 release or satisfy any
original-game Alpha gate.
