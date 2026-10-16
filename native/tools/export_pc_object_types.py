#!/usr/bin/env python3
"""Generate source-only bank-0 conditional object-init parameters for the PC.

Original Z80 at $1B9B-$1C04 is verified against an independent opcode
listing. The 35x10 table is from $1C05-$1D62. No ROM input, actor names,
spatial scenes, or original gameplay are inferred.
"""
import argparse
import pathlib
import re
import struct
import sys
import zlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Ys" / "tools"))
from whole_bank00 import full_bank

START=0x1B9B
CODE_END=0x1C05
TABLE_END=0x1D63
TYPES=35
STRIDE=10
MAGIC=b"YSPC4O01"


def verify_consumer(bank):
    lines=(ROOT/"Ys/phase5/code.lst").read_text().splitlines()
    decoded=[]
    cursor=START
    for line in lines:
        m=re.match(r"^[0-9A-F]{5} ([0-9A-F]{4})\s+((?:[0-9A-F]{2}\s+)+)",line)
        if not m:
            continue
        addr=int(m.group(1),16)
        if START<=addr<CODE_END:
            chunk=bytes.fromhex(m.group(2))
            assert addr==cursor, f"Opcode coverage discontinuity at {addr:04X}"
            decoded.append(chunk)
            cursor+=len(chunk)
    assert cursor==CODE_END and len(decoded)==55
    assert b"".join(decoded)==bank[START:CODE_END]
    assert bank[0x1B9D:0x1BA0]==bytes.fromhex("873816")  # ADD A,A; JR C
    assert bank[0x1BB6:0x1BC2]==bytes.fromhex(
        "6F26005D5429291911051C19")  # 10*(type&0x7f)+$1C05
    assert bank[0x1C02:0x1C05]==bytes.fromhex("E1D1C9")


def package():
    bank=full_bank()  # Verifies the reconstructed source-bank digest.
    assert len(bank)==0x4000
    verify_consumer(bank)
    table=bank[CODE_END:TABLE_END]
    assert len(table)==TYPES*STRIDE
    return MAGIC+struct.pack("<HHI",TYPES,STRIDE,zlib.crc32(table))+table


def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--out",type=pathlib.Path)
    mode.add_argument("--verify",type=pathlib.Path)
    args=p.parse_args()
    derived=package()
    assert len(derived)==366
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_bytes(derived)
    elif args.verify.read_bytes()!=derived:
        raise ValueError("Object type source package drift")
    print("PASS PC-4: source bank0 $1B9B-$1C04 55 opcodes, "
          "35 x 10 conditional object-entry bytes; no ROM input")


if __name__=="__main__":
    try:
        main()
    except (AssertionError,ValueError,OSError) as exc:
        sys.exit("FAIL PC-4 source object init: "+str(exc))
