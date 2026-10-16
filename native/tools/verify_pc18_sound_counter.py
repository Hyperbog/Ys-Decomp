#!/usr/bin/env python3
"""PC-18 check immutable original bank2 sound counter bytes and listing.

This provenance fixture alone does not establish original runtime execution.
"""
import hashlib
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
EXPECTED_SHA="02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9"
SOURCE_BYTES=bytes.fromhex("DD 34 0B DD 7E 0A DD 96 0B CC F1 84")
ROWS={
    "08947": ("8947","DD 34 0B","inc (ix+11)"),
    "0894A": ("894A","DD 7E 0A","ld a,(ix+10)"),
    "0894D": ("894D","DD 96 0B","sub (ix+11)"),
    "08950": ("8950","CC F1 84","call z,$84F1"),
}


def check(path: Path) -> None:
    rom=path.read_bytes()
    if len(rom)!=262144 or hashlib.sha256(rom).hexdigest()!=EXPECTED_SHA:
        raise ValueError("original 16-bank source ROM size/digest mismatch")
    if rom[0x8947:0x8947+len(SOURCE_BYTES)]!=SOURCE_BYTES:
        raise ValueError("original physical bank2 $08947-$08952 byte mismatch")
    listing=(ROOT/"Ys/phase5/code.lst").read_text(encoding="utf-8").splitlines()
    for phys,(cpu,raw,mnemonic) in ROWS.items():
        regex=r"^"+phys+r"\s+"+cpu+r"\s+"+r"\s+".join(raw.split())+r"\s+"+re.escape(mnemonic)+r"\s*$"
        if sum(bool(re.fullmatch(regex,line,re.IGNORECASE)) for line in listing)!=1:
            raise ValueError("independent Phase5 listing mismatch at $"+phys)
    print("PASS PC-18: original source ROM identity and four sound"
          " counter instructions at physical $08947-$08952")


if __name__=="__main__":
    try:
        if len(sys.argv)!=2:
            raise ValueError("usage: verify_pc18_sound_counter.py SOURCE.sms")
        check(Path(sys.argv[1]))
    except (OSError,ValueError) as exc:
        sys.exit("FAIL PC-18 source provenance: "+str(exc))
