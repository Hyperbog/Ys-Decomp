#!/usr/bin/env python3
"""Verify physical bank-6 C198 gate using original source ROM and PC42 oracle."""
import json
from pathlib import Path
import sys
from verify_pc42_route import check as check_pc42

SCHEMA="ys-pc43-original-bank6-c198-gate-v1"
FIELDS={"schema","source","continued_steps","stop_reason","stop_pc",
        "entries","or_hits","gate_hits","call_sites","producer_entries",
        "skip_targets","orphan_gates","branch_zero","branch_nonzero",
        "branch_mismatch","irq_gate","events"}
EVENT={"entry_iteration","gate_iteration","entry_cpu_step","gate_cpu_step",
       "slot2","selector","c198_entry","c199_entry","c1b9_entry",
       "c198_gate","a_gate","f_gate","iff2_gate","or_seen","gate_seen",
       "successor_seen","irq_during_gate","successor_pc",
       "irq_before","irq_after"}

def integer(value,bound=None):
    assert type(value) is int and value>=0,(value,bound)
    if bound is not None: assert value<=bound,value

def unique_json(path):
    def pairs(fields):
        d={}
        for key,val in fields:
            if key in d: raise ValueError("duplicate JSON key: "+key)
            d[key]=val
        return d
    return json.loads(Path(path).read_text(encoding="utf-8"),
                      object_pairs_hook=pairs)

def check(rom,source_path,route_path,gate_path,pc34):
    # Independent PC-42 full original ROM SHA/checkpoints/600k golden.
    check_pc42(rom,source_path,route_path,pc34)
    raw=Path(rom).read_bytes()
    bank6=6*0x4000
    # $9966: LD A,($C198); OR A; JR Z,$99C6; CALL $9932.
    assert raw[bank6+0x1966:bank6+0x196F]==bytes.fromhex(
        "3A 98 C1 B7 28 5A CD 32 99")
    source=(Path(__file__).resolve().parents[2]/
            "Ys/src/wholebank06/bank06_complete.asm").read_text(
                encoding="utf-8")
    assert source.count("    ld a,($C198)\n    or a\n"
                        "    jr z,$99C6\n    call $9932\n")==1
    route=unique_json(route_path)
    gate=unique_json(gate_path)
    assert type(gate) is dict and set(gate)==FIELDS
    assert gate["schema"]==SCHEMA
    assert gate["source"]=="pc42-600k-original-controller"
    assert gate["continued_steps"]==route["continued_steps"]==600000
    assert gate["stop_reason"]==route["stop_reason"]=="budget"
    assert gate["stop_pc"]==route["stop_pc"]=="0046"
    assert type(gate["events"]) is list
    for field in ("entries","or_hits","gate_hits","call_sites",
                  "producer_entries","skip_targets","orphan_gates",
                  "branch_zero","branch_nonzero","branch_mismatch",
                  "irq_gate"):
        integer(gate[field],600000)
    assert len(gate["events"])==gate["entries"]<=64
    assert gate["entries"]==route["events"][19]["hits"]  # phase1 bank6 $9966
    assert gate["producer_entries"]==route["events"][18]["hits"] # phase1 $9932
    assert gate["branch_zero"]+gate["branch_nonzero"]==gate["gate_hits"]-gate["orphan_gates"]
    assert gate["branch_mismatch"]<=gate["gate_hits"]
    assert gate["irq_gate"]<=gate["gate_hits"]
    earlier=-1
    for e in gate["events"]:
        assert type(e) is dict and set(e)==EVENT
        for key in ("entry_iteration","gate_iteration","entry_cpu_step",
                    "gate_cpu_step","slot2","selector","c198_entry",
                    "c199_entry","c1b9_entry","c198_gate","a_gate",
                    "f_gate","iff2_gate","irq_before","irq_after"):
            integer(e[key])
        for key in ("or_seen","gate_seen","successor_seen","irq_during_gate"):
            assert type(e[key]) is bool,(key,e[key])
        for key in ("c198_entry","c199_entry","c1b9_entry","selector",
                    "c198_gate","a_gate","f_gate"):
            integer(e[key],255)
        integer(e["slot2"],15)
        integer(e["iff2_gate"],1)
        assert e["slot2"]==6
        assert earlier<e["entry_iteration"]<600000
        earlier=e["entry_iteration"]
        assert type(e["successor_pc"]) is str and len(e["successor_pc"])==4
        int(e["successor_pc"],16)
        if e["gate_seen"]:
            assert e["entry_iteration"]<e["gate_iteration"]<600000
            assert e["entry_cpu_step"]<e["gate_cpu_step"]
            assert e["successor_seen"]
            assert e["irq_after"]>=e["irq_before"]
            assert e["irq_during_gate"]==(e["irq_after"]!=e["irq_before"])
            if not e["irq_during_gate"]:
                # This compares the CPU's ACTUAL post-step successor
                # with the Z80 branch decision captured BEFORE the JR.
                expected="99C6" if (e["f_gate"]&0x40) else "996C"
                assert e["successor_pc"]==expected,(e,expected)
    # PC-43 original-ROM CI 38966030340: independent source trace.
    # Source $9966 -> $9969 -> $996A -> actual successor $99C6,
    # on thirteen precise post-M45 continuation iterations.
    exact_entries=(526991,535842,539067,545367,551112,557033,
                   562765,569046,574795,580833,586432,592714,598479)
    assert gate["entries"]==gate["or_hits"]==gate["gate_hits"]==13
    assert gate["branch_zero"]==gate["skip_targets"]==13
    for key in ("branch_nonzero","call_sites","producer_entries",
                "orphan_gates","branch_mismatch","irq_gate"):
        assert gate[key]==0,(key,gate[key])
    assert tuple(e["entry_iteration"] for e in gate["events"])==exact_entries
    for e in gate["events"]:
        assert e["c198_entry"]==e["c198_gate"]==e["a_gate"]==0
        assert (e["f_gate"]&0x40)!=0
        assert e["or_seen"] and e["gate_seen"] and e["successor_seen"]
        assert not e["irq_during_gate"] and e["successor_pc"]=="99C6"
        assert e["irq_before"]==e["irq_after"]
    print("PASS PC-43 bank6 original $9966 C198 conditional:",
          "entries=%d gates=%d zero=%d nonzero=%d calls=%d producer=%d"
          " skips=%d" % (gate["entries"],gate["gate_hits"],
          gate["branch_zero"],gate["branch_nonzero"],
          gate["call_sites"],gate["producer_entries"],gate["skip_targets"]))
    for e in gate["events"]:
        print("  iteration=%d bank=%d C198=%d A=%d Z=%d JR->%s"
              " IRQchanged=%s" % (
            e["entry_iteration"],e["slot2"],e["c198_entry"],
            e["a_gate"],int((e["f_gate"]&0x40)!=0),
            e["successor_pc"],e["irq_during_gate"]))

if __name__=="__main__":
    try:
        if len(sys.argv)!=6:
            raise ValueError("usage: verify_pc43_sprite_gate.py ORIGINAL.sms "
                             "PC43-source.json PC43-route.json PC43-gate.json PC34.json")
        check(*sys.argv[1:])
    except (AssertionError,ValueError,KeyError,TypeError,OSError) as error:
        sys.exit("FAIL PC-43 original bank6 gate: "+str(error))
