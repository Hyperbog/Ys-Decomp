#!/usr/bin/env python3
"""Build Ys ROM with Phase17 graphics encoded from editable pixel rows.

UNRECOVERED bytes still come from the user-provided ROM. This is an overlay,
not a source-only rebuild and not an emulator/external assembler validation.
"""
import argparse
import hashlib
import json
from pathlib import Path
from build_sms_phase14 import ROOT, ROM_SIZE, SOURCES, offset, validated_rom
from build_phase16 import build as build16
from source_tables_phase15 import load_verified_sources
from structured_data_phase16 import load_verified as load16
from graphics_source_phase17 import load_verified as load17
from z80_roundtrip_phase10 import assemble


def source_positions(root=ROOT):
    positions=set()
    for rel,bank in SOURCES:
        instructions,_=assemble((root/rel).read_text(encoding='utf-8'))
        positions.update(offset(bank,pc) for pc in instructions)
    for bank,table in load_verified_sources(root).items():
        positions.update(offset(bank,pc) for pc in table['bytes'])
    for bank,record in load16(root).items():
        positions.update(offset(bank,pc) for pc in record['bytes'])
    if len(positions)!=22605:
        raise ValueError('Phase16 provenance changed')
    return positions


def build(rom,root=ROOT):
    validated_rom(rom)
    full,old=build16(rom,root=root)
    prior=source_positions(root)
    added=set()
    out=bytearray(full)
    modules=[]
    for bank,data in sorted(load17(root).items()):
        for pc,v in data['bytes'].items():
            where=offset(bank,pc)
            if where in prior or where in added:
                raise ValueError(f'Phase17 source overlaps existing ROM ownership at {where:05X}')
            if rom[where]!=v:
                raise ValueError(f'Graphics bytes differ from supplied ROM at {where:05X}')
            added.add(where)
            out[where]=v
        modules.append({'bank':bank,'file':data['source'],'source_bytes':len(data['bytes'])})
    if len(added)!=15688 or len(prior|added)!=38293 or bytes(out)!=rom:
        raise ValueError('Phase17 ROM-source coverage or output mismatch')
    report={
      'schema':'ys-phase17-source-overlay-v1',
      'rom_sha256':hashlib.sha256(rom).hexdigest(),
      'rom_bytes':ROM_SIZE,
      'z80_source_bytes':old['z80_source_bytes'],
      'phase15_tables_bytes':old['phase15_structured_source_bytes'],
      'phase16_semantic_records_bytes':old['phase16_new_structured_source_bytes'],
      'phase17_graphics_source_bytes':len(added),
      'source_backed_bytes':len(prior|added),
      'fallback_bytes':ROM_SIZE-len(prior|added),
      'source_backed_percent':round(100*len(prior|added)/ROM_SIZE,4),
      'source_backed_modules':modules,
      'per_bank':[{'bank':i,
                   'source_bytes':sum(i*0x4000<=p<(i+1)*0x4000 for p in prior|added),
                   'fallback_bytes':0x4000-sum(i*0x4000<=p<(i+1)*0x4000 for p in prior|added)} for i in range(16)],
      'prior_candidate_classification_bytes':58133,
      'new_distinct_classified_bytes':0,
      'source_only_full_rom':False,
      'independent_external_assembler_verified':False,
      'emulator_runtime_trace_verified':False,
      'note':'Source-backed 15,688 previously classified graphics bytes; pixel-level source from user ROM, not new discovery. Original ROM required as template for remaining bytes.'
    }
    return bytes(out),report


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('rom',type=Path)
    ap.add_argument('--report',type=Path,default=ROOT/'phase17/build_report.json')
    ap.add_argument('--verify',action='store_true')
    ap.add_argument('--out',type=Path)
    a=ap.parse_args()
    if a.out and a.out.resolve()==a.rom.resolve():
        ap.error('refusing to overwrite source ROM')
    full,report=build(a.rom.read_bytes())
    if a.verify:
        if json.loads(a.report.read_text())!=report:
            raise SystemExit('Phase17 build report drift')
    else:
        a.report.write_text(json.dumps(report,indent=2)+'\n')
    if a.out:a.out.write_bytes(full)
    print(f'Phase17 source-backed {report["source_backed_bytes"]}, fallback {report["fallback_bytes"]}; sha256 {report["rom_sha256"]}')
if __name__=='__main__':main()
