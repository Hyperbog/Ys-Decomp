#!/usr/bin/env python3
"""WLA-DX fixture for 12 complete physical banks; prepare does NOT verify assembly."""
import argparse,hashlib,shutil,subprocess,tempfile
from pathlib import Path
from build_sms_phase14 import ROOT
from wla_system_m8 import fixture as old_fixture
from wla_whole_bank07 import WLA_HEADER
from whole_banks09_11_12 import mixed_source
from build_system_m9 import complete_banks,BANKS

def fixture(n,root=ROOT):
 if n not in (9,11,12):return old_fixture(n,root)
 prefix=WLA_HEADER.replace('Physical bank 7','Physical bank '+str(n)).replace('.BANK 7 SLOT 2',f'.BANK {n} SLOT 2')
 return prefix+mixed_source(n,root).replace('org $8000','.ORGA $8000',1)

def prepare(directory,root=ROOT):
 directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
 digests={}
 for n in BANKS:
  data=fixture(n,root);(directory/f'bank{n:02d}.asm').write_text(data)
  digests[str(n)]=hashlib.sha256(data.encode()).hexdigest()
 (directory/'linkfile').write_text('[objects]\n'+''.join(f'bank{n:02}.o\n' for n in BANKS))
 return {'banks':BANKS,'fixture_sha256':digests,'external_assembler_verified':False}

def verify(directory,assembler='wla-z80',linker='wlalink',root=ROOT):
 if not shutil.which(assembler) or not shutil.which(linker):raise FileNotFoundError('wla-z80 and wlalink required; fixture preparation is not verification')
 directory=Path(directory);prepare(directory,root)
 for n in BANKS:subprocess.run([assembler,'-o',f'bank{n:02}.o',f'bank{n:02}.asm'],cwd=directory,check=True,timeout=120,capture_output=True,text=True)
 subprocess.run([linker,'-r','linkfile','twelve_banks.rom'],cwd=directory,check=True,timeout=120,capture_output=True,text=True)
 rom=(directory/'twelve_banks.rom').read_bytes()
 if len(rom)<13*0x4000:raise ValueError('WLA output too short')
 for n,expected in complete_banks(root).items():
  if rom[n*0x4000:(n+1)*0x4000]!=expected:raise ValueError(f'WLA bank {n} differs')
 return {'banks':BANKS,'matched_bytes':len(BANKS)*0x4000,'external_assembler_verified':True}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 g=p.add_mutually_exclusive_group(required=True);g.add_argument('--prepare',action='store_true');g.add_argument('--run',action='store_true')
 p.add_argument('--directory',type=Path);p.add_argument('--wla-z80',default='wla-z80');p.add_argument('--wlalink',default='wlalink');a=p.parse_args()
 if a.directory:print(prepare(a.directory) if a.prepare else verify(a.directory,a.wla_z80,a.wlalink))
 else:
  with tempfile.TemporaryDirectory(prefix='ys_m9_wla_') as d:
   print(prepare(d) if a.prepare else verify(d,a.wla_z80,a.wlalink))
if __name__=='__main__':main()
