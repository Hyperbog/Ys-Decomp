#!/usr/bin/env python3
"""Phase16: source-backed Z80 and structured record overlay; ROM fallback remains.
No original ROM payload is generated or committed by default.
"""
import argparse
import hashlib
import json
from pathlib import Path
from build_sms_phase14 import ROOT, ROM_SIZE, SOURCES, offset, validated_rom
from build_phase15 import build as phase15_build
from structured_data_phase16 import load_verified
from symbolic_asm_phase16 import verify as symbolic_verify
from z80_roundtrip_phase10 import assemble

def build(rom,root=ROOT):
    validated_rom(rom)
    output, old=phase15_build(rom,root=root)
    owners=set()
    for relative,bank in SOURCES:
        content,_=assemble((root/relative).read_text())
        owners.update(offset(bank,pc) for pc in content)
    from source_tables_phase15 import load_verified_sources
    for bank,entry in load_verified_sources(root).items():
        owners.update(offset(bank,pc) for pc in entry['bytes'])
    if len(owners)!=14703:raise ValueError('baseline Phase15 source byte count changed')
    other=set(); source_modules=[]
    generated=bytearray(output)
    for bank,info in sorted(load_verified(root).items()):
        for pc,byte in info['bytes'].items():
            at=offset(bank,pc)
            if at in owners or at in other:raise ValueError('overlapping Phase16 ROM source at '+hex(at))
            if rom[at]!=byte:raise ValueError(f'Phase16 data/ROM mismatch at {at:05X}')
            other.add(at)
            generated[at]=byte
        source_modules.append({'bank':bank,'path':info['source'],'bytes':len(info['bytes'])})
    if len(other)!=7902 or len(owners|other)!=22605:raise ValueError('bad source ownership count')
    if bytes(generated)!=rom:raise ValueError('full image mismatch')
    symbolic=symbolic_verify(root)
    result={
      'schema':'ys-phase16-source-overlay-v1',
      'rom_sha256':hashlib.sha256(rom).hexdigest(),
      'rom_bytes':ROM_SIZE,
      'z80_source_bytes':old['assembly_source_bytes'],
      'phase15_structured_source_bytes':old['standalone_data_source_bytes'],
      'phase16_new_structured_source_bytes':len(other),
      'source_backed_bytes':len(owners|other),
      'fallback_bytes':ROM_SIZE-len(owners|other),
      'source_backed_percentage':round(100*len(owners|other)/ROM_SIZE,4),
      'structured_data_modules':source_modules,
      'symbolic_equivalent_modules':symbolic,
      'per_bank':[{'bank':i,'source_bytes':sum(i*0x4000<=a<(i+1)*0x4000 for a in owners|other),
                   'fallback_bytes':0x4000-sum(i*0x4000<=a<(i+1)*0x4000 for a in owners|other)} for i in range(16)],
      'prior_candidate_coverage_bytes':58133,
      'source_only_build':False,
      'external_assembler_verified':False,
      'rom_fallback_required':True,
      'note':'7,902 previously classified bytes converted to structured source; no new unique ROM classification. '
             'Data is stored in a field-level derived JSON representation; original asset values are now included. '
             'Symbolic assembly views are equivalent aliases, not additional code coverage.'
    }
    return bytes(generated),result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path)
    p.add_argument('--report',type=Path,default=ROOT/'phase16/build_report.json')
    p.add_argument('--verify',action='store_true')
    p.add_argument('--out',type=Path)
    a=p.parse_args()
    if a.out and a.out.resolve()==a.rom.resolve():p.error('refusing to overwrite input ROM')
    full,report=build(a.rom.read_bytes())
    if a.verify:
        if json.loads(a.report.read_text())!=report:raise SystemExit('Phase16 report drift')
    else:
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(json.dumps(report,indent=2)+'\n')
    if a.out:a.out.write_bytes(full)
    print('Phase16 source-backed:',report['source_backed_bytes'], 'fallback:',report['fallback_bytes'])
    print('SHA-256:',hashlib.sha256(full).hexdigest())
if __name__=='__main__':main()
