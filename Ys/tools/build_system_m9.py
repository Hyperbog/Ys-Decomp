#!/usr/bin/env python3
"""M9: 12 source-only ROM banks; remaining banks 5,13,14,15 use owner ROM fallback."""
import argparse,hashlib,json
from pathlib import Path
from build_sms_phase14 import ROOT,validated_rom
from build_system_m8 import build as previous,complete_banks as prev_banks,SOURCED as OLD
from whole_banks09_11_12 import full_bank,load_new,extra_code
SIZE=0x4000
NEWBANKS=(9,11,12)
BANKS=sorted([*prev_banks(),*NEWBANKS])
ADD={9:SIZE,11:SIZE,12:SIZE-108}
NEW=sum(ADD.values());SOURCED=OLD+NEW

def sha(b):return hashlib.sha256(b).hexdigest()

def complete_banks(root=ROOT):
 b=prev_banks(root)
 for n in NEWBANKS:b[n]=full_bank(n,root)
 if sorted(b)!=BANKS or len(b)!=12 or any(len(v)!=SIZE for v in b.values()):raise ValueError('Bank closure list invalid')
 return b

def build(rom,root=ROOT):
 validated_rom(rom)
 previous_image,old=previous(rom,root)
 output=bytearray(previous_image)
 for n in NEWBANKS:
  b=full_bank(n,root);start=n*SIZE
  if output[start:start+SIZE]!=b or rom[start:start+SIZE]!=b:raise ValueError(f'M9 bank {n} source/original drift')
  output[start:start+SIZE]=b
 if bytes(output)!=rom:raise ValueError('M9 ROM rebuild output drift')
 perbank=[]
 for row in old['per_bank']:
  n=row['bank'];count=row['source_backed_bytes']+ADD.get(n,0)
  if (count==SIZE)!=(n in BANKS) or not 0<=count<=SIZE:raise ValueError('Bank byte accounting mismatch')
  perbank.append({'bank':n,'source_backed_bytes':count,'original_rom_fallback_bytes':SIZE-count,
    'source_only_complete':count==SIZE,'sha256':sha(output[n*SIZE:(n+1)*SIZE])})
 if sum(r['source_backed_bytes'] for r in perbank)!=SOURCED:raise ValueError('Source-backed bytes mismatch')
 source={}
 for n in NEWBANKS:
  data,inventory=load_new(n,root)
  source[str(n)]={'new_source_backed_bytes':ADD[n], 'new_instruction_bytes':len(extra_code(root)[0]) if n==9 else 0,
    'new_data_bytes':len(data),'inventory':inventory}
  if source[str(n)]['new_data_bytes']+source[str(n)]['new_instruction_bytes']!=ADD[n]:raise ValueError('New bank bytes mismatch')
 report={'schema':'ys-whole-system-twelve-banks-v1','rom_sha256':sha(output),'rom_bytes':len(output),
 'source_only_complete_banks':BANKS,'complete_source_only_bank_bytes':len(BANKS)*SIZE,
 'prior_source_backed_bytes':OLD,'new_source_backed_bytes':NEW,'new_bank_metadata':source,
 'source_backed_bytes':SOURCED,'source_backed_pct':round(100*SOURCED/len(output),4),
 'original_rom_fallback_bytes':len(output)-SOURCED,'source_only_complete_rom':False,
 'external_wla_dx_verified':False,'full_emulator_verified':False,'bank09_language_semantics_decoded':False,
 'bank11_resource_semantics_decoded':False,'bank12_resource_semantics_decoded':False,
 'per_bank':perbank,'limitations':[
 'Only banks 5,13,14,15 still require original ROM fallback.',
 'Banks 9 and 11 contain extensive unresolved resource data represented reversibly.',
 'The eight bank9 six-byte records and their Z80 VDP writer are statically supported, not yet gameplay-traced.',
 'Bank12 initial 128-byte curve is a candidate table; no proven consumer was established.',
 'Neither WLA-DX external compilation nor full-system emulator gameplay has been verified.']}
 return bytes(output),report

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('rom',nargs='?',type=Path);p.add_argument('--standalone-banks',action='store_true');p.add_argument('--check',action='store_true')
 p.add_argument('--out',type=Path);p.add_argument('--output-directory',type=Path)
 p.add_argument('--report',type=Path,default=ROOT/'whole_system/build_report_m9.json')
 a=p.parse_args()
 if a.standalone_banks:
  banks=complete_banks()
  for n,b in sorted(banks.items()):
   if a.output_directory:
    a.output_directory.mkdir(parents=True,exist_ok=True);(a.output_directory/f'bank{n:02d}.bin').write_bytes(b)
   print(f'Bank {n:02d}: 16,384 source-only bytes SHA256 {sha(b)}')
  return
 if a.rom is None:p.error('Owner ROM required for four unfinished physical banks')
 if a.out and a.out.resolve()==a.rom.resolve():p.error('Cannot overwrite original ROM')
 output,report=build(a.rom.read_bytes())
 if a.check:
  if report!=json.loads(a.report.read_text()):raise ValueError('M9 build report drift')
 else:a.report.write_text(json.dumps(report,indent=2)+'\n')
 if a.out:a.out.write_bytes(output)
 print('M9 source-only banks',BANKS,'source-backed',SOURCED,'fallback',report['original_rom_fallback_bytes'],'SHA256',sha(output))
if __name__=='__main__':main()
