#!/usr/bin/env python3
"""PC-24 verify original fixed-bank indexed-IY update and nearby calls.

A source-disassembled CALL $476C is not an observed execution event.
"""
from pathlib import Path
import hashlib
import re
import sys
ROOT=Path(__file__).resolve().parents[2]
SHA="02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9"
ROWS={
"00D9F":("0D9F","FD 21 60 C1","ld iy,$C160"),
"00DAA":("0DAA","FD 7E 00","ld a,(iy+0)"),
"00DAE":("0DAE","FD 77 00","ld (iy+0),a"),
"00DB1":("0DB1","23","inc hl"),
"00DB2":("0DB2","FD 23","inc iy"),
"00DB4":("0DB4","10 EF","djnz $0DA5"),
"00DC9":("0DC9","CD C8 0F","call $0FC8"),
"00DCC":("0DCC","CD 6C 47","call $476C")
}
def check(p:Path):
    rom=p.read_bytes()
    if len(rom)!=262144 or hashlib.sha256(rom).hexdigest()!=SHA:
        raise ValueError("original ROM identity mismatch")
    lines=(ROOT/"Ys/phase5/code.lst").read_text(encoding="utf-8").splitlines()
    for physical,(pc,raw,op) in ROWS.items():
        offset=int(physical,16);data=bytes.fromhex(raw)
        if rom[offset:offset+len(data)]!=data:
            raise ValueError("original fixedbank source bytes mismatch "+physical)
        expr=r"^"+physical+r"\s+"+pc+r"\s+"+r"\s+".join(raw.split())+r"\s+"+re.escape(op)+r"\s*$"
        if sum(bool(re.fullmatch(expr,row,re.IGNORECASE)) for row in lines)!=1:
            raise ValueError("source listing mismatch "+physical)
    print("PASS PC-24: fixed bank0 IY loop bytes and conditional bank1 call site verified")
if __name__=="__main__":
    try:
        if len(sys.argv)!=2:raise ValueError("usage: verify_pc24_iy_loop.py SOURCE.sms")
        check(Path(sys.argv[1]))
    except (OSError,ValueError) as exc:
        sys.exit("FAIL PC-24 source loop proof: "+str(exc))
