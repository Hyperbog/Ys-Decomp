#!/usr/bin/env python3
"""PC-32 original fixed bank0 $2654-$2672 pointer-pair save routine.

Source-only ROM and independent Phase6 code listing authentication;
CPU execution observation at $265B is from PC-31 source-armed trace.
"""
from pathlib import Path
import hashlib
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
SHA="02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9"
ROWS={
 "02654":("2654","22 82 C1","ld ($C182),hl"),
 "02657":("2657","ED 53 84 C1","ld ($C184),de"),
 "0265B":("265B","ED 43 10 C2","ld ($C210),bc"),
 "0265F":("265F","C9","ret"),
 "02660":("2660","01 00 00","ld bc,$0000"),
 "02663":("2663","ED 43 86 C1","ld ($C186),bc"),
 "02667":("2667","ED 43 88 C1","ld ($C188),bc"),
 "0266B":("266B","22 8A C1","ld ($C18A),hl"),
 "0266E":("266E","ED 53 8C C1","ld ($C18C),de"),
 "02672":("2672","C9","ret")
}
def check(path):
    rom=path.read_bytes()
    if len(rom)!=262144 or hashlib.sha256(rom).hexdigest()!=SHA:
        raise ValueError("Source-only Ys ROM SHA/size mismatch")
    lines=(ROOT/"Ys/phase6/code.lst").read_text(encoding="utf-8").splitlines()
    for phys,(cpu,raw,op) in ROWS.items():
        off=int(phys,16);data=bytes.fromhex(raw)
        if rom[off:off+len(data)]!=data:
            raise ValueError("Physical bank0 bytes mismatch "+phys)
        expr=r"^"+phys+r"\s+"+cpu+r"\s+"+r"\s+".join(raw.split())+r"\s+"+re.escape(op)+r"\s*$"
        if sum(bool(re.fullmatch(expr,line,re.I)) for line in lines)!=1:
            raise ValueError("Independent Phase6 listing mismatch "+phys)
    print("PASS PC-32: original fixed-bank $2654-$2672 pointer stores,"
          " ten independent source instruction rows and ROM SHA256")
if __name__=="__main__":
    try:
        if len(sys.argv)!=2:raise ValueError("usage: verify_pc32_store_bc.py ORIGINAL.sms")
        check(Path(sys.argv[1]))
    except (OSError,ValueError) as error:
        sys.exit("FAIL PC-32 original bank0 BC provenance: "+str(error))
