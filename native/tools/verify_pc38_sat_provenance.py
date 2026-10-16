#!/usr/bin/env python3
"""PC-38: validate passive visible SAT source buffer mutations.

Value differences between CPU instruction boundaries do not establish
which exact store occurred; same-value writes are invisible.
"""
import json
from pathlib import Path
import sys

FIELDS = {"schema", "source", "continued_steps", "stop_reason",
          "stop_pc", "stop_irq", "stop_vblank", "sampled_boundaries",
          "changed_bytes", "changed_y", "changed_xt", "unique_bytes",
          "upload_count", "changed_uploads", "equal_uploads",
          "upload_diff_bytes", "site_count", "sites"}

def validate(path, p34, p36, p37):
    a=json.loads(Path(path).read_text(encoding="utf-8"))
    others=[json.loads(Path(p).read_text(encoding="utf-8"))
            for p in (p34,p36,p37)]
    assert set(a)==FIELDS,set(a)^FIELDS
    assert a["schema"]=="ys-pc38-sat-wram-boundary-v1"
    assert a["source"]=="pc34-same-run"
    assert type(a["sites"]) is list
    for key in FIELDS-{"schema","source","stop_reason","stop_pc","sites"}:
        assert type(a[key]) is int and a[key]>=0,key
    assert a["continued_steps"]==300000
    assert a["sampled_boundaries"]==a["continued_steps"]
    for key in ("continued_steps","stop_pc","stop_irq","stop_vblank"):
        assert all(a[key]==v[key] for v in others),key
    assert a["stop_reason"]==others[0]["stop_reason"]==others[1]["stop_reason"]
    assert a["upload_count"]==others[1]["entries"]==others[2]["captures"]==27
    assert a["site_count"]==len(a["sites"])
    assert 0<=a["unique_bytes"]<=192
    assert a["changed_bytes"]==a["changed_y"]+a["changed_xt"]
    assert a["changed_uploads"]+a["equal_uploads"]==26
    assert 0<=a["upload_diff_bytes"]<=26*192
    # Golden original-cartridge result: 300k-step fixed PC-34 input schedule.
    # Structural self-consistency alone must not bless a changing trace.
    assert (a["changed_bytes"],a["changed_y"],a["changed_xt"],
            a["unique_bytes"],a["site_count"],a["changed_uploads"],
            a["equal_uploads"],a["upload_diff_bytes"]) == (0,0,0,0,0,0,26,0)
    assert others[1]["first_source_crc32"]==others[1]["last_source_crc32"]
    assert a["changed_bytes"]>=a["unique_bytes"]
    seen=set()
    summed=0
    for site in a["sites"]:
        assert type(site) is dict and set(site)=={"pc","physical_bank","changed_bytes"}
        assert type(site["pc"]) is str and len(site["pc"])==4
        pc=int(site["pc"],16)
        bank=site["physical_bank"]
        count=site["changed_bytes"]
        assert 0<=pc<=0xFFFF
        assert type(bank) is int and (0<=bank<16 or bank in (254,255))
        assert type(count) is int and count>0
        assert (pc,bank) not in seen
        seen.add((pc,bank))
        summed+=count
    assert summed==a["changed_bytes"]
    print("PASS PC-38: visible SAT changes match 27 original source uploads")
    print("PC-38: changes={changed_bytes}, y={changed_y}, "
          "xt={changed_xt}, unique={unique_bytes}, sites={site_count}, "
          "changed_uploads={changed_uploads}, equal_uploads={equal_uploads}"
          .format(**a))
    for site in sorted(a["sites"],key=lambda v:v["changed_bytes"],reverse=True)[:8]:
        print("  mapped boundary PC=%s bank=%d byte-changes=%d"
              %(site["pc"],site["physical_bank"],site["changed_bytes"]))

if __name__=="__main__":
    try:
        if len(sys.argv)!=5:
            raise ValueError("usage: verify_pc38_sat_provenance.py "
                             "PC38.json PC34.json PC36.json PC37.json")
        validate(*sys.argv[1:])
    except (AssertionError,ValueError,OSError,TypeError,KeyError) as error:
        sys.exit("FAIL PC-38 SAT source audit: "+str(error))
