#!/usr/bin/env python3
"""Original Ys PC-42 source run after byte-accurate Z80 refresh M1 support."""
import json
from pathlib import Path
import sys
from verify_pc40_route import verify

def check(rom,source_path,route_path,pc34):
    verify(rom,source_path,route_path,pc34,milestone="pc42")
    source=json.loads(Path(source_path).read_text(encoding="utf-8"))
    route=json.loads(Path(route_path).read_text(encoding="utf-8"))
    assert Path(rom).read_bytes()[0x141A:0x141E]==bytes.fromhex("ED 5F E6 0F")
    assert Path(rom).read_bytes()[0x13F5:0x13F7]==bytes.fromhex("EE 80")
    assert Path(rom).read_bytes()[0x1A77]==0x3F
    # Golden measured in passing original ROM-backed native CI
    # 38961300656. Any new interpreter semantics must preserve the
    # entire trace, not just reach the budget with plausible counters.
    state=(route["continued_steps"],route["stop_reason"],
           route["stop_pc"],route["stop_irq"],route["stop_vblank"],
           route["stop_slot1"],route["stop_slot2"],route["stop_selector"])
    assert state==(600000,"budget","0046",144,148,1,6,6),state
    assert source["observed_collision_calls"]==0
    assert source["sprite_counts"]==[0,0,0,0,52]
    expected_sites={(1,"26B6",0):1,(1,"9966",6):13,(1,"4773",1):13}
    for site in route["events"]:
        assert site["hits"]==expected_sites.get(
            (site["phase"],site["pc"],site["bank"]),0),site
    print("PASS PC-42 original source golden: 600000 budget PC=$0046,"
          " IRQ=144 VBlank=148, slot2=6, mapped $9966=13,"
          " mapped $4773=13, SAT entry sites=52, collisions=0")
    for site in route["events"]:
        if site["hits"]:
            print("  bank=%d PC=$%s phase=%d hits=%d" % (
                site["bank"],site["pc"],site["phase"],site["hits"]))

if __name__=="__main__":
    try:
        if len(sys.argv)!=5:
            raise ValueError("usage: verify_pc42_route.py SOURCE.sms SOURCE.json ROUTE.json PC34.json")
        check(*sys.argv[1:])
    except (AssertionError,TypeError,KeyError,ValueError,OSError) as ex:
        sys.exit("FAIL PC-42 original refresh route: "+str(ex))
