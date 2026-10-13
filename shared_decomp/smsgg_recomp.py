#!/usr/bin/env python3
"""Opt-in SMS/GG Recomp code generation; never commit ROM-derived C."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib


class RecompError(Exception):
    pass


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_rom(rom, manifest):
    data = json.loads(manifest.read_text(encoding="utf-8"))
    identity = data.get("binary", data)
    expected_hash = identity.get("sha256")
    expected_size = identity.get("size", data.get("rom_bytes"))
    if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_hash):
        raise RecompError("manifest must specify an exact SHA-256")
    if not isinstance(expected_size, int) or expected_size <= 0:
        raise RecompError("manifest must specify an exact ROM size")
    size = rom.stat().st_size
    sha = digest(rom)
    if size != expected_size or sha != expected_hash.lower():
        raise RecompError(
            f"ROM identity mismatch: size={size}, sha256={sha}; "
            f"expected size={expected_size}, sha256={expected_hash.lower()}"
        )
    return size, sha


def read_config(config):
    data = tomllib.loads(config.read_text(encoding="utf-8"))
    game = data.get("game", {})
    prefix = game.get("output_prefix", "")
    if not isinstance(prefix, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", prefix):
        raise RecompError("game.toml requires a safe [game].output_prefix")
    if game.get("platform") != "sms":
        raise RecompError("this adapter accepts SMS projects only")
    if not isinstance(game.get("rom"), str) or not game["rom"]:
        raise RecompError("game.toml requires [game].rom (ROM remains external)")
    return prefix


def execute(args):
    config = args.config.resolve(strict=True)
    manifest = args.manifest.resolve(strict=True)
    rom = args.rom.resolve(strict=True)
    size, sha = verify_rom(rom, manifest)
    prefix = read_config(config)

    if args.preflight:
        print(json.dumps({"preflight": "passed", "rom_size": size, "rom_sha256": sha}))
        return

    if args.tool is None:
        raise RecompError("provide --tool pointing to your external SmsRecomp executable")
    tool = args.tool.resolve(strict=True)
    if not tool.is_file():
        raise RecompError("SmsRecomp tool must be a regular file")
    output = (args.output or (config.parent / "generated")).resolve()
    if output.name != "generated":
        raise RecompError("output directory must be named 'generated' (ROM-derived code)")
    names = [f"{prefix}_{suffix}.c" for suffix in ("full", "dispatch", "layout")]

    # The upstream tool writes beside game.toml. Stage off-tree to prevent
    # obsolete generated files from being mistaken for successful output.
    with tempfile.TemporaryDirectory(prefix="smsgg-recomp-") as tmp:
        staged = Path(tmp)
        shutil.copy2(config, staged / "game.toml")
        manifest_seeds = config.parent / "dispatch_manifest.txt"
        if manifest_seeds.is_file():
            shutil.copy2(manifest_seeds, staged / manifest_seeds.name)
        command = [str(tool), str(rom), "--game", str(staged / "game.toml")]
        completed = subprocess.run(
            command, text=True, capture_output=True, timeout=300, check=False
        )
        if completed.returncode:
            raise RecompError(
                f"SmsRecomp exited {completed.returncode}\n"
                f"{completed.stdout[-3000:]}\n{completed.stderr[-3000:]}"
            )
        outputs = [staged / "generated" / name for name in names]
        for path in outputs:
            if not path.is_file() or path.stat().st_size == 0:
                raise RecompError(f"SmsRecomp did not produce {path.name}")

        output.mkdir(parents=True, exist_ok=True)
        evidence = {}
        for source, name in zip(outputs, names):
            target = output / name
            temp_target = output / (name + ".tmp")
            shutil.copyfile(source, temp_target)
            os.replace(temp_target, target)
            evidence[name] = {"bytes": target.stat().st_size, "sha256": digest(target)}

        report = {
            "schema": "smsgg-recomp-codegen-v1",
            "stage": "generated-c-only",
            "runtime_verified": False,
            "rom_size": size,
            "rom_sha256": sha,
            "config_sha256": digest(config),
            "tool_sha256": digest(tool),
            "outputs": evidence,
        }
        report_target = output / "report.json"
        pending = output / "report.json.tmp"
        pending.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(pending, report_target)
        print(f"Generated {len(names)} C files in {output}")
        print("Native compilation, execution and gameplay equivalence: NOT VERIFIED")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--tool", type=Path, help="external SmsRecomp executable")
    parser.add_argument("--output", type=Path, help="directory named generated")
    parser.add_argument("--preflight", action="store_true", help="verify inputs only")
    args = parser.parse_args(argv)
    try:
        execute(args)
    except (OSError, ValueError, tomllib.TOMLDecodeError, RecompError, subprocess.TimeoutExpired) as error:
        print(f"SMS/GG Recomp integration: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
