#!/usr/bin/env python3
"""PC-39: independent accounting of real original Z80 SAT WRAM bus strobes.

The bus hook observes successful writes to physical WRAM, including
same-value writes and the FDxx mirror. This is native-interpreter
execution evidence, not independent hardware equivalence.
"""
import json
from pathlib import Path
import sys

FIELDS={"schema","source","continued_steps","stop_reason","stop_pc",
        "stop_irq","stop_vblank","site_count","phases","sites"}
PHASE_FIELDS={"name","count","same","changed","y","xt","alias","irq","unique"}
SITE_FIELDS={"phase","pc","bank","irq","count","same","first_step","last_step"}

def uint(n, maximum=None):
    assert type(n) is int and n>=0
    if maximum is not None:
        assert n<=maximum
    return n

def validate(output, pc34, pc36, pc37, pc38):
    a=json.loads(Path(output).read_text(encoding="utf-8"))
    old=[json.loads(Path(p).read_text(encoding="utf-8"))
         for p in (pc34,pc36,pc37,pc38)]
    assert type(a) is dict and set(a)==FIELDS
    assert a["schema"]=="ys-pc39-original-sat-wram-strobes-v1"
    assert a["source"]=="pc34-same-run"
    assert a["stop_reason"]=="budget"
    assert a["continued_steps"]==300000
    for key in ("continued_steps","stop_pc","stop_irq","stop_vblank"):
        assert all(a[key]==b[key] for b in old),key
    assert old[1]["entries"]==old[2]["captures"]==old[3]["upload_count"]==27
    uint(a["site_count"],512)
    assert type(a["phases"]) is list and len(a["phases"])==2
    assert type(a["sites"]) is list and len(a["sites"])==a["site_count"]
    totals=[0,0]
    same=[0,0]
    irq=[0,0]
    seen=set()
    for site in a["sites"]:
        assert type(site) is dict and set(site)==SITE_FIELDS
        assert type(site["pc"]) is str and len(site["pc"])==4
        pc=int(site["pc"],16)
        assert 0<=pc<=0xFFFF
        phase=uint(site["phase"],1)
        bank=uint(site["bank"],255)
        assert bank<16 or bank in (254,255)
        assert type(site["irq"]) is bool
        assert (site["pc"],bank,phase,site["irq"]) not in seen
        seen.add((site["pc"],bank,phase,site["irq"]))
        if site["irq"]:
            assert pc==0x0038 and bank==0
        count=uint(site["count"])
        assert count>0
        same_count=uint(site["same"],count)
        first=uint(site["first_step"])
        last=uint(site["last_step"])
        assert first<=last
        totals[phase]+=count
        same[phase]+=same_count
        if site["irq"]:
            irq[phase]+=count
    for p,phase in enumerate(a["phases"]):
        assert type(phase) is dict and set(phase)==PHASE_FIELDS
        assert phase["name"]==("pre-m45","post-m45")[p]
        for name in PHASE_FIELDS-{"name"}:
            uint(phase[name])
        assert phase["count"]==totals[p]
        assert phase["same"]==same[p]
        assert phase["irq"]==irq[p]
        assert phase["count"]==phase["same"]+phase["changed"]
        assert phase["count"]==phase["y"]+phase["xt"]
        assert phase["alias"]<=phase["count"]
        assert phase["unique"]<=192
        assert phase["unique"]<=phase["count"]
    assert old[3]["changed_bytes"]==0
    print("PASS PC-39: real WRAM bus strobes reconcile by opcode bank,"
          " same-value stores, IRQs and two source phases")
    for phase in a["phases"]:
        print("  %s: write-strobes=%d same=%d changed=%d "
              "Y=%d XT=%d mirror=%d IRQ=%d unique-offsets=%d" %
              (phase["name"],phase["count"],phase["same"],
               phase["changed"],phase["y"],phase["xt"],phase["alias"],
               phase["irq"],phase["unique"]))
    for site in sorted(a["sites"],key=lambda x:x["count"],reverse=True)[:10]:
        print("  source PC=$%s bank=%d phase=%d irq=%s stores=%d same=%d" %
              (site["pc"],site["bank"],site["phase"],site["irq"],
               site["count"],site["same"]))

if __name__=="__main__":
    try:
        if len(sys.argv)!=6:
            raise ValueError("usage: verify_pc39_sat_strobes.py "
                             "PC39.json PC34.json PC36.json PC37.json PC38.json")
        validate(*sys.argv[1:])
    except (AssertionError,ValueError,TypeError,OSError,KeyError) as err:
        sys.exit("FAIL PC-39 original SAT WRAM strobe audit: "+str(err))
