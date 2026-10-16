#!/usr/bin/env python3
"""PC-40 fixed-original-ROM 600k route run with an exact PC-34 prefix.

Source research, not original Ys gameplay. No invented events.
"""
import hashlib
import json
from pathlib import Path
import sys
import re

ORIGINAL_SHA="02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9"
PCS=("26B6","26DA","26F3","26F5","2704","2BF2",
     "9932","9966","4773","47C2","486C","48DF")
BANKS=(0,0,0,0,0,0,6,6,1,1,1,1)
FIELDS={"schema","source","continued_steps","stop_reason","stop_pc",
        "stop_irq","stop_vblank","stop_slot1","stop_slot2","stop_selector",
        "prefix_steps","prefix_pc","prefix_slot1","prefix_slot2",
        "prefix_selector","prefix_irq","prefix_vblank","prefix_collisions",
        "prefix_sprite","events"}
EVENT={"phase","pc","bank","hits","first_step","last_step",
       "first_selector","first_slot2"}

def number(value, upper=None):
    assert type(value) is int and value>=0,value
    if upper is not None: assert value<=upper,value

def verify(rom_path,source_json,route_json,pc34_json):
    rom=Path(rom_path).read_bytes()
    assert len(rom)==262144
    assert hashlib.sha256(rom).hexdigest()==ORIGINAL_SHA
    # Source-only fixed bank 0: actual failing NEG, following 16-bit SBC,
    # source selector gate and bank-6 producer call. Match physical bytes
    # AND existing independently committed Z80 listing mnemonics.
    source_rows=((0x267E,"ED 44","neg"),
                 (0x2693,"ED 52","sbc hl,de"),
                 (0x26C3,"ED 4B 10 C2","ld bc,($C210)"),
                 (0x2AFE,"ED A8","ldd"),
                 (0x2B4B,"ED A8","ldd"),
                 (0x26B6,"3A 98 C1","ld a,($C198)"),
                 (0x2704,"CD 32 99","call $9932"))
    listing=(Path(__file__).resolve().parents[2]/
             "Ys/phase6/code.lst").read_text(encoding="utf-8")
    for pc,hexbytes,mnemonic in source_rows:
        raw=bytes.fromhex(hexbytes)
        assert rom[pc:pc+len(raw)]==raw,hex(pc)
        pattern=(rf"^{pc:05X}\s+{pc:04X}\s+"+
                 r"\s+".join(hexbytes.split())+
                 r"\s+"+re.escape(mnemonic)+r"\s*$")
        assert len(re.findall(pattern,listing,re.I|re.M))==1,hex(pc)
    # Physical bank 2 is mapped into CPU $8000-$BFFF. The natural
    # PC-40 $87C6 stop was DD 35 09 = DEC (IX+9), not a bank-0 call.
    assert rom[2*0x4000+0x07C6:2*0x4000+0x07C9]==bytes.fromhex("DD 35 09")
    bank2=(Path(__file__).resolve().parents[2]/
           "Ys/src/wholebank02/bank02_complete.asm").read_text(encoding="utf-8")
    assert bank2.count("    dec (ix+9)")>=1
    # Physical bank1 maps CPU $4000-$7FFF. CB 3F at $61B1
    # naturally stopped the previous source experiment.
    assert rom[1*0x4000+0x21B1:1*0x4000+0x21B3]==bytes.fromhex("CB 3F")
    bank1=(Path(__file__).resolve().parents[2]/
           "Ys/src/wholebank01/bank01_complete.asm").read_text(encoding="utf-8")
    assert "    srl a" in bank1
    a=json.loads(Path(source_json).read_text(encoding="utf-8"))
    r=json.loads(Path(route_json).read_text(encoding="utf-8"))
    b=json.loads(Path(pc34_json).read_text(encoding="utf-8"))
    assert b["schema"]=="ys-pc34-extended-postrelease-source-watch-v1"
    assert a["schema"]=="ys-pc40-long-original-controller-v1"
    assert set(r)==FIELDS,set(r)^FIELDS
    assert r["schema"]=="ys-pc40-source-route-600k-v1"
    assert r["source"]=="pc34-controller-prefix"
    assert r["prefix_steps"]==b["continued_steps"]==300000
    assert 300000<=r["continued_steps"]<=600000
    assert r["continued_steps"]==a["continued_steps"]
    assert r["stop_reason"]==a["stop_reason"]
    assert r["stop_reason"] in {"budget","unsupported","vblank_limit",
                               "collision_observed"}
    if r["stop_reason"]=="budget":
        assert r["continued_steps"]==600000
    for k in ("stop_pc","stop_irq","stop_vblank","stop_slot1",
              "stop_slot2","stop_selector"):
        assert r[k]==a[k],k
    for k in ("stop_irq","stop_vblank"):
        number(r[k])
    for k in ("stop_slot1","stop_slot2"): number(r[k],15)
    number(r["stop_selector"],255)
    for suffix,original in (("pc","stop_pc"),("slot1","stop_slot1"),
                            ("slot2","stop_slot2"),
                            ("selector","stop_selector"),
                            ("irq","stop_irq"),("vblank","stop_vblank")):
        assert r["prefix_"+suffix]==b[original],suffix
    assert r["prefix_collisions"]==b["observed_collision_calls"]
    assert r["prefix_sprite"]==b["sprite_counts"]
    assert type(r["prefix_sprite"]) is list and len(r["prefix_sprite"])==5
    for val in r["prefix_sprite"]: number(val)
    assert type(r["events"]) is list and len(r["events"])==24
    for i,event in enumerate(r["events"]):
        phase=i//len(PCS)
        index=i%len(PCS)
        assert type(event) is dict and set(event)==EVENT
        assert event["phase"]==phase
        assert event["pc"]==PCS[index]
        assert event["bank"]==BANKS[index]
        for k in ("hits","first_step","last_step","first_selector","first_slot2"):
            number(event[k])
        number(event["first_selector"],255)
        number(event["first_slot2"],15)
        if event["hits"]:
            assert event["first_step"]<=event["last_step"]
        else:
            assert event["first_step"]==event["last_step"]==0
            assert event["first_selector"]==event["first_slot2"]==0
    # These are already physical bank-qualified in PC-34/PC-12.
    assert r["events"][6]["hits"]==b["sprite_counts"][3]
    assert sum(r["events"][k]["hits"] for k in (9,10,11))==b["observed_collision_calls"]
    assert r["prefix_irq"]<=r["stop_irq"]
    assert r["prefix_vblank"]<=r["stop_vblank"]
    print("PASS PC-40: exact original 300k prefix, same input schedule,"
          " physical mapper sites, full source SHA and bounded continuation")
    print("PC-40 source-only: steps=%d reason=%s PC=%s IRQ=%d VBlank=%d" %
          (r["continued_steps"],r["stop_reason"],r["stop_pc"],
           r["stop_irq"],r["stop_vblank"]))
    for i,site in enumerate(r["events"]):
        if site["hits"]:
            print("  phase=%d original PC=$%s physical_bank=%d hits=%d" %
                  (site["phase"],site["pc"],site["bank"],site["hits"]))

if __name__=="__main__":
    try:
        if len(sys.argv)!=5:
            raise ValueError("usage: verify_pc40_route.py ORIGINAL.sms "
                             "PC40-source.json PC40-route.json PC34.json")
        verify(*sys.argv[1:])
    except (AssertionError,ValueError,KeyError,TypeError,OSError) as ex:
        sys.exit("FAIL PC-40 original source route: "+str(ex))
