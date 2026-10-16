#!/usr/bin/env python3
"""PC-39: independent accounting of real original Z80 SAT WRAM bus strobes.

The bus hook observes successful writes to physical WRAM, including
same-value writes and the FDxx mirror. This is native-interpreter
execution evidence, not independent hardware equivalence.
"""
import json
from pathlib import Path
import sys
import hashlib
import re

FIELDS={"schema","source","continued_steps","stop_reason","stop_pc",
        "stop_irq","stop_vblank","site_count","phases","sites"}
PHASE_FIELDS={"name","count","same","changed","y","xt","alias","irq","unique"}
SITE_FIELDS={"phase","pc","bank","irq","count","same","first_step","last_step"}

def uint(n, maximum=None):
    assert type(n) is int and n>=0
    if maximum is not None:
        assert n<=maximum
    return n

ROM_SHA="02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9"
ROOT=Path(__file__).resolve().parents[2]
def verify_original_opcodes(source):
    rom=Path(source).read_bytes()
    assert len(rom)==262144 and hashlib.sha256(rom).hexdigest()==ROM_SHA
    # Fixed-bank0 $00B4 LDIR: preceding HL=C010, DE=C011,
    # BC=1E4F, and LD (HL),00. It clears the broad WRAM arena,
    # including all 192 original SAT staging bytes.
    for pos,raw in ((0x00A9,"21 10 C0"),(0x00AC,"11 11 C0"),
                    (0x00AF,"01 4F 1E"),(0x00B2,"36 00"),
                    (0x00B4,"ED B0"),(0x0AA1,"32 00 DD")):
        expect=bytes.fromhex(raw)
        assert rom[pos:pos+len(expect)]==expect,(hex(pos),"original ROM")
    listing=(ROOT/"Ys/phase6/code.lst").read_text(encoding="utf-8")
    assert len(re.findall(r"^00AA1\s+0AA1\s+32\s+00\s+DD"
                          r"\s+ld \(\$DD00\),a\s*$",
                          listing,re.I|re.M))==1
    asm=(ROOT/"Ys/src/wholebank00/bank00_complete.asm").read_text(encoding="utf-8")
    assert asm.count("    ld hl,$C010\n    ld de,$C011\n"
                     "    ld bc,$1E4F\n    ld (hl),$00\n    ldir")==1

def validate(source, output, pc34, pc36, pc37, pc38):
    verify_original_opcodes(source)
    a=json.loads(Path(output).read_text(encoding="utf-8"))
    old=[json.loads(Path(p).read_text(encoding="utf-8"))
         for p in (pc34,pc36,pc37,pc38)]
    assert type(a) is dict and set(a)==FIELDS
    assert a["schema"]=="ys-pc39-original-sat-wram-strobes-v1"
    assert a["source"]=="pc34-same-run"
    assert a["stop_reason"]=="budget"
    assert a["continued_steps"]==300000
    for key in ("continued_steps","stop_pc","stop_irq","stop_vblank"):
        assert all(a[key]==b[key] for b in old),key
    assert old[1]["entries"]==old[2]["captures"]==old[3]["upload_count"]==27
    uint(a["site_count"],512)
    assert type(a["phases"]) is list and len(a["phases"])==2
    assert type(a["sites"]) is list and len(a["sites"])==a["site_count"]
    totals=[0,0]
    same=[0,0]
    irq=[0,0]
    seen=set()
    for site in a["sites"]:
        assert type(site) is dict and set(site)==SITE_FIELDS
        assert type(site["pc"]) is str and len(site["pc"])==4
        pc=int(site["pc"],16)
        assert 0<=pc<=0xFFFF
        phase=uint(site["phase"],1)
        bank=uint(site["bank"],255)
        assert bank<16 or bank in (254,255)
        assert type(site["irq"]) is bool
        assert (site["pc"],bank,phase,site["irq"]) not in seen
        seen.add((site["pc"],bank,phase,site["irq"]))
        if site["irq"]:
            assert pc==0x0038 and bank==0
        count=uint(site["count"])
        assert count>0
        same_count=uint(site["same"],count)
        first=uint(site["first_step"])
        last=uint(site["last_step"])
        assert first<=last
        totals[phase]+=count
        same[phase]+=same_count
        if site["irq"]:
            irq[phase]+=count
    for p,phase in enumerate(a["phases"]):
        assert type(phase) is dict and set(phase)==PHASE_FIELDS
        assert phase["name"]==("pre-m45","post-m45")[p]
        for name in PHASE_FIELDS-{"name"}:
            uint(phase[name])
        assert phase["count"]==totals[p]
        assert phase["same"]==same[p]
        assert phase["irq"]==irq[p]
        assert phase["count"]==phase["same"]+phase["changed"]
        assert phase["count"]==phase["y"]+phase["xt"]
        assert phase["alias"]<=phase["count"]
        assert phase["unique"]<=192
        assert phase["unique"]<=phase["count"]
    assert old[3]["changed_bytes"]==0
    # Golden from native ROM-backed source run 38855605003.
    # A self-consistent but modified audit must not pass silently.
    expected_phases=((193,192,1,65,128,0,0,192),
                     (1,1,0,1,0,0,0,1))
    keys=("count","same","changed","y","xt","alias","irq","unique")
    for p,expected in enumerate(expected_phases):
        assert tuple(a["phases"][p][k] for k in keys)==expected,p
    actual_sites=sorted((s["phase"],s["pc"],s["bank"],s["irq"],
                         s["count"],s["same"]) for s in a["sites"])
    expected_sites=sorted(((0,"00B4",0,False,192,192),
                           (0,"0AA1",0,False,1,0),
                           (1,"0AA1",0,False,1,1)))
    assert actual_sites==expected_sites,actual_sites
    print("PASS PC-39: real WRAM bus strobes reconcile by opcode bank,"
          " same-value stores, IRQs and two source phases")
    for phase in a["phases"]:
        print("  %s: write-strobes=%d same=%d changed=%d "
              "Y=%d XT=%d mirror=%d IRQ=%d unique-offsets=%d" %
              (phase["name"],phase["count"],phase["same"],
               phase["changed"],phase["y"],phase["xt"],phase["alias"],
               phase["irq"],phase["unique"]))
    for site in sorted(a["sites"],key=lambda x:x["count"],reverse=True)[:10]:
        print("  source PC=$%s bank=%d phase=%d irq=%s stores=%d same=%d" %
              (site["pc"],site["bank"],site["phase"],site["irq"],
               site["count"],site["same"]))

if __name__=="__main__":
    try:
        if len(sys.argv)!=7:
            raise ValueError("usage: verify_pc39_sat_strobes.py "
                             "SOURCE.sms PC39.json PC34.json PC36.json "
                             "PC37.json PC38.json")
        validate(*sys.argv[1:])
    except (AssertionError,ValueError,TypeError,OSError,KeyError) as err:
        sys.exit("FAIL PC-39 original SAT WRAM strobe audit: "+str(err))
