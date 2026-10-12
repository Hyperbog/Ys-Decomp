#!/usr/bin/env python3
"""Independent negative and round-trip checks for recovered bank-6 records."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
from tools import recover_bank6_records_phase11b as rec
from tools import rebuild_phase11 as previous


def reject(fn,label):
    try:
        fn()
    except (ValueError,AssertionError):
        print('PASS: rejected',label)
        return
    raise AssertionError('Accepted '+label)


def run(rom):
    assert len(rom)==0x40000 and hashlib.sha256(rom).hexdigest()==rec.ROM_SHA
    # Independent consumer audit: first pass copies N bytes using DJNZ,
    # second pass consumes 2*N source bytes (one transformed, one LDI).
    code=rom[0x19932:0x19966]
    assert code.startswith(bytes.fromhex('3A 99 C1 87 6F 26 80 7E 2C 66 6F 46 48'))
    assert bytes.fromhex('10 FA') in code   # DJNZ loop for first group
    assert bytes.fromhex('ED A0') in code   # LDI from source to destination
    rows=rec.extract(rom)
    assert len(rows)==64 and len(set(r['offset'] for r in rows))==64
    assert sum(r['end']-r['offset'] for r in rows)==6322
    assert all(r['end']-r['offset']==1+3*r['count'] for r in rows)
    assert all(rec.encode_payload(r['decoded'])==rom[r['offset']:r['end']] for r in rows)
    # Independent table/element validation, not just the decoder's own counts.
    for item in rows:
        pointer=int.from_bytes(rom[0x18000+2*item['directory_index']:
                                   0x18002+2*item['directory_index']], 'little')
        assert pointer==item['cpu_address']
        size=1+3*rom[item['offset']]
        assert item['end']==item['offset']+size
    # Independent arithmetic checks across every record and multiple origins.
    for row in rows:
        n,first,pairs=row['decoded']
        for bx,by in ((0,0),(0x30,0x28),(0xff,0xfe)):
            xs,ys=rec.emulate_record_buffers(row['decoded'],bx,by)
            assert len(xs)==n and len(ys)==2*n
            running=bx
            for i,delta in enumerate(first):
                running=(running+delta)&255
                assert xs[i]==running
            running=by
            for i,(delta,kind) in enumerate(pairs):
                running=(running+delta)&255
                assert ys[i*2:i*2+2]==bytes((running,kind))
    print('PASS: 64 count-prefixed records and cumulative output simulation at three origins')
    snapshot=json.loads((ROOT/'phase11/bank6_records.json').read_text())
    assert rec.check_snapshot(rom,snapshot)==snapshot
    assert snapshot['new_structured_data_bytes']==6322
    assert sum(record['bytes'] for record in snapshot['records_by_directory_index'])==6322
    print('PASS: exact committed metadata, unique physical offsets')
    broken=bytearray(rom)
    broken[0x18080]=0x1F
    reject(lambda:rec.extract(bytes(broken)),'invalid record count and span')
    broken=bytearray(rom)
    broken[0x18000]=0x70
    reject(lambda:rec.extract(bytes(broken)),'out-of-range pointer')
    broken=bytearray(rom)
    broken[0x18105]^=1
    reject(lambda:rec.check_snapshot(bytes(broken),snapshot),'payload corruption')
    broken=json.loads(json.dumps(snapshot))
    broken['records_by_directory_index'][0]['bytes']+=1
    reject(lambda:rec.check_snapshot(rom,broken),'incorrect record metadata')
    n,offsets,pairs=rows[0]['decoded']
    reject(lambda:rec.encode_payload((n,offsets[:-1],pairs)),'broken reversible record')
    # Baseline source and report still reproducible after test runner fix.
    previous_report,previous_stats=previous.report_and_sources(rom)
    assert (ROOT/'phase11/report.json').read_text()==previous_report
    assert previous_stats['cumulative_distinct_assembler_matched_code_bytes']==12439
    summary=json.loads((ROOT/'phase11/phase11b_summary.json').read_text())
    assert summary['new']['distinct_structured_data_bytes']==sum(r['bytes'] for r in snapshot['records_by_directory_index'])
    assert summary['new']['elements']==sum(r['elements'] for r in snapshot['records_by_directory_index'])
    assert summary['cumulative']['structured_reencoded_data_bytes']==previous_stats['separate_reencoded_data_bytes']+6322
    assert summary['cumulative']['distinct_code_or_structured_data_bytes']==previous_stats['combined_distinct_code_and_reencoded_data_bytes']+6322
    assert summary['cumulative']['candidate_classification_bytes']==previous_stats['total_candidate_coverage_bytes']+6322
    assert set(range(0x18080,0x19932)).isdisjoint(set(range(0x18000,0x18080)))
    print('PASS: checked Phase 11B deltas and cumulative coverage without pointer double-counting')
    print('PASS: retained 12,439 ROM-identical assembled code bytes')
    print('PHASE 11B: PASS')

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: tests_phase11b.py ROM.sms')
    run(Path(sys.argv[1]).read_bytes())
