#!/usr/bin/env python3
"""PC-20 authentic bank2 $85CF-$85E5 sound event table-address source."""
from pathlib import Path
import hashlib
import re
import sys
ROOT=Path(__file__).resolve().parents[2]
SHA="02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9"
ROWS={
 "085CF":("85CF","D6 80","sub $80"),
 "085D1":("85D1","28 03","jr z,$85D6"),
 "085D3":("85D3","DD 86 05","add a,(ix+5)"),
 "085D6":("85D6","21 58 8A","ld hl,$8A58"),
 "085D9":("85D9","08","ex af,af'"),
 "085DA":("85DA","28 03","jr z,$85DF"),
 "085DC":("85DC","21 EA 8A","ld hl,$8AEA"),
 "085DF":("85DF","08","ex af,af'"),
 "085E0":("85E0","4F","ld c,a"),
 "085E1":("85E1","06 00","ld b,$00"),
 "085E3":("85E3","09","add hl,bc"),
 "085E4":("85E4","09","add hl,bc"),
 "085E5":("85E5","C9","ret"),
}
def check(path:Path):
    rom=path.read_bytes()
    if len(rom)!=262144 or hashlib.sha256(rom).hexdigest()!=SHA:
        raise ValueError("source ROM SHA256 or size incorrect")
    data=bytes.fromhex(" ".join(raw for _,raw,_ in ROWS.values()))
    if rom[0x85CF:0x85CF+len(data)]!=data:
        raise ValueError("source bank2 $85CF-$85E5 byte mismatch")
    lines=(ROOT/"Ys/phase5/code.lst").read_text(encoding="utf-8").splitlines()
    for phys,(pc,raw,mnemonic) in ROWS.items():
        pattern=r"^"+phys+r"\s+"+pc+r"\s+"+r"\s+".join(raw.split())+r"\s+"+re.escape(mnemonic)+r"\s*$"
        if sum(bool(re.fullmatch(pattern,line,re.IGNORECASE)) for line in lines)!=1:
            raise ValueError("Phase5 listing mismatch at "+phys)
    print("PASS PC-20: source-only ROM and 13 original sound-table addressing opcodes $85CF-$85E5")
if __name__=="__main__":
    try:
        if len(sys.argv)!=2: raise ValueError("usage: verify_pc20_sound_table.py ORIGINAL.sms")
        check(Path(sys.argv[1]))
    except (OSError,ValueError) as exc:
        sys.exit("FAIL PC-20 source proof: "+str(exc))
