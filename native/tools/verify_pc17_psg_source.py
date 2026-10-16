#!/usr/bin/env python3
"""PC-17: source-ROM and independent Phase 5 check for the PSG path.

Checks provenance only. A passing check is not native-game or M46c proof.
"""
from pathlib import Path
import hashlib
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
HASH="02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9"
SOURCE=bytes.fromhex("DD 7E 08 E6 0F DD B6 01 C6 10 D3 7F C9")
ROWS={
    "08A4B": ("8A4B","DD 7E 08","ld a,(ix+8)"),
    "08A4E": ("8A4E","E6 0F","and $0F"),
    "08A50": ("8A50","DD B6 01","or (ix+1)"),
    "08A53": ("8A53","C6 10","add a,$10"),
    "08A55": ("8A55","D3 7F","out ($7F),a"),
    "08A57": ("8A57","C9","ret"),
}


def check(path: Path) -> None:
    rom=path.read_bytes()
    if len(rom)!=262144 or hashlib.sha256(rom).hexdigest()!=HASH:
        raise ValueError("original source-cartridge size/digest mismatch")
    if rom[0x8A4B:0x8A4B+len(SOURCE)]!=SOURCE:
        raise ValueError("original physical bank2 $8A4B PSG byte mismatch")
    text=(ROOT/"Ys/phase5/code.lst").read_text(encoding="utf-8")
    lines=text.splitlines()
    for phys,(cpu,raw,mnemonic) in ROWS.items():
        pattern=(r"^"+phys+r"\s+"+cpu+r"\s+"+
                 r"\s+".join(raw.split())+r"\s+"+
                 re.escape(mnemonic)+r"\s*$")
        if len([line for line in lines if re.fullmatch(
                pattern,line,re.IGNORECASE)])!=1:
            raise ValueError("Phase5 listing mismatch at physical $"+phys)
    print("PASS PC-17: original 16-bank source ROM identity and"
          " six independent Phase5 PSG instructions $8A4B-$8A57")


if __name__=="__main__":
    try:
        if len(sys.argv)!=2:
            raise ValueError("usage: verify_pc17_psg_source.py SOURCE.sms")
        check(Path(sys.argv[1]))
    except (OSError,ValueError) as e:
        sys.exit("FAIL PC-17 PSG provenance: "+str(e))
