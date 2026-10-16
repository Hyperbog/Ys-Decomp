#!/usr/bin/env python3
"""PC-22 immutable source listing/bytes for indexed H/L sound stream.

Phase5 mnemonic ixh/ixl differs from hardware semantics for indexed
(HL) memory forms: Zilog rules preserve H/L, see Z80 CPU User Manual.
The original disassembly is deliberately not rewritten.
"""
from pathlib import Path
import hashlib
import re
import sys
ROOT=Path(__file__).resolve().parents[2]
SHA="02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9"
ROWS={
 "089D1":("89D1","DD 6E 0E","ld ixl,(ix+14)"),
 "089D4":("89D4","DD 66 0F","ld ixh,(ix+15)"),
 "08587":("8587","DD 75 0E","ld (ix+14),ixl"),
 "0858A":("858A","DD 74 0F","ld (ix+15),ixh"),
}
def check(p:Path):
    rom=p.read_bytes()
    if len(rom)!=262144 or hashlib.sha256(rom).hexdigest()!=SHA:
        raise ValueError("original source ROM identity")
    lines=(ROOT/"Ys/phase5/code.lst").read_text(encoding="utf-8").splitlines()
    for physical,(pc,raw,mnemonic) in ROWS.items():
        offset=int(physical,16);data=bytes.fromhex(raw)
        if rom[offset:offset+len(data)]!=data:
            raise ValueError("source instruction byte mismatch "+physical)
        expr=r"^"+physical+r"\s+"+pc+r"\s+"+r"\s+".join(raw.split())+r"\s+"+re.escape(mnemonic)+r"\s*$"
        if sum(bool(re.fullmatch(expr,row,re.IGNORECASE)) for row in lines)!=1:
            raise ValueError("unaltered source listing row mismatch "+physical)
    print("PASS PC-22: four original bank2 H/L indexed instruction records; source listing preserved")
if __name__=="__main__":
    try:
        if len(sys.argv)!=2: raise ValueError("usage: verify_pc22_indexed_hl.py SOURCE.sms")
        check(Path(sys.argv[1]))
    except (OSError,ValueError) as exc:
        sys.exit("FAIL PC-22 source H/L proof: "+str(exc))
