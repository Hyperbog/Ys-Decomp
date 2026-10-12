# Whole-System M11 — Independent Emulicious boot and native toolchain onboarding

**Binary source-build baseline:** unchanged at 16/16 complete banks, 262,144
bytes, SHA-256 `02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
All banks still rebuild without a ROM file. This is binary source reconstruction;
asset decoding and many execution paths remain incomplete.

## What changed

1. User provided `Emulicious.zip` and two Windows-Java editions. The portable
   `Emulicious.jar` runs under OpenJDK 21 and Xvfb on this Linux host. Both the
   unchanged owner ROM and ROM-independent source build were launched in distinct
   full-system Emulicious sessions. Both reached the Ys title screen. At fixed
   desktop ROI `(40,90,260,250)`, the displayed RGB pixel bytes matched SHA-256
   `fea1432fc67f05d2ac2d63f2865392597964794978643f743726c73f5b40f39d`
   with 15 distinct colors. This region excludes changing title/credits text.
2. `tools/emulicious_smoke_m11.py` now makes that test reproducible. It builds
   from source, validates ROM size/hash, runs the emulator under unique Xvfb
   displays, handles the first-start update preference dialog, captures visible
   pixels via Java Robot, checks for a nonblank known title region, and (when
   supplied) repeats with the correctly fingerprinted owner ROM. Failures stop
   the process. No screenshot or game ROM is included in Git.
3. `tools/wla_native_m11.py` rejects Windows-only `wla-z80.exe`/`wlalink.exe`
   release ZIPs. It provides safe, local extraction, native CMake build, and a
   full 16-bank **independent assembly comparison** once WLA-DX source is
   separately available. **This step has not yet been executed**: the user's
   Win32/Win64 release archives contain no C source, native executables, or
   Linux-compatible linker; Wine is not installed and DNS/network retrieval
   is unavailable.
4. Fast negative tests and Makefile targets allow this test path to be reused
   without including third-party binaries in the repository.

## Verification

- Original owner ROM fingerprint checked: PASS.
- Source-only M10 complete cartridge rebuilt and compared: PASS (exact SHA-256).
- **External full-system emulator boots + matching title pixels:** PASS, two ROM
  inputs in separate Emulicious JVM processes.
- M11 emulator launcher unit tests: **10/10 passed**.
- M11 native toolchain-source gating tests: **5/5 passed**.
- Full historical M10 regression rerun: **76/76 passed**.
- WLA-DX Windows v10.7 executable format: verified PE `MZ`, amd64 machine 0x8664;
  cannot execute as native Linux ELF.
- Independent external Z80 assembly: **NOT VERIFIED**.
- Whole-game input, audio, mapper, and frame-by-frame behavior: **NOT VERIFIED**.

## Reproducible commands

```sh
cd Ys
python tools/build_system_m10.py --check
make emulator-smoke-tests wla-native-tests
make emulator-verify \
    EMULICIOUS_JAR=/outside/git/Emulicious/Emulicious.jar \
    ROM='/outside/git/Ys - The Vanished Omens (USA, Europe).sms'

# Automatic fetch of pinned public WLA-DX v10.7 (requires network egress):
make wla-build-native

# Offline fallback, if container DNS/outbound access is blocked:
make wla-build-native WLA_SOURCE_ZIP=/outside/git/wla-dx-v10.7-source.zip
```

Runtime prerequisites for emulator verification: Java/JDK, Xvfb, xwininfo,
Python Pillow. The test stores only SHA-256/pixel metadata by default.

## Next genuine project milestone

First compile/link full source with independently built `wla-z80` and
`wlalink`. Next establish emulator-side frame/state/input/PSG/YM2413 traces
beyond the boot image, decode the large remaining resource regions, and
recover any as-yet-unidentified executable code currently stored as data.

**Do not count this runtime verification checkpoint as additional recovered ROM
bytes or a complete semantic decompilation.**

## Public-repository build authorization

WLA-DX builds no longer require manual approval or an explicitly supplied source ZIP.
The `wla-build-native` target attempts to clone the pinned v10.7 tag and builds
under `~/.cache/ys-decomp/`, outside Git. A source ZIP is still an optional
offline route. On the current Linux container the actual automatic clone was
attempted but failed with `Could not resolve host: github.com`; public repo
permissions are not the same as network connectivity. The external assembly
gate remains unverified until both native tools run and the full source image
passes independent comparison.
