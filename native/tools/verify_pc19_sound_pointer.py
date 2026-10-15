#!/usr/bin/env python3
"""PC-19: source-cartridge and independent Phase5 bank2 pointer provenance.

Proves source opcode bytes, not authentic gameplay execution.
"""
from pathlib import Path
import hashlib
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
SHA="02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9"
SOURCE=bytes.fromhex("DD 5E 03 DD 56 04 1A 13")
ROWS={
    "084F1":("84F1","DD 5E 03","ld e,(ix+3)"),
    "084F4":("84F4","DD 56 04","ld d,(ix+4)"),
    "084F7":("84F7","1A","ld a,(de)"),
    "084F8":("84F8","13","inc de"),
}


def check(path: Path) -> None:
    rom=path.read_bytes()
    if len(rom)!=262144 or hashlib.sha256(rom).hexdigest()!=SHA:
        raise ValueError("original 16-bank cartridge digest/size mismatch")
    if rom[0x84F1:0x84F1+len(SOURCE)]!=SOURCE:
        raise ValueError("physical bank2 $084F1-$084F8 bytes mismatch")
    listing=(ROOT/"Ys/phase5/code.lst").read_text(encoding="utf-8").splitlines()
    for phys,(pc,raw,op) in ROWS.items():
        pattern=r"^"+phys+r"\s+"+pc+r"\s+"+r"\s+".join(raw.split())+r"\s+"+re.escape(op)+r"\s*$"
        if sum(bool(re.fullmatch(pattern,row,re.IGNORECASE)) for row in listing)!=1:
            raise ValueError("independent listing mismatch at physical $"+phys)
    print("PASS PC-19: SHA-matched source ROM and four independent"
          " bank2 pointer instruction listings at $084F1-$084F8")


if __name__=="__main__":
    try:
        if len(sys.argv)!=2:
            raise ValueError("usage: verify_pc19_sound_pointer.py SOURCE.sms")
        check(Path(sys.argv[1]))
    except (OSError,ValueError) as e:
        sys.exit("FAIL PC-19 source pointer provenance: "+str(e))
