#!/usr/bin/env python3
"""WLA-DX five-bank fixture preparation, with fail-closed real external assembly."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
from build_sms_phase14 import ROOT
from build_system_m5 import complete_banks,BANKS
from wla_whole_bank07 import WLA_HEADER
from wla_system_m4 import fixture as prior_fixture
from whole_bank02 import mixed_source

def fixture(bank,root=ROOT):
    if bank!=2:return prior_fixture(bank,root)
    header=WLA_HEADER.replace('bank 7','bank 2').replace('.BANK 7 SLOT 2','.BANK 2 SLOT 2')
    text=mixed_source(root)
    if text.count('org $8000')!=1:raise ValueError('Audio bank origin drift')
    return header+text.replace('org $8000','.ORGA $8000',1)

def prepare(directory,root=ROOT):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    hashes={}
    for n in BANKS:
        text=fixture(n,root);(directory/f'bank{n:02}.asm').write_text(text)
        hashes[str(n)]=hashlib.sha256(text.encode()).hexdigest()
    (directory/'linkfile').write_text('[objects]\n'+''.join(f'bank{n:02}.o\n' for n in BANKS))
    return {'banks':BANKS,'fixture_sha256':hashes,'external_assembler_verified':False}

def verify(directory,assembler='wla-z80',linker='wlalink',root=ROOT):
    if not shutil.which(assembler) or not shutil.which(linker):
        raise FileNotFoundError('Independent bank assembly REQUIRES installed wla-z80 and wlalink')
    directory=Path(directory);prepare(directory,root)
    for n in BANKS:
        subprocess.run([assembler,'-o',f'bank{n:02}.o',f'bank{n:02}.asm'],cwd=directory,check=True,timeout=120,capture_output=True,text=True)
    subprocess.run([linker,'-r','linkfile','five_banks.rom'],cwd=directory,check=True,timeout=120,capture_output=True,text=True)
    image=(directory/'five_banks.rom').read_bytes()
    if len(image)<0x20000:raise ValueError('External assembly image too short')
    for n,b in complete_banks(root).items():
        if image[n*0x4000:(n+1)*0x4000]!=b:
            raise ValueError('External WLA-DX mismatch bank '+str(n))
    return {'banks':BANKS,'external_assembler_verified':True,'matched_bytes':5*0x4000}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--prepare',action='store_true');g.add_argument('--run',action='store_true')
    p.add_argument('--directory',type=Path);p.add_argument('--wla-z80',default='wla-z80');p.add_argument('--wlalink',default='wlalink')
    args=p.parse_args()
    def go(d):return prepare(d) if args.prepare else verify(d,args.wla_z80,args.wlalink)
    if args.directory:print(go(args.directory))
    else:
        with tempfile.TemporaryDirectory(prefix='ys_m5_wla_') as d:print(go(d))
if __name__=='__main__':main()
