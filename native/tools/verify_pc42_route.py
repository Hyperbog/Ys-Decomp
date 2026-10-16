#!/usr/bin/env python3
"""PC-42: original source-ROM 600k continuation through real LD A,R.

Independently verifies the exact PC-34 prefix, source ROM SHA, strict
mapper-qualified site schema, and the boundary beyond original PC41.
The C11 source-run asserts the full prior PC41 531478-step checkpoint.
"""
import json
from pathlib import Path
import sys
from verify_pc40_route import verify

def check(rom,source_path,route_path,pc34_path):
    verify(rom,source_path,route_path,pc34_path,milestone="pc41")
    original=Path(rom).read_bytes()
    assert original[0x141A:0x141E]==bytes.fromhex("ED 5F E6 0F")
    assert original[0x13F5:0x13F7]==bytes.fromhex("EE 80")
    assert original[0x1A77:0x1A79]==bytes.fromhex("3F 98")
    source=json.loads(Path(source_path).read_text(encoding="utf-8"))
    route=json.loads(Path(route_path).read_text(encoding="utf-8"))
    assert route["continued_steps"]>531478
    assert route["continued_steps"]<=600000
    assert route["events"][12]["hits"]>=1  # fixed bank0 $26B6
    assert route["events"][19]["hits"]>=1  # physical bank6 $9966
    assert route["events"][20]["hits"]>=2  # physical bank1 $4773
    assert source["sprite_counts"][4]>=41
    print("PASS PC-42: full original ROM, immutable PC34 prefix,"
          " prior mapped bank6 $9966 route and genuine LD A,R continuation")
    print("PC-42: steps=%d reason=%s pc=$%s IRQ=%d VBlank=%d"
          " bank6_9966=%d uploads_entry=%d" %
          (route["continued_steps"],route["stop_reason"],route["stop_pc"],
           route["stop_irq"],route["stop_vblank"],
           route["events"][19]["hits"],source["sprite_counts"][4]))

if __name__=="__main__":
    try:
        if len(sys.argv)!=5:
            raise ValueError("Usage: verify_pc42_route.py ORIGINAL.sms"
                             " SOURCE.json ROUTE.json PC34.json")
        check(*sys.argv[1:])
    except (AssertionError,ValueError,OSError,KeyError,TypeError) as e:
        sys.exit("FAIL PC-42 original refresh route: "+str(e))
