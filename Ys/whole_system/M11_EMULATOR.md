# M11: independent emulator boot validation (Emulicious)

## Scope and outcome

The ROM produced by `Ys/tools/build_system_m10.py` was launched successfully in
**Emulicious.jar** (provided separately by the user) under Linux OpenJDK 21 and
Xvfb. The original Ys SMS ROM was launched in a separate instance for comparison.
Both displayed the intro/title artwork. RGB pixels in a stable 220 × 160 image
region (screen rectangle x=40..259, y=90..249) had exactly the same SHA-256:

`fea1432fc67f05d2ac2d63f2865392597964794978643f743726c73f5b40f39d`

This region excludes animated upper title text and lower credits. The sampled
region had 15 unique colors. Screenshots and the original/rebuilt commercial ROM
are not stored in Git. The saved `emulicious_report_m11.json` stores only digests,
ROI coordinates, evidence flags, and emulator JAR identity.

**Result:** third-party full-system emulator boot/title rendering passes for the
M10 source-rebuilt cartridge. Since the source ROM and original ROM are already
byte-identical, this is an independent execution/smoke check, not independent
assembly, and it is not evidence of independently reconstructed semantics.

**Not tested:** full-game walkthrough, input/state transitions, PSG/YM2413 audio,
save/load, cycle accuracy, or complete ROM code-path execution. Not all graphics
outside the stable title region were compared frame-exactly.

## Reproduce (Linux, Xvfb, JDK + Python Pillow)

Obtain the standard multi-platform Emulicious archive from the emulator's official
website, extract it **outside** this repository, and supply its `Emulicious.jar`:

```sh
cd Ys
make emulator-verify \
  EMULICIOUS_JAR=/local/tools/Emulicious/Emulicious.jar \
  ROM='/local/owned/Ys - The Vanished Omens (USA, Europe).sms'
make emulator-smoke-tests
```

The verifier runs `build_system_m10.build()` without consulting the owned ROM,
checks its 256-KiB SHA-256, launches Emulicious with Java under a temporary Xvfb
display, automatically closes the first-use update preference dialog if present,
uses Java `Robot` to capture the actual desktop framebuffer, then compares the
specified title-art region. It repeats with the independently supplied owner ROM.
If no reference ROM is supplied, the standalone source-only boot can still be
checked against the documented anchor via:

```sh
python tools/emulicious_smoke_m11.py --jar /local/tools/Emulicious/Emulicious.jar
```

The script requires `java`, `javac`, `Xvfb`, `xwininfo`, Python, and Pillow.
It fails closed on missing executables, missing artwork, missing reference,
modified/incorrect ROM, wrong color/content hash, or early emulator termination.
GUI coordinates and the pixel anchor currently assume the default Emulicious
300 × 300 window, zoom 2 and Xvfb display settings. Running on a different
emulator build, platform, theme or zoom may require an independently revalidated
anchor; never silently waive the comparison.

## Independent assembler status

The user provided `wla_dx_v10.7_Win32.zip` and `wla_dx_v10.7_Win64.zip`.
Those archives contain PE/Windows `.exe` assembler/linker binaries, not Linux
binaries or C source. Linux here has no Wine runtime and lacks network DNS access,
so neither release can be executed here. `wla_system_m10.py --prepare` is NOT
independent compilation. To remove the remaining assembler blocker, supply a
WLA-DX source ZIP (GitHub **Code → Download ZIP**) or Linux executables; then
build native `wla-z80`/`wlalink` with CMake and run
`python tools/wla_system_m10.py --run`.

The third-party emulator and assembler are external dependencies. Their binaries
must not be committed with game source.
