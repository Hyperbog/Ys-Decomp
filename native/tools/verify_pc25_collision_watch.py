#!/usr/bin/env python3
"""PC-25 extended collision-only watch, without weakening PC-12's guard.

This opt-in original ROM execution stays passive and unpressed; no original
player/scene claim follows from absence or mere pre-call PC observation.
"""
import json
from pathlib import Path
import sys

PCS=("476C","4773","47C2","486C","48DF")
RAW=("mapper_slot1","mapper_slot2","raw_bank_select2","mapper_control",
     "ix","c100","c119","c181","c20d","c20e","c210","c211",
     "ix13","ix14","ix16","ix17")


def verify(path:Path):
    report=json.loads(path.read_text(encoding="utf-8"))
    assert report["schema"]=="ys-pc12-source-watch-v1"
    assert report["start_pc"]=="0C92"
    assert report["stop_reason"] in (
        "budget","vblank_limit","unsupported","halted","observed")
    steps=report["continued_steps"]
    assert type(steps) is int and 150000<=steps<=300000
    assert type(report["stop_pc"]) is str and len(report["stop_pc"])==4
    int(report["stop_pc"],16)
    assert type(report["stop_cpu_status"]) is int
    for key in ("stop_slot1","stop_slot2","stop_irq","stop_vblank",
                "observed_collision_calls"):
        assert type(report[key]) is int and report[key]>=0,key
    assert report["stop_slot1"]<16 and report["stop_slot2"]<16
    assert report["stop_vblank"]>=85 and report["stop_irq"]>=81
    rows=report["events"]
    assert len(rows)==5 and tuple(r["pc"] for r in rows)==PCS
    assert report["observed_collision_calls"]==sum(
        row["count"] for row in rows[2:])
    for row in rows:
        assert type(row["seen"]) is bool and type(row["count"]) is int
        assert row["count"]>=0 and row["seen"]==(row["count"]>0)
        for field in RAW:
            assert type(row[field]) is int,field
            if field=="ix": assert 0<=row[field]<=65535
            else: assert 0<=row[field]<=255
        for field in ("steps","irq","vblank"):
            assert type(row[field]) is int and row[field]>=0
        if row["seen"]:
            assert row["mapper_slot1"]==1
            assert row["steps"]>=0 and row["vblank"]<=report["stop_vblank"]
    if report["stop_reason"]=="observed":
        assert report["observed_collision_calls"]>0
        print("OBSERVED PC-25: original bank1 mapped collision CALL;"
              " pre-call state only, original player identity unverified")
    else:
        assert report["observed_collision_calls"]==0
        print("BLOCKED PC-25: extended bounded unpressed-input"
              " source continuation did not reach a collision CALL")
    print("PASS PC-25 extended original source watch:"
          f" reason={report['stop_reason']} steps={steps}"
          f" PC=${report['stop_pc']}"
          f" IRQ={report['stop_irq']} VBlank={report['stop_vblank']}")


if __name__=="__main__":
    try:
        if len(sys.argv)!=2:raise ValueError("usage: verify_pc25_collision_watch.py report.json")
        verify(Path(sys.argv[1]))
    except (OSError,ValueError,TypeError,KeyError,AssertionError) as exc:
        sys.exit("FAIL PC-25 extended original source watch: "+str(exc))
