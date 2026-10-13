#!/usr/bin/env python3
"""Configure, build, test and package one user-testable native checkpoint."""
import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path

from package_build import package, promotion_errors


def host_platform():
    machine = platform.machine().lower()
    cpu = "arm64" if machine in ("arm64", "aarch64") else "x64"
    if sys.platform.startswith("win"):
        return "windows-" + cpu
    if sys.platform == "darwin":
        return "macos-" + cpu
    if sys.platform.startswith("linux"):
        return "linux-" + cpu
    raise ValueError("unsupported build host: " + sys.platform)


def run(args, cwd):
    print("+", " ".join(str(arg) for arg in args), flush=True)
    subprocess.run(args, cwd=cwd, check=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", choices=("dev", "alpha", "beta", "final"),
                        default="dev")
    parser.add_argument("--platform", default=None,
                        help="artifact label; defaults to detected host")
    parser.add_argument("--build-dir", type=Path, default=Path("build-native-phase"))
    parser.add_argument("--output-dir", type=Path, default=Path("dist"))
    args = parser.parse_args(argv)
    repo = Path(__file__).resolve().parents[2]
    gates_file = repo / "native" / "release" / "gates.json"
    state = json.loads(gates_file.read_text(encoding="utf-8"))
    missing = promotion_errors(args.channel, state)
    if missing:
        parser.exit(2, "BUILD BLOCKED: " + args.channel +
                    " still lacks verified gates: " + ", ".join(missing) + "\n")
    system = args.platform or host_platform()
    build_dir = args.build_dir.resolve()
    output_dir = args.output_dir.resolve()
    checkpoint = state["checkpoint"]
    run(["cmake", "-S", str(repo / "native"), "-B", str(build_dir),
         "-DCMAKE_BUILD_TYPE=Release", "-DYS_BUILD_CHANNEL=" + args.channel,
         "-DYS_CHECKPOINT=" + checkpoint], repo)
    run(["cmake", "--build", str(build_dir), "--config", "Release", "--parallel"],
        repo)
    run(["ctest", "--test-dir", str(build_dir), "-C", "Release",
         "--output-on-failure"], repo)
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True
    ).strip()
    result = package(args.channel, system, build_dir, output_dir,
                     gates_file, revision)
    print("Verified native phase bundle:", result, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
