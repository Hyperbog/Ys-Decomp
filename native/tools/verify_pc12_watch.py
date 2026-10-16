#!/usr/bin/env python3
"""PC-12 verify source-CPU observation JSON, not a gameplay assertion.

The observed state must come from the locally rebuilt original cartridge
and the unmodified post-M45 native trace. Failure to reach collision callers
is a documented BLOCKER, never silently treated as a real playable scene.
"""
import argparse
import json
import pathlib
import sys

PCS=("476C","4773","47C2","486C","48DF")
EXPECTED={"schema","start_pc","stop_reason","continued_steps","stop_pc",
          "stop_cpu_status","stop_slot1","stop_slot2","stop_irq",
          "stop_vblank","observed_collision_calls","events"}
VALUES=("mapper_slot1","mapper_slot2","raw_bank_select2","mapper_control",
        "ix","c100","c119","c181","c20d","c20e","c210","c211",
        "ix13","ix14","ix16","ix17")


def check(path):
    obj=json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(obj,dict) and set(obj)==EXPECTED
    assert obj["schema"]=="ys-pc12-source-watch-v1"
    assert obj["start_pc"]=="0C92"
    assert obj["stop_reason"] in (
        "budget","vblank_limit","unsupported","halted","observed")
    assert isinstance(obj["continued_steps"],int)
    assert 0<=obj["continued_steps"]<=150000
    assert isinstance(obj["stop_pc"],str) and len(obj["stop_pc"])==4
    int(obj["stop_pc"],16)
    for key in ("stop_cpu_status","stop_slot1","stop_slot2","stop_irq",
                "stop_vblank","observed_collision_calls"):
        assert type(obj[key]) is int and obj[key]>=0,key
    assert obj["stop_slot1"]<16 and obj["stop_slot2"]<16
    entries=obj["events"]
    assert isinstance(entries,list) and len(entries)==5
    assert [x["pc"] for x in entries]==list(PCS)
    assert obj["observed_collision_calls"]==sum(
        x["count"] for x in entries[2:])
    for entry in entries:
        assert isinstance(entry["seen"],bool)
        assert type(entry["count"]) is int and entry["count"]>=0
        assert entry["seen"]==(entry["count"]>0)
        for name in VALUES:
            assert type(entry[name]) is int and (
                0<=entry[name]<=65535 if name=="ix" else
                0<=entry[name]<=255
            ), (entry["pc"],name)
        for name in ("steps","irq","vblank"):
            assert type(entry[name]) is int and entry[name]>=0
        if entry["seen"]:
            assert entry["mapper_slot1"]==1
            assert entry["steps"]>=0
            assert entry["vblank"]<=obj["stop_vblank"]
    if obj["stop_reason"]=="observed":
        assert obj["observed_collision_calls"]>0
    else:
        assert obj["observed_collision_calls"]==0
    if obj["observed_collision_calls"]:
        print("OBSERVED PC-12: original bank1 collision call before"
              " execution; inspect runtime slot2/WRAM/IX to determine"
              " interpretation, not a playable-area claim")
    else:
        print("BLOCKED PC-12: bounded source continuation stopped via"
              f" {obj['stop_reason']} at PC=${obj['stop_pc']};"
              " no original collision caller reached; gameplay unverified")
    print("PASS PC-12 observer: provenance-shaped bounded JSON,"
          " mapped bank1 event qualification, zero injected input")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("report",type=pathlib.Path)
    args=p.parse_args()
    check(args.report)


if __name__=="__main__":
    try:
        main()
    except (OSError,ValueError,AssertionError,TypeError,KeyError) as exc:
        sys.exit("FAIL PC-12 source observation: "+str(exc))
