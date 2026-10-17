#!/usr/bin/env python3
"""Temporary *diagnostic-only* frame SP sampler correction for pinned SmsRecomp.

The pinned upstream runner executes --interp with CPU g_hz, but its frame CSV
samples g_z80.sp in both modes. This copies only live SP into the CSV in an
EXTERNAL, EPHEMERAL checkout. Do not vendor it or change the baseline evaluator.
"""
import argparse
from pathlib import Path
import subprocess
import sys

PINNED_COMMIT = "224d5bb2c150a2c295033d35dec629ef9ee42940"
PINNED_GLUE_BLOB = "264be88e214ffc32e162bcf581113363b00c9191"

PATCHES = (
    (
        "static FILE *g_vdp_trace;",
        "static FILE *g_vdp_trace;\n"
        "/* R1b diagnostic only: the interpreter executes in g_hz, not g_z80. */\n"
        "static bool g_r1b_interp_live;\n"
        "static uint16_t r1b_frame_live_sp(void);"
    ),
    (
        "g_vdp.reg[8], g_vdp.reg[9], g_vdp.reg[0], g_vdp.reg[1], g_z80.sp);",
        "g_vdp.reg[8], g_vdp.reg[9], g_vdp.reg[0], g_vdp.reg[1], "
        "r1b_frame_live_sp());"
    ),
    (
        "static z80  g_hz;",
        "static z80  g_hz;\n"
        "static uint16_t r1b_frame_live_sp(void){\n"
        "    return g_r1b_interp_live ? g_hz.sp : g_z80.sp;\n"
        "}"
    ),
    (
        "void glue_run_interp(void){\n    g_running = true;",
        "void glue_run_interp(void){\n    g_r1b_interp_live = true;\n"
        "    g_running = true;"
    ),
)

def apply_overlay(content):
    newline = "\r\n" if "\r\n" in content else "\n"
    normalized = content.replace("\r\n", "\n")
    for before, after in PATCHES:
        if normalized.count(before) != 1:
            raise ValueError(f"pinned upstream code mismatch at anchor {before!r}")
        normalized = normalized.replace(before, after)
    return normalized.replace("\n", newline)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--upstream", type=Path, required=True,
                    help="temporary checked-out upstream repository, never this repository")
    args = ap.parse_args(argv)
    upstream = args.upstream.resolve(strict=True)
    source = upstream / "runner/glue.c"
    try:
        commit = subprocess.check_output(
            ["git", "-C", str(upstream), "rev-parse", "HEAD"],
            text=True).strip()
        if commit != PINNED_COMMIT:
            raise ValueError(f"upstream revision mismatch: {commit}")
        blob = subprocess.check_output(
            ["git", "-C", str(upstream), "hash-object", str(source)],
            text=True).strip()
        if blob != PINNED_GLUE_BLOB:
            raise ValueError(f"upstream glue.c blob mismatch: {blob}")
        if source.is_symlink() or not source.is_file():
            raise ValueError("upstream runner glue.c must be a regular file")
        original = source.read_bytes()
        revised = apply_overlay(original.decode("utf-8")).encode("utf-8")
        if original == revised:
            raise ValueError("no diagnostic substitution applied")
        source.write_bytes(revised)
    except (OSError, UnicodeError, subprocess.CalledProcessError, ValueError) as exc:
        ap.exit(2, f"R1b diagnostic overlay REJECTED: {exc}\n")
    print("R1b: pinned upstream runner: diagnostic SP sampler uses live "
          "g_hz.sp in --interp, g_z80.sp in generated C")
    print("External temporary checkout modified; original source/oracle and "
          "generated C left unchanged. This is NOT parity certification.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
