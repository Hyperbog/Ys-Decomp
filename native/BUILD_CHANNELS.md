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

- **Checkpoint:** M27 (frame clock and animated synthetic snapshots; Z80 execution still ends at M25). The last validated continuous native trace reached
  Z80 PC `$0B22` after 17,224 instructions, with one explicitly injected
  VBlank interrupt.
- **Available executables:** `ys-native-info`, `ys-native-probe`,
  `ys-native-trace`, `ys-native-preview`, `ys-native-frames`. These are CLI **diagnostic tools**,
  including a stateless video preview, not a PC game.
- **Not available:** Automatic video/IRQ scheduler, game display window,
  live input, native audio output, playable native game executable.
  A 256×192 PPM renderer and ROM-independent synthetic frame clock are available, but do not
  yet establish the Alpha video-renderer gate.
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
dist/ys-m27-dev-linux-x64-<commit>.zip
```

The archive contains `bin/` tools (including `ys-native-preview` and `ys-native-frames`),
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
