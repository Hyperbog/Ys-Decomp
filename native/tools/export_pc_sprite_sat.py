#!/usr/bin/env python3
"""PC-14: independently export original bank-6 indexed sprite SAT records.

The source-only bank6 builder is the ONLY source of binary data; source
reports provide independent Phase11B/Phase19 validations. Original Ys
ROM images, mod content and output assets are NEVER checked into Git.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"Ys"/"tools"))
from whole_bank06 import full_bank
from recover_bank6_records_phase11b import decode_payload,encode_payload,emulate_record_buffers

MAGIC=b"YSPC14S1"
COUNT=64
PTR_BYTES=2*COUNT
STREAM_BYTES=0x9932-0x8080
TOTAL=16+PTR_BYTES+STREAM_BYTES
START=0x8080
END=0x9932


def rebuild():
    b=full_bank()
    assert len(b)==0x4000
    raw=b[:PTR_BYTES+STREAM_BYTES]
    directory=raw[:PTR_BYTES]
    stream=raw[PTR_BYTES:]
    assert len(stream)==STREAM_BYTES
    pointers=[int.from_bytes(directory[i*2:i*2+2],"little")
              for i in range(COUNT)]
    assert len(set(pointers))==COUNT
    records=[]
    for index,pc in enumerate(pointers):
        assert START<=pc<END,(index,pc)
        at=pc-START
        count=stream[at]
        assert 1<=count<=64 and at+1+3*count<=len(stream)
        blob=stream[at:at+1+3*count]
        decoded=decode_payload(blob)
        assert encode_payload(decoded)==blob
        records.append((index,pc,blob,decoded))
    ordered=sorted(records,key=lambda r:r[1])
    cursor=START
    for _,pc,blob,_ in ordered:
        assert pc==cursor, f"sprite record gap or overlap at {pc:04X}"
        cursor+=len(blob)
    assert cursor==END
    ledger=json.loads((ROOT/"Ys/phase11/bank6_records.json").read_text())
    assert ledger["schema"]=="ys-phase11b-records-v1"
    assert ledger["record_count"]==COUNT
    assert ledger["record_payload_sha256"]==hashlib.sha256(stream).hexdigest()
    for item,(_,pc,blob,_) in zip(ledger["records_by_directory_index"],records):
        assert item["cpu_address"]==f"{pc:04X}"
        assert item["sha256"]==hashlib.sha256(blob).hexdigest()
    report=json.loads((ROOT/"Ys/phase19/execution_report.json").read_text())
    assert report["schema"]=="ys-phase19-producer-sat-execution-v1"
    assert report["bounded_producer_and_sat_runs"]==192
    concat=hashlib.sha256()
    for origin_a,origin_b in report["origin_pairs"]:
        assert 0<=origin_a<=255 and 0<=origin_b<=255
        for index,pc,blob,decoded in records:
            count,_,_=decoded
            y,x=emulate_record_buffers(decoded,origin_a,origin_b)
            ybuf=bytearray([0xD0]*64)
            ybuf[:count]=y
            xbuf=bytearray(128)
            xbuf[:2*count]=x
            out=bytes(ybuf+xbuf)
            case=report["cases"][(report["origin_pairs"].index([origin_a,origin_b])*COUNT)+index]
            assert case["record_index"]==index and case["count"]==count
            assert case["first_origin"]==origin_a and case["second_origin"]==origin_b
            assert case["y_table_sha256"]==hashlib.sha256(ybuf).hexdigest(),(index,"Y")
            assert case["xt_table_sha256"]==hashlib.sha256(xbuf).hexdigest(),(index,"XT")
            assert case["sat_output_sha256"]==hashlib.sha256(out).hexdigest(),index
            concat.update(out)
    assert concat.hexdigest()==report["concat_sat_sha256"]
    header=MAGIC+struct.pack("<HHI",COUNT,len(raw),zlib.crc32(raw))
    package=header+raw
    assert len(package)==TOTAL
    return package


def main():
    p=argparse.ArgumentParser(description=__doc__)
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--out",type=Path)
    modes.add_argument("--verify",type=Path)
    args=p.parse_args()
    pkg=rebuild()
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_bytes(pkg)
    elif args.verify.read_bytes()!=pkg:
        raise ValueError("PC-14 sprite package differs from source and oracle")
    print("PASS PC-14: source bank6, 64 sprite records, 6322 record bytes,"
          " 192/192 original Z80 SAT hash cases, 36864 output bytes")


if __name__=="__main__":
    try:
        main()
    except (ValueError,KeyError,AssertionError,OSError,TypeError) as exc:
        sys.exit("FAIL PC-14 original sprite SAT export: "+str(exc))
