#!/usr/bin/env python3
"""Verify Ys SMS sprite SAT pipeline and contiguous bank-6 source region.

ROM input is supplied by the user; the project stores only mnemonic source and
short digests/metadata, never raw graphical/record payloads.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

TOOLS=Path(__file__).resolve().parent
sys.path.insert(0,str(TOOLS))
from rebuild_phase11 import inventory
from rebuild_phase10 import render
from z80_roundtrip_phase10 import assemble,encode
from bank_trace_phase8 import walk_bank
from recover_bank6_records_phase11b import extract

ROOT=TOOLS.parent
REPORT=ROOT/'phase12'/'sprite_pipeline.json'
SOURCE=ROOT/'src'/'phase12'/'bank06_sprite_handlers.asm'
SHA=json.loads((ROOT/'manifest.json').read_text())['sha256']
BLOCKS={
    'record_pointer_directory':(0x18000,0x18080),
    'counted_sprite_records':(0x18080,0x19932),
    'object_work_record_pointers':(0x19A77,0x19A99),
    'sprite_handler_dispatch':(0x19A99,0x19AA9),
    'fourteen_sprite_offsets':(0x19B29,0x19B45),
    'sixteen_sprite_offsets':(0x19B7C,0x19B90),
}
ROOTS=[0x9AF6,0x9AA9,0x9AF7,0x9B45,0x9B90,0x9BC1,0x9BB9,0x9BF4]


def generate(rom):
    if len(rom)!=0x40000 or hashlib.sha256(rom).hexdigest()!=SHA:
        raise ValueError('ROM fingerprint mismatch')
    oldrows,oldowners,*_=inventory(rom)
    code,owners,uncertain=walk_bank(rom,6,{cpu:['bank6 $9A99 indexed handler table'] for cpu in ROOTS})
    assert not uncertain,uncertain
    oldstarts={row[0] for row in oldrows}
    newrows=[]
    for off,(end,inst) in sorted(code.items()):
        if off in oldstarts:
            assert set(range(off,end))<=set(oldowners)
            continue
        assert set(range(off,end)).isdisjoint(oldowners),'New code overlaps prior instruction'
        cpu=0x8000+(off-0x18000)
        raw=rom[off:end]
        assert raw==encode(inst,cpu)
        newrows.append((off,cpu,inst,raw,'phase12 bounded sprite handler CFG'))
    newcode=set().union(*(set(range(r[0],r[0]+len(r[3]))) for r in newrows))
    assert len(newcode)==241 and len(newrows)==119
    # The 8-word table is indexed from HL=$9A99 by RST $0008 in the
    # fixed-bank helper; all eight entries must point to instruction starts.
    assert rom[0x19A68:0x19A6C]==bytes.fromhex('21 99 9A CF')
    dispatch=[int.from_bytes(rom[p:p+2],'little') for p in range(0x19A99,0x19AA9,2)]
    assert dispatch==ROOTS
    assert set(dispatch)<={0x8000+(p-0x18000) for p in code}
    # $9A77 is referenced as a 17-word pointer table via the index scan
    # in the $9A2F-$9A76 object traversal. It enumerates $30-byte RAM slots.
    assert bytes.fromhex('21 77 9A') in rom[0x19A2D:0x19A77]
    objects=[int.from_bytes(rom[p:p+2],'little') for p in range(0x19A77,0x19A99,2)]
    assert objects==list(range(0xC200,0xC501,0x30)) and len(objects)==17
    # Two fixed-size relative-position tables directly precede the handler
    # entrypoints and their lengths are set by immediate loop counters.
    assert rom[0x19AF7:0x19AFA]==bytes.fromhex('21 29 9B')
    assert rom[0x19B01:0x19B03]==bytes.fromhex('06 0E')
    assert rom[0x19B45:0x19B48]==bytes.fromhex('21 7C 9B')
    assert rom[0x19B4F:0x19B51]==bytes.fromhex('06 10')
    assert rom[0x19B6A:0x19B6C]==bytes.fromhex('0E 04')
    # Provenance of the sprite SAT upload: $3F00 and $3F80 control writes,
    # 64 OUTI from $DD00 and 128 OUTI from $DD40.
    assert rom[0x427:0x433]==bytes.fromhex('AF D3 BF 3E 7F D3 BF 0E BE 21 00 DD')
    assert rom[0x433:0x43F]==bytes.fromhex('CD BF 04 3C D3 BF 3D D3 BF 21 40 DD')
    assert rom[0x43F:0x53F]==b'\xED\xA3'*128
    assert rom[0x53F]==0xC9
    # The code in $04BF-$053E is reached first by CALL ($04BF), then by
    # fallthrough from $043F: 64 + 64 + 64 OUTI = 192 bytes total.
    assert rom[0x4BF:0x53F]==b'\xED\xA3'*64
    assert rom[0x43F:0x4BF]==b'\xED\xA3'*64
    records=extract(rom)
    assert len(records)==64 and all(1<=r['count']<=64 for r in records)
    assert all(2*r['count']<=128 for r in records)
    assert len(rom[0x18080:0x19932])==6322
    # The complete contiguous physical region consists entirely of preexisting
    # code, the new handlers, and six bounded data spans. No opaque fill.
    lo,hi=0x18000,0x19C18
    codes=set(oldowners)&set(range(lo,hi))
    newdata=set()
    metadata={}
    for name,(a,b) in BLOCKS.items():
        region=set(range(a,b))
        assert not region&(codes|set(owners)|newdata),f'Overlapping {name}'
        newdata.update(region)
        metadata[name]={'start':f'{a:05X}','end_exclusive':f'{b:05X}',
                        'bytes':b-a,'sha256':hashlib.sha256(rom[a:b]).hexdigest()}
    assert len(codes)==403 and len(newcode)==241
    assert codes|newcode|newdata==set(range(lo,hi))
    assert len(newdata)==6548
    assert len(newdata)-6322-128==98
    # Do not double count data from prior phases.
    assert set(range(0x18000,0x19932)) <= newdata
    reconstructed=render(6,newrows)
    binary,labels=assemble(reconstructed)
    assert not labels and len(binary)==len(newcode)
    for off,cpu,asm,raw,origin in newrows:
        assert bytes(binary[p] for p in range(cpu,cpu+len(raw)))==raw
    code_sha=hashlib.sha256(b''.join(rom[p:p+len(rom[p:e])] for p,(e,_) in sorted(code.items()))).hexdigest()
    report={
        'schema':'ys-phase12-sprite-pipeline-v1','rom_sha256':SHA,
        'contiguous_bank6_region':{'start':'18000','end_exclusive':'19C18','bytes':hi-lo,
                                   'previously_assembled_code_bytes':403,
                                   'newly_assembled_code_bytes':len(newcode),
                                   'structurally_reencoded_data_bytes':len(newdata),
                                   'raw_rom_in_repository':False},
        'new_code':{'instruction_count':len(newrows),'bytes':len(newcode),'rooted_targets': [f'{x:04X}' for x in ROOTS],
                    'sha256':hashlib.sha256(b''.join(row[3] for row in newrows)).hexdigest(),
                    'full_reached_code_sha256':code_sha},
        'data_spans':metadata,
        'object_work_record_pointer_values':{'count':len(objects),'start':'C200','end':'C500','stride':48},
        'handler_dispatch':{'entries':len(dispatch),'targets':[f'{x:04X}' for x in dispatch]},
        'VDP_sprite_attribute_table':{'vram_first':'3F00','ram_first':'DD00','y_bytes':64,
            'vram_second':'3F80','ram_second':'DD40','x_tile_bytes':128,'total_bytes':192,
            'output_port':'BE','control_port':'BF','transfer_opcode':'OUTI'},
        'record_capacity_check':{'record_count':len(records),'maximum_elements':max(r['count'] for r in records),
                                 'max_y_output_bytes':64,'max_x_tile_output_bytes':128},
        'new_distinct_assembly_bytes':241,'new_distinct_structured_data_bytes':98,
        'new_distinct_classified_bytes':339,
        'cumulative_assembler_matched_bytes':12439+241,
        'cumulative_reversible_data_bytes':12082+98,
        'cumulative_code_and_reversible_data_bytes':24521+339,
        'cumulative_candidate_coverage_bytes':44601+339,
        'cumulative_candidate_coverage_percentage':round((44601+339)/0x40000*100,4),
        'limitations':['No independent assembler or emulator trace',
                       'RAM sprite buffers can contain additional data or padding beyond individual records',
                       'Sprite semantics inferred from instruction flow and VDP/SAT hardware layout',
                       'Outside $18000-$19C18 bank6 data boundaries remain unverified']}
    return reconstructed,report


def main():
    p=argparse.ArgumentParser()
    p.add_argument('rom',type=Path)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--write',action='store_true')
    g.add_argument('--check',action='store_true')
    ns=p.parse_args()
    source,report=generate(ns.rom.read_bytes())
    result=json.dumps(report,indent=2)+'\n'
    if ns.write:
        SOURCE.parent.mkdir(parents=True,exist_ok=True)
        REPORT.parent.mkdir(parents=True,exist_ok=True)
        SOURCE.write_text(source)
        REPORT.write_text(result)
    else:
        assert SOURCE.read_text()==source,'Assembly snapshot mismatch'
        assert REPORT.read_text()==result,'Metadata snapshot mismatch'
    print(f"PASS Phase12: {report['new_distinct_assembly_bytes']} new assembled code bytes, "
          f"{report['new_distinct_structured_data_bytes']} new structured data bytes, "
          f"{report['contiguous_bank6_region']['bytes']} fully accounted contiguous bank6 bytes")

if __name__=='__main__':main()
