#!/usr/bin/env python3
"""R1 headless compile/link of *actual* externally generated SMS/GG C.

Never vendors upstream sources or ROM-derived C. Compile success is not
CPU/VDP parity or playable-game evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    "runner/main.c", "runner/glue.c", "runner/video/sms_vdp.c",
    "runner/audio/sn76489.c", "runner/external/superzazu/z80.c",
)


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def require_regular(path, label):
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular file: {path}")


def compile_recomp(args):
    # These inputs are explicitly external; never download an undeclared-license
    # upstream dependency into the Ys source tree.
    manifest = args.manifest.resolve()
    config = args.config.resolve()
    upstream = args.upstream.resolve()
    generated = args.generated.absolute()
    out = args.output.absolute()
    if generated.name != "generated" or generated.is_symlink():
        raise ValueError("generated output must be a non-symlink directory named generated")
    if (out.parent.is_symlink() or out.is_symlink() or
            not out.parent.is_dir()):
        raise ValueError("runner output parent must exist, be real, and not be a link")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", args.prefix):
        raise ValueError("invalid generated C filename prefix")
    require_regular(args.tool, "External recompiler")
    for name in SOURCES:
        require_regular(upstream / name, "Upstream runner source")
    for name in ("include/sms_runtime.h", "include/z80_ops.h"):
        require_regular(upstream / "external/z80-recomp-core" / name,
                        "External shared Z80 ABI")
    suffixes = ("full.c", "dispatch.c", "layout.c", "funcs.h")
    for suffix in suffixes:
        require_regular(generated / f"{args.prefix}_{suffix}", "Generated input")
    require_regular(generated / "report.json", "Generated provenance")
    # Delegate ROM SHA + CRC, config, generator binary and four-file hashes
    # to the canonical existing adapter. Never skip provenance for compilation.
    verify = [
        sys.executable, str(ROOT / "shared_decomp/smsgg_recomp.py"),
        "--rom", str(args.rom), "--manifest", str(manifest),
        "--config", str(config), "--tool", str(args.tool),
        "--output", str(generated), "--verify-generated",
    ]
    subprocess.run(verify, check=True, timeout=90)
    sources = [str(upstream / s) for s in SOURCES]
    sources.extend(str(generated / f"{args.prefix}_{part}.c")
                   for part in ("full", "dispatch", "layout"))
    command = [
        args.cc, "-std=c11", "-O1", "-DSMSGG_HAVE_GAME_LAYOUT",
        "-I" + str(upstream / "runner"),
        "-I" + str(upstream / "runner/include"),
        "-I" + str(upstream / "runner/video"),
        "-I" + str(upstream / "external/z80-recomp-core/include"),
        "-I" + str(generated),
        *sources, "-o", str(out),
    ]
    subprocess.run(command, check=True, timeout=240)
    require_regular(out, "Linked runner")
    report = {
        "schema": "ys-r1-compiled-recomp-v1",
        "compile_link": "passed",
        "executed": False,
        "runtime_verified": False,
        "generated_report_sha256": sha256(generated / "report.json"),
        "runner_sha256": sha256(out),
        "upstream_sources_sha256": {s: sha256(upstream / s) for s in SOURCES},
        "external_core_header_sha256": {
            s: sha256(upstream / "external/z80-recomp-core" / s)
            for s in ("include/sms_runtime.h", "include/z80_ops.h")
        },
    }
    # Keep all derived reports in ignored build/; never mutate adapter's
    # codegen-only provenance report or incorrectly set runtime_verified.
    evidence = out.parent / "compiled-report.json"
    evidence.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, default=ROOT / "Ys/manifest.json")
    ap.add_argument("--config", type=Path, default=ROOT / "Ys/recomp/game.toml")
    ap.add_argument("--generated", type=Path, default=ROOT / "recomp/generated")
    ap.add_argument("--upstream", type=Path, required=True)
    ap.add_argument("--tool", type=Path, required=True)
    ap.add_argument("--prefix", default="ys_sms")
    ap.add_argument("--output", type=Path, default=ROOT / "recomp/build/ys_sms_runner")
    ap.add_argument("--cc", default="cc")
    args = ap.parse_args()
    try:
        output = compile_recomp(args)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        ap.exit(2, f"FAIL R1 compile/link: {error}\n")
    print(f"PASS R1 compiled and linked: {output}")
    print("NOT VERIFIED: actual Ys execution, CPU/VDP parity, gameplay")


if __name__ == "__main__":
    main()
