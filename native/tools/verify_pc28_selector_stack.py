#!/usr/bin/env python3
"""PC-28: independent original ROM + Phase5 proof for the button edge branch.

Byte provenance and stack-load execution tests do not independently prove
a title screen or original gameplay.
"""
from pathlib import Path
import hashlib
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
SHA="02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9"
ROWS={
  "00CC2":("0CC2","ED 7B 2E C0","ld sp,($C02E)"),
  "00CC6":("0CC6","3E 02","ld a,$02"),
  "00CC8":("0CC8","32 1F C0","ld ($C01F),a"),
  "00CCB":("0CCB","C3 56 0B","jp $0B56"),
  "00CD1":("0CD1","3A 1C C0","ld a,($C01C)"),
  "00CD4":("0CD4","E6 30","and $30"),
  "00CD6":("0CD6","20 EA","jr nz,$0CC2"),
}
def check(path):
    rom=path.read_bytes()
    if len(rom)!=262144 or hashlib.sha256(rom).hexdigest()!=SHA:
        raise ValueError("original-source ROM bytes/SHA mismatch")
    lines=(ROOT/"Ys/phase5/code.lst").read_text(encoding="utf-8").splitlines()
    for address,(pc,data,mnemonic) in ROWS.items():
        at=int(address,16)
        blob=bytes.fromhex(data)
        if rom[at:at+len(blob)]!=blob:
            raise ValueError("bank0 original opcode mismatch at "+address)
        expr=r"^"+address+r"\s+"+pc+r"\s+"+r"\s+".join(data.split())+r"\s+"+re.escape(mnemonic)+r"\s*$"
        if sum(bool(re.fullmatch(expr,row,re.I)) for row in lines)!=1:
            raise ValueError("Phase5 code ledger mismatch at "+address)
    print("PASS PC-28: original bank0 $0CC2-$0CCB selector branch bytes,"
          " seven independent Phase5 instruction rows and ROM SHA256")

if __name__=="__main__":
    try:
        if len(sys.argv)!=2:
            raise ValueError("usage: verify_pc28_selector_stack.py SOURCE.sms")
        check(Path(sys.argv[1]))
    except (OSError,ValueError) as err:
        sys.exit("FAIL PC-28 source selector proof: "+str(err))
