#!/usr/bin/env python3
"""16-bank Ys SMS build: true source-only banks 3 and 7, explicit fallback elsewhere.

Full-system source independence is NOT yet attained. --standalone-banks works
without the original ROM and can output only the reconstructed bank images.
"""
import argparse
import hashlib
import json
from pathlib import Path
from build_sms_phase14 import ROOT,EXPECTED_SHA,validated_rom
from build_phase21 import build as baseline_build
from whole_bank03 import full_bank as bank03, BASE as BASE3
from whole_bank07 import full_bank as bank07, BASE as BASE7

BANK_BYTES=16384
PHASE21_SOURCE=46349
BANK3_NEW=4147
BANK7_NEW=2753
NEW_SOURCE=BANK3_NEW+BANK7_NEW
SOURCED=PHASE21_SOURCE+NEW_SOURCE
NEW_BOUNDED=1620+349

def sha(b):return hashlib.sha256(b).hexdigest()

def assemble_complete_banks(root=ROOT):
    return {3:bank03(root),7:bank07(root)}

def build(rom,root=ROOT):
    validated_rom(rom)
    result,baseline=baseline_build(rom,root=root)
    out=bytearray(result)
    independent=assemble_complete_banks(root)
    for bank,content in sorted(independent.items()):
        start=bank*BANK_BYTES
        if len(content)!=BANK_BYTES or result[start:start+BANK_BYTES]!=content:
            raise ValueError(f'Complete bank {bank} does not match ROM or phase21 baseline')
        out[start:start+BANK_BYTES]=content
    if bytes(out)!=rom or sha(out)!=EXPECTED_SHA:raise ValueError('16-bank output mismatch')
    per_bank=[]
    for row in baseline['per_bank']:
        bank=row['bank']
        added={3:BANK3_NEW,7:BANK7_NEW}.get(bank,0)
        src=row['source_bytes']+added
        if (bank in independent)!=(src==BANK_BYTES):
            raise ValueError(f'Complete-bank accounting error in bank {bank}')
        per_bank.append({'bank':bank,'source_backed_bytes':src,
                         'original_rom_fallback_bytes':BANK_BYTES-src,
                         'source_only_complete':src==BANK_BYTES,
                         'sha256':sha(out[bank*BANK_BYTES:(bank+1)*BANK_BYTES])})
    if sum(x['source_backed_bytes'] for x in per_bank)!=SOURCED:
        raise ValueError('System-wide byte accounting mismatch')
    return bytes(out),{
        'schema':'ys-whole-system-two-complete-banks-v1',
        'rom_bytes':len(out),'rom_sha256':sha(out),'rom_bank_count':16,
        'complete_source_only_banks':[3,7],
        'complete_source_only_bank_bytes':len(independent)*BANK_BYTES,
        'previous_source_backed_bytes':PHASE21_SOURCE,
        'new_source_backed_bytes':NEW_SOURCE,
        'new_source_backed_bank3':BANK3_NEW,'new_source_backed_bank7':BANK7_NEW,
        'total_source_backed_bytes':SOURCED,
        'total_source_backed_pct':round(SOURCED*100/len(out),4),
        'total_fallback_bytes':len(out)-SOURCED,
        'new_structurally_bounded_nonpadding_bytes':NEW_BOUNDED,
        'new_explicit_padding_bytes':45+1843,
        'new_unresolved_visual_bytes':1088+1955,
        'new_matched_instruction_bytes':173,
        'candidate_coverage_bytes':58490+NEW_BOUNDED,
        'full_rom_source_only':False,
        'external_wla_dx_verified':False,
        'full_system_emulator_verified':False,
        'per_bank':per_bank,
        'qualification':'Banks3/7 byte-complete from source; compression, text grammar and parts of map records remain semantically unresolved. All other bank fallbacks still come from original ROM.'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',nargs='?',type=Path)
    p.add_argument('--standalone-banks',action='store_true')
    p.add_argument('--output-directory',type=Path)
    p.add_argument('--check',action='store_true')
    p.add_argument('--out',type=Path)
    p.add_argument('--report',type=Path,default=ROOT/'whole_system/build_report.json')
    a=p.parse_args()
    if a.standalone_banks:
        banks=assemble_complete_banks()
        if a.output_directory:
            a.output_directory.mkdir(parents=True,exist_ok=True)
            for bank,blob in banks.items():
                (a.output_directory/f'bank{bank:02}.bin').write_bytes(blob)
        for bank,blob in banks.items():
            print(f'Source-only bank{bank:02}: {len(blob)} bytes SHA256 {sha(blob)}')
        return
    if a.rom is None:p.error('Complete template-assisted 256KiB ROM build requires input ROM')
    if a.out and a.rom.resolve()==a.out.resolve():p.error('Refusing to overwrite original ROM')
    result,report=build(a.rom.read_bytes())
    if a.check:
        if json.loads(a.report.read_text())!=report:raise ValueError('Whole-system build report drift')
    else:
        a.report.write_text(json.dumps(report,indent=2)+'\n')
    if a.out:a.out.write_bytes(result)
    print('Whole system: source-backed',report['total_source_backed_bytes'],
          'fallback',report['total_fallback_bytes'],'whole banks',report['complete_source_only_banks'],
          'SHA256',report['rom_sha256'])
if __name__=='__main__':main()
