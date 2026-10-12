#!/usr/bin/env python3
"""Independent byte comparisons, data/pointer constraints and negative tests."""
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
EXPECTED_NEW = 14521


def ok(condition, label):
    if not condition:
        raise AssertionError(label)
    print('PASS:',label)


def checker(root, rom, script='z80_cfg_phase6.py'):
    return subprocess.run([sys.executable, str(root/'tools'/script),str(rom),'--check'],
                          text=True,capture_output=True)


def main(rom_path):
    rom = rom_path.read_bytes()
    manifest=json.loads((ROOT/'manifest.json').read_text())
    cfg=json.loads((ROOT/'phase6/regions.json').read_text())
    report=json.loads((ROOT/'phase6/coverage.json').read_text())
    ok(hashlib.sha256(rom).hexdigest()==manifest['sha256'], 'original ROM fingerprint')
    result=checker(ROOT,rom_path)
    ok(result.returncode==0, 'reproduce phase6 code listing and report')
    ok(checker(ROOT,rom_path,'song_headers_phase6.py').returncode==0,
       'reproduce typed audio descriptor CSV')

    lines=(ROOT/'phase6/code.lst').read_text().splitlines()
    positions={}
    codebytes=set()
    for line in lines:
        match=re.fullmatch(r'^([0-9A-F]{5}) ([0-9A-F]{4})  ([0-9A-F ]{19}) (.+)$', line)
        if not match:continue
        pos=int(match[1],16)
        payload=bytes.fromhex(match[3])
        ok_bytes=(pos<0x4000 and pos==int(match[2],16) and
                  rom[pos:pos+len(payload)]==payload and len(payload)>=1 and
                  not codebytes.intersection(range(pos,pos+len(payload))))
        if not ok_bytes: raise AssertionError(f'bad or overlapping decoded byte at {pos:05X}')
        codebytes.update(range(pos,pos+len(payload)))
        positions[pos]=len(payload)
    ok(len(positions)==2027 and len(codebytes)==4474,
       'independent instruction start/byte comparisons (2,027 / 4,474)')

    databytes=set()
    for item in cfg['data']:
        lo,hi=int(item['start'],16),int(item['end_exclusive'],16)
        ok(hashlib.sha256(rom[lo:hi]).hexdigest()==item['sha256'],
           f'data digest {lo:05X}–{hi-1:05X}')
        span=set(range(lo,hi))
        assert not databytes.intersection(span) and not codebytes.intersection(span)
        databytes.update(span)
    ok(len(databytes)==10047, '10,047 unique data bytes exclude all instruction bytes')
    ok(report['new_code_bytes']==4474 and report['new_data_bytes']==10047 and
       report['new_total_bytes']==EXPECTED_NEW and report['cumulative_distinct_bytes']==21523,
       '14,521 new bytes, 21,523 cumulative')
    ok(EXPECTED_NEW >= 2*4934, 'Phase 6 exceeds twice Phase 5 new coverage')

    for start,end,count in [(0x205A,0x20AC,41),(0x2C24,0x2C36,9)]:
        targets=[int.from_bytes(rom[a:a+2], 'little') for a in range(start,end,2)]
        ok(len(targets)==count and all(t in positions for t in targets),
           f'dispatch table ${start:04X}, {count} destinations are instruction starts')
    dirptrs=[int.from_bytes(rom[p:p+2],'little') for p in range(0x8C90,0x8CFE,2)]
    ok(len(dirptrs)==55 and len(set(dirptrs))==45,
       '55 song-directory entries resolve to 45 distinct pointers')
    rows=list(csv.DictReader(io.StringIO((ROOT/'phase6/audio_descriptors.csv').read_text())))
    ok(len(rows)==84 and len({(r['directory_index'],r['voice_index']) for r in rows})==84,
       '21 regular four-channel audio descriptors = 84 distinct records')
    seen=set()
    for row in rows:
        idx=int(row['directory_index'])
        voice=int(row['voice_index'])
        base=0xAA77+37*idx
        stream =int(row['stream_pointer_cpu'],16)
        blob=rom[base+1+9*voice:base+1+9*(voice+1)]
        assert hashlib.sha256(blob).hexdigest()==row['record_sha256']
        assert int.from_bytes(blob[3:5],'little')==stream
        assert dirptrs[idx]==base and rom[base]==4
        seen.add(stream)
    ok(len(seen)>60, f'audio stream pointers independently verified ({len(seen)} unique)')
    ok(any('0DDA -> mapped CPU 86C1' in edge for edge in report['unresolved_edges']),
       'prior bank-0 mapper ambiguity retained unresolved')
    ok(all(p not in codebytes for p in range(0x205A,0x20AC)),
       'game-state dispatch words not treated as instructions')

    with tempfile.TemporaryDirectory(prefix='ys_phase6_') as tmp:
        work=Path(tmp)/'Ys'
        shutil.copytree(ROOT,work,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        file=work/'phase6/code.lst'
        before=file.read_text()
        file.write_text(before.replace('02002 2002', 'XXXXX 2002', 1))
        ok(checker(work,rom_path).returncode!=0, 'modified listing rejected')
        file.write_text(before)
        file=work/'phase6/coverage.json'
        before=file.read_text()
        file.write_text(before.replace('"new_total_bytes": 14521','"new_total_bytes": 14522',1))
        ok(checker(work,rom_path).returncode!=0,'modified metrics rejected')
        file.write_text(before)
        file=work/'phase6/regions.json'
        before=file.read_text()
        bad=json.loads(before)
        bad['data'][0]['sha256']='0'*64
        file.write_text(json.dumps(bad))
        ok(checker(work,rom_path).returncode!=0, 'corrupt table digest rejected')
        bad=json.loads(before)
        bad['entrypoints'].append('205A')
        file.write_text(json.dumps(bad))
        ok(checker(work,rom_path).returncode!=0, 'dispatch-table-as-code rejected')
        file.write_text(before)
        file=work/'phase6/audio_descriptors.csv'
        before=file.read_text()
        file.write_text(before.replace('8D57','FFFF',1))
        ok(checker(work,rom_path,'song_headers_phase6.py').returncode!=0,
           'corrupt descriptor CSV rejected')
        file.write_text(before)
        broken=Path(tmp)/'modified.sms'
        data=bytearray(rom)
        data[0xAA77]^=1
        broken.write_bytes(data)
        ok(checker(work,broken).returncode!=0, 'modified ROM rejected')
    print('PASS: Phase 6 independent regression checks complete')

if __name__=='__main__':
    try:
        if len(sys.argv)!=2:raise ValueError('Usage: tests_phase6.py original.sms')
        main(Path(sys.argv[1]).resolve())
    except (AssertionError, OSError, ValueError, IndexError) as exc:
        sys.exit(f'FAIL Phase6: {exc}')
