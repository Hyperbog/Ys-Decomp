#!/usr/bin/env python3
"""Package *built* native diagnostics; never reconstruct or distribute game ROMs.

Promotion is gated by native/release/gates.json evidence and, for Alpha+,
the presence of a real ys-native-game executable. Development builds are
explicitly diagnostic-only.
"""
import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

REQUIRED = {
    "dev": (),
    "alpha": ("boot_to_title", "automatic_frames", "video_renderer",
              "live_controls", "interactive_gameplay"),
    "beta": ("complete_game", "save_load", "audio_playback",
             "content_parity", "no_blocking_bugs"),
    "final": ("cross_platform", "fidelity_validation", "release_audit"),
}
EXE_NAMES = ("ys-native-info", "ys-native-probe", "ys-native-trace",
             "ys-native-preview", "ys-native-frames",
             "ys-native-timing", "ys-native-timed-rom")
OPTIONAL_EXE_NAMES = ("ys-native-display",)
WINDOWS_REQUIRED_EXE = "ys-native-window"
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,47}$")


def promotion_errors(channel, state):
    if channel not in REQUIRED:
        raise ValueError("unknown channel: " + channel)
    gates = state.get("gates", {})
    missing = []
    for stage in ("alpha", "beta", "final"):
        if stage == "final" and channel not in ("final",):
            break
        if stage == "beta" and channel not in ("beta", "final"):
            break
        if stage == "alpha" and channel == "dev":
            break
        for name in REQUIRED[stage]:
            item = gates.get(name, {})
            if item.get("passed") is not True or not isinstance(
                    item.get("evidence"), str) or not item["evidence"].strip():
                missing.append(name)
    return missing


def locate_binary(build_dir, name, platform):
    suffix = ".exe" if platform.startswith("windows-") else ""
    for root in (build_dir, build_dir / "Release"):
        binary = root / (name + suffix)
        if binary.is_file():
            return binary
    raise FileNotFoundError("missing compiled binary: " + name + suffix)


def package(channel, platform, build_dir, output_dir, state_path, revision):
    if channel not in REQUIRED:
        raise ValueError("unknown release channel")
    if not IDENTIFIER.fullmatch(platform):
        raise ValueError("invalid platform label")
    if not re.fullmatch(r"[0-9a-fA-F]{7,40}", revision):
        raise ValueError("revision must be a 7-40 character git hash")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("schema_version") != 1:
        raise ValueError("unsupported release-gates schema")
    checkpoint = state.get("checkpoint", "")
    if not isinstance(checkpoint, str) or not IDENTIFIER.fullmatch(checkpoint):
        raise ValueError("missing or invalid checkpoint in release gates")
    missing = promotion_errors(channel, state)
    if missing:
        raise ValueError(channel + " promotion blocked; unmet evidence gates: " +
                         ", ".join(missing))
    names = list(EXE_NAMES)
    if platform.startswith("windows-"):
        # The persistent, dependency-free GUI is mandatory in Windows ZIPs.
        names.append(WINDOWS_REQUIRED_EXE)
    if channel != "dev":
        # A passing checklist does not make a diagnostic trace playable.
        names.append("ys-native-game")
    binaries = {name: locate_binary(build_dir, name, platform) for name in names}
    if not platform.startswith("windows-"):
        for name in OPTIONAL_EXE_NAMES:
            try:
                binaries[name] = locate_binary(build_dir, name, platform)
            except FileNotFoundError:
                pass  # Optional SDL2; Windows instead gets guaranteed GDI GUI.
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = "ys-" + checkpoint.lower() + "-" + channel + "-" + platform + "-" + revision[:8]
    archive = output_dir / (stem + ".zip")
    hashes = {}
    contents = {}
    for name, binary in binaries.items():
        archive_name = "bin/" + binary.name
        raw = binary.read_bytes()
        contents[archive_name] = raw
        hashes[archive_name] = hashlib.sha256(raw).hexdigest()
    readme_lines = [
        f"Ys native C11 {checkpoint} - {channel.upper()}",
        f"Commit: {revision}",
        f"Platform: {platform}",
        "",
        "This bundle does NOT contain any game ROM or proprietary assets.",
        ("DEVELOPMENT DIAGNOSTICS ONLY: NOT A PLAYABLE PC GAME."
         if channel == "dev" else
         "Playable native game: bin/ys-native-game (check release notes)."),
        "",
        "In a terminal run bin/ys-native-info --help.",
        "Diagnostics (requires a user-supplied, legally obtained 256 KiB "
        "Ys Master System ROM image):",
        "    bin/ys-native-probe PATH_TO_YOUR.sms",
        "    bin/ys-native-trace PATH_TO_YOUR.sms",
        "The tracer stops at a bounded decompilation checkpoint.",
        "Synthetic video preview (no ROM necessary):",
        "    bin/ys-native-preview synthetic.ppm",
        "Snapshot actual VDP state at the bounded checkpoint:",
        "    bin/ys-native-trace PATH_TO_YOUR.sms --frame checkpoint.ppm",
        "Export ROM-independent synthetic VDP frames:",
        "    bin/ys-native-frames demo 12 ntsc",
        "Auto-timed synthetic Z80/IM1 VBlank check:",
        "    bin/ys-native-timing --check",
        "Trace ROM through 12288 graphics and 5344 staged WRAM bytes to $0C92:",
        "    bin/ys-native-timed-rom PATH_TO_YOUR.sms",
        "    bin/ys-native-timed-rom PATH_TO_YOUR.sms --frame checkpoint.ppm",
    ]
    if platform.startswith("windows-"):
        readme_lines[:0] = [
            "WINDOWS: EXTRACT THE ENTIRE ZIP first, then double-click",
            r"START_HERE.cmd, or bin\ys-native-window.exe to open the GUI.",
            "The GUI opens a ROM-free synthetic SMS VIDEO DIAGNOSTIC by default.",
            "In START_HERE.cmd choose 3 to load a real ROM's VDP snapshot.",
            "The snapshot is a bounded initialization state, NOT gameplay.",
            "The other .exe tools are command-line utilities; double-clicking",
            "them may briefly open a console and close. Run START_HERE.cmd.",
            "",
        ]
    else:
        readme_lines += [
            "Optional bin/ys-native-display is an SDL2 diagnostic window;",
            "it requires a separately installed SDL2 runtime (not bundled).",
        ]
    readme_lines += [
        "These are PPM files readable by image editors and viewers.",
        "Use a compatible SMS emulator to play the original cartridge;",
        "these binaries are a native reconstruction workbench.",
    ]
    readme = ("\n".join(readme_lines) + "\n").encode("utf-8")
    if platform.startswith("windows-"):
        launcher = (Path(__file__).resolve().parents[1] /
                    "release" / "START_HERE.cmd").read_bytes()
        contents["START_HERE.cmd"] = launcher
        hashes["START_HERE.cmd"] = hashlib.sha256(launcher).hexdigest()
    contents["README.txt"] = readme
    hashes["README.txt"] = hashlib.sha256(readme).hexdigest()
    manifest = {
        "schema_version": 1,
        "project": "Ys Sega Master System native C11",
        "entrypoint": ("START_HERE.cmd" if platform.startswith("windows-")
                       else "bin/ys-native-info"),
        "graphical_diagnostic": ("bin/ys-native-window.exe"
                                 if platform.startswith("windows-") else None),
        "channel": channel,
        "checkpoint": checkpoint,
        "platform": platform,
        "revision": revision,
        "playable": channel != "dev",
        "rom_included": False,
        "gates": {name: state["gates"][name] for stage in ("alpha", "beta", "final")
                  for name in REQUIRED[stage]
                  if (stage == "alpha" and channel != "dev") or
                     (stage == "beta" and channel in ("beta", "final")) or
                     (stage == "final" and channel == "final")},
        "sha256": hashes,
    }
    contents["manifest.json"] = (json.dumps(manifest, indent=2, sort_keys=True) +
                                 "\n").encode("utf-8")
    contents["SHA256SUMS.txt"] = "".join(
        sha + "  " + name + "\n" for name, sha in sorted(hashes.items())
    ).encode("utf-8")
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED,
                         compresslevel=9) as zipped:
        for name, raw in sorted(contents.items()):
            info = zipfile.ZipInfo(name)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (0o100755 if name.startswith("bin/") else
                                  0o100644) << 16
            zipped.writestr(info, raw)
    return archive


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", choices=tuple(REQUIRED), default="dev")
    parser.add_argument("--platform", required=True,
                        help="e.g. linux-x64, windows-x64, macos-arm64")
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--gates", type=Path,
                        default=Path(__file__).resolve().parents[1] /
                                "release" / "gates.json")
    parser.add_argument("--revision", required=True)
    args = parser.parse_args(argv)
    try:
        result = package(args.channel, args.platform, args.build_dir,
                         args.output_dir, args.gates, args.revision)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(2, "BUILD BLOCKED: " + str(exc) + "\n")
    print("PACKAGE READY:", result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
