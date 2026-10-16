#!/usr/bin/env python3
"""PC-34 extended, opt-in 300k source-controller observation.

Uses the same source-armed one-sample button1 input and genuine release as
PC-27/33, but independently measures the following 150k source steps.
It cannot establish original-game Alpha without external emulator evidence.
"""
import json
from pathlib import Path
import sys

FIELDS={
 "schema","start_pc","start_selector","stop_reason","continued_steps",
 "stop_pc","stop_selector","stop_slot1","stop_slot2","stop_irq",
 "stop_vblank","arm_hits","edge_check_hits","edge_bit4_hits",
 "last_edge","mode_write_hits","mode2_seen","pressed","released",
 "press_pc","release_pc","press_step","release_step","mode2_step",
 "port_dc","port_dd","input_reads_dc","input_reads_dd",
 "observed_collision_calls","release_sampled","sprite_counts"
}
def check(path):
    obj=json.loads(path.read_text(encoding="utf-8"))
    assert set(obj)==FIELDS,(set(obj)^FIELDS)
    assert obj["schema"]=="ys-pc34-extended-postrelease-source-watch-v1"
    assert obj["start_pc"]=="0C92" and obj["start_selector"]==1
    assert obj["stop_reason"] in (
         "budget","vblank_limit","unsupported","collision_observed")
    assert type(obj["continued_steps"]) is int
    assert 150000<=obj["continued_steps"]<=300000
    assert type(obj["stop_pc"]) is str and len(obj["stop_pc"])==4
    int(obj["stop_pc"],16)
    for key in FIELDS-{
        "schema","start_pc","stop_reason","stop_pc","mode2_seen",
        "pressed","released","release_sampled","press_pc","release_pc",
        "sprite_counts"}:
        assert type(obj[key]) is int and obj[key]>=0,key
    for key in ("mode2_seen","pressed","released","release_sampled"):
        assert type(obj[key]) is bool and obj[key],key
    assert obj["press_pc"]==obj["release_pc"]=="0773"
    assert obj["press_step"]>0 and obj["release_step"]>obj["press_step"]
    # press/release steps are ABSOLUTE cpu.steps since reset, but
    # continued_steps is a DIFFERENT clock: post-M45 sample count.
    assert obj["arm_hits"]>=1 and obj["edge_bit4_hits"]>=1
    assert obj["mode_write_hits"]>=1 and obj["mode2_step"]>=obj["press_step"]
    assert obj["port_dc"]==255 and obj["port_dd"]==255
    assert obj["stop_slot1"]<16 and obj["stop_slot2"]<16
    assert obj["stop_selector"]<=255 and obj["last_edge"]<=255
    assert obj["input_reads_dc"]>=2
    assert isinstance(obj["sprite_counts"],list) and len(obj["sprite_counts"])==5
    assert all(type(count) is int and
               0<=count<=obj["continued_steps"] for count in obj["sprite_counts"])
    if obj["stop_reason"]=="collision_observed":
        assert obj["observed_collision_calls"]>0
    print("PASS PC-34: validated original Z80 post-release 300k research"
          " with independent source input/mapper sprite call monitoring")
    print("PC-34 original-source result: reason={stop_reason}"
          " steps={continued_steps} PC=${stop_pc}"
          " slot2={stop_slot2} IRQ={stop_irq} VBlank={stop_vblank}"
          " mode={start_selector}->{stop_selector}"
          " collision={observed_collision_calls}"
          " sprite_counts={sprite_counts}".format(**obj))
if __name__=="__main__":
    try:
        if len(sys.argv)!=2:
            raise ValueError("usage: verify_pc34_extended_postrelease.py WATCH.json")
        check(Path(sys.argv[1]))
    except (OSError,ValueError,AssertionError,KeyError,TypeError) as error:
        sys.exit("FAIL PC-34 extended source controller research: "+str(error))
