#!/usr/bin/env python3
"""Phase 11: independent coverage accounting, source and data mutation gates."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
ROOT=Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))  # Legacy Phase 8 utilities use top-level imports.
from tools import rebuild_phase11 as build
from tools.z80_regions import decode

def check(ok,message):
    assert ok,message
    print('PASS:',message)

def must_reject(fn,message):
    try:fn()
    except (AssertionError,ValueError,IndexError,KeyError,FileNotFoundError):
        print('PASS: rejection:',message)
    else:raise AssertionError('Unexpectedly accepted '+message)

def run(path):
    rom=path.read_bytes()
    check(hashlib.sha256(rom).hexdigest()==build.ROM_SHA and len(rom)==262144,
          'exact original ROM fingerprint')
    rows,owned,baseline,new=build.inventory(rom)
    check(len(baseline)==4960 and sum(len(row[3]) for row in baseline)==10188,
          'previous 4,960 instructions and 10,188 bytes unchanged')
    check(len(new)==1198 and sum(len(row[3]) for row in new)==2251,
          '1,198 additional instructions / 2,251 independently mapped code bytes')
    check(len(rows)==6158 and len(owned)==12439,'6,158 unique starts / 12,439 bytes, no overlaps')
    bank6=[row for row in new if row[0]//0x4000==6]
    check(len(bank6)==228 and sum(len(x[3]) for x in bank6)==403,
          '228 newly traced bank-6 instructions / 403 bytes')
    assert (0x19932,0x9932) == bank6[0][:2]
    # Every instruction must have a separately decoded ending, correct slot,
    # and in-project encoder result checked by rebuild_phase11.inventory.
    for offset,pc,text,raw,name in rows:
        end,_=decode(rom,offset,0 if offset<0x8000 else (2-(offset>>14))*0x4000)
        assert end==offset+len(raw)
        assert pc==(offset if offset<0x8000 else 0x8000+(offset&0x3fff))
    check(True,'independent decoder agrees with 6,158 instruction boundaries')
    metadata=build.data_audit(rom)
    check(metadata['entries']==64 and metadata['record_width']==2 and
          metadata['unique_destinations']==64 and
          int(metadata['minimum_target'],16)>=0x8000 and
          int(metadata['maximum_target'],16)<0x9932,
          '64 index-addressed bank-6 pointers distinct and physically bounded')
    # Test the structurally anchored boundary, not only the global ROM hash.
    badptr=bytearray(rom);badptr[0x18001]=0x40
    must_reject(lambda:build.data_audit(bytes(badptr)), 'out-of-bank pointer')
    wrong_limit=bytearray(rom);wrong_limit[0x18080]=0
    wrong_limit[0x18081]=0x90
    must_reject(lambda:build.data_audit(bytes(wrong_limit)), 'unjustified table extension')
    blocks=build.graphics_audit(rom)
    check(sum(b['bytes'] for b in blocks)==5632 and sum(b['tiles'] for b in blocks)==176,
          '176 reversibly interpreted 32-byte tiles')
    result,text=build.report_and_sources(rom)
    check(text['cumulative_distinct_assembler_matched_code_bytes']==12439 and
          text['combined_distinct_code_and_reencoded_data_bytes']==18199 and
          text['new_candidate_classification_bytes']==531,
          'no coverage double-counting; 531 new code/table ROM bytes')
    check((ROOT/'phase11/report.json').read_text()==result,'committed report reproducibility')
    broken=bytearray(rom); broken[0x19932]^=1
    must_reject(lambda:build.report_and_sources(bytes(broken)), 'modified bank-6 ROM opcode')
    broken=bytearray(rom); broken[0xc000]^=1
    must_reject(lambda:build.report_and_sources(bytes(broken)), 'modified graphics ROM byte')
    with tempfile.TemporaryDirectory() as temp:
        tmp=Path(temp)/'asm'
        shutil.copytree(build.ASM,tmp)
        original_path=build.ASM
        try:
            build.ASM=tmp
            f=tmp/'bank06.asm'
            original=f.read_text()
            f.write_text(original.replace('ld a,($C199)','ld a,($C198)',1))
            must_reject(lambda:build.report_and_sources(rom), 'mutated bank-6 assembly source')
        finally:build.ASM=original_path
    print('PHASE 11: PASS')

if __name__=='__main__':
    assert len(sys.argv)==2,'Usage: tests_phase11.py ROM.sms'
    run(Path(sys.argv[1]))
