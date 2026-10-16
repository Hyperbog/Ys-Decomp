#!/usr/bin/env python3
"""PC-31 immutable bank8 original sound/title pointer context at $23F18.

ROM bank identity is supported by the PC-30 mapper-qualified source
watch slot2=8, CPU=$BF18, bytes=ED_53_A1_C1; this checker separately
hashes original ROM and verifies bank-8 disassembly rows.
"""
import hashlib
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
SHA="02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9"
ROWS={
 "23F14":("BF14","5E","ld e,(hl)"),
 "23F15":("BF15","23","inc hl"),
 "23F16":("BF16","56","ld d,(hl)"),
 "23F17":("BF17","23","inc hl"),
 "23F18":("BF18","ED 53 A1 C1","ld ($C1A1),de"),
 "23F1C":("BF1C","7E","ld a,(hl)"),
 "23F1D":("BF1D","32 2A C2","ld ($C22A),a"),
 "23F20":("BF20","23","inc hl")
}
def check(path):
    rom=path.read_bytes()
    if len(rom)!=262144 or hashlib.sha256(rom).hexdigest()!=SHA:
        raise ValueError("Original source-only 16-bank SMS cartridge identity mismatch")
    source=(ROOT/"Ys/phase8/banked_code.lst").read_text(encoding="utf-8").splitlines()
    for phys,(cpu,raw,mnem) in ROWS.items():
        data=bytes.fromhex(raw)
        off=int(phys,16)
        if rom[off:off+len(data)]!=data:
            raise ValueError("Original physical bank8 byte mismatch at "+phys)
        expr=r"^"+phys+r"\s+"+cpu+r"\s+"+r"\s+".join(raw.split())+r"\s+"+re.escape(mnem)+r"\s*$"
        if sum(bool(re.fullmatch(expr,line,re.I)) for line in source)!=1:
            raise ValueError("Independent bank8 Phase8 code row mismatch "+phys)
    print("PASS PC-31: original bank8 $23F18 ED 53 and eight independent listing rows")
if __name__=="__main__":
    try:
        if len(sys.argv)!=2: raise ValueError("usage: verify_pc31_bank8_pointer.py SOURCE.sms")
        check(Path(sys.argv[1]))
    except (OSError,ValueError) as error:
        sys.exit("FAIL PC-31 bank8 original pointer provenance: "+str(error))
