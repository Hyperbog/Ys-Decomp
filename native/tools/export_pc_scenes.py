#!/usr/bin/env python3
"""Export two ORIGINAL but independent Ys scene selectors for native tools.

Fixed bank $2C24 has 9 dispatch destinations indexed by $C119.
Bank 1 $4C03 has 8 dispatch destinations and $4C2B can write $C181.
Fixed-bank object initializer separately reads $C181 & $7F to select
one of 22 bank-7 object groups. These values are NOT a proven map link.
"""
import argparse
import pathlib
import struct
import sys
import zlib

ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"Ys"/"tools"))
from whole_bank00 import full_bank as bank00_source
from whole_bank01 import full_bank as bank01_source

MAGIC=b"YSPC5S01"
SCENES=9
BANK1=8
SCENE_TABLE=0x2C24
BANK1_TABLE=0x4C03


def build():
    fixed=bank00_source()
    mapped=bank01_source()
    assert len(fixed)==len(mapped)==0x4000
    # Original $2C1B-$2C23: LD A,($C119); LD HL,$2C24; JP $0008.
    dispatch=bytes.fromhex("3a19c121242cc30800")
    assert fixed[0x2C1B:0x2C1B+len(dispatch)]==dispatch, (
        "bank-0 original scene dispatcher opcode identity drift")
    # Bank1 scene handler path $4C26-$4C30 writes $C181=A,
    # while the earlier $4C13 path loads A=1 and jumps to $4C2B.
    bank1_writer=bytes.fromhex("08cd484c083281c1cd5426")
    assert mapped[0x4C26-0x4000:0x4C26-0x4000+len(bank1_writer)]==bank1_writer
    assert mapped[0x4C1C-0x4000:0x4C26-0x4000]==bytes.fromhex(
        "3e01211f00018c801805")
    # The bank-0 object initializer $1B41-$1B4D reads and bounds
    # a DIFFERENT selector: $C181 & $7F < 22, then bank7 $BA3B.
    object_select=bytes.fromhex("3a81c1e67ffe163050213bbadf")
    assert fixed[0x1B41:0x1B41+len(object_select)]==object_select

    table0=fixed[SCENE_TABLE:SCENE_TABLE+SCENES*2]
    table1=mapped[BANK1_TABLE-0x4000:BANK1_TABLE-0x4000+BANK1*2]
    handlers=list(struct.unpack("<9H",table0))
    entries=list(struct.unpack("<8H",table1))
    assert handlers==[0x2C36,0x2D9D,0x2F2A,0x3014,0x3194,
                      0x329C,0x333B,0x3415,0x3519]
    assert all(0x4C13<=v<0x4C80 for v in entries)
    payload=table0+table1
    blob=MAGIC+struct.pack("<HHI",SCENES,BANK1,zlib.crc32(payload))+payload
    assert len(blob)==50
    return blob


def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--out",type=pathlib.Path)
    group.add_argument("--verify",type=pathlib.Path)
    args=p.parse_args()
    blob=build()
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_bytes(blob)
    elif args.verify.read_bytes()!=blob:
        raise ValueError("independent scene selector package differs from source")
    print("PASS PC-5: source fixed-bank 9 dispatch targets, "
          "bank1 8 entries and $4C2B C181 writer; active scene/map unknown")


if __name__=="__main__":
    try:
        main()
    except (AssertionError,ValueError,OSError) as exc:
        sys.exit("FAIL PC-5 scene source: "+str(exc))
