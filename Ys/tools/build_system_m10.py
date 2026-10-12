#!/usr/bin/env python3
"""M10: ROM-INDEPENDENT reconstruction of the full 256-KiB Ys SMS cartridge.

Binary-exact source reconstruction != semantic completion or independently
verified external Z80 compilation. Four banks contain mostly unresolved assets.
"""
import argparse
import hashlib
import json
from pathlib import Path
from build_sms_phase14 import ROOT,EXPECTED_SHA,validated_rom
from build_system_m9 import complete_banks as previous_banks
from whole_banks05_13_14_15 import BANKS as NEW_BANKS,source_parts,full_bank

SIZE=0x4000
ALL=list(range(16))
SOURCE_BYTES=SIZE*16

def sha(b):return hashlib.sha256(b).hexdigest()

def complete_banks(root=ROOT):
 banks=previous_banks(root)
 for n in NEW_BANKS:
  if n in banks:raise ValueError('Source bank ownership overlaps prior phase')
  banks[n]=full_bank(n,root)
 if sorted(banks)!=ALL or any(len(b)!=SIZE for b in banks.values()):
  raise ValueError('Source-only cartridge missing bank, wrong bank length, or duplicate bank')
 return banks

def build(root=ROOT):
 banks=complete_banks(root)
 image=b''.join(banks[n] for n in ALL)
 if len(image)!=0x40000 or sha(image)!=EXPECTED_SHA:
  raise ValueError('Source-built cartridge mismatches original verified SHA-256')
 per_bank=[{'bank':n,'source_backed_bytes':SIZE,'original_rom_fallback_bytes':0,
            'source_only_complete':True,'sha256':sha(banks[n])} for n in ALL]
 added={}
 for n in NEW_BANKS:
  _,sections=source_parts(n,root)
  added[str(n)]={'source_backed_bytes':SIZE,'newly_recovered_mnemonic_bytes':0,
                 'data_sections':sections}
 opaque=sum(part['bytes'] for entry in added.values() for part in entry['data_sections'] if part['classification'].startswith('asset/resource bytes'))
 typed=sum(part['bytes'] for entry in added.values() for part in entry['data_sections'] if part['classification'].startswith('50 resource pointers'))
 fill=sum(part['bytes'] for entry in added.values() for part in entry['data_sections'] if part['classification']=='bank-end FF filler')
 if opaque+typed+fill!=len(NEW_BANKS)*SIZE or typed!=100 or fill!=997:
  raise ValueError('Final-four source classifications inconsistent')
 report={'schema':'ys-complete-source-cartridge-m10-v1','rom_bytes':len(image),
         'rom_sha256':sha(image),'bank_count':16,'source_only_complete_banks':ALL,
         'source_backed_bytes':SOURCE_BYTES,'source_backed_pct':100.0,
         'original_rom_fallback_bytes':0,'source_only_complete_rom':True,
         'prior_source_backed_bytes':12*SIZE,'new_source_backed_bytes':len(NEW_BANKS)*SIZE,
         'final_four_unresolved_resource_bytes':opaque,'final_four_structured_pointer_bytes':typed,
         'final_four_explicit_fill_bytes':fill,'newly_recovered_mnemonic_bytes':0,
         'new_bank_metadata':added,'per_bank':per_bank,
         'external_wla_dx_verified':False,'full_emulator_verified':False,
         'all_game_assets_semantically_decoded':False,'all_game_routines_understood':False,
         'limitations':['Complete cartridge can be regenerated without the original ROM using checked-in source records and in-project encoding.',
                        'Final four banks mostly preserve unresolved source bytes, NOT decoded game assets or Z80 routines.',
                        'Additional previously completed banks also contain semantically unresolved asset bytes.',
                        'External WLA-DX assembly/linking has not been executed successfully.',
                        'Whole-game behavioral/emulator validation is outstanding.']}
 return image,report

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--out',type=Path,help='Owner-controlled output path for reconstructed ROM; never put in Git')
 p.add_argument('--report',type=Path,default=ROOT/'whole_system/build_report_m10.json')
 p.add_argument('--check',action='store_true',help='Check saved manifest/report as well as source identity')
 p.add_argument('--verify-rom',type=Path,help='Optional comparison to fingerprinted owner ROM; NOT needed to build')
 p.add_argument('--standalone-banks',action='store_true')
 p.add_argument('--output-directory',type=Path)
 a=p.parse_args()
 if a.out and a.verify_rom and a.out.resolve()==a.verify_rom.resolve():p.error('Cannot overwrite original ROM')
 image,report=build()
 if a.verify_rom and validated_rom(a.verify_rom.read_bytes())!=image:raise ValueError('User ROM mismatch')
 if a.check:
  if not a.report.is_file() or json.loads(a.report.read_text())!=report:raise ValueError('M10 report drift')
  manifest=ROOT.parent/'shared_decomp/examples/ys_sms_manifest.json'
  if manifest.exists():
   obj=json.loads(manifest.read_text());rows=obj['partitions']
   if len(rows)!=16 or any(rows[i]['source_backed_bytes']!=SIZE or rows[i]['fallback_bytes'] or not rows[i]['source_only_complete'] or rows[i]['sha256']!=report['per_bank'][i]['sha256'] for i in ALL):
    raise ValueError('Portable whole-ROM manifest drift')
 else:
  a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n')
 if a.out:
  a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_bytes(image)
 if a.output_directory:
  a.output_directory.mkdir(parents=True,exist_ok=True)
  for n in ALL:(a.output_directory/f'bank{n:02}.bin').write_bytes(image[n*SIZE:(n+1)*SIZE])
 if a.standalone_banks:
  for n in ALL:print(f'Bank {n:02}: 16,384 source-only bytes SHA256 {report["per_bank"][n]["sha256"]}')
 print(f'M10: 16/16 source-only banks, {len(image)} bytes; ROM fallback=0; SHA256={sha(image)}')
if __name__=='__main__':main()
