#!/usr/bin/env python3
"""PC-15 verify mapper-qualified actual-source sprite watch semantics.

No observed event or unsupported CPU instruction must ever be treated
as an authentic Ys active player/scene/sprite selection.
"""
import argparse
import json
from pathlib import Path
import sys

PCS=("26F3","26F5","2704","9932","0427")
RAW8=("slot1","slot2","bank_select2","mapper_control",
      "c199","c210","c211","c100","reg0","reg1","reg5","reg6")
RAW16=("dd00","dd40","ix")
RAW64=("vram_writes","cram_writes","steps","irqs","vblanks")

def check(path):
    data=json.loads(path.read_text(encoding="utf-8"))
    assert data["schema"]=="ys-pc15-original-sprite-watch-v1"
    assert data["start_pc"]=="0C92"
    assert data["stop_reason"] in ("budget","vblank_limit","unsupported","observed")
    assert type(data["continued_steps"]) is int
    assert 0<=data["continued_steps"]<=150000
    assert isinstance(data["stop_pc"],str) and len(data["stop_pc"])==4
    int(data["stop_pc"],16)
    assert type(data["stop_slot2"]) is int and 0<=data["stop_slot2"]<=255
    for key in ("stop_irqs","stop_vblanks"):
        assert type(data[key]) is int and data[key]>=0
    rows=data["events"]
    assert isinstance(rows,list) and len(rows)==len(PCS)
    assert tuple(row["pc"] for row in rows)==PCS
    for row in rows:
        assert type(row["seen"]) is bool
        assert type(row["count"]) is int and row["count"]>=0
        assert row["seen"]==(row["count"]>0)
        for name in RAW8:
            assert type(row[name]) is int and 0<=row[name]<=255,name
        for name in RAW16:
            assert type(row[name]) is int and 0<=row[name]<=65535,name
        for name in RAW64:
            assert type(row[name]) is int and row[name]>=0,name
        assert type(row["display_enabled"]) is bool
        if row["seen"]:
            assert row["vblanks"]<=data["stop_vblanks"]
            assert row["steps"]>=0
        if row["pc"]=="9932" and row["seen"]:
            assert row["slot2"]==6
    if rows[3]["seen"]:
        assert data["stop_reason"]=="observed"
        print("OBSERVED PC-15: real original bank6 $9932 entry;",
              "selector/origins and VDP state recorded, player ID unverified")
    else:
        assert data["stop_reason"]!="observed"
        print("BLOCKED PC-15: no mapped original sprite producer"
              " observed within bounded source CPU execution;",
              " unsupported/budget is not a game-state conclusion")
    print("PASS PC-15 bounded sprite watch:",
          "reason="+data["stop_reason"],
          "steps="+str(data["continued_steps"]),
          "PC=$"+data["stop_pc"],
          "C199="+str(rows[3]["c199"]) if rows[3]["seen"] else
          "C199=UNOBSERVED")

if __name__=="__main__":
    try:
        ap=argparse.ArgumentParser(description=__doc__)
        ap.add_argument("report",type=Path)
        check(ap.parse_args().report)
    except (OSError,ValueError,AssertionError,KeyError,TypeError) as exc:
        sys.exit("FAIL PC-15 sprite watch: "+str(exc))
