# Ys native PC build channels: Development → Alpha → Beta → Final

This is a **functionality-based** release process for the native PC port,
not a percentage-of-decompilation label. A complete source-ROM reconstruction
does not by itself qualify as a playable PC build.

## Promotion definitions

| Channel | Required user experience | Quality bar |
| --- | --- | --- |
| **Development** (available) | Command-line diagnostic executables; source-ROM execution checkpoints and test results | Build and run unit tests; report what works and does not. **Not a playable game.** |
| **Alpha** (blocked) | A genuine native desktop game executable boots into visible gameplay. Automatic frame progression, rendering, live controller/keyboard input, and a meaningful, reproducible gameplay loop work without injecting frames or manually selecting a PC. | Useful hands-on gameplay testing. Incomplete content, sound and polish may be documented. |
| **Beta** (blocked) | The complete game can be played start to finish. Save/load, native PSG/FM audio playback and game content are available, with no progression-blocking bugs. | Fidelity testing, regressions, input/audio/video polish, and known minor deviations. |
| **Final** (blocked) | Near-original mechanics, timing, video, audio and content are verified against reference play. Windows/Linux/macOS releases and their dependencies are validated, and legal/distribution checks are complete. | Release sign-off, reproducible builds, bug triage, checksums and archival tags. |

A different project that is already playable end to end and is nearly
original-fidelity is a **Beta or release-candidate candidate**, not automatically
an Alpha. The channel depends on measured completeness, regressions and
release evidence, not the age of the project.

## Current baseline

- **Checkpoint:** M39 — source-ROM execution reaches bank 2 at
  `PC=$8803` after **104,749** instructions and **16** natural
  IM1 interrupts; the CALL stack holds return `$0C55`. The previous
  M38 1,792-byte VDP name-table clear remains verified.
- **Available executables:** `ys-native-info`, `ys-native-probe`,
  `ys-native-trace`, `ys-native-preview`, `ys-native-frames`, `ys-native-timing`, `ys-native-timed-rom`. These are CLI **diagnostic tools**,
  including a stateless video preview, not a PC game.
- **Available Development diagnostics:** nominal Z80-timed NTSC/PAL
  scanline/VBlank scheduler, source-ROM bounded frame execution,
  256×192 PPM renderer and Windows native GDI test window.
  **Not yet available:** actual game-driven live desktop window,
  live Ys gameplay input, native audio playback or a playable
  `ys-native-game` executable. These capabilities do not yet
  satisfy the Alpha video/controls/interactive gates.
- **Promotion record:** `native/release/gates.json`. Each gate starts
  `passed: false` with empty `evidence`. A promotion requires
  `passed: true` plus a nonempty link or path to evidence (test log,
  screenshot/video, reproducible playtest or issue resolution).

### Exact promotion gates

| Alpha | Beta (in addition to Alpha) | Final (in addition to Beta) |
| --- | --- | --- |
| `boot_to_title` | `complete_game` | `cross_platform` |
| `automatic_frames` | `save_load` | `fidelity_validation` |
| `video_renderer` | `audio_playback` | `release_audit` |
| `live_controls` | `content_parity` | |
| `interactive_gameplay` | `no_blocking_bugs` | |

**Code-level guard:** Even if every Alpha gate is marked passed, the
packager refuses to create an Alpha/Beta/Final bundle unless it finds a
compiled **`ys-native-game` executable**. The current CMake project does
not have that target. This prevents a trace-only binary from being
published as an Alpha.

The evidence fields are reviewable project records, **not automated gameplay
proof**. Updating them should follow the stated tests; they are not a
substitute for human gameplay/fidelity review.

## Build and test your current phase locally

Requires CMake, a C11 compiler, Python 3.11+ and Git:

```sh
python3 -m unittest discover -s native/tools -p 'test_*.py' -v
python3 native/tools/build_phase.py --channel dev
```

On Windows PowerShell, use `python` instead of `python3`.

The build command configures CMake, compiles a Release build, executes
**all native CTest suites**, and only if they pass creates a versioned
archive in `dist/`. It does **not** reconstruct the ROM.

An example output filename:

```text
dist/ys-m39-dev-linux-x64-<commit>.zip
```

The archive contains `bin/` tools (including `ys-native-preview` and `ys-native-frames`, `ys-native-timing`, `ys-native-timed-rom`),
`README.txt`, `manifest.json`,
and `SHA256SUMS.txt`. It embeds the Git revision, release channel,
milestone and file checksums. No cartridge image, proprietary game ROM,
original binary art or music assets are bundled. You supply your own
legally obtained 256 KiB Ys SMS image to the diagnostic executables:

```sh
./bin/ys-native-info --help
./bin/ys-native-probe /path/to/your/Ys.sms
./bin/ys-native-trace /path/to/your/Ys.sms
./bin/ys-native-preview synthetic.ppm
./bin/ys-native-frames demo 12 ntsc
./bin/ys-native-timing --check
./bin/ys-native-timed-rom /path/to/your/Ys.sms
./bin/ys-native-trace /path/to/your/Ys.sms --frame checkpoint.ppm
```

The synthetic preview writes a demonstrative tile/sprite fixture, not
original Ys graphics. The source-ROM snapshot captures VRAM at the bounded
checkpoint `$0B22`; scene setup is unfinished, so it may be mostly blank.
Both outputs are portable PPM (P6) images. On Windows, executables have
`.exe` suffixes.

**Testing previous phases:** Choose a particular `Ys` branch commit
in a separate worktree, then run `build_phase.py` there. The artifact
includes the commit hash, so different M-series checkpoints can be
compared without changing the current branch or using a reconstructed
ROM in the downloadable bundle.

## Download builds from GitHub Actions

The [native phase builds workflow](../.github/workflows/ys-phase-build.yml)
runs automatically on native changes, separately from the fast native
CI. Its matrix builds development archives on **Windows, Linux and macOS**.
Each job compiles its host executable, executes its native tests and the
packager's negative release-gate tests, then uploads an artifact identified
by **the exact commit SHA**. Download from the run's *Artifacts* section.
Artifacts are retained for 30 days; archive a specific checkpoint elsewhere
if you need it beyond that period.

For a manual build, open **Actions → Ys native phase builds → Run workflow**
and select `dev`, `alpha`, `beta` or `final`. Alpha/Beta/Final currently
exit with an explicit **BUILD BLOCKED** report listing unmet gates.
Once gates, tests and the real game target exist, the same workflow can
package that channel without a separate implementation.

The workflow packages **only executables and metadata**. It does not
run the M10 256 KiB reconstruction. The existing native CI continues
to reconstruct only with `rom_trace=true` or `[rom-check]` on a commit
message when a *new execution boundary* needs verification.

## Suggested development route

1. **Development / foundation:** complete the Z80/VDP/SMS device paths
   needed for title and gameplay, with reproducible checkpoint tests.
2. **Development / first frame:** event-driven frame clock and display,
   keyboard/controller polling, memory banking, visible startup.
3. **Development / playable loop:** movement, map transition, menus,
   collisions and battle state; expose `ys-native-game` and promote to
   **Alpha** after reproducible interactive testing.
4. **Alpha → Beta:** finish the campaign, inventory/save systems, all maps,
   bosses, PSG/FM playback, and eliminate blocking regressions.
5. **Beta → Final:** compare reference game behavior and content, run
   longer cross-platform and save-data tests, resolve high-severity
   compatibility bugs, and sign off licensing and packaging.

Publishing a **Final** archive is distinct from creating a public
GitHub Release or signed installer. Releasing tagged binaries to end
users remains a deliberate, reviewed step.


### M27 frame-clock limitations and optional window

`ys-native-frames` generates synthetic diagnostic PPM frames from a
caller-advanced NTSC/PAL scanline clock. `sms_runtime.c` can deliver the
VBlank IM1 interrupt at instruction boundaries, but the Z80 interpreter
does not yet emit T-state durations. Neither this diagnostic nor its
frame count establishes automatic source-ROM game execution.

The SDL2-based `ys-native-display` diagnostic window is built only
when SDL2 is available to CMake; the optional executable may be packaged
if found. Its SDL2 shared runtime is not distributed and may need to be
installed separately. A window containing synthetic tiles/sprites is not
a native Ys gameplay or title screen. The Alpha gates remain blocked.


### M28 measured Z80 timing (Development only)

`ys-native-timing --check` executes a synthetic NOP/EI instruction stream
with automatic scanline-clock advancement and confirms an IM1 VBlank
interrupt and VDP status acknowledgment. Instruction timings are known
for the current bounded Z80 subset; a new opcode without timing is not
accepted by the timed runtime. Nominal T-state timing does **not** prove
real-game fidelity. The source-built Ys trace still stops at $0B22 after
one deliberately injected VBlank, and Alpha remains blocked.


### M29 first naturally generated source-ROM VBlank

`ys-native-timed-rom` runs the original startup under CPU-derived
NTSC scanline timing to its first accepted IM1 interrupt and original
VDP status acknowledgment at `$003B`. It requires a user-supplied
256 KiB SMS ROM. This is a different, earlier endpoint than the existing
M25 trace ending at `$0B22`, which injected its first VBlank explicitly.
Neither path establishes a playable desktop game or original-hardware
cycle-accurate timing. See `native/research/M29_TIMED_SOURCE_TRACE.md`.

**M29 verified evidence:** The first automatically accepted IRQ in the
real reconstructed cartridge occurred at interrupt return PC `$0764`
after 338,842 nominal T-states, with five generated VBlank events
and one accepted IM1. The original ISR cleared VBlank status at
`$003B`. See [gated CI 38343836595](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38343836595).
This does not change Alpha eligibility.


### M30 verified timed ISR completion

[Full source-ROM CI 38344640720](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38344640720)
verified **17,205** instructions and **346,813** nominal CPU T-states,
**6** clock-generated VBlank events, **2** accepted IM1 interrupts,
a legitimate immediate second IRQ after the first ISR `EI; RET`,
and a stable second ISR return to **PC=$0764 / SP=$DFEC**.
All main/alternate general-purpose registers, IX/IY and ROM mapper
state were restored. The original cartridge SHA-256 remained unchanged.
These bounded source-ROM diagnostics still do **not** show actual
Ys title-screen rendering or interactive Alpha gameplay.

### M31 Windows click-to-run Development archive

Earlier diagnostic ZIPs were *not* Windows GUI applications: the console
executables generally exit when double-clicked without arguments, and the
SDL2 optional viewer could require a missing DLL. The Windows M31 archive
now **requires** the dependency-free `ys-native-window.exe` graphical
video diagnostic, and includes root-level `START_HERE.cmd` with a menu,
log capture and explicit pauses. MSVC Release artifacts use the static
C runtime to avoid a mandatory VC++ Redistributable dependency.

**Extract both layers** if the GitHub Actions artifact itself contains a
versioned `ys-m39-dev-windows-x64-...zip`. Double-click
`START_HERE.cmd` from the folder containing `bin`. Choose 1 for a
ROM-free animated SMS **test pattern**, or choose 3 for the bounded
source-ROM timed diagnostic (requires a user-supplied Ys SMS ROM).
Double-clicking the other CLI `.exe` files is not the intended interface.

The graphical output is synthetic, **not playable Ys**. Alpha/Beta/Final
release gates still remain false; M30 CPU startup and ROM reconstruction
checks have not advanced.


### M32 real-ROM VDP snapshot integration

In the Windows M32 Development package, choose **3** in
`START_HERE.cmd`, enter the path to your legal Ys SMS ROM, and the
launcher runs `ys-native-timed-rom ROM --frame checkpoint.ppm` and
opens that PPM in the guaranteed Win32 viewer. The image is taken from
the authentic VDP state when the source CPU reaches the first frame
wait (`$0046`) after two naturally accepted IM1 interrupts. It can
appear blank until further game VDP setup is verified. The viewer is
**not yet a game** and the snapshot is not a live frame loop.
Tests include the ROM-free synthetic PPM loader and gated cartridge
reconstruction; Alpha gameplay gates remain unpassed.


### M33 original-game frame-wait completion

The bounded `ys-native-timed-rom` command now follows the source
`$0046` wait loop to the next naturally clocked VBlank ISR,
through original sprite/VDP/sound processing, and returns to the
cold-boot dispatcher at `$00C4` once the game itself clears
`$C021`. With `--frame` it exports the later cartridge-derived
VDP framebuffer, which can be viewed using Windows
`START_HERE.cmd` option 3. This is **not** a live Windows game;
the Alpha, Beta and Final release evidence gates remain false.


**M33 gated verification passed:** [CI 38348188019](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38348188019)
confirmed `23,583` actual ROM Z80 instructions and `409,651`
nominal T-states, from reset through IRQ 3 and `$00C4`,
with 192 real VRAM writes and 44 total PSG writes.
The later saved VDP snapshot passed P6/size checks; the
Windows executable is still a **Development visual diagnostic**,
not a playable Ys binary.


### M34 timed palette initialization

The Development cartridge trace retains M29–M33 VBlank checkpoints,
then executes state-0/state-1 dispatch and the exact
`$0B10` 32-byte staging copy and `$0B22`
palette-nibble transform before `$0AF6 CALL $0BC5`.
The saved VDP image is not a finished title or a live game.
A ROM-free fixture validates the Z80 arithmetic/rotation flags
and 32 source palette iterations. Alpha gates remain blocked.


**Verified M34 execution:** [ROM CI 38348967643](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38348967643)
confirmed `$0C4A` state dispatch at 23,615 instructions,
`$0B22` palette staging at 23,755, and `$0AF6` after
713 authentic palette transformation steps, totaling
**24,468 instructions** and **416,854 nominal T-states**.
No extra VBlank was injected, and the full source-ROM checksum
was unchanged. [M34 Development build artifacts](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38348967882)
include the Windows GDI diagnostic and `START_HERE.cmd`.


### M35 full palette fade and 12 source VBlank waits

[Full gated ROM run 38350370954](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38350370954)
verified four source fade levels, twelve original frame-wait bridge
returns, **96,733** total Z80 instructions and **1,126,507**
nominal T-states to `$0B00` with **15** accepted IM1 IRQs,
**19** clock VBlank events, **2,496** VRAM and **176** PSG writes.
The source `$03EE` ISR clears its `$C02C` palette update flag.
The next bank-7 graphics/palette data transfer has **not** run.
The Windows viewer still shows a saved cartridge snapshot, not live Ys.


### M36 bank-7 source transfer and VDP setup

[Verified original-ROM run](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38382817751)
records a 16-byte LDI transfer from physical bank 7 (ROM `$B9C3`)
to `$C170-$C17F`, checking every cartridge-sourced byte and
restoring the original stack. It then executes original VDP
register 0/1 writes (`$26/$A0`) and sprite-Y terminator
`$3F00=$D0`, returning to `$0A5E` after **96,849** instructions,
**1,127,522** nominal T-states and no newly injected interrupts.
The optional Windows image remains a **saved initialization
snapshot**, not a live game, title screen or proof of gameplay.


### M37 source graphics-memory initialization

[Gated full-ROM test 38383836571](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38383836571)
verified the same M36 source-ROM boot through **97,144**
instructions and **1,129,966** T-states to `PC=$0A77`.
The real Z80 code wrote scroll registers `R8=R9=0`,
cleared WRAM `$C018/$C019`, and wrote 64 zero bytes
to VRAM `$0000–$003F` through the source `$06D4`
helper. The VDP data write pointer advanced to `$0040`.
Cumulative VRAM writes reached **2,561**, with no new
accepted IRQ or VBlank at this boundary. The Windows
binary still presents static cartridge VDP snapshots,
not interactive gameplay. Alpha gates remain blocked.

### M38 original graphics-memory clear; opt-in SMS/GG recompiler

[ROM verification](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38425466962)
confirmed 896 source words / 1,792 VDP byte writes with a
naturally occurring IM1 interrupt at saved `$06DE` and
an original tail-call RET to `$0C4D`. No synthetic IRQ or
original game source modifications were used.

[SMS/GG Recomp Phase 1](../Ys/recomp/README.md) is independently
merged and CI-tested. It gates external generated-C output by
ROM SHA-256/CRC-32 and artifact provenance; it **does not**
yet compile or execute a static-recompiled game runner.


### M39 original sound entry and SMS/GG Recomp ROM identity

[Full source-ROM CI 38443152403](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38443152403)
passed at `PC=$8803`, mapper bank 2, saved return `$0C55`, opcode `$E5`,
**104,749** Z80 instructions and **1,194,183** nominal T-states.
The same CI job also verified `shared_decomp/smsgg_recomp.py --preflight`
against the **actual source-rebuilt 256 KiB Ys ROM**: SHA-256 and
configured CRC-32 `B33E2827` both matched. This proves identity,
not compilation or execution of generated C, nor audio/gameplay.
