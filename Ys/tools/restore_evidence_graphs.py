#!/usr/bin/env python3
"""Verify and optionally unpack the losslessly archived Ys evidence graphs.

Usage:
    python Ys/tools/restore_evidence_graphs.py --verify
    python Ys/tools/restore_evidence_graphs.py --restore

Requires only Python's standard library.  Both files are deterministic gzip
archives of the original committed source-audit JSON, with SHA-256 checks.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
from pathlib import Path

WHOLE_SYSTEM = Path(__file__).resolve().parents[1] / "whole_system"
EVIDENCE = {
    "evidence_graph.json": (
        4_558_351,
        "7ec4a6b615b4f24f9d11d3d0616e83ed02e4fadae2e987ef2923336dc84cccae",
        "c0e01c84f5d1c1e748e1ad87ef3f369e790dcc71ae73bd867c0db83f174840a8",
    ),
    "evidence_graph_m3.json": (
        6_530_431,
        "b88793c4085c061ce98dca28c67fda9262607b259daadeb339baf040814d4d10",
        "9d5368d4283f4b3a90f716f897a97c22e43270ee6612c98f46b93e731d2ee3a5",
    ),
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--verify", action="store_true", help="Verify compressed data only")
    action.add_argument("--restore", action="store_true", help="Restore original JSON files")
    args = parser.parse_args()

    for name, (size, sha, zipped_sha) in EVIDENCE.items():
        compressed = (WHOLE_SYSTEM / (name + ".gz")).read_bytes()
        if digest(compressed) != zipped_sha:
            raise ValueError(f"{name}: compressed SHA-256 mismatch")
        data = gzip.decompress(compressed)
        if len(data) != size or digest(data) != sha:
            raise ValueError(f"{name}: uncompressed size or SHA-256 mismatch")
        target = WHOLE_SYSTEM / name
        if args.restore:
            if target.exists() and target.read_bytes() != data:
                raise ValueError(f"{name}: existing file differs; refusing overwrite")
            if not target.exists():
                target.write_bytes(data)
        print(f"OK {name}: {size} bytes, sha256={sha}" + (" (restored)" if args.restore else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
