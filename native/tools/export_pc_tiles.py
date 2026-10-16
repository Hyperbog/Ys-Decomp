#!/usr/bin/env python3
"""Build an optional, untracked PC tile gallery asset from Ys source only.

These 176 bank-3 8x8 Mode-4 patterns are reversible, but their actual
in-game tile usage and palette are not yet established. Never treat
grayscale preview pixels as original colors. No owner ROM is read.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Ys" / "tools"))
from whole_bank03 import full_bank
from mode4_tiles_phase8 import decode_tile, encode_tile

MAGIC = b"YSPC4T01"
TILES = 176
STRIDE = 32
BANK_PREFIX = TILES * STRIDE


def make_package():
    bank = full_bank()
    assert len(bank) == 0x4000
    meta = json.loads((ROOT / "Ys/phase8/tile_metadata.json").read_text())
    assert meta["tiles_total"] == TILES and meta["interpreted_bytes"] == BANK_PREFIX
    assert [b["raw_bytes"] for b in meta["blocks"]] == [4096, 1536]
    blocks = (bank[:4096], bank[4096:BANK_PREFIX])
    for raw, expected in zip(blocks, meta["blocks"]):
        assert hashlib.sha256(raw).hexdigest() == expected["sha256"]
    pixels = [decode_tile(bank[k:k + STRIDE])
              for k in range(0, BANK_PREFIX, STRIDE)]
    assert len(pixels) == TILES
    assert b"".join(encode_tile(p) for p in pixels) == bank[:BANK_PREFIX]
    raw = bank[:BANK_PREFIX]
    package = MAGIC + struct.pack("<HHI", TILES, 0, zlib.crc32(raw)) + raw
    assert len(package) == 16 + BANK_PREFIX
    return package


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--out", type=Path, help="Output untracked derived asset")
    group.add_argument("--verify", type=Path, help="Verify existing derived asset")
    args = parser.parse_args()
    asset = make_package()
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(asset)
    else:
        if args.verify.read_bytes() != asset:
            raise ValueError("PC tile asset differs from bank-3 source")
    print("PASS PC-1: 176 source-derived Mode-4 tiles, 5632 bytes, "
          "full digest and reversible decode; original palette/usage unknown")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, AssertionError, OSError) as exc:
        sys.exit("FAIL PC-1 source tile packaging: " + str(exc))
