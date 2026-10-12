#!/usr/bin/env python3
"""Phase21 strict ROM-template build with new independently regenerated data.

The source itself builds without input ROM; full ROM still needs the original
for all unrecovered addresses. Unknown audio commands and bank-3 text controls
are deliberately not claimed semantically decoded.
"""
import argparse
import hashlib
import json
from pathlib import Path
from build_sms_phase14 import ROOT, ROM_SIZE, offset, validated_rom
from build_phase17 import build as previous_build, source_positions
from graphics_source_phase17 import load_verified as graphics
from phase21_semantic_sources import load_verified

OLD=38293
NEW=8056

def old_positions(root=ROOT):
    old=source_positions(root)
    for bank,data in graphics(root).items():
        for pc in data['bytes']:
            i=offset(bank,pc)
            if i in old:raise ValueError('Phase17 owner overlap')
            old.add(i)
    if len(old)!=OLD:raise ValueError('Previously verified source region changed')
    return old


def build(rom, root=ROOT):
    validated_rom(rom)
    old_image,old_report=previous_build(rom,root=root)
    covered=old_positions(root)
    sources,region_count,digest=load_verified(root)
    image=bytearray(old_image)
    added=set()
    for (bank,pc),value in sources.items():
        pos=offset(bank,pc)
        if pos in covered or pos in added:raise ValueError(f'Phase21 source overlap at {pos:05X}')
        if rom[pos]!=value:raise ValueError(f'Phase21 source mismatches original ROM at {pos:05X}')
        image[pos]=value
        added.add(pos)
    if len(added)!=NEW or len(covered|added)!=OLD+NEW or bytes(image)!=rom:
        raise ValueError('Source ownership/output mismatch')
    report={
      'schema':'ys-phase21-source-overlay-v1',
      'rom_sha256':hashlib.sha256(image).hexdigest(),
      'rom_bytes':ROM_SIZE,
      'previous_source_backed_bytes':OLD,
      'new_source_backed_bytes':NEW,
      'new_regions':region_count,
      'new_source_sha256':digest,
      'source_backed_bytes':OLD+NEW,
      'fallback_bytes':ROM_SIZE-OLD-NEW,
      'source_backed_percent':round((OLD+NEW)*100/ROM_SIZE,4),
      'candidate_classification_bytes':58133+357,
      'new_distinct_classification_bytes':357,
      'new_distinct_scope':'24 x (1+9*N) variable music descriptor headers; event bodies remain only bounded',
      'per_bank':[{'bank':i,'source_bytes':sum(i*0x4000<=a<(i+1)*0x4000 for a in covered|added),
                   'fallback_bytes':0x4000-sum(i*0x4000<=a<(i+1)*0x4000 for a in covered|added)} for i in range(16)],
      'source_only_rom':False,
      'external_wla_verified':False,
      'full_system_emulator_verified':False,
      'note':'Source text stores numeric glyph slots and unresolved metadata as literal bytes, NOT decrypted game dialogue. Original ROM still supplies all fallback bytes. 357 additional previously unclassified descriptor headers are structurally anchored; other regenerated regions were previously classified.'}
    return bytes(image),report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path)
    p.add_argument('--check',action='store_true')
    p.add_argument('--report',type=Path,default=ROOT/'phase21/build_report.json')
    p.add_argument('--out',type=Path)
    a=p.parse_args()
    if a.out and a.out.resolve()==a.rom.resolve():p.error('Refusing to overwrite original ROM')
    output,report=build(a.rom.read_bytes())
    if a.check:
        if json.loads(a.report.read_text())!=report:raise SystemExit('Phase21 build report drift')
    else:
        a.report.write_text(json.dumps(report,indent=2)+'\n')
    if a.out:a.out.write_bytes(output)
    print('Phase21 source-backed',report['source_backed_bytes'], 'fallback', report['fallback_bytes'],'SHA',report['rom_sha256'])

if __name__=='__main__':main()
