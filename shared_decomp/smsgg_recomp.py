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
import zlib


class RecompError(Exception):
    pass


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_crc(value, label):
    if value is None:
        return None
    if isinstance(value, bool):
        raise RecompError(f"{label} must be an unsigned CRC-32")
    if isinstance(value, int) and 0 <= value <= 0xFFFFFFFF:
        return value
    if isinstance(value, str) and re.fullmatch(r"(?:0[xX])?[0-9a-fA-F]{1,8}", value):
        return int(value[2:] if value[:2].lower() == "0x" else value, 16)
    raise RecompError(f"{label} must be an unsigned CRC-32")


def crc32_file(path):
    result = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result = zlib.crc32(chunk, result)
    return result & 0xFFFFFFFF


def verify_rom(rom, manifest):
    data = json.loads(manifest.read_text(encoding="utf-8"))
    identity = data.get("binary", data)
    expected_hash = identity.get("sha256")
    expected_size = identity.get("size", data.get("rom_bytes"))
    if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_hash):
        raise RecompError("manifest must specify an exact SHA-256")
    if not isinstance(expected_size, int) or isinstance(expected_size, bool) or expected_size <= 0:
        raise RecompError("manifest must specify an exact ROM size")
    size = rom.stat().st_size
    sha = digest(rom)
    if size != expected_size or sha != expected_hash.lower():
        raise RecompError(
            f"ROM identity mismatch: size={size}, sha256={sha}; "
            f"expected size={expected_size}, sha256={expected_hash.lower()}"
        )
    crc = crc32_file(rom)
    manifest_crc = parse_crc(identity.get("crc32", data.get("crc32")),
                             "manifest crc32")
    if manifest_crc is not None and crc != manifest_crc:
        raise RecompError(f"ROM CRC-32 mismatch: {crc:08X} != manifest {manifest_crc:08X}")
    return size, sha, crc


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
    config_crc = parse_crc(game.get("crc32"), "game.toml crc32")
    mapper_kind = data.get("mapper", {}).get("kind")
    if not isinstance(mapper_kind, str) or mapper_kind not in ("sega", "codemasters"):
        raise RecompError("game.toml requires a supported [mapper].kind")
    return prefix, config_crc


def verify_generated(output, names, size, sha, crc, config, tool):
    report_path = output / "report.json"
    if output.is_symlink() or report_path.is_symlink():
        raise RecompError("generated directory/report must not be symbolic links")
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise RecompError(f"generated report is missing or invalid: {error}") from error
    expected = {
        "schema": "smsgg-recomp-codegen-v1",
        "stage": "generated-c-only",
        "runtime_verified": False,
        "rom_size": size,
        "rom_sha256": sha,
        "rom_crc32": f"{crc:08X}",
        "config_sha256": digest(config),
        "tool_sha256": digest(tool),
    }
    for key, value in expected.items():
        if report.get(key) != value:
            raise RecompError(f"generated report {key} does not match verified inputs")
    outputs = report.get("outputs")
    if not isinstance(outputs, dict) or set(outputs) != set(names):
        raise RecompError("generated report output file list does not match game config")
    for name in names:
        path = output / name
        entry = outputs[name]
        if not isinstance(entry, dict) or not path.is_file() or path.is_symlink():
            raise RecompError(f"generated output missing or unsafe: {name}")
        if path.stat().st_size != entry.get("bytes") or digest(path) != entry.get("sha256"):
            raise RecompError(f"generated output integrity mismatch: {name}")
    print(f"Verified {len(names)} generated C files; runtime execution NOT VERIFIED")


def execute(args):
    config = args.config.resolve(strict=True)
    manifest = args.manifest.resolve(strict=True)
    rom = args.rom.resolve(strict=True)
    size, sha, crc = verify_rom(rom, manifest)
    prefix, config_crc = read_config(config)
    # Upstream only WARNS when TOML's CRC differs; fail closed instead.
    if config_crc is not None and config_crc != crc:
        raise RecompError(
            f"game.toml CRC-32 mismatch: configured {config_crc:08X}, actual {crc:08X}"
        )

    if args.preflight:
        print(json.dumps({"preflight": "passed", "rom_size": size,
                          "rom_sha256": sha, "rom_crc32": f"{crc:08X}"}))
        return

    if args.tool is None:
        raise RecompError("provide --tool pointing to your external SmsRecomp executable")
    tool = args.tool.resolve(strict=True)
    if not tool.is_file():
        raise RecompError("SmsRecomp tool must be a regular file")
    output_candidate = args.output or (config.parent / "generated")
    if output_candidate.is_symlink():
        raise RecompError("generated output directory must not be a symbolic link")
    output = output_candidate.resolve()
    if output.name != "generated":
        raise RecompError("output directory must be named 'generated' (ROM-derived code)")
    names = [f"{prefix}_{suffix}.c" for suffix in ("full", "dispatch", "layout")]
    if args.verify_generated:
        verify_generated(output, names, size, sha, crc, config, tool)
        return

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
            if path.is_symlink() or not path.is_file() or path.stat().st_size == 0:
                raise RecompError(f"SmsRecomp did not produce {path.name}")

        output.mkdir(parents=True, exist_ok=True)
        evidence = {}
        for source, name in zip(outputs, names):
            target = output / name
            temp_target = output / (name + ".tmp")
            # Atomic unique create: never follow an attacker-controlled
            # pre-existing .tmp symbolic link in the generated directory.
            with tempfile.NamedTemporaryFile(dir=output,
                    prefix=".smsgg-" + name + "-", delete=False) as stream:
                temp_target = Path(stream.name)
                with source.open("rb") as inp:
                    shutil.copyfileobj(inp, stream)
            os.replace(temp_target, target)
            evidence[name] = {"bytes": target.stat().st_size, "sha256": digest(target)}

        report = {
            "schema": "smsgg-recomp-codegen-v1",
            "stage": "generated-c-only",
            "runtime_verified": False,
            "rom_size": size,
            "rom_sha256": sha,
            "rom_crc32": f"{crc:08X}",
            "config_sha256": digest(config),
            "tool_sha256": digest(tool),
            "outputs": evidence,
        }
        report_target = output / "report.json"
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8",
                dir=output, prefix=".smsgg-report-", delete=False) as stream:
            pending = Path(stream.name)
            stream.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
        os.replace(pending, report_target)
        verify_generated(output, names, size, sha, crc, config, tool)
        print(f"Generated {len(names)} C files in {output}")
        print("Native compilation, execution and gameplay equivalence: NOT VERIFIED")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--tool", type=Path, help="external SmsRecomp executable")
    parser.add_argument("--output", type=Path, help="directory named generated")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--preflight", action="store_true", help="verify inputs only")
    modes.add_argument("--verify-generated", action="store_true",
                       help="hash-check existing generated C against ROM/config/tool")
    args = parser.parse_args(argv)
    try:
        execute(args)
    except (OSError, ValueError, tomllib.TOMLDecodeError, RecompError, subprocess.TimeoutExpired) as error:
        print(f"SMS/GG Recomp integration: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
