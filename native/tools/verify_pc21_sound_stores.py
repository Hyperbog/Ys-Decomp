#!/usr/bin/env python3
"""PC-21 verify independently cataloged bank2 sound indexed stores and loads."""
from pathlib import Path
import hashlib
import re
import sys
ROOT=Path(__file__).resolve().parents[2]
SHA="02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9"
ROWS={
"08510":("8510","DD 77 0E","ld (ix+14),a"),
"08515":("8515","DD 77 0F","ld (ix+15),a"),
"08521":("8521","DD 77 12","ld (ix+18),a"),
"08524":("8524","DD 77 11","ld (ix+17),a"),
"0852E":("852E","DD 77 11","ld (ix+17),a"),
"0853D":("853D","DD 77 0A","ld (ix+10),a"),
"08543":("8543","DD 46 02","ld b,(ix+2)"),
"0854D":("854D","DD 77 0A","ld (ix+10),a"),
"08550":("8550","DD 77 15","ld (ix+21),a"),
"08554":("8554","DD 77 0C","ld (ix+12),a"),
"08557":("8557","DD 77 0D","ld (ix+13),a"),
"0855A":("855A","DD 77 0B","ld (ix+11),a"),
"0855D":("855D","DD 77 13","ld (ix+19),a"),
"08560":("8560","DD 77 14","ld (ix+20),a"),
"08563":("8563","DD 73 03","ld (ix+3),e"),
"08566":("8566","DD 72 04","ld (ix+4),d"),
}
def check(path:Path):
    rom=path.read_bytes()
    if len(rom)!=262144 or hashlib.sha256(rom).hexdigest()!=SHA:
        raise ValueError("source ROM size/sha mismatch")
    listing=(ROOT/"Ys/phase5/code.lst").read_text(encoding="utf-8").splitlines()
    for phys,(pc,raw,op) in ROWS.items():
        data=bytes.fromhex(raw)
        if rom[int(phys,16):int(phys,16)+len(data)]!=data:
            raise ValueError("original indexed store/load bytes mismatch at "+phys)
        expr=r"^"+phys+r"\s+"+pc+r"\s+"+r"\s+".join(raw.split())+r"\s+"+re.escape(op)+r"\s*$"
        if sum(bool(re.fullmatch(expr,line,re.IGNORECASE)) for line in listing)!=1:
            raise ValueError("Phase5 opcode listing mismatch at "+phys)
    print("PASS PC-21: 16 bank2 source indexed store/load records, full ROM SHA")
if __name__=="__main__":
    try:
        if len(sys.argv)!=2: raise ValueError("usage: verify_pc21_sound_stores.py ORIGINAL.sms")
        check(Path(sys.argv[1]))
    except (OSError,ValueError) as exc:
        sys.exit("FAIL PC-21 source proof: "+str(exc))
