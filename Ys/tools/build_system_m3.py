#!/usr/bin/env python3
"""Whole-system strict ROM overlay with complete source-only banks 0, 3, and 7.

The remaining 13 banks still require the user's original ROM as a template.
"""
import argparse
import hashlib
import json
from pathlib import Path
from build_sms_phase14 import ROOT, validated_rom
from build_whole_system import build as previous_build,assemble_complete_banks,BANK_BYTES
from whole_bank00 import full_bank as bank00

OLD=53249
NEW=8142
SOURCED=OLD+NEW

def digest(v):return hashlib.sha256(v).hexdigest()

def complete_banks(root=ROOT):
    result={0:bank00(root),**assemble_complete_banks(root)}
    if sorted(result)!=[0,3,7]:raise ValueError('Missing source-only bank')
    if any(len(blob)!=BANK_BYTES for blob in result.values()):raise ValueError('Short source-only bank')
    return result

def build(rom,root=ROOT):
    validated_rom(rom)
    old,report=previous_build(rom,root=root)
    out=bytearray(old)
    banks=complete_banks(root)
    for n,content in sorted(banks.items()):
        i=n*BANK_BYTES
        if old[i:i+BANK_BYTES]!=content or rom[i:i+BANK_BYTES]!=content:
            raise ValueError(f'Complete source bank{n} differs from original image')
        out[i:i+BANK_BYTES]=content
    if bytes(out)!=rom:raise ValueError('Full-ROM overlay mismatch')
    rows=[]
    for prior in report['per_bank']:
        n=prior['bank'];number=prior['source_backed_bytes']+(NEW if n==0 else 0)
        rows.append({'bank':n,'source_backed_bytes':number,
                     'original_rom_fallback_bytes':BANK_BYTES-number,
                     'source_only_complete':number==BANK_BYTES,
                     'sha256':digest(out[n*BANK_BYTES:(n+1)*BANK_BYTES])})
    if sum(r['source_backed_bytes'] for r in rows)!=SOURCED or [r['bank'] for r in rows if r['source_only_complete']]!=[0,3,7]:
        raise ValueError('System coverage accounting mismatch')
    source_meta=json.loads((root/'wholebank00/digests.json').read_text())
    result={'schema':'ys-whole-system-three-banks-v1','rom_sha256':digest(out),
        'rom_bytes':len(out),'bank_count':16,'source_only_complete_banks':[0,3,7],
        'source_only_complete_bank_bytes':3*BANK_BYTES,
        'prior_source_backed_bytes':OLD,'new_source_backed_bytes':NEW,
        'new_bank0_z80_instruction_bytes':source_meta['new_code_bytes'],
        'new_bank0_field_or_unresolved_data_bytes':source_meta['new_data_bytes'],
        'new_bank0_typed_and_fill_bytes':source_meta['new_structured_bytes'],
        'new_bank0_unresolved_bytes':source_meta['unresolved_bytes'],
        'source_backed_bytes':SOURCED,'source_backed_pct':round(SOURCED*100/len(out),4),
        'original_rom_fallback_bytes':len(out)-SOURCED,
        'external_wla_dx_verified':False,'full_emulator_verified':False,
        'source_only_complete_rom':False,'per_bank':rows,
        'limitations':['Full source-only byte closure is achieved only in banks 0,3,7.',
          'Some bank0 data remains opaque and candidate Z80 instructions are not all execution-traced.',
          'Other banks require original-ROM fallback. External assembler and gameplay traces remain unverified.']}
    return bytes(out),result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',nargs='?',type=Path)
    p.add_argument('--check',action='store_true')
    p.add_argument('--report',type=Path,default=ROOT/'whole_system/build_report_m3.json')
    p.add_argument('--standalone-banks',action='store_true')
    p.add_argument('--output-directory',type=Path)
    p.add_argument('--out',type=Path)
    a=p.parse_args()
    if a.standalone_banks:
        banks=complete_banks()
        if a.output_directory:
            a.output_directory.mkdir(parents=True,exist_ok=True)
            for n,b in banks.items():(a.output_directory/f'bank{n:02}.bin').write_bytes(b)
        for n,b in banks.items():print(f'Bank {n}: {len(b)} independently rebuilt bytes, SHA256 {digest(b)}')
        return
    if a.rom is None:p.error('Full-ROM overlay requires the locally owned original ROM')
    if a.out and a.out.resolve()==a.rom.resolve():p.error('Refusing to overwrite original ROM')
    result,report=build(a.rom.read_bytes())
    if a.check:
        if json.loads(a.report.read_text())!=report:raise ValueError('Milestone 3 build ledger drift')
    else:a.report.write_text(json.dumps(report,indent=2)+'\n')
    if a.out:a.out.write_bytes(result)
    print('Complete banks',report['source_only_complete_banks'],'source-backed',report['source_backed_bytes'],
          'fallback',report['original_rom_fallback_bytes'],'SHA256',report['rom_sha256'])

if __name__=='__main__':main()
