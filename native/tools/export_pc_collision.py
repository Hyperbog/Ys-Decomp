#!/usr/bin/env python3
"""Export verified original Ys bank-4 collision DESCRIPTORS, not a map.

Source bank4 $8000-$807B contains 31 four-byte box descriptors; its
$807C-$80A1 routine implements a carry-returning overlap predicate.
Bank1 has three statically matching call sites, but mapper state and
actual gameplay object-coordinate meaning are NOT established.
"""
import argparse
import json
from pathlib import Path
import struct
import sys
import zlib

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"Ys"/"tools"))
from whole_bank01 import full_bank as bank1_source
from whole_bank04 import full_bank as bank4_source
from bank04_crossbank_ledger import build as crossbank_evidence

MAGIC=b"YSPC9C01"
BOXES=31
STRIDE=4
CODE=bytes.fromhex(
    "87876f26807e2cdd8611d0b92807d0863812b8380f"
    "2c7edd8610d0bb2806d02c863801ba3fc9"
)
CALLS=((0x47C2,14),(0x486C,14),(0x48DF,13))


def package():
    bank4=bank4_source()
    bank1=bank1_source()
    assert len(bank4)==len(bank1)==0x4000
    assert len(CODE)==38 and bank4[0x7c:0xa2]==CODE
    data=bank4[:BOXES*STRIDE]
    assert len(data)==124
    for pc,disp in CALLS:
        p=pc-0x4000
        assert bank1[p-3:p]==bytes((0xDD,0x7E,disp))
        assert bank1[p:p+4]==bytes((0xCD,0x7C,0x80,0xD9))
    ledger=crossbank_evidence()
    assert len(ledger["call_references"])==3
    assert ledger["mapper_proven_at_calls"] is False
    report=json.loads((ROOT/"Ys/wholebank04/collision_report.json").read_text())
    assert report["case_count"]==3968 and report["descriptor_records"]==BOXES
    assert report["collision_positive_cases"]==3033
    # Independent old Z80 opcode interpreter's SHA256 outcome ledger.
    assert report["outcome_trace_sha256"] == (
        "4290475a0305428d1fe857ba5b3bdafa2ba787fc63af15cf8d9d6a520a28d977")
    return MAGIC+struct.pack("<HHI",BOXES,STRIDE,zlib.crc32(data))+data


def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--out",type=Path)
    mode.add_argument("--verify",type=Path)
    args=p.parse_args()
    binary=package()
    assert len(binary)==140
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_bytes(binary)
    elif args.verify.read_bytes()!=binary:
        raise ValueError("PC-9 bank4 source collision package mismatch")
    print("PASS PC-9 source: 31 bank4 descriptors; $807C 38-byte "
          "predicate; three bank1 candidate calls; "
          "3968 previously Z80-checked cases (mapper NOT proven)")


if __name__=="__main__":
    try:
        main()
    except (AssertionError,ValueError,OSError,KeyError,TypeError) as e:
        sys.exit("FAIL PC-9 original collision source: "+str(e))
