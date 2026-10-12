#!/usr/bin/env python3
"""Whole-ROM strict overlay with source-only physical banks 0, 3, 6, 7.

Normal independent bank assembly does not read the original game ROM. The full
16-bank overlay still requires the user's original ROM for the 12 other banks.
"""
import argparse
import hashlib
import json
from pathlib import Path
from build_sms_phase14 import ROOT, validated_rom
from build_system_m3 import build as build_m3,complete_banks as m3_banks
from whole_bank06 import full_bank as bank06,new_chunks

SIZE=0x4000
M3_BYTES=61391
BANK6_NEW=9192
SOURCE_BYTES=M3_BYTES+BANK6_NEW
EXPECTED_COMPLETE=[0,3,6,7]

def sha(b):return hashlib.sha256(b).hexdigest()

def complete_banks(root=ROOT):
    banks=m3_banks(root)
    banks[6]=bank06(root)
    if sorted(banks)!=EXPECTED_COMPLETE or any(len(s)!=SIZE for s in banks.values()):
        raise ValueError('Complete-bank list or length drift')
    return banks

def build(rom,root=ROOT):
    validated_rom(rom)
    old,previous=build_m3(rom,root)
    new=bank06(root)
    start=6*SIZE
    if rom[start:start+SIZE]!=new or old[start:start+SIZE]!=new:
        raise ValueError('Bank6 source-only bytes mismatch whole ROM')
    result=bytearray(old)
    result[start:start+SIZE]=new
    if bytes(result)!=rom:raise ValueError('Whole-ROM byte comparison failed')
    rows=[]
    for prior in previous['per_bank']:
        n=prior['bank'];value=prior['source_backed_bytes']+(BANK6_NEW if n==6 else 0)
        if (value==SIZE)!=(n in EXPECTED_COMPLETE):raise ValueError('Whole system bank ownership drift')
        rows.append({'bank':n,'source_backed_bytes':value,
                     'original_rom_fallback_bytes':SIZE-value,
                     'source_only_complete':value==SIZE,
                     'sha256':sha(result[n*SIZE:(n+1)*SIZE])})
    _,ownership=new_chunks(root)
    if sum(x['source_backed_bytes'] for x in rows)!=SOURCE_BYTES or len(rows)!=16:
        raise ValueError('System-level accounting mismatch')
    return bytes(result),{'schema':'ys-whole-system-four-complete-banks-v1',
        'rom_sha256':sha(result),'rom_bytes':len(result),'bank_count':16,
        'source_only_complete_banks':EXPECTED_COMPLETE,
        'complete_source_only_bank_bytes':4*SIZE,
        'prior_source_backed_bytes':M3_BYTES,
        'new_source_backed_bytes':BANK6_NEW,
        'source_backed_bytes':SOURCE_BYTES,
        'source_backed_pct':round(SOURCE_BYTES*100/len(result),4),
        'original_rom_fallback_bytes':len(result)-SOURCE_BYTES,
        'bank6_new_region_cpu_start':'9C18',
        'bank6_new_region_cpu_end_exclusive':'C000',
        'bank6_new_segments':ownership,
        'bank6_new_mnemonic_instruction_bytes':0,
        'bank6_new_count_prefixed_triplet_records':7,
        'bank6_new_layout_pointer_words':8,
        'bank6_new_unresolved_visual_bytes':7408,
        'external_wla_dx_verified':False,
        'full_system_emulator_verified':False,
        'full_rom_source_only':False,
        'per_bank':rows,
        'limitations':['Four banks byte-rebuild without original ROM; other twelve remain input-ROM-backed.',
          'Count-prefixed triplets have proven boundaries but uncertain field semantics; eight-byte visual lanes preserve bytes rather than prove a pixel format.',
          'Existing bounded sprite tests are not complete-game emulator runs; WLA-DX external validation not executed.']}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',nargs='?',type=Path)
    p.add_argument('--standalone-banks',action='store_true')
    p.add_argument('--output-directory',type=Path)
    p.add_argument('--out',type=Path)
    p.add_argument('--check',action='store_true')
    p.add_argument('--report',type=Path,default=ROOT/'whole_system/build_report_m4.json')
    args=p.parse_args()
    if args.standalone_banks:
        banks=complete_banks()
        if args.output_directory:
            args.output_directory.mkdir(parents=True,exist_ok=True)
            for n,b in banks.items():(args.output_directory/f'bank{n:02}.bin').write_bytes(b)
        for n,b in sorted(banks.items()):print(f'Bank {n:02} source-only {len(b)} bytes SHA256 {sha(b)}')
        return
    if args.rom is None:p.error('Whole-ROM overlay requires the original ROM')
    if args.out and args.rom.resolve()==args.out.resolve():p.error('Will not overwrite input ROM')
    rebuilt,report=build(args.rom.read_bytes())
    if args.check:
        if json.loads(args.report.read_text())!=report:raise ValueError('M4 ledger differs')
    else:args.report.write_text(json.dumps(report,indent=2)+'\n')
    if args.out:args.out.write_bytes(rebuilt)
    print('Complete source-only banks',report['source_only_complete_banks'],'source-backed',SOURCE_BYTES,
          'fallback',report['original_rom_fallback_bytes'],'full SHA256',report['rom_sha256'])
if __name__=='__main__':main()
