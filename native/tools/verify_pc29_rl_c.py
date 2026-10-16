#!/usr/bin/env python3
"""PC-29 verify authentic fixed bank0 $0F8D/$0F8E and $0F9A/$0F9B.

Independent source bytes and Phase5 listing, no game-state promotion.
"""
import hashlib
import re
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
DIGEST="02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9"
ROWS={
 "00F8D":("0F8D","07","rlca"),
 "00F8E":("0F8E","CB 11","rl c"),
 "00F90":("0F90","21 A4 C1","ld hl,$C1A4"),
 "00F9A":("0F9A","07","rlca"),
 "00F9B":("0F9B","CB 11","rl c"),
 "00F9D":("0F9D","3E 03","ld a,$03"),
}
def check(path):
    rom=path.read_bytes()
    if len(rom)!=262144 or hashlib.sha256(rom).hexdigest()!=DIGEST:
        raise ValueError("original source-only ROM size/hash mismatch")
    lines=(ROOT/"Ys/phase5/code.lst").read_text(encoding="utf-8").splitlines()
    for physical,(pc,raw,op) in ROWS.items():
        blob=bytes.fromhex(raw)
        offset=int(physical,16)
        if rom[offset:offset+len(blob)]!=blob:
            raise ValueError("original bytes mismatch at "+physical)
        pattern=r"^"+physical+r"\s+"+pc+r"\s+"+r"\s+".join(raw.split())+r"\s+"+re.escape(op)+r"\s*$"
        if sum(bool(re.fullmatch(pattern,line,re.I)) for line in lines)!=1:
            raise ValueError("unaltered Phase5 source mismatch at "+physical)
    print("PASS PC-29: source ROM SHA and six bank0 original RL C"
          " flags/dispatch context listing rows $0F8D-$0F9D")
if __name__=="__main__":
    try:
        if len(sys.argv)!=2: raise ValueError("usage: verify_pc29_rl_c.py SOURCE.sms")
        check(Path(sys.argv[1]))
    except (OSError,ValueError) as error:
        sys.exit("FAIL PC-29 source rotate proof: "+str(error))
