#!/usr/bin/env python3
"""Seven-bank, ROM-independent source closures + template-assisted cartridge.

Bank4 is fully byte-owned; unresolved graphical format is not declared decoded.
"""
import argparse
import hashlib
import json
from pathlib import Path
from build_sms_phase14 import ROOT,validated_rom
from build_system_m6 import build as previous_build,complete_banks as old_banks,SOURCED as PREVIOUS
from whole_bank04 import full_bank as bank04,new_chunks
SIZE=0x4000; BANKS=[0,1,2,3,4,6,7]; NEW=16222; SOURCED=PREVIOUS+NEW

def sha(data):return hashlib.sha256(data).hexdigest()
def complete_banks(root=ROOT):
    banks=old_banks(root);banks[4]=bank04(root)
    if sorted(banks)!=BANKS or any(len(x)!=SIZE for x in banks.values()):
        raise ValueError('M7 source-only bank layout drift')
    return banks

def build(rom,root=ROOT):
    validated_rom(rom)
    old,prior=previous_build(rom,root)
    bank=bank04(root);at=SIZE*4
    if old[at:at+SIZE]!=bank or rom[at:at+SIZE]!=bank:
        raise ValueError('Bank4 new source mismatches original ROM')
    output=bytearray(old);output[at:at+SIZE]=bank
    if bytes(output)!=rom:raise ValueError('M7 whole-ROM reconstruction drift')
    rows=[]
    for r in prior['per_bank']:
        n=r['bank'];count=r['source_backed_bytes']+(NEW if n==4 else 0)
        if not 0<=count<=SIZE or (count==SIZE)!=(n in BANKS):
            raise ValueError('M7 bank completeness ledger mismatch')
        rows.append({'bank':n,'source_backed_bytes':count,
            'original_rom_fallback_bytes':SIZE-count,'source_only_complete':count==SIZE,
            'sha256':sha(output[n*SIZE:(n+1)*SIZE])})
    data,inv=new_chunks(root)
    if len(data)!=NEW or sum(x['bytes'] for x in inv)!=NEW or sum(x['source_backed_bytes'] for x in rows)!=SOURCED:
        raise ValueError('M7 bank ownership count mismatch')
    report={'schema':'ys-whole-system-seven-banks-v1','rom_sha256':sha(output),
        'rom_bytes':len(output),'bank_count':16,'source_only_complete_banks':BANKS,
        'complete_source_only_bank_bytes':SIZE*len(BANKS),
        'prior_source_backed_bytes':PREVIOUS,'new_source_backed_bytes':NEW,
        'new_bank4_source_data_bytes':NEW,'bank4_known_collision_descriptor_bytes':124,
        'bank4_known_collision_code_bytes':38,
        'bank4_four_lane_group_count':502,'bank4_unresolved_data_bytes':16064+86,
        'bank4_padding_bytes':72,'bank4_source_inventory':inv,
        'source_backed_bytes':SOURCED,'source_backed_pct':round(SOURCED*100/len(output),4),
        'original_rom_fallback_bytes':len(output)-SOURCED,
        'source_only_complete_rom':False,'external_wla_dx_verified':False,
        'full_emulator_verified':False,'bank4_graphics_format_decoded':False,
        'per_bank':rows,'limitations':[
          'Seven banks generated from source; nine banks remain dependent on original-ROM fallback.',
          'Bank4 502 grouping x32 is organizational only; actual graphics encoding and source format not proven.',
          'Collision routine bounded executions are not whole-system gameplay or timing verification.',
          'Independent WLA-DX assembly remains unverified.']}
    return bytes(output),report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',nargs='?',type=Path);p.add_argument('--standalone-banks',action='store_true')
    p.add_argument('--out',type=Path);p.add_argument('--output-directory',type=Path)
    p.add_argument('--check',action='store_true')
    p.add_argument('--report',type=Path,default=ROOT/'whole_system/build_report_m7.json')
    args=p.parse_args()
    if args.standalone_banks:
        banks=complete_banks()
        if args.output_directory:
            args.output_directory.mkdir(parents=True,exist_ok=True)
            for n,b in banks.items():(args.output_directory/f'bank{n:02}.bin').write_bytes(b)
        for n,b in sorted(banks.items()):print(f'Bank {n:02} {len(b)} ROM-free source bytes {sha(b)}')
        return
    if args.rom is None:p.error('Owner ROM required for nine remaining fallback banks')
    if args.out and args.out.resolve()==args.rom.resolve():p.error('Cannot overwrite original ROM')
    rom=args.rom.read_bytes();out,report=build(rom)
    if args.check:
        if report!=json.loads(args.report.read_text()):raise ValueError('M7 build report drift')
    else:args.report.write_text(json.dumps(report,indent=2)+'\n')
    if args.out:args.out.write_bytes(out)
    print('M7',BANKS,'source-backed',SOURCED,'fallback',report['original_rom_fallback_bytes'],'SHA256',sha(out))
if __name__=='__main__':main()
