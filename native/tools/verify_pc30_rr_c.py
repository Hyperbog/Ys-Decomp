#!/usr/bin/env python3
"""PC-30 original bank0 rotating controller/game-state dispatch indices.

Only source-opcode provenance, not source input or gameplay correctness.
"""
import hashlib
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
SHA="02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9"
ROWS={
    "00FEB":("0FEB","1F","rra"),
    "00FEC":("0FEC","CB 19","rr c"),
    "00FEE":("0FEE","47","ld b,a"),
    "00FEF":("0FEF","2A 33 C0","ld hl,($C033)"),
    "00FF2":("0FF2","09","add hl,bc"),
    "00FF3":("0FF3","22 35 C0","ld ($C035),hl"),
    "00FF6":("0FF6","C9","ret"),
}
def check(path):
    rom=path.read_bytes()
    if len(rom)!=262144 or hashlib.sha256(rom).hexdigest()!=SHA:
        raise ValueError("Original source-ROM SHA-256/size mismatch")
    lines=(ROOT/"Ys/phase5/code.lst").read_text(encoding="utf-8").splitlines()
    for address,(pc,raw,mnemonic) in ROWS.items():
        offset=int(address,16)
        data=bytes.fromhex(raw)
        if rom[offset:offset+len(data)]!=data:
            raise ValueError("Original bank0 byte mismatch at "+address)
        regex=r"^"+address+r"\s+"+pc+r"\s+"+r"\s+".join(raw.split())+r"\s+"+re.escape(mnemonic)+r"\s*$"
        if sum(bool(re.fullmatch(regex,line,re.I)) for line in lines)!=1:
            raise ValueError("Independent Phase5 listing mismatch at "+address)
    print("PASS PC-30: fixed bank0 RR C/HL dispatch context ROM SHA and seven listing rows")
if __name__=="__main__":
    try:
        if len(sys.argv)!=2:raise ValueError("usage: verify_pc30_rr_c.py SOURCE.sms")
        check(Path(sys.argv[1]))
    except (OSError,ValueError) as error:
        sys.exit("FAIL PC-30 original rotating-index source: "+str(error))
