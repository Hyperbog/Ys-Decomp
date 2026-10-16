#!/usr/bin/env python3
"""PC-33 separate continuation after original $0773 controller release.

Validates genuine unmodified source execution and input-event provenance;
does NOT independently prove original gameplay or native controls.
"""
import json
from pathlib import Path
import sys

FIELDS={
 "schema","start_pc","start_selector","stop_reason","continued_steps",
 "stop_pc","stop_selector","stop_slot1","stop_slot2","stop_irq","stop_vblank",
 "arm_hits","edge_check_hits","edge_bit4_hits","last_edge",
 "mode_write_hits","mode2_seen","pressed","released",
 "press_pc","release_pc","press_step","release_step","mode2_step",
 "port_dc","port_dd","input_reads_dc","input_reads_dd",
 "observed_collision_calls","release_sampled","sprite_counts"
}
def check(path):
    value=json.loads(path.read_text(encoding="utf-8"))
    assert set(value)==FIELDS,sorted(set(value)^FIELDS)
    assert value["schema"]=="ys-pc33-postrelease-source-watch-v1"
    assert value["start_pc"]=="0C92"
    assert value["start_selector"]==1
    assert value["stop_reason"] in (
       "budget","vblank_limit","unsupported","collision_observed")
    assert type(value["continued_steps"]) is int
    assert 96281<value["continued_steps"]<=150000
    assert type(value["stop_pc"]) is str and len(value["stop_pc"])==4
    int(value["stop_pc"],16)
    for key in FIELDS-{
        "schema","start_pc","stop_reason","stop_pc","mode2_seen",
        "pressed","released","release_sampled","sprite_counts",
        "press_pc","release_pc"}:
        assert type(value[key]) is int and value[key]>=0,key
    for key in ("mode2_seen","pressed","released","release_sampled"):
        assert type(value[key]) is bool and value[key],key
    assert isinstance(value["sprite_counts"],list) and len(value["sprite_counts"])==5
    assert all(type(n) is int and 0<=n<=value["continued_steps"]
               for n in value["sprite_counts"])
    assert value["press_pc"]=="0773" and value["release_pc"]=="0773"
    assert value["press_step"]>0 and value["release_step"]>value["press_step"]
    # DO NOT compare post-M45 continued_steps with absolute cpu.steps.
    # The explicit release_sampled flag is set only AFTER the source
    # Z80 executed the authentic release port IN at $0773.
    assert value["arm_hits"]>0 and value["edge_bit4_hits"]>0
    assert value["mode_write_hits"]>0 and value["stop_selector"]>=0
    assert value["mode2_step"]>=value["press_step"]
    assert value["stop_slot1"]<16 and value["stop_slot2"]<16
    assert value["port_dc"]==255 and value["port_dd"]==255
    assert value["input_reads_dc"]>=2
    if value["stop_reason"]=="collision_observed":
        assert value["observed_collision_calls"]>0
    print("PASS PC-33: independent post-release controller source watch,"
          " real original $0773 input sample executed")
    print("PC-33 result: reason={stop_reason} steps={continued_steps}"
          " PC=${stop_pc} mode={start_selector}->{stop_selector}"
          " release_step={release_step} readsDC={input_reads_dc}"
          " IRQ={stop_irq} VBlank={stop_vblank}"
          " collision_calls={observed_collision_calls}"
          " sprite_counts={sprite_counts}"
          .format(**value))

if __name__=="__main__":
    try:
        if len(sys.argv)!=2:
            raise ValueError("usage: verify_pc33_postrelease_watch.py WATCH.json")
        check(Path(sys.argv[1]))
    except (OSError,ValueError,AssertionError,KeyError,TypeError) as err:
        sys.exit("FAIL PC-33 original post-release watch: "+str(err))
