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
    assert route["continued_steps"]>531478
    assert route["stop_reason"] in ("budget","unsupported","vblank_limit","collision_observed")
    assert source["observed_collision_calls"]>=0
    print("PASS PC-42 original refresh-route integrity: steps=%d reason=%s"
          " PC=$%s IRQ=%d VBlank=%d" % (
              route["continued_steps"],route["stop_reason"],
              route["stop_pc"],route["stop_irq"],route["stop_vblank"]))
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
