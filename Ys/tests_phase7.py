#!/usr/bin/env python3
"""Phase-7 ROM-backed static-analysis regression and negative tests.

Each test checks the independently supplied ROM, not semantic certainty of
candidate bank-3 payloads. No runtime mapping or sound/graphics decoding proof.
"""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent


def verify(cond, desc):
    if not cond:
        raise AssertionError(desc)
    print('PASS:',desc)


def invoke(root,rom):
    return subprocess.run([sys.executable,str(root/'tools/z80_bank1_phase7.py'),str(rom),'--check'],
                          capture_output=True,text=True)


def main(rom_path):
    data=rom_path.read_bytes()
    report=json.loads((ROOT/'phase7/coverage.json').read_text())
    original_sha=json.loads((ROOT/'manifest.json').read_text())['sha256']
    verify(hashlib.sha256(data).hexdigest()==original_sha,'input fingerprint is exact')
    verify(invoke(ROOT,rom_path).returncode==0,'Phase7 snapshot reproducible')
    verify(data[0x008C:0x009A].hex()=='21fcff3680233600233601233602',
           'startup sets mapper $FFFC=$80, $FFFD=0, $FFFE=1, $FFFF=2')
    expected_roots={0x42ba,0x476c,0x60b5,0x61ae,0x6215,0x64cd}
    verify({int(x,16) for x in report['bank1_direct_roots']}==expected_roots,
           'bank-1 seeds originate from six fixed-bank direct references')
    assert report['bank1_direct_roots']['61AE']==['27A0','2FFE']
    print('PASS: multiple independent callers to bank-1 $61AE')

    code=set(); starts=set()
    lines=(ROOT/'phase7/code.lst').read_text().splitlines()
    for line in lines:
        m=re.fullmatch(r'([0-9A-F]{5}) ([0-9A-F]{4})  ([0-9A-F ]{19}) (.+)',line)
        if not m:continue
        pos=int(m[1],16)
        payload=bytes.fromhex(m[3])
        assert 0x4000<=pos<0x8000 and pos==int(m[2],16)
        assert data[pos:pos+len(payload)]==payload
        assert not code.intersection(range(pos,pos+len(payload))), f'overlap at {pos:04X}'
        assert pos not in starts
        starts.add(pos)
        code.update(range(pos,pos+len(payload)))
    verify((len(starts),len(code))==(376,763),'376 instruction starts, 763 matching disjoint bytes')
    verify(hashlib.sha256(bytes(data[p] for p in sorted(code))).hexdigest()==report['bank1_code_sha256'],
           'independent bank-1 instruction-byte digest')
    verify(all(int(x,16) in starts for x in report['bank1_direct_roots']),
           'all mapped entrypoints are instruction boundaries')
    data_owner=set()
    for block in report['bank3_segments']:
        lo,hi=int(block['offset_start'],16),int(block['offset_end_exclusive'],16)
        assert 0xC000<=lo<hi<=0x10000
        assert not data_owner.intersection(range(lo,hi))
        assert block['size']==hi-lo and block['status']=='provisional_opaque_data'
        assert hashlib.sha256(data[lo:hi]).hexdigest()==block['sha256']
        assert data[lo:hi].count(0xFF)==block['ff_bytes']
        assert len(set(data[lo:hi]))==block['byte_values_distinct']
        data_owner.update(range(lo,hi))
    verify(len(data_owner)==14541 and data_owner==set(range(0xC000,0xF8CD)),
           'four contiguous provisional bank-3 sections total 14,541 bytes')
    verify(all(b==0xFF for b in data[0xF8CD:0x10000]) and data[0xF8CC]!=0xFF,
           '1,843-byte terminal FF padding excluded')
    verify(not (code & data_owner) and report['phase7_candidate_total_new']==15304,
           '15,304 additional distinct candidate ROM bytes')
    verify(report['candidate_cumulative_coverage']==36827 and
           report['earlier_phase_1_to_6_classified']==21523,
           'previous snapshots preserved and candidate cumulative sum correct')
    verify(report['bank3_provisional_data_bytes']==14541 and 'not_proven' in report,
           'provisional classification and remaining limits explicit')
    verify(any('slot-2 bank unknown' in x for x in report['unresolved_slot2_edges']),
           'mapper-dependent calls are recorded as unresolved')

    with tempfile.TemporaryDirectory(prefix='ys_phase7_') as td:
        work=Path(td)/'Ys'
        shutil.copytree(ROOT,work,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        snap=work/'phase7/code.lst'
        baseline=snap.read_text()
        snap.write_text(baseline.replace('0476C','X476C',1))
        verify(invoke(work,rom_path).returncode!=0,'altered listing refused')
        snap.write_text(baseline)
        snap=work/'phase7/coverage.json'
        baseline=snap.read_text()
        j=json.loads(baseline)
        j['phase7_candidate_total_new']+=1
        snap.write_text(json.dumps(j,indent=2)+'\n')
        verify(invoke(work,rom_path).returncode!=0,'altered coverage refused')
        snap.write_text(baseline)
        broken=Path(td)/'wrong.sms'
        altered=bytearray(data)
        altered[0xD400]^=0x1
        broken.write_bytes(altered)
        verify(invoke(work,broken).returncode!=0,'modified ROM refused')
        altered=bytearray(data)
        altered[0xF8CD]=0
        broken.write_bytes(altered)
        verify(invoke(work,broken).returncode!=0,'changed padding boundary refused')
    print('PASS: Phase 7 regression checks finished')

if __name__ == '__main__':
    try:
        if len(sys.argv)!=2:raise ValueError('Usage: tests_phase7.py <ROM>')
        main(Path(sys.argv[1]).resolve())
    except (AssertionError,ValueError,OSError,IndexError) as ex:
        sys.exit(f'FAIL Phase7: {ex}')
