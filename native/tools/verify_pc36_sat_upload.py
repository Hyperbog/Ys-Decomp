#!/usr/bin/env python3
"""PC-36 original 64+128-byte SAT upload verification.

The first $053F RET finishes the 64-byte Y helper; the second
finishes the 128-byte XT sequence. Input still experimental.
"""
from pathlib import Path
import hashlib
import json
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
ROM_SHA="02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9"
ROWS={
"00427":("0427","AF","xor a"),
"00428":("0428","D3 BF","out ($BF),a"),
"0042A":("042A","3E 7F","ld a,$7F"),
"0042C":("042C","D3 BF","out ($BF),a"),
"00430":("0430","21 00 DD","ld hl,$DD00"),
"00433":("0433","CD BF 04","call $04BF"),
"0043C":("043C","21 40 DD","ld hl,$DD40"),
"0043F":("043F","ED A3","outi"),
"004BF":("04BF","ED A3","outi"),
"0053D":("053D","ED A3","outi"),
"0053F":("053F","C9","ret"),
}
EXPECTED={"schema","source","continued_steps","stop_reason","stop_pc",
"stop_irq","stop_vblank","stop_slot2","entry_pc","return_pc",
"source_y","source_xt","vram_y","vram_xt","bytes_per_upload",
"entries","halfway","completed","matched","mismatched","abandoned",
"pending","bytes_compared","bytes_different","first_mismatch_1based",
"first_expected","first_actual","first_completion","last_completion",
"last_write_delta","first_source_crc32","first_vram_crc32",
"last_source_crc32","last_vram_crc32"}
TEXT_FIELDS={"schema","source","stop_reason","stop_pc","entry_pc","return_pc",
             "source_y","source_xt","vram_y","vram_xt"}

def validate(source,pc34,pc36):
    rom=Path(source).read_bytes()
    assert len(rom)==262144 and hashlib.sha256(rom).hexdigest()==ROM_SHA
    lines=(ROOT/"Ys/phase5/code.lst").read_text(encoding="utf-8").splitlines()
    for at,(pc,raw,insn) in ROWS.items():
        binary=bytes.fromhex(raw)
        pos=int(at,16)
        assert rom[pos:pos+len(binary)]==binary,(at,"ROM")
        expr=r"^"+at+r"\s+"+pc+r"\s+"+r"\s+".join(raw.split())+r"\s+"+re.escape(insn)+r"\s*$"
        assert sum(bool(re.fullmatch(expr,line,re.I)) for line in lines)==1,(at,"listing")
    # 128 sequential physical-bank0 OUTI from $043F to $053D,
    # of which the subroutine from $04BF contains 64.
    for start,end,count in ((0x043F,0x053F,128),(0x04BF,0x053F,64)):
        assert (end-start)//2==count
        for pc in range(start,end,2):
            assert rom[pc:pc+2]==bytes.fromhex("ED A3"),hex(pc)
            regex=rf"^{pc:05X}\s+{pc:04X}\s+ED\s+A3\s+outi\s*$"
            assert sum(bool(re.fullmatch(regex,line,re.I)) for line in lines)==1,hex(pc)
    reference=json.loads(Path(pc34).read_text(encoding="utf-8"))
    audit=json.loads(Path(pc36).read_text(encoding="utf-8"))
    assert set(audit)==EXPECTED,set(audit)^EXPECTED
    assert audit["schema"]=="ys-pc36-sat-source-upload-v1"
    assert audit["source"]=="pc34-same-run"
    assert reference["schema"]=="ys-pc34-extended-postrelease-source-watch-v1"
    for k in ("continued_steps","stop_reason","stop_pc","stop_irq",
              "stop_vblank","stop_slot2"):
        assert audit[k]==reference[k],k
    assert audit["entries"]==reference["sprite_counts"][4]
    assert audit["continued_steps"]==300000
    assert (audit["entry_pc"],audit["return_pc"])==("0427","053F")
    assert (audit["source_y"],audit["source_xt"])==("DD00","DD40")
    assert (audit["vram_y"],audit["vram_xt"])==("3F00","3F80")
    assert audit["bytes_per_upload"]==192
    assert type(audit["pending"]) is bool
    for k in EXPECTED-TEXT_FIELDS-{"pending"}:
        assert type(audit[k]) is int and audit[k]>=0,k
    assert audit["entries"]==audit["completed"]+audit["abandoned"]+int(audit["pending"])
    assert audit["halfway"]>=audit["completed"]
    assert audit["halfway"]<=audit["entries"]
    assert audit["completed"]==audit["matched"]+audit["mismatched"]
    # Source-observed golden result on the fixed PC-34 ROM/input schedule.
    # A consistent but corrupted renderer is NOT a successful regression.
    assert (audit["entries"],audit["halfway"],audit["completed"],
            audit["matched"],audit["mismatched"],audit["abandoned"],
            audit["pending"],audit["bytes_compared"],audit["bytes_different"],
            audit["last_write_delta"])==(27,27,27,27,0,0,False,5184,0,192),(
            "original SAT upload golden result changed",audit)
    assert audit["first_source_crc32"]==audit["first_vram_crc32"]
    assert audit["last_source_crc32"]==audit["last_vram_crc32"]
    assert audit["bytes_compared"]==192*audit["completed"]
    assert audit["bytes_different"]<=audit["bytes_compared"]
    assert audit["first_mismatch_1based"]<=192
    if audit["bytes_different"]:
        assert audit["first_mismatch_1based"]>=1
    else:
        assert audit["first_mismatch_1based"]==0
    if audit["completed"]:
        assert 0<audit["first_completion"]<=audit["last_completion"]
    else:
        assert audit["first_completion"]==audit["last_completion"]==0
    assert all(audit[f]<=255 for f in ("first_expected","first_actual"))
    assert all(audit[f]<=0xFFFFFFFF for f in ("first_source_crc32",
       "first_vram_crc32","last_source_crc32","last_vram_crc32"))
    print("PASS PC-36 original ROM: two-stage 64+128 OUTI instruction"
          " range, source listing and same-run sprite entry count")
    print("PC-36 measured original VDP SAT:"
          " starts={entries} Y_return={halfway} completed={completed}"
          " match={matched} mismatch={mismatched} abandoned={abandoned}"
          " pending={pending} bytes={bytes_compared} diff_bytes={bytes_different}"
          " write_delta_last={last_write_delta}".format(**audit))

if __name__=="__main__":
    try:
        if len(sys.argv)!=4:
            raise ValueError("usage: verify_pc36_sat_upload.py SOURCE.sms PC34.json PC36.json")
        validate(*sys.argv[1:])
    except (AssertionError,OSError,ValueError,TypeError,KeyError) as error:
        sys.exit("FAIL PC-36 source SAT upload: "+str(error))
