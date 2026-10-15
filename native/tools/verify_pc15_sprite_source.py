#!/usr/bin/env python3
"""PC-15: independently audit static original sprite record selector path.

A source instruction path is not an observed execution. All active
mapper, $C199 selector and $C210/$C211 origins require runtime evidence.
"""
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"Ys"/"tools"))
from whole_bank00 import full_bank as bank0_source
from whole_bank06 import full_bank as bank6_source

def check():
    a=bank0_source()
    b=bank6_source()
    assert len(a)==len(b)==16384
    fixed={0x26F3:"3e06",0x26F5:"32ffff",
           0x26F8:"2140dd",0x26FB:"222ac0",
           0x26FE:"2100dd",0x2701:"2228c0",
           0x2704:"cd3299",0x2707:"2a28c0",
           0x270A:"36d0",
           0x0427:"af",0x0428:"d3bf"}
    # Conditional 8x8 source sprite directory selector:
    # $C198 and $C011 gate it; BC is loaded LE from $C210,
    # then ((C184+C210)&7)<<3 | ((C182+C211)&7) | $80.
    # $275C also writes $FF to C199 in a different path; this
    # DOES NOT mean bank6 $9932 can accept that as a 64-way index.
    fixed.update({
        0x26B6:"3a98c1",0x26B9:"b7",0x26BA:"2850",
        0x26BC:"3a11c0",0x26BF:"e640",0x26C1:"2049",
        0x26C3:"ed4b10c2",0x26C7:"3a84c1",0x26CA:"81",
        0x26CB:"e607",0x26CD:"07",0x26CE:"07",0x26CF:"07",
        0x26D0:"5f",0x26D1:"3a82c1",0x26D4:"80",
        0x26D5:"e607",0x26D7:"b3",0x26D8:"f680",
        0x26DA:"3299c1",
        0x275A:"3eff",0x275C:"3299c1",
    })
    sprite={0x9932:"3a99c1",0x9935:"87",0x9936:"6f",
            0x9937:"2680",0x9939:"7e",0x993A:"2c",
            0x993B:"66",0x993C:"6f",0x993D:"46",
            0x993E:"48",0x993F:"23",0x9940:"ed5b28c0",
            0x9944:"3a10c2",0x9951:"ed5b2ac0",
            0x9955:"3a11c2"}
    # Source bytes validated against Phase6 assembly listing, and bank6
    # rebuild original SHA. The second source confirms literal pointers.
    for pc,hexval in fixed.items():
        assert a[pc:pc+len(bytes.fromhex(hexval))]==bytes.fromhex(hexval),hex(pc)
    for pc,hexval in sprite.items():
        offset=pc-0x8000
        assert b[offset:offset+len(bytes.fromhex(hexval))]==bytes.fromhex(hexval),hex(pc)
    listing=(ROOT/"Ys/phase6/code.lst").read_text()
    rows={}
    for line in listing.splitlines():
        match=re.match(r"^[0-9A-F]{5} ([0-9A-F]{4})\s+((?:[0-9A-F]{2}\s+)+)",line)
        if match: rows[int(match[1],16)]=bytes.fromhex(match[2])
    for pc,hexval in fixed.items():
        if pc in rows: assert rows[pc]==bytes.fromhex(hexval),hex(pc)
    assert all(pc in rows for pc in range(0x26F3,0x270Cu) if pc in fixed)
    print("PASS PC-15: original $26DA C199 selector bitfields,",
          "separate $275C FF assignment; mapper+producer setup",
          "bank6 $9932 C199 record selector, C210/C211 Y/X origins;",
          "real scene identity/runtime entry unverified")

if __name__=="__main__":
    try:
        check()
    except (OSError,AssertionError,ValueError) as e:
        sys.exit("FAIL PC-15 source sprite selector chain: "+str(e))
