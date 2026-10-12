#!/usr/bin/env python3
"""Phase16 full overlay, structural/semantic validation, and mutation tests."""
import copy
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'tools'))
from build_phase16 import build
from build_sms_phase14 import offset, EXPECTED_SHA
from structured_data_phase16 import (capture,segments,load_verified,generate_sources,digest)
from symbolic_asm_phase16 import resolve,verify as verify_symbolic
from z80_roundtrip_phase10 import assemble

ROOT=Path(__file__).resolve().parent

def rejects(call,what):
    try:call()
    except (ValueError,KeyError,AssertionError,IndexError):
        print('PASS: rejects',what)
        return
    raise AssertionError('Accepted invalid '+what)

def run(rom):
    assert hashlib.sha256(rom).hexdigest()==EXPECTED_SHA
    original=json.loads((ROOT/'phase16/records.json').read_text())
    assert capture(rom)==original
    print('PASS: semantic record extraction reproduces checked-in source')
    parts=segments(original)
    assert len(parts)==64+64+2+1
    perbank=load_verified()
    all_bytes={}
    for bank,entry in perbank.items():
        for pc,b in entry['bytes'].items():
            at=offset(bank,pc)
            assert at not in all_bytes
            all_bytes[at]=b
            assert rom[at]==b
    assert len(all_bytes)==7902 and len(set(all_bytes))==7902
    assert [len(perbank[n]['bytes']) for n in (4,6,7)]==[124,6370,1408]
    print('PASS: 7,902 separately reencoded record bytes match ROM')
    syms=verify_symbolic()
    assert sum(r['bytes'] for r in syms.values())==8579
    assert syms['src/phase16/bank00_symbolic.asm']['symbolic_bindings']>=4
    print('PASS: three symbolic Z80 views preserve canonical assembly')
    output,summary=build(rom)
    assert output==rom and summary==json.loads((ROOT/'phase16/build_report.json').read_text())
    assert summary['source_backed_bytes']==22605
    assert summary['fallback_bytes']==239539
    assert summary['phase16_new_structured_source_bytes']==7902
    assert sum(v['source_bytes'] for v in summary['per_bank'])==22605
    assert sum(v['fallback_bytes'] for v in summary['per_bank'])==239539
    print('PASS: complete ROM template overlay matches original SHA-256')
    malformed=copy.deepcopy(original)
    malformed['bank6_sprite_records'][0]['delta_y'].pop()
    rejects(lambda:segments(malformed),'wrong record count')
    malformed=copy.deepcopy(original)
    malformed['bank6_sprite_records'][0]['delta_y'][0]^=1
    rejects(lambda:segments(malformed),'corrupted delta')
    malformed=copy.deepcopy(original)
    malformed['bank7_secondary_records'][0]['pairs'][0][1]^=1
    rejects(lambda:segments(malformed),'corrupted secondary record')
    malformed=copy.deepcopy(original)
    malformed['sprite_offset_tables'][0]['pairs'][0][0]^=1
    rejects(lambda:segments(malformed),'corrupted offset table')
    malformed=copy.deepcopy(original)
    malformed['bank4_index_records'][0][0]^=1
    rejects(lambda:segments(malformed),'corrupted bank4 record')
    malformed=copy.deepcopy(original)
    malformed['bank6_sprite_records'][0]['index']=1
    rejects(lambda:segments(malformed),'duplicate index')
    malformed=copy.deepcopy(original)
    malformed['bank6_sprite_records'][0]['delta_y'][0]=300
    rejects(lambda:segments(malformed),'out-of-range source byte')
    incorrect=bytearray(rom);incorrect[0x18080]^=1
    rejects(lambda:build(bytes(incorrect)),'wrong ROM fingerprint')
    symbolic=(ROOT/'src/phase16/bank06_symbolic.asm').read_text()
    mutated=symbolic.replace('SpriteRecordConsumer equ $9932','SpriteRecordConsumer equ $9933',1)
    canonical=(ROOT/'src/phase11_roundtrip/bank06.asm').read_text()
    output_a,_=assemble(canonical)
    output_b,_=assemble(resolve(mutated))
    assert output_a!=output_b
    print('PASS: wrong symbolic address creates mismatched opcode bytes')
    rejects(lambda:assemble(resolve('org $9932\n  call NonexistentSymbol\n')),'undefined symbolic target')
    print('PHASE 16: PASS')

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: python Ys/tests_phase16.py ROM.sms')
    run(Path(sys.argv[1]).read_bytes())
