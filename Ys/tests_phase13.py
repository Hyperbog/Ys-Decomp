#!/usr/bin/env python3
"""Phase 13 independent bank-7 directory/VDP code and negative regression tests."""
import hashlib
import json
from pathlib import Path
import sys
from contextlib import contextmanager

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
from tools import phase13_bank7_graphics as p13
from tools.z80_regions import decode
from tools.z80_roundtrip_phase10 import assemble

@contextmanager
def temporary_content(path, text):
    previous=path.read_text()
    try:
        path.write_text(text)
        yield
    finally:
        path.write_text(previous)


def must_reject(callback, name):
    try:
        callback()
    except (AssertionError, ValueError, KeyError, IndexError):
        print('PASS rejects:',name)
        return
    raise AssertionError('Mutation accepted: '+name)


def assert_snapshots(rom):
    src,report=p13.generate(rom)
    assert p13.SOURCE.read_text()==src
    assert p13.REPORT.read_text()==json.dumps(report,indent=2)+'\n'


def run(rom):
    source,meta=p13.generate(rom)
    assert_snapshots(rom)
    assert len(meta['graphics_records'])==64
    assert meta['new_distinct_classified_bytes']==13193
    assert meta['cumulative_candidate_coverage_bytes']==58133
    assert meta['cumulative_assembler_matched_bytes']==14025
    print('PASS ROM SHA-256, deterministic source, metadata, coverage totals')
    b=rom[p13.BASE:p13.BASE+0x4000]
    # This test independently reconstructs directory semantics without calling
    # the phase13 table-walker: checks 4-byte records and linear 22-byte table.
    assert len(b[0:0x100])==64*4
    assert len(b[0x100:0x180])==64*2
    pairs=[]
    for i in range(64):
        code=int.from_bytes(b[4*i:4*i+2],'little')
        data=int.from_bytes(b[4*i+2:4*i+4],'little')
        ptr=int.from_bytes(b[0x100+2*i:0x100+2*i+2],'little')
        assert 0x8180<=code<=0x8300
        assert ptr==0xAFBF+22*i
        length=(0x86C0-code)//8
        pairs.append((data,data+length))
        desc=meta['graphics_records'][i]
        assert length==desc['graphics_bytes']
        assert hashlib.sha256(b[data-0x8000:data-0x8000+length]).hexdigest()==desc['graphics_sha256']
        assert hashlib.sha256(b[ptr-0x8000:ptr-0x8000+22]).hexdigest()==desc['secondary_sha256']
    assert sum(y-x for x,y in pairs)==10056
    assert sorted(pairs)[0][0]==0x8877
    assert sorted(pairs)[-1][1]==0xAFBF
    assert all(a[1]==z[0] for a,z in zip(sorted(pairs),sorted(pairs)[1:]))
    print('PASS two directories, 64 exact adjacent graphics records, 64 adjacent secondary records')
    # Check each assembled byte against a separately decoded instruction length.
    built,labels=assemble(source)
    assert not labels and len(built)==1345
    p=p13.BASE+0x180
    insts=0
    while p<p13.BASE+0x6C1:
        end,mnemonic=decode(rom,p,(2-7)*0x4000)
        at=0x8000+p-p13.BASE
        assert bytes(built[a] for a in range(at,at+end-p))==rom[p:end]
        p=end
        insts+=1
    assert insts==673
    assert b[0x180:0x6c0]==bytes.fromhex('ED A3 D3 BE D3 BE D3 BE')*168
    assert b[0x6c0]==0xC9
    print('PASS 673 decoded Z80 instructions, 1,345 assembler-matched bytes')
    # Local port-write simulation: a source byte followed by three zero planes.
    # Reversible for each row, no asset byte arrays persisted to repository.
    for lo,hi in pairs:
        src=b[lo-0x8000:hi-0x8000]
        expanded=b''.join(bytes((x,0,0,0)) for x in src)
        assert len(expanded)==(hi-lo)*4
        assert expanded[::4]==src
        assert all(z==0 for j,z in enumerate(expanded) if j%4)
    assert sum((y-x)*4 for x,y in pairs)==40224
    print('PASS reversible 1-plane to four-plane 40,224-byte cumulative transfer model')
    # Negative cases with ROM SHA updated in memory so the tests actually
    # reach the structural validators, not just the top-level fingerprint.
    for pos,flipped,name in [(0x1C000,0x01,'unrolled entry pointer'),
                             (0x1C002,0x01,'record pointer coverage'),
                             (0x1C100,0x01,'secondary 22-byte stride'),
                             (0x1C180,0x01,'OUTI opcode')]:
        corrupted=bytearray(rom)
        corrupted[pos]^=flipped
        corrupted=bytes(corrupted)
        origsha=p13.ROM_SHA
        try:
            p13.ROM_SHA=hashlib.sha256(corrupted).hexdigest()
            must_reject(lambda:p13.generate(corrupted),name+' (past fingerprint)')
        finally:
            p13.ROM_SHA=origsha
    orig=p13.SOURCE.read_text()
    with temporary_content(p13.SOURCE,orig.replace('outi','nop ',1)):
        must_reject(lambda:assert_snapshots(rom),'mutated Z80 mnemonic source')
    original_meta=json.loads(p13.REPORT.read_text())
    altered=dict(original_meta)
    altered['cumulative_candidate_coverage_bytes']+=1
    with temporary_content(p13.REPORT,json.dumps(altered,indent=2)+'\n'):
        must_reject(lambda:assert_snapshots(rom),'inflated candidate coverage')
    print('PHASE 13: PASS')


if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: tests_phase13.py ROM.sms')
    run(Path(sys.argv[1]).read_bytes())
