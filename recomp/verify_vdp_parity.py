#!/usr/bin/env python3
"""Compare upstream runner recomp and interpreter VDP/WRAM frame checkpoints.

The runner uses the SAME VDP/hardware implementation in both paths. This is
a CPU translation regression check, not independent hardware validation.
"""
import argparse
from pathlib import Path
import re
import sys

# Upstream revision 224d5bb prints an eight-column legacy header while its
# emitted rows contain ten fields (it added RAM/SP after the header string).
HEADER = "frame,vram_h,cram_h,reg_h,r8,r9,r0,r1"
FIELDS = ("frame", "VRAM", "CRAM", "VDP registers", "WRAM",
          "R8", "R9", "R0", "R1", "SP")


def load(path, frames):
    text = Path(path).read_text(encoding="utf-8").splitlines()
    if not text or text[0] != HEADER:
        raise ValueError(f"incorrect pinned upstream trace header in {path}")
    if len(text) != frames + 1:
        raise ValueError(f"{path}: wanted {frames} frames, found {len(text)-1}")
    rows = []
    for frame, line in enumerate(text[1:], 1):
        parts = line.split(",")
        if len(parts) != 10 or parts[0] != str(frame):
            raise ValueError(f"{path}: invalid/nonconsecutive frame {frame}")
        for index, value in enumerate(parts[1:], 1):
            length = 16 if index < 5 else (4 if index == 9 else 2)
            if not re.fullmatch(f"[0-9A-Fa-f]{{{length}}}", value):
                raise ValueError(f"{path}: invalid {FIELDS[index]} at frame {frame}")
        rows.append(tuple(part.lower() for part in parts))
    return rows


def compare(recomp_path, oracle_path, frames):
    if type(frames) is not int or not 1 <= frames <= 36000:
        raise ValueError("frame count out of range")
    actual = load(recomp_path, frames)
    expected = load(oracle_path, frames)
    first = None
    differences = [0] * len(FIELDS)
    for frame, (a, b) in enumerate(zip(actual, expected), 1):
        for field, (left, right) in enumerate(zip(a, b)):
            if left != right:
                differences[field] += 1
                if first is None:
                    first = (frame, field, left, right)
    if first is not None:
        frame, field, left, right = first
        totals = ", ".join(f"{name}={differences[i]}" for i, name in
                           enumerate(FIELDS) if differences[i])
        raise ValueError(f"first divergence frame={frame}, field={FIELDS[field]} "
                         f"recompiled={left}, oracle={right}; "
                         f"divergent frame counts: {totals}")
    return f"PASS: {frames} complete frame VDP/WRAM/SP checkpoints match upstream interpreter"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recompiled", type=Path)
    parser.add_argument("interpreter", type=Path)
    parser.add_argument("--frames", type=int, required=True)
    args = parser.parse_args()
    try:
        print(compare(args.recompiled, args.interpreter, args.frames))
    except (ValueError, OSError) as error:
        print(f"FAIL R1 frame parity: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
