# Enhanced native PC port (separate development track)

[PC-0 foundation and build instructions](ENHANCED_PC_PORT.md)
and [PC-1 source-only bank-3 tile gallery](research/PC1_BANK3_TILE_GALLERY.md),
plus [PC-2 source bank-7 map-object record verification](research/PC2_BANK7_MAP_RECORDS.md)
and [PC-4 original conditional object parameter recovery](research/PC4_OBJECT_TYPE_INITIALIZER.md)
and [PC-5 separate scene selector directories](research/PC5_SCENE_SELECTORS.md)
and [PC-6 authentic initialization name-table bytes](research/PC6_INITIAL_NAMETABLE.md)
and [PC-7 native pixel-index composition of original pattern/name-table data](research/PC7_PATTERN_NAME_PREVIEW.md)
and [PC-8 single-checkpoint original VDP/CRAM register capture](research/PC8_SIMULTANEOUS_VDP.md)
and [PC-9 verified source bank-4 object collision predicate](research/PC9_SOURCE_COLLISION.md),
[PC-10 canonical prototype scene contract](research/PC10_CANONICAL_CONTENT.md)
and [Ys modding support profile](YS_MODDING_PROFILE.md)
and [PC-11 conditional original bank-1 collision-call routes](research/PC11_BANK1_COLLISION_ROUTES.md)
and [PC-12 bounded original CPU collision call observation](research/PC12_RUNTIME_COLLISION_WATCH.md)
and [PC-13 native two-room prototype campaign replay](research/PC13_CAMPAIGN_VERTICAL_SLICE.md)
and [PC-3 source object-work projection](research/PC3_OBJECT_WORK_PROJECTION.md) describe
the new SDL2 `ys-native-game` placeholder-room prototype, native
fixed-tick gameplay core and tests. It does not execute the original ROM.
The source-ROM Z80/VDP utilities below remain separate reference tools;
no real Ys Alpha gameplay is yet verified.

---

## M45 — Original Ys four-column resource staging verified

The original Ys Master System cartridge now executes continuously
through the M44 12,288-byte VRAM pattern transfer and the subsequent
**four-column source-data staging routine**, reaching **Z80 PC=$0C92**.

The [gated full-ROM CI run](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38478502672)
passed **430,886** interpreted Z80 instructions and **3,579,261**
nominal T-states, across **56** naturally accepted interrupts and
**60** generated VBlanks. An independent decoder verified all
**5,344** WRAM destination bytes against **4,425** compressed
cartridge bytes. The 16 source-only ROM banks rebuilt without
fallback, with the original 256 KiB ROM SHA-256 unchanged.

The separately checked [SMS/GG Static Recomp adapter](../Ys/recomp/README.md)
passed its original-ROM SHA-256/CRC-32 preflight in the same
gated run. That integration is still **Phase-1 code generation and
provenance**, not compilation, linking, execution or gameplay
verification of externally recompiled C. M45 provides the WRAM,
Z80/interrupt and VDP evidence boundary for a future differential
generated-C runner.

Windows users can extract both ZIP layers, open
`START_HERE.cmd`, and choose **1** for the ROM-free synthetic
window or **3** to run their own Ys SMS cartridge through
`$0C92` and view a saved, authentic but **static** VDP image.

```sh
bin/ys-native-timed-rom /path/to/your/Ys.sms --frame checkpoint.ppm
```

See [M45 four-column evidence](research/M45_FOUR_COLUMN.md).
**This is not a playable native PC game**; all Alpha/Beta/Final
promotion gates remain false.

## Previous milestone — M44

# M44 — Source Ys 4-row graphics decompression verified

[Full source-ROM CI run 38474627069](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38474627069)
passed with **382,973 original Z80 instructions**, **3,233,133**
nominal T-states, **50** naturally accepted IM1 IRQs,
**54** generated VBlank events and **18,177** cumulative VRAM writes,
ending at CPU **PC=$0C87**.

The original `$0695-$06C0` graphics decoder executed **12,288
`OUT ($BE),A` instructions**, expanding four interleaved
graphics rows from the mapped cartridge. An independently written
reference decoder matched every VRAM byte at each changed address.
The native Z80 interpreter gained tested `RES b,r` and
`RES b,(HL)` instructions for `RES 7,B`.

[SMS/GG Recomp adapter CI](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38472231122)
passed **14/14 codegen/provenance tests**. The integration remains
**Phase 1**: actual upstream-generated C has not been compiled,
linked or executed in the native game runtime. These graphics
results are from the **existing C11 Z80 interpreter**, not an
AOT-recompiled game.

Windows: extract both ZIP layers and double-click `START_HERE.cmd`.
Option **1** opens synthetic graphics; option **3** traces your
own Ys Master System ROM to `$0C87` and opens its **static**
cartridge-derived 256×192 VDP image. It is not playable Ys.

See [M44 graphics differential](research/M44_PATTERN_ROWS.md).
Alpha/Beta/Final promotion gates remain false.

## Previous milestone — M43

# M43 — Source Ys graphics VRAM upload verified

[Original-ROM CI 38471475804](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38471475804)
passed 127,325 real Z80 instructions and 1,376,546 T-states
to **PC=$0C7E**, with 19 naturally accepted IRQs, 23 VBlanks
and 5,889 cumulative VRAM writes. The original `$06C1` helper
executed **1,536 OUTI port instructions**, copying the independently
verified source WRAM `$D600–$DBFF` to VDP VRAM `$3900–$3EFF`
byte-for-byte. No artificial interrupt or game state edit was used.

[SMS/GG static-recompiler adapter CI](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38470606026)
passes 14/14 tests. The integration is **Phase-1 provenance/code
generation only**; no actual upstream-generated C has been compiled,
linked or executed in the native runtime. The M43 results above are
from the **existing C11 interpreter**, not the static recompiler.

Windows: extract both ZIP layers and double-click `START_HERE.cmd`.
Menu 1 runs ROM-free synthetic video; option 3 executes your
legally owned Ys SMS ROM and opens a **static** authentic VDP
snapshot at `$0C7E`. This is not playable Ys.
See [M43 verification](research/M43_VRAM_UPLOAD.md).
Alpha/Beta/Final evidence gates remain false.

## Previous milestone — M42

# M42 — Native source resource staging verified

The original Ys SMS ROM runs through the source bank-5 decompressor and
the `$0BEF–$0C1F` two-row staging routine, stopping at **PC=$0C72**.
[Gated source-ROM CI](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38470163784)
passed with **122,272 instructions**, **1,323,179 nominal T-states**,
**18 naturally accepted interrupts** and **22 VBlanks**. The source
consumed **748** decompressed bytes and performed **1,536 WRAM
writes**. An independent decoder matched every byte of the non-stack
`$D600–$DFBF` staging workspace. The genuine IM1 CPU stack
`$DFC0–$DFFF` was excluded from that comparison.

[SMS/GG Recomp adapter CI](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38463864482)
passed 14/14 synthetic tests and Ys Makefile wiring. It is a
**Phase-1 codegen/provenance integration**: external-generated C
has not been compiled, linked or executed as a native game.

Windows Development: extract both ZIP layers and run `START_HERE.cmd`.
Menu **1** shows synthetic SMS graphics; **3** traces your own Ys SMS
ROM through `$0C72` and views its static VDP snapshot. This is
**not playable Ys**; graphics upload and live input remain blocked.

See [M42 source and integration evidence](research/M42_STAGED_RESOURCE.md).
Alpha/Beta/Final release gates remain false.

## Previous milestone — M41

# M41 — Original Ys resource decompression and SMS/GG recomp review

The verified original-cartridge runtime now reaches **Z80 PC=$0C67**
after **109,081** instructions and **1,226,741** nominal T-states,
with 16 accepted interrupts and 20 VBlanks. Bank-5's genuine
source decompressor consumes 518 bytes and produces **748 verified
WRAM bytes**, compared byte-for-byte with an independent bounded
decoder. Z80 `ED 73` now stores SP with authentic 20-T-state timing.

[Source-only ROM CI](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38463154158)
passed with all 16 banks and the unchanged 256 KiB digest.
[SMS/GG Recomp adapter CI](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38462981399)
also passed **14/14** synthetic provenance/integration tests.
The adapter invokes a user-installed upstream recompiler, but
no real upstream-generated C has been compiled, linked or run
as an Ys game yet.

Windows: extract both Development ZIP layers and run
`START_HERE.cmd`; choose **1** for synthetic video diagnostics
or **3** to trace your own Ys SMS ROM and open its saved
VDP image at `$0C67`. The image is **static**, not playable
gameplay. All Alpha, Beta and Final release gates remain false.

See [M41 resource verification](research/M41_BANK5_RLE.md).

## Previous milestone — M40

# M40 — Original bank-2 sound initializer completed; recomp integration review

The original Ys SMS source-ROM executes the authentic bank-2
`$8803–$8877` sound-state reset and returns to
**PC=$0C55** after **105,009 instructions** and **1,196,582 nominal
Z80 T-states**, preserving the earlier natural 16 IRQs and
20 VBlank events. No original ROM source, registers or CPU state
were patched to reach this checkpoint.

[Gated source-ROM verification](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38453169948)
passed: ten overlapping sound workspace `LDI` operations,
eleven PSG writes to `$7F`, and six YM2413 `$F0/$F1`
register-address/data pairs. All 16 source-built ROM banks
still match SHA-256
`02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
**The sound backend logs register writes but plays no audio.**

**SMS/GG Recomp Phase 1:** the optional adapter, ROM hash/CRC
identity check, Ys TOML configuration, Make targets and independent
synthetic provenance tests are integrated. The real source-ROM identity
passed its adapter preflight. However, CI does **not** invoke a real
upstream SmsRecomp generator, and no generated-C CPU code has
been compiled or linked into the native game. This remains
an integration scaffold, not a functioning static recompile.

Windows: extract both ZIP layers, run `START_HERE.cmd`,
choose **1** for a ROM-free synthetic video test or **3** to
trace your legal Ys ROM to `$0C55` and view the saved VDP image.
The screenshot is frozen, potentially blank, and not a game.

See [M40 original sound initialization and recomp boundary](research/M40_SOUND_INIT.md).
Alpha, Beta and Final release gates remain blocked.

## Previous milestone — M39

# M39 — Verified bank-2 sound call and SMS/GG Recomp ROM preflight

The original Ys SMS source-ROM trace now reaches **Z80 PC=$8803** by
executing the game's actual `$0C4D` load, `$0C4F` Sega mapper
selection, and `$0C52 CALL $8803`. The source CPU's stack holds
the real return address `$0C55`, with **104,749 instructions**,
**1,194,183 nominal T-states**, **16** accepted interrupts and
**20** generated VBlank events. The first bank-2 opcode is `$E5`.
[Gated source-ROM CI passed](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38443152403).
The sound initializer itself has **not** been executed yet.

The [SMS/GG Recomp Phase-1 adapter](../Ys/recomp/README.md) also
passed its ROM identity preflight against the **actual Ys source-built
256 KiB cartridge**, confirming SHA-256
`02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`
and CRC-32 `B33E2827`. Its separately integrated
[adapter CI](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38424674348)
passed **9 synthetic tests**. The external SmsRecomp tool is not
vendored or executed in CI, and its generated C is **not yet
compiled, linked or run** in the native game runtime.

Windows: extract both ZIP layers, double-click `START_HERE.cmd`,
choose **1** for synthetic SMS video diagnostics or **3** to run your
own legally obtained Ys ROM to `$8803` and view a frozen VDP
screenshot. This is a **Development-only test, not playable Ys**.

See [M39 sound handoff and identity evidence](research/M39_SOUND_HANDOFF.md).
Alpha/Beta/Final promotion remains blocked.

## Previous milestone — M38

# M38 — Original 1792-byte VRAM name-table clearing

The continuous original Ys SMS Z80 trace executes **104,746**
instructions and **1,194,146** nominal T-states from cold reset
through a genuine VBlank interrupt during the original
`$0A77 / $06D4` VRAM name-table clear.

The source wrote **896 16-bit words (1,792 bytes)** through VDP
port `$BE`, and a real IM1 IRQ suspended CPU execution at
`$06DE`. The native runtime preserved and resumed original
execution to **PC=$0C4D**, with **16** accepted interrupts,
**20** generated VBlanks and **4,353** cumulative VRAM writes.
[Full source-ROM verification passed](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38425466962);
all 16 original ROM banks and the 256 KiB hash were unchanged.

The separate [SMS/GG Static Recomp Phase 1](../Ys/recomp/README.md)
adapter is also integrated. It verifies an owner's ROM hash/CRC,
invokes a separately installed recompiler and checks the hashes
of generated C files. It does **not** currently build or execute
a recompiled Ys runner, and its integration is not gameplay evidence.

Windows users should extract both ZIP layers and double-click
`START_HERE.cmd`. Option **1** runs a synthetic SMS hardware
test; option **3** traces a user-supplied Ys ROM and opens the
**saved static VDP snapshot** at `$0C4D`. This is still
a Development diagnostic, not playable Ys.

```sh
bin/ys-native-timed-rom /path/to/your/Ys.sms --frame checkpoint.ppm
```

See [M38 original source and IRQ trace](research/M38_NAMETABLE_CLEAR.md).
Alpha/Beta/Final gates remain blocked.

## Previous milestone — M37

# M37 — First source ROM graphics-memory clear verified

The continuous native Z80 implementation has now executed the actual
Ys Sega Master System cartridge through its VDP scroll-register updates
and the first **64-byte VRAM clear**. The original game naturally
reaches **PC=$0A77**, having written zeroes to VRAM `$0000-$003F`
through the unmodified `$06D4` helper.

[The full source-ROM verification](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38383836571)
passed: **97,144 source Z80 instructions**, **1,129,966 nominal
T-states**, **15** accepted interrupts, **19** generated VBlanks,
**2,561** cumulative VRAM writes, and VDP scroll registers
`R8=$00/R9=$00`. The authentic VDP write pointer ended at `$0040`.
All 16 source-only ROM banks rebuilt with the established SHA-256;
the older M25 manually injected path and previous M29–M36 naturally
clocked milestones remain passing.

On Windows, **extract both ZIP layers**, then double-click
`START_HERE.cmd`. Choose **1** for a persistent synthetic graphics
test window or **3** to trace your own legally obtained 256 KiB
Ys SMS ROM to `$0A77` and view its **static** VDP-state image.

```sh
bin/ys-native-timed-rom /path/to/your/Ys.sms --frame checkpoint.ppm
```

See [M37 graphics-memory source trace](research/M37_FIRST_VRAM.md).
This initial 64-byte VRAM operation does not constitute a rendered
Ys title screen or interactive native gameplay. The longer
`$3800` name-table clear remains the next source-ROM milestone.
All Alpha/Beta/Final promotion gates remain false.

## Previous milestone — M36

# M36 — Actual bank-7 data copy and original VDP initialization

The C11 source-ROM tracer now runs continuously from cold reset through
M35's **twelve real frame waits**, then switches slot 2 to original
ROM bank 7 and copies 16 source palette bytes from `$B9C3` into
WRAM `$C170-$C17F` using the unmodified `LDI` loop.

[Full gated source-ROM verification](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38382817751)
passed at **PC=`$0A5E`**: 96,849 original Z80 instructions,
1,127,522 nominal T-states, exactly 16 bank-7 LDI operations,
15 accepted interrupts and 19 generated VBlanks. Original VDP
registers 0/1 are `$26/$A0`; the source wrote `$D0` to
sprite Y-table VRAM `$3F00`. The 16-bank 256 KiB ROM digest matched
the established source reconstruction, and 13 native tests passed.

The Windows Development launcher `START_HERE.cmd` still provides
option **1** for its standalone, ROM-free hardware-test window and
option **3** for a user-supplied Ys SMS ROM's **saved** real-cartridge
VDP image at the later `$0A5E` checkpoint:

```sh
bin/ys-native-timed-rom /path/to/your/Ys.sms --frame checkpoint.ppm
```

The real screen can remain blank at this early graphics-initialization
point. **This does not yet run Ys graphics or gameplay live**, and
Alpha/Beta/Final promotion evidence remains blocked.
See [M36 source-backed bank-7 and VDP trace](research/M36_BANK7_VDP.md).

## Previous milestone — M35

# M35 — Twelve original Ys palette waits, four fade levels

The original Sega Master System cartridge now runs continuously from
cold reset through **four palette nibble transforms and twelve
clock-generated VBlank waits**, reaching **PC=`$0B00`**, just before
the bank-7 graphics/palette data transfer.

[Full source-ROM verification](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38350370954)
passed: **96,733** Z80 instructions, **1,126,507** nominal T-states,
**19** generated VBlanks, **15** accepted IM1 IRQs,
**2,496** VRAM writes and **176** PSG writes. No IRQ was injected
and all 16 source-only 256 KiB ROM banks retained the established SHA-256.
The source ISR clears the palette-update flag at `$C02C` as part of
each palette/frame update; the final value is correctly `00`.

The Windows Development ZIP still contains `START_HERE.cmd` and a
standalone native Win32 GDI window. Choose **1** for the synthetic
hardware-display animation or **3** to run your own Ys Master System
ROM to `$0B00` and view a **static** real-cartridge VDP screenshot.
The exported screenshot is not a running game or completed title screen.

```sh
bin/ys-native-timed-rom /path/to/your/Ys.sms --frame checkpoint.ppm
```

See [M35 palette-delay source verification](research/M35_PALETTE_DELAYS.md).
All Alpha, Beta and Final promotion gates remain false.

## Previous milestone — M34

# M34 — Original dispatcher and palette nibble transform

The Development runtime continues from M33's naturally completed
`$00C4` wait into the source dispatcher, its state 0 initialization
and state 1 transition at `$0C4A`. It traces the 32-byte
staging copy `$0B10` and authentic `$0B22` Z80
`RLD/SUB C/RRCA/RLCA/DJNZ` palette transform, stopping
at **`$0AF6`** before the next timed palette-delay loop.

The interpreter now supports Z80 `SUB r`, `RLCA` and `RRCA`
with source-accurate flags and documented nominal T-states.
A ROM-free, byte-accurate fixture validates 32 iterations;
the gated original-cartridge check independently validates
the continuous CPU path. No `Ys/**` sources change.

```sh
bin/ys-native-timed-rom /path/to/your/Ys.sms --frame checkpoint.ppm
```

Windows `START_HERE.cmd` option **3** runs this original-cartridge
trace and shows the saved VDP PPM image in a native GDI window.
The screenshot is **static early initialization**, not a
live title or playable game, and may still lack tile graphics.

See [M34 source-backed palette trace](research/M34_TIMED_PALETTE.md).
Alpha/Beta/Final promotion gates remain false.

**M34 verified:** [ROM check 38348967643](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38348967643)
executed **24,468 source-ROM Z80 instructions** and **416,854 nominal
T-states** to original `PC=$0AF6`, after a 713-step palette nibble
transformation. The earlier dispatcher, 32-byte staging copy,
three naturally accepted IRQs and 192 VRAM writes remain verified.
M34 Release tests passed on Windows/Linux/macOS.

## Previous milestone — M33

# M33 — First original frame wait completed under automatic VBlank

The real Ys SMS cartridge's timed execution now targets the first
**source VBlank-wait completion**, not merely the ISR entry or the
frame-wait polling instruction. Beginning at M32 `$0046`, the
interpreter continues through the original `LD A,($C021); OR A;
JR NZ,$0046` loop. A naturally generated VBlank invokes the actual
source `$0038` handler. Its nonzero-wait branch updates the VDP,
handles sprites/input and bank-2 sound, clears the wait flag, and
returns through the saved-register `$0BC5` bridge to startup
**PC=$00C4**. No IRQ is injected and no source game state is
patched or skipped.

`bin/ys-native-timed-rom Ys.sms --frame checkpoint.ppm` captures
the real 256×192 RGB VDP state at this **later checkpoint**, after
the first VBlank VRAM transfer, rather than the previous early
`$0046` blank-state capture. Windows `START_HERE.cmd` option 3
exports that image and opens it in the GDI viewer. It remains a
**read-only snapshot**, not live Ys gameplay, and may not display
the title image until additional initialization has run.

See [M33 source verification contract](research/M33_TIMED_WAIT.md).
Alpha remains blocked; source-only ROM rebuild remains gated.

**Verified M33 evidence:** [gated source-ROM run 38348188019](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38348188019)
passed with `23,583` instructions, `409,651` nominal Z80
T-states, `7` generated VBlank events, `3` accepted IM1 interrupts,
and exact original source PC `$00C4`. The final ISR produced
`192` VRAM writes and a cumulative `44` PSG writes.
An actual cartridge VDP snapshot was verified as a 147,471-byte
P6 PPM image. The 16-bank 256 KiB source-only ROM digest matched.

## Previous milestone — M32

# M32 — Real Ys startup image linked to Windows Development viewer

The **timed original-cartridge trace** now continues beyond M30's
completed two-IRQ zero-state handler at `$0764`:

1. Execute source `$0764 POP AF`, `$0765 OUT ($BE),A`,
   `$0767 RET`, returning to original reset/startup at `$00C1`.
2. Enter the bank-0 `$00C1 CALL $0BC5` VBlank-wait bridge, which
   saves registers and jumps to `$0042`.
3. Verify the bridge sets `$C021=1`, executes `EI`, and reaches
   **`PC=$0046`**, before the first original wait-loop poll.
4. Stop, without injecting interrupts or supplying fake input.
   The existing M30 checkpoints continue to be asserted first.

**New Development command** (requires your own 256 KiB Ys SMS image):

```sh
bin/ys-native-timed-rom /path/to/your/Ys.sms --frame checkpoint.ppm
```

This records a portable 256×192 P6 RGB image of the **real Ys VDP
register/VRAM/CRAM state** at PC=$0046. This very early boot
checkpoint may render a blank image because display initialization and
title graphics are incomplete. The exporter does not change the
game's VDP registers to force a visually convincing image.

On Windows, the existing `START_HERE.cmd` **menu option 3** now
performs this ROM-backed trace and opens `checkpoint.ppm` in
`ys-native-window.exe --ppm checkpoint.ppm`. The viewer supports
read-only screenshot presentation in addition to the independent,
ROM-free synthetic animation (option 1). The loaded screenshot does
**not** continue executing ROM code or accept gameplay input.

CI includes a Windows GUI PPM-loading smoke test with a synthetic
image. A single explicitly marked `[rom-check]` verification also
checks the authentic 16-bank ROM reconstruction, verifies actual
source PC/$C021/IRQ conditions, and validates the exported PPM size.
No source-ROM files were modified.

**Alpha, Beta and Final are still gated.** M32 proves neither title
rendering nor native gameplay; it is the first visual inspection
pipeline from actual cartridge execution in the Windows launcher.

## Earlier milestones — M31 and before

# M31 — First usable Windows Development diagnostic

Previous Development ZIPs shipped mostly **command-line tools** and an
optional SDL2 viewer. Double-clicking a console executable in Explorer
typically launched it briefly and exited; the SDL2 viewer could be absent
or require an unbundled DLL. Those packages were *not* suitable as
click-to-run Windows tests.

M31 fixes the **user-facing Development test experience**, not gameplay:

- Guaranteed `bin/ys-native-window.exe`: a persistent Windows-native
  window built with GDI and the Win32 API, using no SDL2 or third-party
  dynamic library. Its native C11 renderer displays moving synthetic SMS
  tiles/sprites, a frame counter, and a clear "NOT YS GAMEPLAY" message.
  Arrow keys move a test sprite, Space pauses, F1 shows help and Escape
  closes the window.
- Mandatory `START_HERE.cmd` in the **root of the extracted Windows
  build ZIP**. Double-click it for a persistent selection menu; options
  open the graphics window, check timed CPU/VBlank execution, run the
  bounded real-ROM startup tracer, export an image or show build info.
  Console results are copied to `last-diagnostic.txt`; the menu remains
  open when errors occur.
- Windows Release builds use MSVC's **static C runtime (/MT)** instead
  of relying on a separately installed VC++ Redistributable. The native
  Windows GUI always ships in the ZIP; packaging fails if the compiled
  `ys-native-window.exe` is absent.
- CTest runs `ys-native-window.exe --self-test` using the Windows
  GUI-subsystem executable without requiring a graphical desktop.
  Packaging tests require a launcher and graphical binary in every
  Windows Development ZIP and confirm its correct manifest.
- Source-ROM behavior remains independently verified by the existing
  M30 timed trace to `$0764`. No ROM recompilation or game-frame claims
  are added by M31.

## How to run on Windows

1. Open the **Ys native phase builds** workflow for M31 and download
   the **windows-2022** artifact.
2. GitHub's artifact download might itself be a ZIP containing the
   versioned `ys-m31-dev-windows-x64-...`.zip. **Extract both ZIPs**,
   leaving `START_HERE.cmd` and a `bin` folder together.
3. Double-click `START_HERE.cmd`, choose **1**. Or double-click
   `bin/ys-native-window.exe`. A window should remain open even
   without a ROM, showing a **synthetic** tile-and-sprite animation.
4. For native cartridge startup, choose **3** in the menu and enter
   the full path to *your* legally obtained **Ys SMS 256 KiB ROM**.
   The program displays output and writes `last-diagnostic.txt`.

If Windows blocks the downloaded archive or refuses to open it, consult
Windows Security/Properties for the exact reported reason; do not disable
security protections simply to run an unfamiliar binary. If the program
still fails, provide the Windows version, exact error or screenshot and,
for diagnostics, the contents of `last-diagnostic.txt`.

**What M31 is NOT:** This test window does not execute the Ys game,
display real Ys title graphics, or provide native gameplay. Only the
CLI `ys-native-timed-rom` uses a user-supplied ROM and still stops at a
bounded startup checkpoint. The **Alpha** gate remains blocked.

## Previous checkpoint — M30

# M30 — Timed zero-state ISR return to original startup

The full source-ROM trace now executes from cold reset through **two
naturally generated VBlank interrupt entries**. The first ISR returns
from `$01AA EI / $01AB RET` while another VBlank is pending, so
IM1 immediately re-enters at `$0038`. The second zero-state ISR
finishes with a stable return to **PC=$0764**, before the source
`POP AF` at that address.

**Verified:** [GitHub Actions run 38344640720](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38344640720):
17,205 executed Z80 instructions, 346,813 nominal T-states, 6
generated VBlank events, 2 accepted interrupts, final SP=$DFEC,
mapper control $80, bank 2 selected. Both the initial re-entry and
the final return preserve main/alternate Z80 general registers,
IX/IY and mapper state. The original 16-bank source-built
256 KiB cartridge matched SHA-256, and 13 CTest suites passed.

```sh
bin/ys-native-timed-rom /path/to/your/Ys.sms
```

This is still a **Development** diagnostic, not a game window, title,
continuous startup or playable Alpha. The older `ys-native-trace`
continues to verify the separate manually injected M25 path to
`$0B22`. [M30 detailed source/clock trace](research/M30_TIMED_ISR.md).

No further M10 rebuild is needed for these documentation and build-label
changes. Alpha/Beta/Final promotion gates remain false.

## Previous milestone — M29

# M29 — Actual source-ROM reset to first timed VBlank

The Development build now includes `ys-native-timed-rom`, a
**user-supplied ROM diagnostic** which executes the original Ys startup
with automatically generated scanline VBlank instead of injected IRQ
status. It stops after the source ISR `$0038 PUSH AF` /
`$0039 IN A,($BF)` clears VBlank, with program counter `$003B`.
It prints actual CPU instructions, nominal T-states, scanline, IRQ
count and interrupted return PC.

**Verified full-ROM result:** [GitHub Actions 38343836595](https://github.com/Hyperbog/Ys-Decomp/actions/runs/38343836595)
passed, confirming `16,379` instructions and `338,842` nominal
T-states, with **5** generated VBlank events and **1** accepted IM1 IRQ.
The interrupted PC was `$0764` (during VDP initialization), and the
original status read stopped at `PC=$003B`, `SP=$DFE8`.
The established 256 KiB ROM checksum matched the source-only rebuild.
The separately gated M25 trace still passed to `$0B22`.

```sh
bin/ys-native-timed-rom /path/to/your/Ys.sms
```

It never bundles a ROM; existing `ys-native-trace` still exercises
the separate M25 checkpoint at `$0B22` with its explicit VBlank event.
The M29 diagnostic **does not complete the ISR, display a title or
provide gameplay**. See [M29 source-timed trace](research/M29_TIMED_SOURCE_TRACE.md).

Alpha/Beta/Final promotion gates remain unpassed. Real instruction T-state
counts are nominal, with VDP contention and line interrupts deferred.

## Previous milestone — M28

# M28 — CPU-timed VBlank runtime (Development build)

The native Z80 core now records per-instruction T-state counts and a
running total. `ys_sms_runtime_step_auto` advances the M27 NTSC/PAL
frame clock from those counts, including conditional-branch timing,
a 13-T IM1 acknowledge, and 4-T refresh while HALTed. This enables
automatic *hardware event recognition* without manually injecting IRQ
events, but it is not yet a playable or faithfully synchronized Ys game.

The ROM-independent Development executable
`ys-native-timing --check` verifies the full synthetic NOP/EI → VBlank
→ IM1 `$0038` → status-acknowledge sequence. This new milestone does
**not** change the source-ROM execution boundary at M25 PC `$0B22`.
No proprietary ROM, assets, or full reconstruction are required.

See [M28 timing contract and tests](research/M28_TIMING.md). Alpha
promotion gates remain false pending genuine game-frame execution,
desktop game rendering, live input, and interactive gameplay.

## Previous milestone: M27

# M27 — Frame clock, automatic VBlank recognition and synthetic live frames

The native C11 Development build now includes an explicitly T-state-driven
SMS NTSC/PAL scanline clock, an IM1 VBlank-delivery bridge, and a
ROM-independent `ys-native-frames` CLI capable of exporting a sequence of
animated 256×192 PPM frames. No original ROM/image assets are bundled.

```sh
bin/ys-native-frames --check
bin/ys-native-frames demo 12 ntsc
bin/ys-native-frames demo-pal 12 pal
```

The second command writes `demo-000.ppm` through `demo-011.ppm`.
Each image uses the synthetic M26 tile-and-sprite fixture, not Ys game art.
On systems where the SDL2 development library was installed when CMake
configured the build, an **optional** `ys-native-display` executable
opens a scaled desktop window with this *same synthetic animation*.
The SDL2 runtime library must also be installed on the recipient machine.
The cross-platform downloadable Development build **always** supports
headless PPM sequences but **may not** include the optional window binary.

Core device interfaces: `sms_clock.[ch]` emits NTSC 262-line and PAL
313-line clocks with 228 caller-supplied Z80 T-states per line. Line 192
sets the sticky VDP VBlank status bit (0x80), which persists until a VDP
status-port read. `sms_runtime.[ch]` advances this clock and automatically
vectors an eligible IM1 CPU interrupt when VBlank is enabled in VDP
register 1, bit 5, respecting CPU IFF1 and EI delay.

**Timing limitation:** `z80.c` does not yet report instruction T-state
durations. The runtime bridge consumes T-states supplied by its caller.
Its synthetic animation advances a whole frame clock per generated image;
it does not claim Z80 instruction-accurate gameplay frames. The existing
source-ROM execution trace still stops before `$0B22` after 17,224
instructions and one specifically injected VBlank. This milestone
**does not** pass a new original-ROM checkpoint, so no M10 rebuild is
required and original ROM/source files are unchanged.

The Alpha gates for boot-to-title, frame accuracy, finished renderer,
live game controls and interactive gameplay all remain false.

## Previous checkpoint — M26

# M26 — Native SMS video snapshots (Development build)

The Development artifacts now contain **ys-native-preview**, a standalone
256×192 Sega Master System mode-4 video diagnostic that writes a portable
PPM image. It uses an entirely synthetic tile/sprite scene; it is **not**
a screenshot of Ys, and it does not require or bundle game assets.

From a released Development ZIP (or locally built binaries):

```sh
bin/ys-native-preview synthetic.ppm
bin/ys-native-preview --check
bin/ys-native-trace /path/to/your/Ys.sms --frame checkpoint.ppm
```

The third command renders the current VRAM, CRAM and register state from the
**actual user-supplied cartridge** at the already-verified M25 execution
boundary (PC=$0B22). The scene is not yet fully initialized and may appear
mostly blank. The standalone preview is the recommended way to test the
renderer itself. Both PPM files can be opened in many graphics editors or
converted to PNG with image tools.

`native/sms_video.c` implements stateless 256×192 mode-4 background tile
decoding, CRAM RGB222→RGB888, horizontal/vertical scroll, tile flips,
palette selection and priority, the left 8-pixel mask, sprite-pattern and
attribute lookup, sprite order, transparency, 8-per-scanline limit, size
8×16 and zoom. Tests cover the individual behaviors and PPM format.
It does **not** emulate 224/240-line modes, scanline timing, collisions as
CPU-visible status or a screen window. It does not draw a completed game
frame without the game's ROM code having first initialized its VRAM.

**Build and packaging:** `native/release/gates.json` names checkpoint M26;
the `dev` archive includes the preview executable and unchanged diagnostic
probe/trace utilities. Alpha's `video_renderer` gate stays **false**
because an interactive video window, actual frame pacing and complete title
screen are not proven.

**No new ROM reconstruction** is required: this change does not advance Z80
execution beyond the already source-verified M25 $0B22 boundary. Native
builds and video test fixtures run with no game ROM.

## Earlier milestones

# Ys native C11 — M25: state-table dispatch enters scene preparation

The continuous source-ROM trace now follows the first two startup states
after the fully verified initial VBlank interrupt and return.
The dispatch loop at `$00C4` reads `$C01F=0` and vectors via `RST $08`
to `$00FC`, which sets state `$C01F=1` and returns.
The next dispatch resolves the ROM word table to `$0C4A` and calls
`$0A5B` → `$0A80` → `$0AE8` → `$0B10`. The final routine copies 32
bytes from `$C160` into `$C530`; the acceptance point is PC=`$0B22`,
**before executing the palette/tile nibble conversion**.

The Z80 core adds `ED 6F` (`RLD`) for upcoming nibble-processing code,
with carry-preserving flags and fail-closed writes. A source-backed
nonzero WRAM fixture and dedicated `RLD` tests validate the new behavior.
See [M25 source trace](research/M25_SOURCE_TRACE.md).

Ordinary native CI continues to run six fast test suites without
ROM rebuilding. An explicitly tagged `[rom-check]` commit or manual
`rom_trace=true` dispatch can validate this new ROM-dependent boundary.
Automatic VBlank frames, rendering, sound synthesis, live controller
events, fully loaded title-screen data and playable gameplay remain out
of scope.

## Previous milestones
# Ys native C11 — M24: first VBlank interrupt returns to startup

The current source-ROM trace reaches **PC=$00C4 / SP=$DFF0** after
**17,052 Z80 instructions** from reset and one explicitly injected VBlank.
All main and alternate general registers, IX/IY, stack and mapper state
were verified against the pre-interrupt snapshot. The bank-2 $8000
sound-update path writes 22 cumulative PSG bytes and 12 FM register/data
pairs (including the repeat initialization at $8803).

New bounded CPU instructions: indexed and nonindexed BIT, LD IX/IY,nn,
ADD IX/IY,rr, CP r and conditional CALL cc,nn. The source-backed tests
cover first-frame sound idle-channel scans and zero-bit flags.

All six native CTest suites and the explicitly requested 256 KiB
source-ROM checkpoint passed in CI:
https://github.com/Hyperbog/Ys-Decomp/actions/runs/38334911711

See [M24 source tracing](research/M24_SOURCE_TRACE.md) for opcode evidence.

Routine native commits do **not** rebuild the cartridge: use
workflow_dispatch rom_trace=true or a [rom-check] commit marker.
The original decompilation is unchanged and no ROM binary is committed.

The opcode at $00C4 has **not** executed yet. Video frame clocks,
automatic interrupts, native rendering, sound synthesis, controller
event polling and playable game logic remain unfinished.

## Previous checkpoint — M23
# Ys native C11 — M23: first-frame sprite upload and controller sample

The bounded CPU/VDP runtime now extends the *first manually triggered*
VBlank service sequence from bank 0's `$01B4` through its `$0427` sprite
attribute-table upload, `$03E8` conditional return, EI, bank 0's `$0773`
controller sampler, and dispatch into the `$8000` sound-frame update.
Execution stops **before the first instruction at `$8000`**.

## Native CI and reconstruction policy

```sh
cmake -S native -B build-native -DCMAKE_BUILD_TYPE=Debug
cmake --build build-native --parallel
ctest --test-dir build-native --output-on-failure
```

Fast default CI executes all native unit suites without reconstructing ROM
banks. Run the ROM-dependent trace **only** when it advances a meaningful
source-backed checkpoint, by an explicit `workflow_dispatch` with input
`rom_trace=true` or a commit containing `[rom-check]`.
For a manual source-verified test:

```sh
python3 Ys/tools/build_system_m10.py --check --out /tmp/ys-source-built.sms
./build-native/ys-native-trace /tmp/ys-source-built.sms
```

The source reconstruction asserts the original 256 KiB cartridge SHA-256
`02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
No commercial ROM or image/assets are committed.

## VBlank sprite transfer

Recovered bank-0 ROM source shows `$0427` setting VDP VRAM write addresses
`$3F00` and `$3F80`, then executing 64 and 128 literal `OUTI` instructions.
These copy the byte ranges `$DD00-$DD3F` (sprite Y coordinates) and
`$DD40-$DDBF` (sprite X/tile values) to the corresponding VDP sprite
attribute table. The model validates the 192 bytes and total write count,
including address wrapping at `$3FFF`, without drawing actual sprites.

The source-backed `$03E8` handler sees `$C02C=0` following reset and
returns to `$0125`. The code re-enables interrupts with EI and calls the
controller sampler at `$0773`. `sms_input.[ch]` supplies explicit active-low
snapshots at ports `$DC/$DD`, initially `$FF` for no input. It does **not**
automatically poll a keyboard/controller or implement other SMS I/O ports.

Additional bounded Z80 opcodes: conditional `RET` family, register
`AND/XOR/OR` forms, and `CPL`; invalid/unsupported instructions and ports
still fail closed. `test_irq.c` tests the actual source-backed sprite
upload sequence with nonzero synthetic data and controller sampling with
both pressed and unpressed buttons.

## Explicit non-goals

The full first VBlank ISR **has not returned** to the interrupted caller;
`$8000` is the next unexecuted instruction. No reliable emulated frame
clock, H/VBlank scheduling, audio synthesis, controller polling, video
rendering, SDL frontend or playable game loop is present. Existing SMS
mapper-revision assumptions and incomplete Z80 opcode/flag coverage remain.

## Earlier milestones

# Ys native C11 — M22: first VBlank VDP dispatch checkpoint

## M22 acceptance boundary

The bounded native interpreter now executes the real bank-0 ISR from
`$0108` through the Z80 `OUTD`/indirect-port register transfers and
one-based `RST $08` dispatch, stopping **before the handler at `$01B4`**.
The prior source-ROM trace reaches `$0108` from reset, the SRAM and WRAM
initializers, the bank-2 sound initializer, the VDP initializer, and an
**explicitly injected** IM 1 VBlank interrupt. M22 adds no automatic clock,
frame generation, or fabricated return from that handler.

The ROM-dependent trace checks:
- Four additional VDP register commands for registers 10, 9, 8 and 5.
- Source-RAM bytes `$C01A`, `$C019`, `$C018`, and constant `$FF`
  are written to those registers in that order.
- A total of 15 VDP register writes and 32 VDP control-port bytes
  since initial native VDP reset.
- `RST $08` indexes the ROM word table at `$01AA` with selector 1,
  resolves target `$01B4`, and leaves return address `$0125`
  on the stack. The test does not execute the `$01B4` routine.

Native Z80 additions are `OUTD` (`ED AB`), `ADD A,r` (8-bit),
`JP (HL)` and the eight Z80 `RST` opcodes. `test_irq.c` executes
source-backed synthetic bytes for both the ISR and `RST $08`
helper, including VDP register and stack assertions.

### Efficient verification

The GitHub native workflow runs CMake/CTest **without** rebuilding the
cartridge on routine pushes and pull requests. Full ROM reconstruction is
reserved for an explicit workflow dispatch with `rom_trace=true`, or a
commit message containing `[rom-check]`. The independent integrity workflow
still runs for changes to the original `Ys/**` source and on manual dispatch.
A source-ROM rebuild is warranted for this new `$01B4` checkpoint.

### Limits

No clock-driven interrupts, ISR return, main loop dispatch, controller polling,
VDP rendering, audio synthesis, SDL display or playable PC build are claimed.
The original ROM reconstruction, source data and digests remain untouched.
The next objective is to investigate the handler at `$01B4` and its callees,
then resume the interrupted startup after independently verified state changes.

## Earlier milestone notes

# Ys native C11 — M21 interrupt-entry checkpoint

Current M21 boundary: continuous reset executes through the banked sound
initializer and initial VDP register programming, then enters the actual
$0BC5 bridge and $0042 VBlank wait. The test explicitly injects one IM 1
interrupt **after EI defer expires** and runs the original $0038 handler
through $0102 to the $0108 branch point. The event is manually injected;
there is no frame clock or automatic interrupt delivery.

Implemented M21 Z80 support: EX AF/AF', EXX, PUSH/POP IX/IY, conditional JP,
RETI/RETN, EI deferral and externally delivered maskable interrupts. Synthetic
and source-backed unit cases are in test_irq.c. All unsupported IX/IY prefixed
opcodes still fail closed.

Fast CI runs the five native test suites without cartridge reconstruction.
The ROM-dependent trace runs only when explicitly requested with rom_trace=true
or a [rom-check] commit marker. No playable native game loop, graphics renderer,
audio output, clock-driven IRQs or controller input is claimed.

## Prior checkpoint: M20

# Ys native C11 — M20: continuous banked sound + VDP startup

This is a **bounded execution harness**, not a playable port or a complete
Z80/Sega Master System emulator. The verified ROM-source baseline, ROM digest,
and existing decompilation artifacts remain unchanged.

## Execute fast native tests

```sh
cmake -S native -B build-native -DCMAKE_BUILD_TYPE=Debug
cmake --build build-native --parallel
ctest --test-dir build-native --output-on-failure
```

The default native workflow now runs **only the native C11 unit tests**. No
full 256 KiB ROM reconstruction is run on ordinary native commits. To validate
the full cartridge when a new boot boundary warrants it, push a commit whose
message includes `[rom-check]`, or manually trigger the native workflow with
`rom_trace=true`. The separate M13–M17 cartridge-integrity workflow runs on
`Ys/**`, changes to its own workflow, or `AGENTS.md` (not native-only
changes). Its on-demand `workflow_dispatch` entry also remains available.

## Explicit cartridge checkpoint (slow)

```sh
python3 Ys/tools/build_system_m10.py --check --out /tmp/ys-source-built.sms
./build-native/ys-native-trace /tmp/ys-source-built.sms
```

M10 verifies SHA-256
`02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9`.
The native tracer checks the image size/header, *not* its digest; do not use
unverified ROM inputs. Never commit the reconstructed commercial game ROM.

### Continuous execution

The trace now executes real Ys instructions from the reset vector at
`$0000`, through the `$079A` SRAM signature setup, the `$00A5` work RAM
clear, physical ROM Bank 2's `$8803` sound initializer (including
`$8842` and its `$8883` delay stub), and Bank 0's `$0749` VDP initializer.
The trace halts at `$00C1`, **before `CALL $0BC5`**.

The sound initialization routine sends 11 literal bytes from physical ROM
Bank 2 `$8878` to PSG port `$7F`, then selects YM2413 FM registers
`$20–$25` through `$F0` and writes zero through `$F1`. The output sink
(`sms_sound.c`) observes I/O bytes and stores initial register state only.
**No audio synthesis, frequency timing, or player output is present.**

The VDP routine writes 11 register values from Bank 0 table `$0768` to VDP
control port `$BF`, copies that table into work RAM, and writes one zero byte
to CRAM at `$10` through data port `$BE`. Unlike the previous milestone,
this VDP call is now reached through normal reset execution without manually
seeding the routine's CPU stack.

### Additional Z80 subset

- `LDI`, `OUTI`, `OUT (C),r`, `ADD HL,rr` (with documented flags).
- Existing `LDIR` support is still bounded and approximate for undocumented
  flags; only the executed opcodes are supported.
- The fail-closed port dispatch distinguishes VDP `$BE/$BF` from PSG `$7F`
  and FM `$F0/$F1`; other I/O ports are rejected.
- Synthetic unit fixtures exercise the above instructions with mapper-selected
  bank 2; real cartridge instructions are tested in the explicitly gated
  trace step.

## Unimplemented

Further CPU instructions, cycle-accurate flags/interrupt scheduling, VDP
frame/scanline timing and rendering, PSG/YM2413 synthesis, controller input,
SDL3 frontend, save RAM persistence and full boot/gameplay. The Sega mapper
model retains its documented Phase 1 hardware-revision assumptions. Neither
the source-built ROM nor the C11 runtime has yet produced native frames.

Next milestone: continue from `$0BC5` through interrupt/state initialization
using evidence-driven CPU/port expansions, and introduce deterministic native
VDP state checks.
