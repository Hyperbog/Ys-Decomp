#!/usr/bin/env python3
"""Six-source-bank (0,1,2,3,6,7) ROM overlay and closure ledger."""
import argparse
import hashlib
import json
from pathlib import Path
from build_sms_phase14 import ROOT, validated_rom
from build_system_m5 import build as prior_build,complete_banks as prior_banks,SOURCED as PRIOR
from whole_bank01 import full_bank as bank01, new_data as bank01_data,new_code as bank01_code

SIZE=0x4000
NEW=15605
SOURCED=PRIOR+NEW
BANKS=[0,1,2,3,6,7]
def sha(b):return hashlib.sha256(b).hexdigest()

def complete_banks(root=ROOT):
    banks=prior_banks(root);banks[1]=bank01(root)
    if sorted(banks)!=BANKS or any(len(x)!=SIZE for x in banks.values()):
        raise ValueError('Six-bank source-only partition drift')
    return banks

def build(rom,root=ROOT):
    validated_rom(rom)
    baseline,prior=prior_build(rom,root)
    bank=bank01(root)
    if baseline[SIZE:2*SIZE]!=bank or rom[SIZE:2*SIZE]!=bank:
        raise ValueError('Bank1 independently sourced image mismatch')
    output=bytearray(baseline);output[SIZE:2*SIZE]=bank
    if bytes(output)!=rom:raise ValueError('M6 full ROM byte identity mismatch')
    rows=[]
    for r in prior['per_bank']:
        n=r['bank'];covered=r['source_backed_bytes']+(NEW if n==1 else 0)
        if not 0<=covered<=SIZE or (covered==SIZE)!=(n in BANKS):
            raise ValueError('Six-bank source ownership discrepancy')
        rows.append({'bank':n,'source_backed_bytes':covered,
             'original_rom_fallback_bytes':SIZE-covered,
             'source_only_complete':covered==SIZE,
             'sha256':sha(output[n*SIZE:(n+1)*SIZE])})
    if len(rows)!=16 or sum(r['source_backed_bytes'] for r in rows)!=SOURCED:
        raise ValueError('M6 16-bank coverage ledger disagreement')
    metadata=json.loads((root/'wholebank01/digests.json').read_text())
    data,inventory=bank01_data(root);code=bank01_code(root)
    if len(data)+len(code)!=NEW or metadata['new_data_bytes']!=len(data):
        raise ValueError('M6 source/data split drift')
    report={'schema':'ys-whole-system-six-banks-v1','rom_sha256':sha(output),
         'rom_bytes':len(output),'bank_count':16,'source_only_complete_banks':BANKS,
         'complete_source_only_bank_bytes':SIZE*len(BANKS),
         'prior_source_backed_bytes':PRIOR,'new_source_backed_bytes':NEW,
         'new_bank1_candidate_z80_instruction_bytes':len(code),
         'new_bank1_source_data_bytes':len(data),
         'bank1_unresolved_semantics_bytes':metadata['unresolved_bytes'],
         'bank1_structured_pointer_bytes':metadata['pointer_bytes'],
         'bank1_ff_padding_bytes':metadata['padding_bytes'],
         'source_backed_bytes':SOURCED,'source_backed_pct':round(SOURCED*100/len(output),4),
         'original_rom_fallback_bytes':len(output)-SOURCED,
         'source_only_complete_rom':False,'external_wla_dx_verified':False,
         'full_emulator_verified':False,'bank1_semantics_fully_decoded':False,
         'per_bank':rows,
         'limitations':['Six physical banks generate independently; ten still use owner ROM fallback.',
             'Bank1 has many unresolved bytes potentially mixing code and data.',
             'Candidate Z80 decoding does not certify the original executable boundaries.',
             'No independent WLA-DX compilation or full-game emulation verified.']}
    return bytes(output),report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',nargs='?',type=Path);p.add_argument('--standalone-banks',action='store_true')
    p.add_argument('--out',type=Path);p.add_argument('--output-directory',type=Path)
    p.add_argument('--check',action='store_true')
    p.add_argument('--report',type=Path,default=ROOT/'whole_system/build_report_m6.json')
    args=p.parse_args()
    if args.standalone_banks:
        banks=complete_banks()
        if args.output_directory:
            args.output_directory.mkdir(parents=True,exist_ok=True)
            for n,v in banks.items():(args.output_directory/f'bank{n:02}.bin').write_bytes(v)
        for n,v in sorted(banks.items()):print(f'Bank {n:02}: {len(v)} independent bytes, SHA256 {sha(v)}')
        return
    if args.rom is None:p.error('Original user-owned ROM is required for full-cartridge fallback')
    if args.out and args.out.resolve()==args.rom.resolve():p.error('Refusing to overwrite source ROM')
    image,report=build(args.rom.read_bytes())
    if args.check:
        if json.loads(args.report.read_text())!=report:raise ValueError('M6 report drift')
    else:args.report.write_text(json.dumps(report,indent=2)+'\n')
    if args.out:args.out.write_bytes(image)
    print('M6 six complete banks',BANKS,'source-backed',SOURCED,'fallback',report['original_rom_fallback_bytes'],'SHA256',report['rom_sha256'])
if __name__=='__main__':main()
