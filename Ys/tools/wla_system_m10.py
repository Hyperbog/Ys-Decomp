#!/usr/bin/env python3
"""Full 16-bank WLA-DX validation adapter; prepare is not verification."""
import argparse,hashlib,shutil,subprocess,tempfile
from pathlib import Path
from build_sms_phase14 import ROOT
from wla_system_m9 import fixture as previous_fixture
from wla_whole_bank07 import WLA_HEADER
from whole_banks05_13_14_15 import BANKS as FINAL,mixed_source
from build_system_m10 import complete_banks

ALL=list(range(16))
def fixture(bank,root=ROOT):
 if bank not in FINAL:return previous_fixture(bank,root)
 prefix=WLA_HEADER.replace('Physical bank 7',f'Physical bank {bank}').replace('.BANK 7 SLOT 2',f'.BANK {bank} SLOT 2')
 return prefix+mixed_source(bank,root).replace('org $8000','.ORGA $8000',1)

def prepare(directory,root=ROOT):
 directory=Path(directory);directory.mkdir(exist_ok=True,parents=True)
 refs={}
 for n in ALL:
  src=fixture(n,root);file=directory/f'bank{n:02}.asm';file.write_text(src)
  refs[str(n)]=hashlib.sha256(src.encode()).hexdigest()
 (directory/'linkfile').write_text('[objects]\n'+''.join(f'bank{n:02}.o\n' for n in ALL))
 return {'banks':ALL,'prepared_assembly_files':16,'source_sha256':refs,'external_wla_dx_verified':False}

def verify(directory,assembler='wla-z80',linker='wlalink',root=ROOT):
 if not shutil.which(assembler) or not shutil.which(linker):
  raise FileNotFoundError('Independent WLA-DX validation unavailable: both wla-z80 and wlalink are required')
 directory=Path(directory);prepare(directory,root)
 for n in ALL:
  subprocess.run([assembler,'-o',f'bank{n:02}.o',f'bank{n:02}.asm'],cwd=directory,check=True,timeout=150,capture_output=True,text=True)
 subprocess.run([linker,'-r','linkfile','entire_cartridge.sms'],cwd=directory,check=True,timeout=150,capture_output=True,text=True)
 output=(directory/'entire_cartridge.sms').read_bytes()
 source=b''.join(complete_banks(root)[n] for n in ALL)
 if output!=source:raise ValueError('Independent WLA-DX output differs from source-built cartridge')
 return {'externally_verified':True,'matched_bytes':len(source)}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 x=p.add_mutually_exclusive_group(required=True);x.add_argument('--prepare',action='store_true');x.add_argument('--run',action='store_true')
 p.add_argument('--directory',type=Path);p.add_argument('--wla-z80',default='wla-z80');p.add_argument('--wlalink',default='wlalink');a=p.parse_args()
 if a.directory:print(prepare(a.directory) if a.prepare else verify(a.directory,a.wla_z80,a.wlalink))
 else:
  with tempfile.TemporaryDirectory(prefix='ys_m10_wla_') as d:
   print(prepare(d) if a.prepare else verify(d,a.wla_z80,a.wlalink))
if __name__=='__main__':main()
