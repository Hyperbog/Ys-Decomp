#!/usr/bin/env python3
"""PC-41: strict exact original ROM continuation golden and PC40 prefix.

CPU/IRQ/mapper and sprite-site history through 525358 is checked
on each pre-instruction source step by ys_pc41_historical_checkpoint.
This verifier pins the *next natural stop* and mapped route sites.
"""
import json
from pathlib import Path
import sys

from verify_pc40_route import verify

PC41_GOLDEN=(531478,"unsupported","141A",133,137,1,7,6)
PC41_SITES={(1,"26B6",0):1,(1,"9966",6):1,(1,"4773",1):2}

def check(rom_path,source_json,route_json,pc34_json):
    # This performs its own independent ROM SHA verification and the
    # exact source-only PC34 300000-iteration checkpoint cross-check.
    verify(rom_path,source_json,route_json,pc34_json,milestone="pc41")
    # Natural NEXT blocker after indexed SET: $141A ED 5F = LD A,R,
    # immediately followed by E6 0F. Do NOT approximate R as zero.
    raw=Path(rom_path).read_bytes()
    assert raw[0x141A:0x141E]==bytes.fromhex("ED 5F E6 0F")

    source=json.loads(Path(source_json).read_text(encoding="utf-8"))
    route=json.loads(Path(route_json).read_text(encoding="utf-8"))
    observed=(route["continued_steps"],route["stop_reason"],route["stop_pc"],
              route["stop_irq"],route["stop_vblank"],route["stop_slot1"],
              route["stop_slot2"],route["stop_selector"])
    assert observed==PC41_GOLDEN,(observed,PC41_GOLDEN)
    assert source["observed_collision_calls"]==0
    assert source["sprite_counts"]==[0,0,0,0,41]
    for entry in route["events"]:
        expected=PC41_SITES.get((entry["phase"],entry["pc"],
                                  entry["bank"]),0)
        # Index by exact validated source PC and physical bank, not
        # by inferred traversal order or CPU PC without mapper.
        assert entry["hits"]==expected,(entry,expected)
    print("PASS PC-41 golden: source=531478 steps, unsupported $141A,"
          " IRQ=133 VBlank=137; bank6 $9966=1, bank1 $4773=2,"
          " bank0 $26B6=1, SAT entry sites=41, collisions=0")

if __name__=="__main__":
    try:
        if len(sys.argv)!=5:
            raise ValueError("usage: verify_pc41_route.py SOURCE.sms "
                             "PC41-source.json PC41-route.json PC34.json")
        check(*sys.argv[1:])
    except (AssertionError,ValueError,KeyError,TypeError,OSError) as error:
        sys.exit("FAIL PC-41 source route: "+str(error))
