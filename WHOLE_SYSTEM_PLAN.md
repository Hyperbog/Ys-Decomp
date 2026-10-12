# Ys: The Vanished Omens — whole-bank / whole-system reconstruction policy

## Project completion criterion

**The project is complete only when all sixteen 16-KiB physical ROM banks can be built from reviewed source without reading any original-ROM bytes and the independent complete-ROM build matches the known 256-KiB original.** Source verification alone does not establish emulation fidelity. Whole-system completion additionally requires representative emulator-backed execution of initialization, mapper, VDP, input, PSG/YM2413 sound, object logic, and scenario progression.

**No more percentage-only milestone releases.** Future check-ins should close at least a complete bank, or a complete logically connected subsystem (with verified entrypoints, inputs, outputs, build integration and tests). Smaller discoveries accumulate inside the next whole-bank/system milestone rather than being presented as finished phases.

Definitions:

1. **Byte-complete bank:** independently generated from committed source, exactly 16,384 bytes, no ROM fallback for any byte, with a reproducible SHA-256 match.
2. **Semantically understood bank:** data formats and code paths are explained with supported interpretations. A byte-complete bank may still contain explicitly unresolved source data; these are NOT complete decompilation of game logic.
3. **Externally assembled bank:** `wla-z80` and `wlalink` actually execute; the resulting machine bytes match the original. Preparing a WLA fixture is not the same as this result.
4. **Runtime-verified subsystem:** instructions and hardware side-effects are verified by an independent emulator or sufficiently complete audited emulator trace. The current bounded interpreter is evidence only for exercised paths.
5. **Source-only whole ROM:** all 262,144 bytes regenerate without the ROM template. **Achieved at M10 for byte reconstruction**, using a mixture of real instructions, typed source, and explicitly unresolved byte-owned assets. This does **not** satisfy independent assembler or semantic-completeness criteria.

## Verified current build topology

* Physical ROM: 262,144 bytes, sixteen 16,384-byte banks, SHA256 `02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
* **Complete standalone source banks: 3, 7.** Both separately regenerate exactly 16,384 original bytes without opening the source ROM. Their full mixed Z80/DB/DW listings also reassemble under the project's encoder.
* Other banks: all explicitly partial. `Ys/whole_system/build_report.json` is the machine-readable authoritative inventory.
* Bank3: 176 Mode4 tiles; candidate text/control byte lanes; newly recovered 60 indexed four-byte descriptors with pointers into the text region; 1,843 bytes of explicit `$FF` bank padding. An additional 1,955-byte visual-looking region remains undecoded and is preserved as unresolved source bytes.
* Bank7: 64-entry code/graphics directories, 168-group unrolled VDP transfer code, primary grid data, 64 secondary graphics records, additional code at `$B53F`, `$B9D6`, and `$BA1E`, 22 groups of four-byte object-like records indexed by pointers, and 21 indexed text spans. A 1,088-byte visual-looking data span remains undecoded and is preserved explicitly.
* Whole-ROM template-assisted output remains byte-identical; the remaining **208,895 bytes** are still dependent on the original ROM.

## Build and verification

```sh
cd Ys
make two-bank-source
make wholebank03
make wholebank07
make whole-rom-verify ROM='/path/to/Ys - The Vanished Omens (USA, Europe).sms'
make whole-system-verify ROM='/path/to/Ys - The Vanished Omens (USA, Europe).sms'
# Only prepares external assembler fixtures (NOT independent verification):
make whole-system-wla-prepare
# Requires actual independently installed wla-z80 + wlalink, fail-closed:
make whole-system-wla-verify
```

The `--standalone-banks` command reads no ROM and does not write output by default. Use `--output-directory` outside the repository if private built bank binaries are required. Never commit/re-distribute ROM images.

## Next milestone targets

Prioritize **bank 0** (fixed-bank game control, boot, 8,142 fallback bytes), **bank 6** (complete sprite/object pipeline, 9,192 fallback), **bank 2** (music engine/data, 12,599 fallback), and then remaining banks. Recover real code and parsers rather than mechanically converting unknown bytes to `DB`. Group mapper, graphics, input and sound work by complete executable subsystems. Add independent third-party assembly and full-system emulator traces as capability gates, not superficial checklist items.

A complete bank with unresolved bytes is a binary-reconstruction achievement, not proof of full understanding. Reports must continue counting those bytes separately.

## System CFG/evidence inventory (post-`adeed6b`)

The new `Ys/whole_system/EVIDENCE_GRAPH.md` documents 7,047 matched Z80 instructions / 14,198 verified code bytes, 1,765 static basic blocks and a typed 8,155-edge graph. It highlights five bank-0 call targets without existing matching source and 17 mapper-slot edges whose destination banks remain unresolved. The architecture-neutral graph validator lives in `shared_decomp/evidence.py`; use its interface when developing graph producers for 6502 and PC programs. This work does not increase ROM coverage or complete another physical bank. Future whole-bank closure still requires ROM-independent assembly, all-data ownership, and actual build/test evidence.

## M3 update — 3 independently byte-complete banks

Physical banks 0, 3, and 7 now reassemble without original-ROM fallback
(49,152 bytes). This raises total source-backed bytes to 61,391 and leaves
200,753 bytes in thirteen partially/unreconstructed banks. Bank0 source
recovers 6,518 additional mnemonic Z80 bytes; 1,161 newly sourced bank0 data
bytes remain semantically unresolved. Next target: bank6 sprite/object system
completion, then additional whole-bank closure. Full emulator traces and WLA-DX
assembly remain separate required validation gates.


## M4 update — sprite/object bank closed at binary level

Physical banks **0,3,6,7** now rebuild without the original ROM (65,536 bytes
combined). Project source-backed: **70,583 bytes**; remaining original-ROM
fallback: **191,561 bytes**. Bank 6 contributes 9,192 newly regenerated data
bytes with seven verified count+triplet layout records. Graphical byte-lane
meaning remains unresolved; evidence is recorded in `wholebank06/asset_ledger.json`.
Use `tools/build_system_m4.py` and `whole_system/build_report_m4.json` for
latest accounting. Remaining whole-bank targets: bank2 sound and bank1 control;
then banks with minimal existing source. Full-source ROM and full emulator
behavioral proof remain outstanding.


## M5 update — source-only sound bank2

Physical banks **0, 2, 3, 6, 7** now rebuild without the original ROM:
**81,920** complete-bank bytes; **83,182** source-backed bytes including
partial other banks, **178,962** fallback bytes. This closes bank2's complete
binary image, including note period tables and 24 pointer-bounded song event
bodies, but **does not decode the music command grammar or prove sound playback**.
See `Ys/wholebank02/README.md` and `Ys/whole_system/M5_README.md`.
Next whole-bank target: bank1, with full-system audio traces as parallel work.

## M6 update — complete physical bank 1 (binary source closure)

Complete 16-KiB source banks: **0, 1, 2, 3, 6, 7**. Total source-backed: **98,787 bytes**; original-ROM fallback **163,357 bytes** across the remaining ten banks. Source-only bank1 emits 1,717 candidate mnemonic instruction bytes and 13,888 data bytes beyond the previous bank1 source coverage; **13,528 data bytes are semantically unresolved and may include code**. Next priority: whole-bank 4 and concrete dynamic system integration. See `Ys/whole_system/M6_README.md`.

## M7 update — whole bank 4 + collision subsystem evidence

Seven banks are source-only byte complete: **0,1,2,3,4,6,7**. Total source-backed **115,009** bytes, ROM fallback **147,135**. New bank4 reconstruction accounts for all 16KiB; most of its graphical-looking bytes are organizationally grouped but **unresolved**. Collision routine at bank4 `$807C` has 3,968 bounded synthetic-state ROM instruction runs against a direct arithmetic model, and three bank1 calls are statically confirmed but mapper state remains unresolved. Next priority: complete additional physical banks (5/8/9/10/11/12/13/14/15) and independently assemble/validate actual system execution. Source byte counts cannot substitute for behavior.

### Milestone 8 — two-bank system expansion

* Banks 8 and 10 source-only closure, raising complete banks to 9/16.
* Recover late-bank Z80 source and evidence-anchored five-byte lookup tables
  and FF-terminated text directories, without misclassifying opaque assets.
* Add bounded bank-10 decimal writer execution (265 test values) and static
  fixed-bank mapper/caller links to both banks.
* Continue focusing on seven remaining banks (5,9,11,12,13,14,15), resource
  semantic decoding, independent WLA-DX assembly, and actual SMS emulator traces.

## M9 current ledger

Source-only banks: 0,1,2,3,4,6,7,8,9,10,11,12 (12/16, 196,608 bytes). Remaining banks 5,13,14,15. M9 code discovery: 65 bank9 instruction bytes and eight fixed six-byte VDP sequences. Prioritize decoding the cross-bank text/glyph producer and sprite/graphics records over ungrounded opcode classification, then complete the remaining four banks. A true standalone cartridge assembler, independent WLA-DX binary matching, and full-system emulation are still required.

## M10 — Complete cartridge source-ownership, not complete semantic decompilation

**All 16 banks rebuild without original-ROM fallback**, and the full cartridge source-built digest matches the owner's 256-KiB ROM exactly. The final four banks add 65,536 bytes: 64,439 unresolved resource bytes, 100 bytes of index pointers, and 997 bytes of padding. Binary reconstruction is now complete; code/data understanding, independent WLA-DX verification, and emulator-level functional equivalence are **still open**. See `Ys/whole_system/M10_README.md`.

For future checkpoints, do not count repeated raw asset bytes or already-matched code as new semantic decompilation; prioritize independent compilation, concrete decoded formats, and runtime traces.

## M11 independent runtime/toolchain milestone (2026-10-11)

- COMPLETE: Emulicious.jar executes on this Linux container with Java/Xvfb.
- COMPLETE: Source-only ROM and owner ROM boot independently to the same
  stable, 220×160-pixel Ys title artwork (SHA-256 verified).
- COMPLETE: A repeatable fail-closed emulator verification command, negative
  tests, and external-tool provenance report are integrated into the project.
- BLOCKED: WLA-DX 10.7 provided executables are Windows PE. Native CMake
  build support exists but requires the **source ZIP**, not Win32/Win64 release.
- NEXT: independent Z80 assembler pass, emulator-side gameplay/audio traces,
  semantic recovery of still-unresolved game resources.

## Milestone 12 evidence

An independent Z80 assembler embedded in owner-provided Emulicious.jar has
verified 22,552 mnemonic bytes from 11,009 instructions across ten banks.
This is an opcode-level external comparison, not independent WLA linkage or
semantic closure of the remaining opaque DB/DW regions. See
`Ys/whole_system/M12_README.md`.
