#!/usr/bin/env python3
"""R1b diagnostic: locate per-frame state differences and first differing WRAM byte.

Explicitly non-certifying. The strict uncompromised parity gate runs separately.
Source-ROM, dump PNGs, RAM images and generated C stay in temporary directories.
"""
import argparse
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verify_vdp_parity import FIELDS, load

RAM_BYTES = 0x2000


def mismatches(compiled, interpreter):
    if len(compiled) != len(interpreter):
        raise ValueError("trace lengths do not match")
    differences = {name: [] for name in FIELDS[1:]}
    for n, (a, b) in enumerate(zip(compiled, interpreter), 1):
        if a[0] != str(n) or b[0] != str(n):
            raise ValueError("trace frame numbering is not contiguous")
        for field in range(1, len(FIELDS)):
            if a[field] != b[field]:
                differences[FIELDS[field]].append(n)
    return differences


def first_ram_difference(left, right):
    if len(left) != RAM_BYTES or len(right) != RAM_BYTES:
        raise ValueError("each WRAM snapshot must be exactly 8192 bytes")
    for n, (a, b) in enumerate(zip(left, right)):
        if a != b:
            return (0xC000 + n, a, b)
    return None


def run_dump(exe, rom, folder, frame, use_interp):
    prefix = folder / ("interpreter" if use_interp else "compiled")
    args = [str(exe), str(rom)]
    if use_interp:
        args.append("--interp")
    args += ["--frames", str(frame), "--dump-frame", str(frame),
             "--dump-out", str(prefix) + ".png"]
    process = subprocess.run(args, cwd=folder, text=True, capture_output=True,
                             timeout=90, check=False)
    ram = Path(str(prefix) + ".png.ram")
    if process.returncode != 0 or not ram.is_file():
        raise ValueError(f"dump failed: {'interpreter' if use_interp else 'compiled'}, "
                         f"frame={frame}, exit={process.returncode}")
    return ram.read_bytes()


def diagnose(recompiled, interpreter, frames, exe=None, rom=None, scratch=None):
    a, b = load(recompiled, frames), load(interpreter, frames)
    diffs = mismatches(a, b)
    for field, indices in diffs.items():
        print(f"DIAGNOSTIC {field}: differing frames={len(indices)} "
              f"first={indices[:8]}")
    wrams = diffs["WRAM"]
    if wrams and (exe is None or rom is None or scratch is None):
        raise ValueError("WRAM differs: provide --runner, --rom and --scratch for byte-level isolation")
    if wrams:
        scratch.mkdir(parents=True, exist_ok=True)
        # Probe the first observed WRAM frame only; no game bytes are published.
        frame = wrams[0]
        ours = run_dump(exe, rom, scratch, frame, False)
        theirs = run_dump(exe, rom, scratch, frame, True)
        first = first_ram_difference(ours, theirs)
        if first is None:
            raise ValueError(f"WRAM hash differed at frame {frame} but exact bytes matched")
        address, our_byte, their_byte = first
        print(f"DIAGNOSTIC WRAM first byte: frame={frame} cpu_address="
              f"0x{address:04X} recomp=0x{our_byte:02X} "
              f"interp=0x{their_byte:02X}")
    return diffs


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("recompiled", type=Path)
    ap.add_argument("interpreter", type=Path)
    ap.add_argument("--frames", type=int, required=True)
    ap.add_argument("--runner", type=Path)
    ap.add_argument("--rom", type=Path)
    ap.add_argument("--scratch", type=Path)
    args = ap.parse_args()
    try:
        diagnose(args.recompiled, args.interpreter, args.frames,
                 args.runner, args.rom, args.scratch)
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        ap.exit(2, f"FAIL R1b diagnostics: {error}\n")
    print("R1b DIAGNOSTIC COMPLETE; this does NOT override the strict parity gate.")


if __name__ == "__main__":
    main()
