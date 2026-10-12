#!/usr/bin/env python3
"""Phase 8: independent ROM mapping, code-byte and Mode-4 reversibility tests."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parent


def check(condition,message):
    assert condition,message
    print('PASS:',message)


def invoke(root,program,rom):
    return subprocess.run([sys.executable,str(root/'tools'/program),str(rom),'--check'],
                          capture_output=True,text=True)


def main(path):
    rom=path.read_bytes()
    expected=json.loads((ROOT/'manifest.json').read_text())['sha256']
    check(hashlib.sha256(rom).hexdigest()==expected,'original ROM SHA-256 matches')
    check(invoke(ROOT,'bank_trace_phase8.py',path).returncode==0,'mapper + banked listing reproducible')
    check(invoke(ROOT,'mode4_tiles_phase8.py',path).returncode==0,'tile classification reproducible')
    j=json.loads((ROOT/'phase8/mapper_audit.json').read_text())
    k=json.loads((ROOT/'phase8/tile_metadata.json').read_text())
    check(j['mapper_write_count']==46 and j['mapper_writes_with_adjacent_immediate_bank']>25,
          '46 mapper writes audited, with explicit source values where available')
    anchors={(0x0DD7,7,'86C1'),(0x0C4F,2,'8803'),(0x01C8,7,'8819'),
             (0x026DF,7,'8856'),(0x0FB3,8,'BEE8'),
             (0x03DC3,12,'9EFC'),(0x03E88,10,'BEF7')}
    audit={int(row['write_offset'],16):row for row in j['mapper_audit']}
    for location,bank,target in anchors:
        assert audit[location]['bank_immediately_loaded']==bank
        assert audit[location]['immediate_slot2_call_or_jump']==target
    check(True,'mapper-selected jump/call destinations match ROM operand bytes')
    owner=set(); starts=set()
    lines=(ROOT/'phase8/banked_code.lst').read_text().splitlines()
    for line in lines:
        m=re.fullmatch(r'([0-9A-F]{5}) ([0-9A-F]{4})  ([0-9A-F ]{19}) (.+)',line)
        if not m:continue
        off,addr=int(m[1],16),int(m[2],16)
        raw=bytes.fromhex(m[3])
        bank=off//0x4000
        assert bank in (4,7,8,10,12)
        assert addr==0x8000+off%0x4000
        assert rom[off:off+len(raw)]==raw
        assert not owner.intersection(range(off,off+len(raw)))
        owner.update(range(off,off+len(raw)))
        starts.add(off)
    check(len(owner)==797 and len(starts)==502,
          '797 disjoint instruction bytes and 502 instruction boundaries backed by ROM')
    for key,bankinfo in j['banked_code'].items():
        bank=int(key)
        subset=bytes(rom[p] for p in sorted(owner) if p//0x4000==bank)
        assert len(subset)==bankinfo['bytes']
        assert hashlib.sha256(subset).hexdigest()==bankinfo['code_sha256']
    check(True,'separate physical-bank instruction digests match')
    tbl=j['bank4_indexed_table']
    blob=rom[0x10000:0x1007C]
    check(tbl['records']==31 and tbl['record_size']==4 and
          tbl['sha256']==hashlib.sha256(blob).hexdigest() and
          not set(range(0x10000,0x1007C)).intersection(owner),
          '31 indexed bank-4 records disjoint from code')
    from tools.mode4_tiles_phase8 import decode_tile,encode_tile
    for item in k['blocks']:
        lo,hi=int(item['file_start'],16),int(item['file_end_exclusive'],16)
        assert hashlib.sha256(rom[lo:hi]).hexdigest()==item['sha256']
        assert item['mode4_tile_count']==(hi-lo)//32
        assert all(encode_tile(decode_tile(rom[p:p+32]))==rom[p:p+32]
                   for p in range(lo,hi,32))
    check(k['tiles_total']==176 and k['interpreted_bytes']==5632,
          '176 Mode-4-compatible tiles round-trip to 5,632 original bytes')
    check(j['new_distinct_code_plus_table_bytes']==921 and
          j['cumulative_candidate_coverage_bytes']==37748 and
          k['coverage_note'].find('ZERO new distinct bytes')>=0,
          'candidate coverage is a distinct-byte union; no tile double-counting')
    with tempfile.TemporaryDirectory(prefix='ys_p8_') as temporary:
        root=Path(temporary)/'Ys'
        shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for snapshot,program in [('mapper_audit.json','bank_trace_phase8.py'),
                                 ('tile_metadata.json','mode4_tiles_phase8.py')]:
            f=root/'phase8'/snapshot
            orig=f.read_bytes()
            f.write_bytes(orig+b'X')
            check(invoke(root,program,path).returncode!=0,f'{snapshot} mutation rejected')
            f.write_bytes(orig)
        bad=Path(temporary)/'mutated.sms'
        altered=bytearray(rom)
        altered[0x1c6c1]^=1
        bad.write_bytes(altered)
        check(invoke(root,'bank_trace_phase8.py',bad).returncode!=0,
              'changed bank-7 ROM rejected')
        altered=bytearray(rom)
        altered[0xc000]^=1
        bad.write_bytes(altered)
        check(invoke(root,'mode4_tiles_phase8.py',bad).returncode!=0,
              'changed graphics ROM rejected')
    print('PASS Phase 8 suite finished')

if __name__=='__main__':
    try:
        if len(sys.argv)!=2:raise ValueError('Usage: tests_phase8.py ROM.sms')
        main(Path(sys.argv[1]).resolve())
    except (AssertionError,ValueError,OSError,IndexError) as ex:sys.exit('FAIL Phase8: '+str(ex))
