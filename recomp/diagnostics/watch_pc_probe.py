#!/usr/bin/env python3
"""R1b diagnostic: run same-ROM instruction-PC watchpoints in both CPU paths.

The pinned upstream runner supplies the original generated-C watch mechanism.
The temporary overlay adds a *read-only* equivalent in --interp mode. Values
are compared per hit at identical PC, not at free-running VDP frame boundaries.
No success here certifies paths/frames outside the observed watchpoints.
"""
import argparse
from pathlib import Path
import subprocess
import sys

HEADER = "hit,cyc,a,f,b,c,d,e,h,l,ix,iy,sp,i,r,iff1"
FIELDS = HEADER.split(",")
MAX_ROWS = 500000


def read_watch(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != HEADER:
        raise ValueError(f"{path}: unexpected watchpoint CSV header")
    if len(lines) - 1 > MAX_ROWS:
        raise ValueError(f"{path}: watchpoint hit limit exceeded")
    values = []
    for index, line in enumerate(lines[1:]):
        parts = line.split(",")
        if len(parts) != len(FIELDS):
            raise ValueError(f"{path}: watchpoint row {index} field count mismatch")
        if any(not value.isascii() or not value.isdecimal() for value in parts):
            raise ValueError(f"{path}: nondecimal watchpoint value at hit {index}")
        nums = tuple(int(x) for x in parts)
        if nums[0] != index or nums[1] < 0:
            raise ValueError(f"{path}: incorrect watchpoint hit index")
        for n in range(2, len(FIELDS)):
            max_value = 65535 if FIELDS[n] in ("ix", "iy", "sp") else 1 if FIELDS[n] == "iff1" else 255
            if nums[n] > max_value:
                raise ValueError(f"{path}: {FIELDS[n]} out of range")
        values.append(nums)
    return values


def difference(a, b):
    if not a and not b:
        return "NO_HITS"
    if len(a) != len(b):
        return f"HIT_COUNT recomp={len(a)} interpreter={len(b)}"
    for index, (left, right) in enumerate(zip(a, b)):
        for field, (x, y) in enumerate(zip(left, right)):
            if x != y:
                return f"hit={index} field={FIELDS[field]} recomp={x} interpreter={y}"
    return f"MATCHED {len(a)} hits in {len(FIELDS)} fields"


def run_watch(exe, rom, out, frames, pc, interpreter):
    args = [str(exe), str(rom), "--frames", str(frames),
            "--cyc-watch", f"0x{pc:04X}", str(out)]
    if interpreter:
        args.insert(2, "--interp")
    result = subprocess.run(args, cwd=out.parent, text=True, capture_output=True,
                            check=False, timeout=90)
    if result.returncode != 0 or not out.is_file():
        raise ValueError(f"PC=0x{pc:04X} mode={'interp' if interpreter else 'recomp'} "
                         f"runner failure exit={result.returncode}: {result.stderr[-500:]}")
    return read_watch(out)


def probe(exe, rom, folder, frames, anchors):
    folder.mkdir(parents=True, exist_ok=True)
    if not 1 <= frames <= 36000 or not anchors:
        raise ValueError("invalid frame count or empty anchors")
    results = {}
    for pc in anchors:
        if not 0 <= pc <= 0xFFFF:
            raise ValueError("PC address out of range")
        a = run_watch(exe, rom, folder / f"pc_{pc:04x}_compiled.csv", frames, pc, False)
        b = run_watch(exe, rom, folder / f"pc_{pc:04x}_interp.csv", frames, pc, True)
        result = difference(a, b)
        results[pc] = result
        print(f"PC 0x{pc:04X}: {result}")
    if not any(value.startswith("MATCHED") for value in results.values()):
        raise ValueError("no matched instruction PC anchor across both paths")
    print("DIAGNOSTIC ONLY: unobserved PCs, IRQ windows and guest stack bytes remain unverified")
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runner", type=Path, required=True)
    ap.add_argument("--rom", type=Path, required=True)
    ap.add_argument("--folder", type=Path, required=True)
    ap.add_argument("--frames", type=int, default=60)
    ap.add_argument("--anchors", nargs="+", default=["079A", "8803", "0038", "0749", "0BC5"])
    args = ap.parse_args()
    try:
        pcs = [int(x, 16) for x in args.anchors]
        probe(args.runner.resolve(strict=True), args.rom.resolve(strict=True),
              args.folder, args.frames, pcs)
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        ap.exit(2, f"FAIL R1b PC probe: {exc}\n")


if __name__ == "__main__":
    main()
