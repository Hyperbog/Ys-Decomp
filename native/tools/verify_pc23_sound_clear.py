#!/usr/bin/env python3
"""PC-23 original bank2 LD (IX+d),n sound clearing instructions."""
from pathlib import Path
import hashlib
import re
import sys
ROOT=Path(__file__).resolve().parents[2]
SHA="02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9"
ROWS={
"088FF":("88FF","DD 36 07 00","ld (ix+7),$00"),
"08903":("8903","3E FF","ld a,$FF"),
"08905":("8905","D3 7F","out ($7F),a"),
"08907":("8907","C9","ret"),
"08A39":("8A39","DD 36 13 FF","ld (ix+19),$FF")
}
def check(p:Path):
    rom=p.read_bytes()
    if len(rom)!=262144 or hashlib.sha256(rom).hexdigest()!=SHA:
        raise ValueError("256KiB source ROM size/SHA256 mismatch")
    lines=(ROOT/"Ys/phase5/code.lst").read_text(encoding="utf-8").splitlines()
    for physical,(pc,raw,op) in ROWS.items():
        offset=int(physical,16);data=bytes.fromhex(raw)
        if rom[offset:offset+len(data)]!=data:
            raise ValueError("original bank2 byte mismatch "+physical)
        expr=r"^"+physical+r"\s+"+pc+r"\s+"+r"\s+".join(raw.split())+r"\s+"+re.escape(op)+r"\s*$"
        if sum(bool(re.fullmatch(expr,row,re.IGNORECASE)) for row in lines)!=1:
            raise ValueError("Phase5 source listing mismatch "+physical)
    print("PASS PC-23: five original bank2 PSG/zero-store instructions verified")
if __name__=="__main__":
    try:
        if len(sys.argv)!=2: raise ValueError("usage: verify_pc23_sound_clear.py SOURCE.sms")
        check(Path(sys.argv[1]))
    except (OSError,ValueError) as e:
        sys.exit("FAIL PC-23 sound source: "+str(e))
