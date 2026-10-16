#!/usr/bin/env python3
"""PC-27 verified observed source $0CD1 rising-edge logic + opt-in controller trial.

A user-like controller stimulus is imposed experimentally; any real source
branch observed is NOT independently validated against title/gameplay timing.
"""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
ROM_SHA="02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9"
ROWS={
 "00CBD":("0CBD","CD CE 0C","call $0CCE"),
 "00CC2":("0CC2","ED 7B 2E C0","ld sp,($C02E)"),
 "00CC6":("0CC6","3E 02","ld a,$02"),
 "00CC8":("0CC8","32 1F C0","ld ($C01F),a"),
 "00CCE":("0CCE","CD C5 0B","call $0BC5"),
 "00CD1":("0CD1","3A 1C C0","ld a,($C01C)"),
 "00CD4":("0CD4","E6 30","and $30"),
 "00CD6":("0CD6","20 EA","jr nz,$0CC2"),
}
def verify(rompath,reportpath):
    rom=rompath.read_bytes()
    assert len(rom)==262144 and hashlib.sha256(rom).hexdigest()==ROM_SHA
    lines=(ROOT/"Ys/phase5/code.lst").read_text(encoding="utf-8").splitlines()
    for at,(pc,raw,op) in ROWS.items():
        start=int(at,16)
        assert rom[start:start+len(bytes.fromhex(raw))]==bytes.fromhex(raw),(at,"bytes")
        expr=r"^"+at+r"\s+"+pc+r"\s+"+r"\s+".join(raw.split())+r"\s+"+re.escape(op)+r"\s*$"
        assert sum(bool(re.fullmatch(expr,line,re.I)) for line in lines)==1,(at,"listing")
    obj=json.loads(reportpath.read_text(encoding="utf-8"))
    keys={"schema","start_pc","start_selector","stop_reason",
          "continued_steps","stop_pc","stop_selector","stop_slot1",
          "stop_slot2","stop_irq","stop_vblank","arm_hits",
          "edge_check_hits","edge_bit4_hits","last_edge",
          "mode_write_hits","mode2_seen","pressed","released",
          "press_pc","release_pc","press_step","release_step",
          "mode2_step","port_dc","port_dd","input_reads_dc",
          "input_reads_dd","observed_collision_calls"}
    assert set(obj)==keys,set(obj)^keys
    assert obj["schema"]=="ys-pc27-original-button-probe-v1"
    assert obj["start_pc"]=="0C92" and obj["start_selector"]==1
    assert obj["stop_reason"] in (
      "budget","unsupported","vblank_limit","mode2_after_release",
      "collision_observed")
    assert type(obj["continued_steps"]) is int
    assert 0<=obj["continued_steps"]<=150000
    assert len(obj["stop_pc"])==4
    int(obj["stop_pc"],16)
    for k in keys-{"schema","start_pc","stop_reason","stop_pc",
                    "mode2_seen","pressed","released","press_pc","release_pc"}:
        assert type(obj[k]) is int and obj[k]>=0,k
    for k in ("mode2_seen","pressed","released"):
        assert type(obj[k]) is bool,k
    assert obj["press_pc"]==obj["release_pc"]=="0773"
    assert obj["port_dd"]==255
    assert obj["port_dc"]==(255 if obj["released"] or not obj["pressed"] else 239)
    assert obj["stop_slot1"]<16 and obj["stop_slot2"]<16
    assert obj["stop_selector"]<=255 and obj["last_edge"]<=255
    assert obj["edge_bit4_hits"]<=obj["edge_check_hits"]
    assert obj["mode_write_hits"]>0 if obj["mode2_seen"] else True
    assert obj["press_step"]>0 if obj["pressed"] else obj["press_step"]==0
    assert obj["arm_hits"]>0 if obj["pressed"] else True
    if obj["released"]:
        assert obj["pressed"] and obj["release_step"]>obj["press_step"]
    if obj["mode2_seen"]:
        assert obj["mode2_step"]>=obj["press_step"]
        assert obj["mode_write_hits"]>0
    if obj["stop_reason"]=="mode2_after_release":
        assert obj["released"] and obj["mode2_seen"] and obj["stop_selector"]==2
    if obj["stop_reason"]=="collision_observed":
        assert obj["observed_collision_calls"]>0
    print("PASS PC-27: original bank0 wait-loop, input edge branch and"
          " selector store independently matched source ROM")
    print("PC-27 experimental controller result: reason={stop_reason}"
          " steps={continued_steps} mode={start_selector}->{stop_selector}"
          " armed_wait={arm_hits} pressed={pressed} released={released}"
          " checked_edges={edge_check_hits} bit4_checks={edge_bit4_hits}"
          " mode2_seen={mode2_seen} collisions={observed_collision_calls}"
          .format(**obj))
if __name__=="__main__":
    try:
        if len(sys.argv)!=3: raise ValueError(
            "usage: verify_pc27_button_probe.py SOURCE.sms REPORT.json")
        verify(Path(sys.argv[1]),Path(sys.argv[2]))
    except (AssertionError,OSError,ValueError,TypeError,KeyError) as exc:
        sys.exit("FAIL PC-27 source-arm probe: "+str(exc))
