#!/usr/bin/env python3
"""PC-44: physical C198 original-ROM WRAM store provenance.

Includes an independent original ROM/PC43 gate verifier and validates
both real CPU-write phases. Never treats an unchanged sample as a store.
"""
import json
from pathlib import Path
import sys

from verify_pc43_sprite_gate import check as check_pc43

SCHEMA="ys-pc44-physical-c198-writes-v1"
KEYS={"schema","stop_reason","continued_steps","final_pc",
      "final_value","count","phase_counts","same","changed",
      "aliases","events"}
EVENT_KEYS={"phase","iteration","cpu_step","logical","physical",
            "pc","bank","before","after","a","f","selector",
            "slot2","irq"}

def strict(path):
    def no_duplicates(pairs):
        d={}
        for k,v in pairs:
            if k in d: raise ValueError("duplicate key: "+k)
            d[k]=v
        return d
    return json.loads(Path(path).read_text(encoding="utf-8"),
                      object_pairs_hook=no_duplicates)

def nat(value,maximum=None):
    assert type(value) is int and value>=0
    if maximum is not None: assert value<=maximum

def check(rom,source_path,route_path,gate_path,write_path,pc34):
    check_pc43(rom,source_path,route_path,gate_path,pc34)
    raw=Path(rom).read_bytes()  # original SHA checked inside check_pc43
    listing=(Path(__file__).resolve().parents[2]/
             "Ys/phase6/code.lst").read_text(encoding="utf-8")
    for pc in (0x2041,0x2281):
        assert raw[pc:pc+3]==bytes.fromhex("32 98 C1"),hex(pc)
        assert len([row for row in listing.splitlines()
                    if row.startswith("%05X %04X  32 98 C1" % (pc,pc))
                    and "ld ($C198),a" in row])==1,hex(pc)
    source=strict(source_path)
    gate=strict(gate_path)
    w=strict(write_path)
    assert type(w) is dict and set(w)==KEYS
    assert w["schema"]==SCHEMA and w["stop_reason"]=="budget"
    assert w["continued_steps"]==source["continued_steps"]==600000
    assert w["final_pc"]==source["stop_pc"]=="0046"
    assert type(w["events"]) is list
    nat(w["count"],256)
    assert len(w["events"])==w["count"]
    for k in ("final_value",):
        nat(w[k],255)
    for k in ("phase_counts","same","changed","aliases"):
        assert type(w[k]) is list and len(w[k])==2
        for value in w[k]:nat(value,256)
    assert sum(w["phase_counts"])==w["count"]
    for p in range(2):
        assert w["phase_counts"][p]==w["same"][p]+w["changed"][p]
        assert w["aliases"][p]<=w["phase_counts"][p]
    derived=[[0,0,0,0] for _ in range(2)]
    last_value=0
    last_step=-1
    last_iteration=-1
    phase=0
    known_sites={"00B4":"clear RAM LDIR", "2041":"increment original state",
                 "2281":"clear original state"}
    for e in w["events"]:
        assert type(e) is dict and set(e)==EVENT_KEYS
        for k in ("phase","iteration","cpu_step","bank","before",
                  "after","a","f","selector","slot2","irq"):
            nat(e[k])
        assert e["phase"] in (0,1)
        assert e["phase"]>=phase
        if e["phase"]!=phase:
            phase=e["phase"]
            last_iteration=-1
        assert e["cpu_step"]>=last_step
        last_step=e["cpu_step"]
        if phase==0: assert e["iteration"]==0
        else:
            assert last_iteration<=e["iteration"]<600000
            last_iteration=e["iteration"]
        assert type(e["pc"]) is str and len(e["pc"])==4
        assert type(e["logical"]) is str and len(e["logical"])==4
        assert e["physical"]=="0198"
        assert e["logical"] in ("C198","E198")
        assert e["bank"] in (*range(16),254,255)
        assert e["irq"] in (0,1)
        for k in ("before","after","a","f","selector","slot2"):
            nat(e[k],255)
        # Because the hook observes every *successful physical WRAM*
        # store, the before byte must equal the previous after byte.
        assert e["before"]==last_value,(e,last_value)
        last_value=e["after"]
        derived[phase][0]+=1
        derived[phase][1]+=int(e["before"]==e["after"])
        derived[phase][2]+=int(e["before"]!=e["after"])
        derived[phase][3]+=int(e["logical"]=="E198")
        if e["pc"] in ("2041","2281"):
            assert e["bank"]==0 and e["irq"]==0
            assert e["logical"]=="C198"
            assert e["after"]==e["a"]
    assert last_value==w["final_value"]
    for p in (0,1):
        assert derived[p]==[w["phase_counts"][p],w["same"][p],
                             w["changed"][p],w["aliases"][p]]
    # Every original PC43 physically-mapped gate can see the most
    # recent completed WRAM writer, including reset/M45 and no-op
    # stores. This demands physical state, not a fabricated shortcut.
    latest=0
    for gate_event in gate["events"]:
        t=gate_event["entry_iteration"]
        for e in w["events"]:
            if e["phase"]==1 and e["iteration"]>=t:break
            latest=e["after"]
        assert latest==gate_event["c198_entry"],(t,latest,gate_event)
        assert gate_event["c198_entry"]==gate_event["c198_gate"]==0
    print("PASS PC-44 source physical C198 writes: reset=%d post=%d"
          " same=%s changed=%s aliases=%s final=%d" % (
          w["phase_counts"][0],w["phase_counts"][1],w["same"],
          w["changed"],w["aliases"],w["final_value"]))
    for e in w["events"]:
        print("  phase=%d iteration=%d cpu_step=%d pc=$%s bank=%d"
              " logical=$%s before=%d after=%d A=%d irq=%d" % (
               e["phase"],e["iteration"],e["cpu_step"],e["pc"],
               e["bank"],e["logical"],e["before"],e["after"],
               e["a"],e["irq"]))

if __name__=="__main__":
    try:
        if len(sys.argv)!=7:
            raise ValueError("usage: verify_pc44_c198_writes.py ORIGINAL.sms "
                "SOURCE.json ROUTE.json GATE.json WRITES.json PC34.json")
        check(*sys.argv[1:])
    except (ValueError,AssertionError,KeyError,TypeError,OSError) as err:
        sys.exit("FAIL PC-44 original C198 provenance: "+str(err))
