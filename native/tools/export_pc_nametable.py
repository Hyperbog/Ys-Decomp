#!/usr/bin/env python3
"""Reconstruct original Ys INITIALIZATION name-table bytes at VRAM $3900-$3EFF.

M41 bank5 $B61A incremental/literal RLE -> $C600 (748 bytes).
M42 source $0BEF interleaves two command columns -> $D600 (1536).
M43 source $0C72/$06C1 sends $D600 to VRAM $3900, exactly 1536 bytes.

This does not reconstruct first $3800-$38FF, active gameplay maps,
VRAM pattern tile residence, CRAM palette, or collision. No ROM is read.
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
from whole_banks05_13_14_15 import full_bank as source_bank

START=0xB61A
VRAM_START=0x3900
OUTPUT_LEN=0x600
MAGIC=b"YSPC6N01"


def verify_code(bank):
    lines=(ROOT/"Ys/phase5/code.lst").read_text().splitlines()
    for start,stop in ((0x0C20,0x0C3E),(0x0C55,0x0C7E),(0x06C1,0x06D4)):
        cursor=start
        data=bytearray()
        for line in lines:
            match=re.match(
                r"^[0-9A-F]{5} ([0-9A-F]{4})\s+((?:[0-9A-F]{2}\s+)+)",line)
            if not match: continue
            addr=int(match.group(1),16)
            if start<=addr<stop:
                fragment=bytes.fromhex(match.group(2))
                assert addr==cursor, f"source instruction gap at ${addr:04X}"
                data.extend(fragment)
                cursor+=len(fragment)
        assert cursor==stop and data==bank[start:stop], (
            f"source code mismatch ${start:04X}-${stop:04X}")
    assert bank[0x0C5E:0x0C67]==bytes.fromhex("211ab61100c6cd200c")
    assert bank[0x0C67:0x0C72]==bytes.fromhex("2100c61100d60e02cdef0b")
    assert bank[0x0C72:0x0C7E]==bytes.fromhex(
        "2100d6110079010006cdc106")


def initial_rle(source):
    out=bytearray()
    cursor=START-0x8000
    for _ in range(4096):
        assert cursor<len(source),"bank5 RLE unterminated"
        op=source[cursor]; cursor+=1
        if op==0: break
        n=op&0x7f if op&0x80 else op
        if n==0: n=256
        if op&0x80:
            assert cursor+n<=len(source),"bank5 literal truncated"
            out.extend(source[cursor:cursor+n]);cursor+=n
        else:
            assert cursor<len(source),"bank5 incremental truncated"
            first=source[cursor];cursor+=1
            out.extend((first+i)&255 for i in range(n))
        assert len(out)<=0x1000,"bank5 decoded overflow"
    else:
        raise ValueError("bank5 RLE command budget exceeded")
    assert cursor-(START-0x8000)==518
    assert len(out)==748
    return bytes(out)


def staged_two_rows(stream):
    out=bytearray(OUTPUT_LEN)
    written=bytearray(OUTPUT_LEN)
    at=0
    count=0
    for row in range(2):
        dst=row
        for command in range(2048):
            assert at<len(stream),"staging stream truncated"
            op=stream[at];at+=1
            if op==0:break
            n=op&0x7f if op&0x80 else op
            if n==0:n=256
            if op&0x80:
                assert at+n<=len(stream)
                values=stream[at:at+n];at+=n
            else:
                assert at<len(stream)
                values=bytes((stream[at],))*n;at+=1
            for v in values:
                assert dst<OUTPUT_LEN, "staging write outside nametable"
                assert not written[dst], "overlapping column bytes"
                out[dst]=v;written[dst]=1;count+=1;dst+=2
        else:
            raise ValueError("row not terminated")
    assert at==748 and count==OUTPUT_LEN and all(written)
    return bytes(out)


def package():
    fixed=fixed_bank()
    bank5=source_bank(5)
    assert len(fixed)==len(bank5)==0x4000
    verify_code(fixed)
    rle=initial_rle(bank5)
    data=staged_two_rows(rle)
    # Format: 8-byte magic; LE VRAM start $3900, LE size $0600,
    # CRC32 of all 1536 authentic uploaded bytes; then raw bytes.
    return MAGIC+struct.pack("<HHI",VRAM_START,OUTPUT_LEN,zlib.crc32(data))+data


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--out",type=pathlib.Path)
    group.add_argument("--verify",type=pathlib.Path)
    args=parser.parse_args()
    data=package()
    assert len(data)==1552
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_bytes(data)
    elif args.verify.read_bytes()!=data:
        raise ValueError("M43 source name-table output drift")
    print("PASS PC-6: original bank5 RLE 518->748, two rows -> 1536"
          " source-verified VRAM $3900-$3EFF bytes; active map unknown")


if __name__=="__main__":
    try:main()
    except (ValueError,AssertionError,OSError) as exc:
        sys.exit("FAIL PC-6 name-table source: "+str(exc))
