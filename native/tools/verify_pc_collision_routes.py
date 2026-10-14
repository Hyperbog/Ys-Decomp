#!/usr/bin/env python3
"""PC-11: source-only bank-1 -> bank-4 collision-call mapping proof.

Proves conditional execution entered at $476C selects physical bank 4
before any of its three $807C calls. Does NOT demonstrate a live Ys
playable area, runtime entry into $476C or actor/world coordinates.
"""
import pathlib
import re
import sys

ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"Ys"/"tools"))
from whole_bank01 import full_bank as source_bank01
from whole_bank04 import full_bank as source_bank04

START=0x476C
LAST_END=0x48E2
CALLS=(0x47C2,0x486C,0x48DF)
ORIGIN_INDEX_OFFSETS=(14,14,13)


def source_opcode_index():
    rows=(ROOT/"Ys/phase7/code.lst").read_text().splitlines()
    entries={}
    for row in rows:
        m=re.match(
            r"^[0-9A-F]{5} ([0-9A-F]{4})\s+((?:[0-9A-F]{2}\s+)+)",
            row)
        if not m:
            continue
        pc=int(m.group(1),16)
        if START<=pc<LAST_END:
            assert pc not in entries,f"duplicate source opcode {pc:04X}"
            entries[pc]=bytes.fromhex(m.group(2))
    cursor=START
    for pc in sorted(entries):
        assert pc==cursor,f"gap in original bank1 CFG {cursor:04X}"
        cursor+=len(entries[pc])
    assert cursor==LAST_END
    return entries


def verify():
    bank1=source_bank01()
    bank4=source_bank04()
    assert len(bank1)==len(bank4)==0x4000
    index=source_opcode_index()
    assert b"".join(index[pc] for pc in sorted(index))==(
        bank1[START-0x4000:LAST_END-0x4000])
    # Early nonzero C100 -> return. Only path from routine entry
    # to collision workers passes a *direct* bank4 mapper write.
    expected={
        0x476C:"3a00c1",0x476F:"b7",0x4770:"c0",
        0x4771:"3e04",0x4773:"32ffff",
        0x477C:"3a1bc1",0x477F:"0f",0x4780:"da9f48",
        0x4783:"3a0dc2",0x4786:"87",0x4787:"c8",
        0x478A:"2680",0x489F:"3a01c2",0x48A4:"c0",
        0x48A5:"3a0ec2",0x48A9:"c8",0x48AC:"2680"
    }
    for pc,hexstr in expected.items():
        assert index[pc]==bytes.fromhex(hexstr), (
            f"original bank-1 routed opcode mismatch {pc:04X}")
    # Exactly three call instructions, each original $807C, in
    # this bounded source window; no later mapper writes/calls
    # that could invalidate simple straight-line mapping.
    calls={pc:b for pc,b in index.items() if b[0]==0xCD}
    assert list(sorted(calls))==list(CALLS)
    assert all(b==bytes.fromhex("cd7c80") for b in calls.values())
    assert [pc for pc,b in index.items()
            if b==bytes.fromhex("32ffff")]==[0x4773]
    assert all(not b.startswith(bytes.fromhex("32ffff"))
               for pc,b in index.items() if pc>0x4773)
    for call_pc,ixoff in zip(CALLS,ORIGIN_INDEX_OFFSETS):
        assert index[call_pc-3]==bytes((0xDD,0x7E,ixoff)), (
            f"source IX descriptor selector wrong at {call_pc:04X}")
        assert bank1[call_pc-0x4000:call_pc-0x4000+3] == (
            bytes.fromhex("cd7c80"))
    # Bank4 must contain the same original 31x4 collision records
    # and exact 38-byte predicate as the independent PC-9 exporter.
    sys.path.insert(0,str(ROOT/"native/tools"))
    from export_pc_collision import package
    blob=package()
    assert bank4[:124]==blob[16:]
    assert bank4[0x7C:0xA2]==bytes.fromhex(
        "87876f26807e2cdd8611d0b92807d0863812b8380f"
        "2c7edd8610d0bb2806d02c863801ba3fc9")
    return index


def main():
    index=verify()
    print("PASS PC-11: original bank1 $476C-$48E1",
          f"{len(index)} instructions/source bytes verified;")
    print("  $4773 selects bank4; conditional $4780 branch -> $489F;")
    print("  call $807C at $47C2 (IX+14), $486C (IX+14),",
          "$48DF (IX+13);")
    print("  no subsequent direct slot2 mapper writes before calls.")
    print("  Live gameplay entry and world tile/collision meaning UNVERIFIED.")


if __name__=="__main__":
    try:
        main()
    except (AssertionError,OSError,ValueError,KeyError) as e:
        sys.exit("FAIL PC-11 source caller mapping: "+str(e))
