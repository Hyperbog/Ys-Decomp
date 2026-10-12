#!/usr/bin/env python3
"""Nine source-only 16KiB SMS banks: 0,1,2,3,4,6,7,8,10.

Full cartridge remains an owner-ROM-assisted overlay for seven unfinished banks.
"""
import argparse
import hashlib
import json
from pathlib import Path
from build_sms_phase14 import ROOT,validated_rom
from build_system_m7 import build as previous,complete_banks as prev_banks,SOURCED as OLD
from whole_banks08_10 import full_bank,new_bytes,new_code

SIZE=0x4000;BANKS=[0,1,2,3,4,6,7,8,10];ADD={8:SIZE-138,10:SIZE-75}
NEW=sum(ADD.values());SOURCED=OLD+NEW

def sha(b):return hashlib.sha256(b).hexdigest()
def complete_banks(root=ROOT):
    out=prev_banks(root)
    for n in ADD:out[n]=full_bank(n,root)
    if sorted(out)!=BANKS or any(len(b)!=SIZE for b in out.values()):raise ValueError('Source-only bank list invalid')
    return out

def build(rom,root=ROOT):
    validated_rom(rom)
    old,prior=previous(rom,root)
    output=bytearray(old)
    for bank in ADD:
        b=full_bank(bank,root);start=bank*SIZE
        if old[start:start+SIZE]!=b or rom[start:start+SIZE]!=b:
            raise ValueError(f'Bank{bank} source mismatch against verified baseline')
        output[start:start+SIZE]=b
    if bytes(output)!=rom:raise ValueError('M8 whole-ROM drift')
    rows=[]
    for row in prior['per_bank']:
        n=row['bank'];count=row['source_backed_bytes']+ADD.get(n,0)
        if not 0<=count<=SIZE or (count==SIZE)!=(n in BANKS):
            raise ValueError('Source bank accounting incorrect')
        rows.append({'bank':n,'source_backed_bytes':count,
          'original_rom_fallback_bytes':SIZE-count,'source_only_complete':count==SIZE,
          'sha256':sha(output[n*SIZE:(n+1)*SIZE])})
    if sum(row['source_backed_bytes'] for row in rows)!=SOURCED:raise ValueError('Source owner count drift')
    index={}
    for n in ADD:
        data,ownership=new_bytes(n,root)
        index[str(n)]={'previous_instruction_bytes':SIZE-ADD[n],
              'new_instruction_bytes':len(new_code(root)) if n==8 else 0,
              'new_source_data_bytes':len(data),'newly_source_backed_bytes':ADD[n],
              'inventory':ownership}
        if len(data)+index[str(n)]['new_instruction_bytes']!=ADD[n]:
            raise ValueError('Bank closure source accounting mismatch')
    report={'schema':'ys-whole-system-nine-banks-v1','rom_sha256':sha(output),
       'rom_bytes':len(output),'bank_count':16,'source_only_complete_banks':BANKS,
       'complete_source_only_bank_bytes':SIZE*len(BANKS),
       'prior_source_backed_bytes':OLD,'new_source_backed_bytes':NEW,
       'newly_completed_banks':list(ADD),'new_bank_metadata':index,
       'source_backed_bytes':SOURCED,'source_backed_pct':round(100*SOURCED/len(output),4),
       'original_rom_fallback_bytes':len(output)-SOURCED,
       'source_only_complete_rom':False,'external_wla_dx_verified':False,
       'full_emulator_verified':False,'bank8_script_format_decoded':False,
       'bank10_resource_format_decoded':False,'per_bank':rows,
       'limitations':['Nine physical ROM banks are source-independent; seven still need original-ROM fallback.',
          'Bank8 main script and bank10 assets are preserved in explicit unresolved source chunks.',
          'Bank10 encoded text bytes are pointer-bounded, but font/character encoding is not established.',
          'New bank8 mnemonics match byte encoding but are not gameplay-emulator traced.',
          'External Z80 assembler and whole-system emulator still unverified.']}
    return bytes(output),report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',nargs='?',type=Path);p.add_argument('--standalone-banks',action='store_true')
    p.add_argument('--output-directory',type=Path);p.add_argument('--out',type=Path)
    p.add_argument('--check',action='store_true')
    p.add_argument('--report',type=Path,default=ROOT/'whole_system/build_report_m8.json')
    a=p.parse_args()
    if a.standalone_banks:
        banks=complete_banks()
        if a.output_directory:
            a.output_directory.mkdir(exist_ok=True,parents=True)
            for n,b in banks.items():(a.output_directory/f'bank{n:02}.bin').write_bytes(b)
        for n,b in sorted(banks.items()):print(f'Bank {n:02}: {len(b)} ROM-free source bytes, SHA256 {sha(b)}')
        return
    if a.rom is None:p.error('Owner ROM required for seven other banks')
    if a.out and a.out.resolve()==a.rom.resolve():p.error('Cannot overwrite owner ROM')
    out,report=build(a.rom.read_bytes())
    if a.check:
        if report!=json.loads(a.report.read_text()):raise ValueError('M8 report drift')
    else:a.report.write_text(json.dumps(report,indent=2)+'\n')
    if a.out:a.out.write_bytes(out)
    print('M8 nine complete banks',BANKS,'source-backed',SOURCED,'fallback',report['original_rom_fallback_bytes'],'SHA256',sha(out))
if __name__=='__main__':main()
