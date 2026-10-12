#!/usr/bin/env python3
"""System-wide strict ROM overlay incorporating independent FULL bank-7 source.

Use --bank7-only without a ROM for the true source-only physical bank-7 build.
All 15 other banks remain explicitly partial and need the original ROM template.
"""
import argparse
import hashlib
import json
from pathlib import Path
from build_sms_phase14 import ROOT, EXPECTED_SHA, validated_rom
from build_phase21 import build as prior_build
from whole_bank07 import full_bank, SIZE, BASE

NEW=2753
PRIOR=46349
CLASSIFIED_PRIOR=58490
NEW_CLASSIFIED=1665

def sha(b):return hashlib.sha256(b).hexdigest()

def build(rom,root=ROOT):
    validated_rom(rom)
    image,prior=prior_build(rom,root=root)
    standalone=full_bank(root)
    if image[BASE:BASE+SIZE]!=standalone or rom[BASE:BASE+SIZE]!=standalone:
        raise ValueError('Independent bank 7 differs from original ROM at some location')
    result=bytearray(image)
    result[BASE:BASE+SIZE]=standalone
    if bytes(result)!=rom or sha(result)!=EXPECTED_SHA:raise ValueError('Entire ROM does not match')
    by_bank=[]
    for item in prior['per_bank']:
        bank=item['bank'];src=item['source_bytes']+(NEW if bank==7 else 0)
        if bank==7 and src!=SIZE:raise ValueError('Bank 7 ownership not complete')
        by_bank.append({'bank':bank,'source_bytes':src,'fallback_bytes':SIZE-src,
                        'whole_bank_source_only':src==SIZE})
    sourced=PRIOR+NEW
    if sourced!=sum(x['source_bytes'] for x in by_bank):raise ValueError('System ownership ledger drift')
    report={
      'schema':'ys-whole-bank07-system-overlay-v1','rom_sha256':sha(result),
      'total_rom_bytes':len(result), 'bank_size_bytes':SIZE, 'bank_count':16,
      'whole_source_only_banks':[7],
      'whole_bank07_sha256':sha(standalone),
      'prior_source_backed_bytes':PRIOR,'new_source_backed_bytes':NEW,
      'source_backed_bytes':sourced,'source_backed_percent':round(100*sourced/len(result),4),
      'fallback_bytes':len(result)-sourced,'source_only_complete_rom':False,
      'candidate_classification_bytes':CLASSIFIED_PRIOR+NEW_CLASSIFIED,
      'new_structurally_bounded_bytes':NEW_CLASSIFIED,
      'new_semantically_unresolved_bytes':1088,
      'new_instruction_bytes':173,
      'new_bounded_structured_and_padding_bytes':NEW_CLASSIFIED-173,
      'independent_wla_dx_verified':False,'full_system_emulator_verified':False,
      'per_bank':by_bank,
      'note':'Bank7 is source-only and byte-complete. 1088 late-bank data bytes are reversible, deliberately semantically unresolved. Full ROM still contains 213042 ROM-template bytes from other banks.'}
    return bytes(result),report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',nargs='?',type=Path)
    p.add_argument('--bank7-only',action='store_true')
    p.add_argument('--out',type=Path)
    p.add_argument('--check',action='store_true')
    p.add_argument('--report',type=Path,default=ROOT/'wholebank07/build_report.json')
    a=p.parse_args()
    if a.bank7_only:
        bank=full_bank()
        if a.out:a.out.write_bytes(bank)
        print('Standalone, input-ROM-independent bank7:',len(bank),'bytes sha256',sha(bank))
        return
    if a.rom is None:p.error('full 16-bank template-assisted build requires original ROM')
    if a.out and a.out.resolve()==a.rom.resolve():p.error('Refusing to overwrite original ROM')
    binary,report=build(a.rom.read_bytes())
    if a.check:
        if json.loads(a.report.read_text())!=report:raise ValueError('Whole-bank build report drift')
    else:a.report.write_text(json.dumps(report,indent=2)+'\n')
    if a.out:a.out.write_bytes(binary)
    print('Whole-bank source backed:',report['source_backed_bytes'],'fallback:',report['fallback_bytes'],'SHA:',report['rom_sha256'])

if __name__=='__main__':main()
