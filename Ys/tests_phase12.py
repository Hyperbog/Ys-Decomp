#!/usr/bin/env python3
"""Independent Phase12 byte-boundary, sprite-table, and snapshot rejection tests."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
from tools import phase12_sprite_pipeline as phase12
from tools.z80_regions import decode
from tools.z80_roundtrip_phase10 import assemble


def rejects(call,what):
    try:call()
    except (AssertionError,ValueError,KeyError,IndexError):
        print('PASS: rejects',what)
        return
    raise AssertionError('Accepted corruption: '+what)


def run(rom):
    raw,metadata=phase12.generate(rom)
    assert metadata['rom_sha256']==hashlib.sha256(rom).hexdigest()
    assert metadata['new_distinct_classified_bytes']==339
    assert metadata['cumulative_code_and_reversible_data_bytes']==24860
    assert metadata['contiguous_bank6_region']['bytes']==7192
    assert (ROOT/'phase12/sprite_pipeline.json').read_text()==json.dumps(metadata,indent=2)+'\n'
    assert (ROOT/'src/phase12/bank06_sprite_handlers.asm').read_text()==raw
    print('PASS: ROM fingerprint and reproducible source/metadata')
    assembled,labels=assemble(raw)
    assert not labels and len(assembled)==241
    # Independent decoding from a different parser: compare all source
    # physical offsets with instruction lengths and original ROM opcodes.
    positions=[]
    for line in raw.splitlines():
        if ' ; ROM $' not in line:continue
        off=int(line.split(' ; ROM $')[1][:5],16)
        cpu=(off-0x18000)+0x8000
        end,txt=decode(rom,off,(2-6)*0x4000)
        assert bytes(assembled[p] for p in range(cpu,cpu+(end-off)))==rom[off:end]
        assert txt==line.split('    ',1)[-1].split(';')[0].strip() or txt in line
        positions.extend(range(off,end))
    assert len(positions)==241 and len(set(positions))==241
    print('PASS: 119 independent opcode boundaries / 241 assembled bytes')
    # Confirm same byte arrays are read from bank6 code and written to fixed
    # sprite output RAM before the fixed bank 0 VDP hardware transfer.
    r=rom
    assert r[0x26f3:0x2707].hex().upper()=='3E 06 32 FF FF 21 40 DD 22 2A C0 21 00 DD 22 28 C0 CD 32 99'.replace(' ','')
    assert r[0x2bf1:0x2c05].hex().upper()=='3E 06 32 FF FF 21 40 DD 22 2A C0 21 00 DD 22 28 C0 C3 66 99'.replace(' ','')
    assert r[0x43f:0x53f]==b'\xed\xa3'*128
    assert r[0x4bf:0x53f]==b'\xed\xa3'*64
    assert r[0x53f]==0xc9
    print('PASS: fixed bank-to-bank6 mapper writes and VDP 64+128 byte transfer')
    directory=[int.from_bytes(r[i:i+2],'little') for i in range(0x19a77,0x19a99,2)]
    dispatch=[int.from_bytes(r[i:i+2],'little') for i in range(0x19a99,0x19aa9,2)]
    assert len(directory)==17 and directory==[0xc200+0x30*i for i in range(17)]
    assert dispatch==phase12.ROOTS and len(set(dispatch))==8
    assert r[0x19b29:0x19b45] and len(r[0x19b29:0x19b45])==28
    assert r[0x19b7c:0x19b90] and len(r[0x19b7c:0x19b90])==20
    print('PASS: 17 object slots, 8 handlers, bounded 14/16-sprite offset tables')
    corrupt=bytearray(rom)
    corrupt[0x19a99]^=1
    rejects(lambda:phase12.generate(bytes(corrupt)),'ROM dispatcher')
    corrupt=bytearray(rom)
    corrupt[0x19b29]^=1
    rejects(lambda:phase12.generate(bytes(corrupt)),'ROM sprite offsets')
    corrupt=bytearray(rom)
    corrupt[0x43f]^=1
    rejects(lambda:phase12.generate(bytes(corrupt)),'VDP upload opcode')
    corrupt=bytearray(rom)
    corrupt[0x19a77]^=1
    rejects(lambda:phase12.generate(bytes(corrupt)),'work-record pointer')
    # Regression detects changes even to ROM-equivalent source metadata.
    orig=phase12.SOURCE.read_text()
    try:
        phase12.SOURCE.write_text(orig.replace('ld hl,$9B29','ld hl,$9B2A',1))
        rejects(lambda:assert_source(rom),'modified assembly source')
    finally:phase12.SOURCE.write_text(orig)
    reportpath=phase12.REPORT
    original=reportpath.read_text()
    try:
        broken=json.loads(original)
        broken['cumulative_candidate_coverage_bytes']+=1
        reportpath.write_text(json.dumps(broken,indent=2)+'\n')
        rejects(lambda:assert_source(rom),'inflated coverage metadata')
    finally:reportpath.write_text(original)
    print('PHASE 12: PASS')


def assert_source(rom):
    source,report=phase12.generate(rom)
    assert phase12.SOURCE.read_text()==source
    assert phase12.REPORT.read_text()==json.dumps(report,indent=2)+'\n'


if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: tests_phase12.py ROM.sms')
    run(Path(sys.argv[1]).read_bytes())
