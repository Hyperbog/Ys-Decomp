#!/usr/bin/env python3
"""PC-16: verify bank-2 $8307 EX DE,HL against original source-built ROM.

This source-integrity check does not demonstrate game runtime or M46c success.
"""
import hashlib
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SHA256 = "02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9"
# Original source Phase4 consecutive instructions at $8302..$830C.
SOURCE_BYTES = bytes.fromhex("E5 21 13 00 19 EB E1 01 17 83 C5")
OFFSET = 0x8302


def verify(rom_path: Path) -> None:
    rom = rom_path.read_bytes()
    if len(rom) != 0x40000:
        raise ValueError("expected exactly 16 unheadered 16-KiB banks")
    digest = hashlib.sha256(rom).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError("source cartridge SHA-256 mismatch")
    if rom[OFFSET:OFFSET + len(SOURCE_BYTES)] != SOURCE_BYTES:
        raise ValueError("original physical bank-2 $8302-$830C differs")
    listing = (ROOT / "Ys/phase4/code.lst").read_text(encoding="utf-8")
    rows = [row for row in listing.splitlines() if re.match(
        r"^08307\s+8307\s+EB\s+ex\s+de,hl\s*$", row, re.IGNORECASE)]
    if len(rows) != 1:
        raise ValueError("Phase4 opcode/source mnemonic evidence missing")
    print("PASS PC-16: source-built ROM SHA-256 and physical $08307 EB "
          "(EX DE,HL), following source bytes verified")


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            raise ValueError("usage: verify_pc16_sound_exchange.py SOURCE.sms")
        verify(Path(sys.argv[1]))
    except (OSError, ValueError) as exc:
        sys.exit("FAIL PC-16 source exchange: " + str(exc))
