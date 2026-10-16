#!/usr/bin/env python3
"""Validate original bank-0 input source bytes and passive PC-26 audit.

Observations are from the same unpressed original-ROM run as PC-25,
not a simulated gameplay scene or fabricated button transition.
"""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
DIGEST="02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9"
ROWS={
 "00126":("0126","3A 1F C0","ld a,($C01F)"),
 "0012D":("012D","CD 73 07","call $0773"),
 "00138":("0138","DB DD","in a,($DD)"),
 "00773":("0773","DB DC","in a,($DC)"),
 "0077D":("077D","70","ld (hl),b"),
 "00780":("0780","77","ld (hl),a"),
}
SITES=("0126","012D","0773","077D","0780","0138")
FIELDS={"schema","start_pc","stop_reason","continued_steps","samples",
 "stop_pc","stop_slot1","stop_slot2","stop_irq","stop_vblank",
 "input_dc","input_dd","reads_dc","reads_dd",
 "initial_selector","last_selector","initial_pressed","initial_edges",
 "last_pressed","last_edges","selector_changes","nonzero_pressed_samples",
 "nonzero_edge_samples","vram_writes","cram_writes","display_reg1","sites"}

def check_source(path):
    rom=path.read_bytes()
    assert len(rom)==262144 and hashlib.sha256(rom).hexdigest()==DIGEST
    lines=(ROOT/"Ys/phase2/code.lst").read_text(encoding="utf-8").splitlines()
    for addr,(pc,raw,mnemonic) in ROWS.items():
        at=int(addr,16)
        blob=bytes.fromhex(raw)
        assert rom[at:at+len(blob)]==blob,(addr,"bytes")
        expr=r"^"+addr+r"\s+"+pc+r"\s+"+r"\s+".join(raw.split())+r"\s+"+re.escape(mnemonic)+r"\s*$"
        assert sum(bool(re.fullmatch(expr,row,re.I)) for row in lines)==1,(addr,"listing")

def check_report(path):
    o=json.loads(path.read_text(encoding="utf-8"))
    assert set(o)==FIELDS,(set(o)^FIELDS)
    assert o["schema"]=="ys-pc26-original-input-audit-v1"
    assert o["start_pc"]=="0C92"
    assert o["stop_reason"] in ("budget","vblank_limit","observed","unsupported")
    assert type(o["continued_steps"]) is int and 0<=o["continued_steps"]<=300000
    assert type(o["samples"]) is int and o["samples"] in (o["continued_steps"],o["continued_steps"]+1)
    assert type(o["stop_pc"]) is str and len(o["stop_pc"])==4
    int(o["stop_pc"],16)
    for key in FIELDS-{"schema","start_pc","stop_pc","stop_reason","sites"}:
        assert type(o[key]) is int and o[key]>=0,key
    assert o["input_dc"]==255 and o["input_dd"]==255
    assert o["stop_slot1"]<16 and o["stop_slot2"]<16
    for key in ("initial_selector","last_selector","initial_pressed",
                "initial_edges","last_pressed","last_edges","display_reg1"):
        assert o[key]<=255,key
    for key in ("selector_changes","nonzero_pressed_samples","nonzero_edge_samples"):
        assert o[key]<=o["samples"],key
    assert isinstance(o["sites"],list) and len(o["sites"])==len(SITES)
    assert tuple(e["pc"] for e in o["sites"])==SITES
    seen=0
    for entry in o["sites"]:
        assert set(entry)=={"pc","count","first_step","last_step",
                            "first_selector","last_selector","last_pressed","last_edges"}
        for name in set(entry)-{"pc"}:
            assert type(entry[name]) is int and entry[name]>=0,name
        assert entry["first_selector"]<=255 and entry["last_selector"]<=255
        assert entry["last_pressed"]<=255 and entry["last_edges"]<=255
        assert entry["count"]<=o["samples"]
        if entry["count"]:
            assert entry["first_step"]<=entry["last_step"]
        seen+=entry["count"]
    assert seen<=o["samples"]
    print("PASS PC-26: input audit validates authentic Phase2 port/DC, DD"
          " and WRAM dispatch opcodes against original ROM")
    print("PC-26 measured input: reason={stop_reason} steps={continued_steps} "
          "read_dc={reads_dc} read_dd={reads_dd} sampler={sampler} "
          "C01F_first={initial_selector} C01F_last={last_selector} "
          "selector_changes={selector_changes} pressed_samples={nonzero_pressed_samples} "
          "edges_samples={nonzero_edge_samples}".format(
             **o,sampler=o["sites"][2]["count"]))

if __name__=="__main__":
    try:
        if len(sys.argv)!=3:
            raise ValueError("usage: verify_pc26_input_audit.py SOURCE.sms AUDIT.json")
        check_source(Path(sys.argv[1]))
        check_report(Path(sys.argv[2]))
    except (OSError,ValueError,AssertionError,TypeError,KeyError) as exc:
        sys.exit("FAIL PC-26 source input audit: "+str(exc))
