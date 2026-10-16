#!/usr/bin/env python3
"""Rebuild M44 original Ys initialization pattern VRAM $0000-$2FFF.

Source-only bank 5 $8000 four-column opcode $0695, 12288 bytes.
M43 name table $3900-$3EFF and these patterns are recovered from
adjacent original initialization stages; NO live-screen/palette claim.
"""
import argparse
import pathlib
import re
import struct
import sys
import zlib

ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"Ys"/"tools"))
from whole_bank00 import full_bank as fixed_bank
from whole_banks05_13_14_15 import full_bank as asset_bank

MAGIC=b"YSPC7P01"
DEST_BYTES=0x3000
SOURCE_BASE=0x8000


def verify_code(fixed):
    rows=(ROOT/"Ys/phase5/code.lst").read_text().splitlines()
    for begin,end in ((0x0695,0x06C1),(0x0C7E,0x0C87)):
        cursor=begin
        assembly=bytearray()
        for row in rows:
            m=re.match(r"^[0-9A-F]{5} ([0-9A-F]{4})\s+((?:[0-9A-F]{2}\s+)+)",row)
            if m and begin<=int(m.group(1),16)<end:
                addr=int(m.group(1),16)
                b=bytes.fromhex(m.group(2))
                assert addr==cursor,f"Missing original opcode at ${cursor:04X}"
                assembly.extend(b)
                cursor+=len(b)
        assert cursor==end and assembly==fixed[begin:end], (
            f"Original M44 opcode mismatch ${begin:04X}-${end:04X}")
    assert fixed[0x0C7E:0x0C87]==bytes.fromhex("210080110040cd9506")


def decode(bank):
    pos=0
    out=bytearray(DEST_BYTES)
    touched=bytearray(DEST_BYTES)
    writes=0
    for plane in range(4):
        dest=plane
        for command in range(1024):
            assert pos<len(bank),"M44 source ended without plane terminator"
            code=bank[pos];pos+=1
            if code==0: break
            n=code&0x7f
            if n==0:n=256  # DJNZ on B=0 executes 256 times
            if code&0x80:
                assert pos+n<=len(bank),"M44 literal crosses bank"
                values=bank[pos:pos+n];pos+=n
            else:
                assert pos<len(bank),"M44 repeat truncated"
                values=bytes((bank[pos],))*n;pos+=1
            for value in values:
                assert dest<DEST_BYTES, "M44 pattern VRAM overrun"
                assert not touched[dest], "M44 pattern plane collision"
                out[dest]=value
                touched[dest]=1
                writes+=1
                dest+=4
        else:
            raise ValueError("M44 command budget exhausted")
    assert writes==DEST_BYTES and all(touched), (
        f"expected 12288 original pattern writes, got {writes}")
    return bytes(out),pos


def package():
    fixed=fixed_bank()
    bank5=asset_bank(5)
    assert len(fixed)==len(bank5)==0x4000
    verify_code(fixed)
    data,used=decode(bank5)
    assert used<=len(bank5)
    pkg=MAGIC+struct.pack("<HHI",0,DEST_BYTES,zlib.crc32(data))+data
    assert len(pkg)==12304
    return pkg,used


def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--out",type=pathlib.Path)
    group.add_argument("--verify",type=pathlib.Path)
    a=p.parse_args()
    blob,used=package()
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_bytes(blob)
    elif a.verify.read_bytes()!=blob:
        raise ValueError("M44 source pattern-byte asset drift")
    print("PASS PC-7: source-only M44 4-plane patterns; 12288 VRAM bytes "
          f"(384 tiles), {used} encoded bank5 bytes; CRAM/scene unknown")


if __name__=="__main__":
    try:main()
    except (ValueError,AssertionError,OSError) as e:
        sys.exit("FAIL PC-7 source pattern export: "+str(e))
