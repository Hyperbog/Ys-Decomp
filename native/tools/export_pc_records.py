#!/usr/bin/env python3
"""Export verified bank-7 source map-object tuples as inspection metadata.

No geometric interpretation, tile IDs, collision, world screen selection, or
authentic CRAM colors are asserted. This does not read an owner ROM.
"""
import argparse
import json
import pathlib
import struct
import sys
import zlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Ys" / "tools"))
from whole_bank07 import full_bank
from whole_bank00 import full_bank as fixed_bank

MAGIC=b"YSPC7M01"
GROUPS=22
RECORDS=209
START=0xBA67
END=0xBDBF
STAGING=0xB9C3
EXPECTED_SIZE=1000


def build():
    source=json.loads((ROOT/"Ys/wholebank07/source.json").read_text())
    bank=full_bank()   # Verifies full physical bank-7 source digest.
    fixed=fixed_bank() # Independently source-built physical bank 0.
    # Source $1B3C-$1B60: select bank 7; read $C181 & 0x7F;
    # compare group index to 0x16; look up $BA3B via RST $18;
    # stop upon zero first byte; otherwise store to object slots.
    consumer=bytes.fromhex(
        "3e0732ffff3a81c1e67ffe163050213bbadf"
        "dd2130c27eb72844dd7700dd7729237edd7720")
    assert fixed[0x1B3C:0x1B3C+len(consumer)]==consumer
    # PC-3 field projection: source $1B56-$1B98 writes selected
    # object-work slots in a $30-byte-stride array. Opcode bytes
    # disambiguate the indexed-memory LD ... ,L/H exceptions.
    source_stores={
        0x1B56: "dd7700dd7729",
        0x1B5C: "237edd7720",
        0x1B66: "6e260029292911080019",
        0x1B70: "dd7506dd7407dd752bdd742c",
        0x1B7C: "e123e56e2600292929",
        0x1B85: "dd7503dd7404dd752ddd742e",
        0x1B91: "e123113000dd1918b8",
    }
    for addr,ops in source_stores.items():
        expected=bytes.fromhex(ops)
        assert fixed[addr:addr+len(expected)]==expected, (
            f"original object projection changed at {addr:04X}")

    assert source["schema"]=="ys-bank07-complete-tail-v1"
    pointers=source["map_pointers"]
    groups=source["map_groups"]
    assert len(pointers)==len(groups)==GROUPS
    assert pointers[0]==START and pointers[-1]==0xBDBA
    assert all(a<b for a,b in zip(pointers,pointers[1:]))
    assert all(0x8000<=x<0xC000 for x in pointers)
    raw=bytearray()
    metadata=bytearray()
    terminators=0
    for i,(addr,group) in enumerate(zip(pointers,groups)):
        assert addr==group["start"]
        rows=group["records"]
        assert all(len(row)==4 and all(type(v)==int and 0<=v<=255
                                      for v in row) for row in rows)
        # The fixed-bank consumer uses record[0]==0 as terminator.
        assert len(rows)<=16  # $C230 + $30*i object work slots
        assert all(row[0]!=0 for row in rows)
        assert type(group["terminator_zero"])==bool
        term=int(group["terminator_zero"])
        stop=pointers[i+1] if i+1<GROUPS else END
        assert addr+4*len(rows)+term==stop
        rowbytes=bytes(v for row in rows for v in row)
        assert bank[addr-0x8000:stop-0x8000]==rowbytes+(b"\0" if term else b"")
        raw.extend(rowbytes)
        metadata.extend(struct.pack("<HHBB",addr,len(rows),term,0))
        terminators+=term
    assert len(raw)==4*RECORDS and terminators==20
    ptrbytes=b"".join(struct.pack("<H",v) for v in pointers)
    assert bank[0xBA3B-0x8000:0xBA67-0x8000]==ptrbytes
    staging=bank[STAGING-0x8000:STAGING-0x8000+16]
    assert len(staging)==16
    payload=metadata+raw+staging
    packet=MAGIC+struct.pack("<HHI",GROUPS,RECORDS,zlib.crc32(payload))+payload
    assert len(packet)==EXPECTED_SIZE
    return packet


def main():
    p=argparse.ArgumentParser(description=__doc__)
    grp=p.add_mutually_exclusive_group(required=True)
    grp.add_argument("--out",type=pathlib.Path)
    grp.add_argument("--verify",type=pathlib.Path)
    args=p.parse_args()
    data=build()
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_bytes(data)
    elif args.verify.read_bytes()!=data:
        raise ValueError("derived bank-7 tuple package drift")
    print("PASS PC-2 bank7 source: 22 groups, 209 four-byte records, "
          "20 zero terminators, bank0 $1B3C/$1B56-$1B98 consumers confirmed, "
          "16 staging bytes; geometry/palette unknown")


if __name__=="__main__":
    try:
        main()
    except (ValueError,AssertionError,OSError,KeyError,TypeError) as exc:
        sys.exit("FAIL PC-2 bank7 source: "+str(exc))
