#!/usr/bin/env python3
"""Reassemble and verify the complete 44-commit Ys M14 Git bundle backup.

Usage:
    python3 Ys/tools/restore_m14_git_history.py --output ./Ys-M14-Foundation.bundle
    git bundle verify ./Ys-M14-Foundation.bundle
    git clone -b Ys ./Ys-M14-Foundation.bundle ys-original-history

The original Git history is stored in tracked binary chunks to accommodate
per-operation payload limits in the GitHub connector.  Only the transfer was
split; the original Git bundle is restored byte-for-byte.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

DIRECTORY = Path(__file__).resolve().parents[1] / "history" / "m14_bundle_parts"
EXPECTED_SIZE = 1_931_042
EXPECTED_SHA256 = "56672a6c7e7423f857ff8459719fd8e5d191425ed897915ff831f19d92e8c606"
PARTS = [
    (262144, "ae95791f4a286169db710b552f97640c639c7d14b001fe6e04272fbe11999b57"),
    (262144, "dece8c1f09ffe18843a1bc2273855ccc621e2e32f61f963b4301e1e6b51d80af"),
    (262144, "8e9fdb7deee8d5061ffaf2b6c5f3db07618b4e47320c6dc9e1e69ba3dc6269c3"),
    (262144, "a464dd12a1af54f7e57952f5b1233dbdab003b83fc475d19ee9c4eb54722f938"),
    (262144, "6e4eb5c1dae35eecf42de4c51617a6d243434182dfc7145738ef14c8f26cbad7"),
    (262144, "e0eddeec52d18161e336ffcc3d6b6a9027cf0212a2ec06f6a2b27a339f02d500"),
    (262144, "a5843dc3a1fad796ba15d9680e854b14da11e05b9f86936d5515ca49ee6ab5b4"),
    (96034, "3f231287d89f88354d7f6e19932dbf40f26bdec94277c39aeb39bdb6fce7307d"),
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Output .bundle path")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"Refusing to overwrite existing {args.output}")

    chunks = []
    for i, (length, checksum) in enumerate(PARTS):
        part = DIRECTORY / f"Ys-M14-Foundation.bundle.part{i:03d}"
        data = part.read_bytes()
        if len(data) != length or hashlib.sha256(data).hexdigest() != checksum:
            raise ValueError(f"Bad length or SHA-256: {part.name}")
        chunks.append(data)
    bundle = b"".join(chunks)
    if len(bundle) != EXPECTED_SIZE or hashlib.sha256(bundle).hexdigest() != EXPECTED_SHA256:
        raise ValueError("Reassembled bundle failed size/SHA-256 verification")
    args.output.write_bytes(bundle)
    print(f"Restored {args.output}: {EXPECTED_SIZE} bytes, sha256={EXPECTED_SHA256}")


if __name__ == "__main__":
    main()
