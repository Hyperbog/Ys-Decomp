# Phase 20: Bank-6 object path + reusable external toolchain adapter

## Scope and proof status

The ROM is **Ys: The Vanished Omens (USA, Europe)**, 256 KiB, with SHA-256 in `../manifest.json`. Phase 20 extends the prior bounded Z80 interpreter to execute the original physical-bank-6 `$9966` alternate producer and `$9AA9` object routine under **synthetic, explicitly constructed state**. This is *not* an emulator observed game frame; `Machine` does not emulate Z80 cycles or an actual VDP renderer. All unsupported Z80 instructions fail closed.

Entry `$9966` is entered with physical bank 6 manually loaded in `$8000–$BFFF`, `$C198=1`, `$C1B9=$80`, a 25-byte descriptor at `$C200`, initial buffer pointers `$C028=DD00`, `$C02A=DD40`, and a record index at `$C199`. `$C210/C211` take three origin pairs `(0,0), (17,29), (240,250)`. The descriptor's bit-1 skip flag is cleared, its pointer bytes `$C217/C218` select `$C200`, and its index `$C214` is zero. This drives the specific path:

`$9966 -> CALL $9932 -> LD IX,$C200 -> CALL $9AA9 -> JP M,$9A71 -> RET`.

The test then invokes the previously recovered fixed-bank `$0427` SAT upload in **the same RAM image**, verifying all 192 VDP data-port writes, including the four object-added sprites. Expected sprite-record offsets are computed separately from `emulate_record_buffers`, the four object X/Y positions from origin arithmetic, and tile bytes directly from the original bank-6 ROM address (not from the interpreter's read method). The result is stored as hashes and counts in `object_execution.json`, not as extracted sprite payloads.

No newly classified ROM bytes or new source-backed bytes are claimed. Source-backed ownership remains **38,293 / 262,144 bytes (14.61%)**; fallback remains **223,851 bytes**. Candidate classification remains **58,133 / 262,144 bytes (22.18%)**.

### Validation boundaries

**Verified:** 64 bank-6 input records under three origin pairs, object BIT guard, descriptor/index handling, exact generated RAM buffers, pointers, and post-call VDP bytes; 14 Phase 20 tests include ROM mutation, instruction-budget, wrong mapper, skipped-object, and WLA fixture format checks.

**Not verified:** Whether the synthesized `$C200` descriptor occurs during gameplay; execution of the other `$9966` paths; third-party assembler output; full emulation, frame timing, visual sprite attributes and audio output.

## Independent WLA-DX integration

An adapter now prepares an independently assemblable *fixture* from the **checked-in Z80 assembly source** `src/phase13/bank07_unrolled_vdp.asm`. It supplies a three-slot SMS `.MEMORYMAP`, 16 × 16-KiB `.ROMBANKMAP`, physical bank 7 in slot 2, `.ORGA $8180`, and a linkfile. This follows WLA-DX's published quickstart and assembler-directive conventions:

- https://wla-dx.readthedocs.io/en/stable/quickstart.html
- https://wla-dx.readthedocs.io/en/latest/asmdiv.html
- https://wla-dx.readthedocs.io/en/latest/compiling.html
- https://wla-dx.readthedocs.io/en/latest/man/wlalink.html

`wla-z80` and `wlalink` are **not installed** in this environment; the WLA build cannot be marked passing. When available, `wla_z80_check.py` compiles, links, and byte-compares the independently generated ROM region at physical offset `$1C180` for 1,345 bytes. The fixture is generated on demand to a temporary directory, and neither the ROM nor linked outputs are committed. The adapter's preflight passes; no independent assembler equality is claimed.

## Reproduce

From `Ys/`:

```sh
make smoke ROM='/path/to/Ys.sms'
make verify ROM='/path/to/Ys.sms'
make build-verify ROM='/path/to/Ys.sms'
make wla-prepare ROM='/path/to/Ys.sms'    # only validates fixture structure
make wla-verify ROM='/path/to/Ys.sms'     # requires installed WLA-DX
```

Or run `python Ys/tests_phase20.py '/path/to/Ys.sms'` and `python Ys/tools/phase20_object_execution.py '/path/to/Ys.sms' --check` from the project root. The unified runner includes all earlier suites, Phase 11B, function-level matching, and the full-ROM overlay SHA comparison. Phase 20 adds a bounded `--jobs 4` execution mode; a complete run passed 23/23 suites and is saved in `regression_report.json`, in deterministic suite order despite concurrent completion.

## Project-wide next priorities

1. Obtain an external SMS-compatible emulator and WLA-DX binaries and make their versions reproducible. Independently validate the existing assembly; do not re-label custom-encoder matches as independent.
2. Trace runtime mapper writes and sprite/VDP behavior from actual save states, reconciling the static/controlled paths with gameplay.
3. Replace fallback bytes by semantic source and independently matched assembly, with per-bank coverage and no counting of merely opaque data as reconstructed.
4. Expand typed RAM/object descriptors and share symbols across all sources. Verify branch consistency and correctness of Z80 condition flags in any expanded emulator paths.
5. Build a complete stand-alone ROM only when the source files cover every byte and the external assembler/linker produces an exact SHA-256 without copying unrecovered bytes from an input ROM.
