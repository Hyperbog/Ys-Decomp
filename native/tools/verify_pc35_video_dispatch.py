#!/usr/bin/env python3
"""PC-35 read-only VDP/dispatch audit on the unchanged PC-34 source run.

Observes actual Z80 output and VDP write counters, not a game scene.
"""
import json
from pathlib import Path
import sys

FIELDS={"schema","source","continued_steps","stop_reason","stop_pc",
"stop_irq","stop_vblank","release_sampled","mode2_seen",
"selector_transitions","first_selector2_step","stop_selector",
"display_transitions","display_enabled_samples","first_display_step",
"display_enabled_final","vram_writes_delta","cram_writes_delta",
"slot2_transitions","slot2_final","sprite_upload0427_hits",
"bank6_sprite9932_hits","collision_calls"}

def validate(video,source):
    v=json.loads(Path(video).read_text(encoding="utf-8"))
    s=json.loads(Path(source).read_text(encoding="utf-8"))
    assert set(v)==FIELDS, set(v)^FIELDS
    assert v["schema"]=="ys-pc35-source-video-dispatch-v1"
    assert v["source"]=="pc34-same-run"
    assert s["schema"]=="ys-pc34-extended-postrelease-source-watch-v1"
    for field in ("continued_steps","stop_reason","stop_pc","stop_irq","stop_vblank"):
        assert v[field]==s[field],field
    assert v["stop_selector"]==s["stop_selector"]
    assert v["slot2_final"]==s["stop_slot2"]
    assert v["release_sampled"]==s["release_sampled"]
    assert v["mode2_seen"]==s["mode2_seen"]
    assert v["sprite_upload0427_hits"]==s["sprite_counts"][4]
    assert v["bank6_sprite9932_hits"]==s["sprite_counts"][3]
    assert v["collision_calls"]==s["observed_collision_calls"]
    for field in FIELDS-{"schema","source","stop_reason","stop_pc",
                         "release_sampled","mode2_seen","display_enabled_final"}:
        assert type(v[field]) is int and v[field]>=0,field
    for field in ("release_sampled","mode2_seen","display_enabled_final"):
        assert type(v[field]) is bool,field
    assert 150000<=v["continued_steps"]<=300000
    assert v["selector_transitions"]>=1 and v["first_selector2_step"]>0
    assert v["first_selector2_step"]<=v["continued_steps"]+600000
    assert v["display_enabled_samples"]<=v["continued_steps"]
    assert v["display_transitions"]<=v["continued_steps"]
    assert v["slot2_transitions"]<=v["continued_steps"]
    assert v["first_display_step"]>0 if v["display_enabled_samples"] else v["first_display_step"]==0
    assert 0<=v["slot2_final"]<16
    print("PASS PC-35: video/selector counters agree with original PC-34 same-run source watcher")
    print("PC-35 source-only measurements: display_active_samples={display_enabled_samples}"
          " display_transitions={display_transitions}"
          " vram_delta={vram_writes_delta} cram_delta={cram_writes_delta}"
          " selector_transitions={selector_transitions}"
          " slot2_transitions={slot2_transitions}"
          " sprite_uploads={sprite_upload0427_hits}"
          " bank6_producer={bank6_sprite9932_hits}"
          " original_collisions={collision_calls}".format(**v))

if __name__=="__main__":
    try:
        if len(sys.argv)!=3:
            raise ValueError("usage: verify_pc35_video_dispatch.py VIDEO.json PC34.json")
        validate(sys.argv[1],sys.argv[2])
    except (ValueError,AssertionError,OSError,TypeError,KeyError) as e:
        sys.exit("FAIL PC-35 video source audit: "+str(e))
