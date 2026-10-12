#!/usr/bin/env python3
"""Prepare WLA-DX fixtures for banks 0,3,6,7; run only with real external tools."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
from build_sms_phase14 import ROOT
from wla_system_m3 import source_fixture as old_fixture, BANKS as OLD
from wla_whole_bank07 import WLA_HEADER
from whole_bank06 import full_bank, mixed_source
from build_system_m4 import complete_banks

BANKS=(0,3,6,7)
def fixture(bank,root=ROOT):
    if bank!=6:return old_fixture(bank,root)
    header=WLA_HEADER.replace('DEFAULTSLOT 2','DEFAULTSLOT 0').replace('.BANK 7 SLOT 2','.BANK 6 SLOT 2')
    source=mixed_source(root)
    if source.count('org $8000')!=1:raise ValueError('Bank6 origin drift')
    return header+source.replace('org $8000','.ORGA $8000',1)

def prepare(directory,root=ROOT):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    hashes={}
    for n in BANKS:
        text=fixture(n,root)
        (directory/f'bank{n:02}.asm').write_text(text)
        hashes[str(n)]=hashlib.sha256(text.encode()).hexdigest()
    (directory/'linkfile').write_text('[objects]\n'+''.join(f'bank{n:02}.o\n' for n in BANKS))
    return {'banks':list(BANKS),'fixture_sha256':hashes,'external_assembler_verified':False}

def verify(directory,assembler='wla-z80',linker='wlalink',root=ROOT):
    if not shutil.which(assembler) or not shutil.which(linker):
        raise FileNotFoundError('Independent verification REQUIRES installed wla-z80 and wlalink')
    directory=Path(directory);prepare(directory,root)
    for n in BANKS:
        subprocess.run([assembler,'-o',f'bank{n:02}.o',f'bank{n:02}.asm'],cwd=directory,check=True,timeout=120,capture_output=True,text=True)
    subprocess.run([linker,'-r','linkfile','assembled.rom'],cwd=directory,check=True,timeout=120,capture_output=True,text=True)
    image=(directory/'assembled.rom').read_bytes()
    if len(image)<0x20000:raise ValueError('External assembly image incomplete')
    for n,b in complete_banks(root).items():
        if image[n*0x4000:(n+1)*0x4000]!=b:raise ValueError(f'WLA source mismatch bank{n}')
    return {'banks':list(BANKS),'matched_bytes':4*0x4000,'external_assembler_verified':True}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare',action='store_true')
    mode.add_argument('--run',action='store_true')
    parser.add_argument('--directory',type=Path)
    parser.add_argument('--wla-z80',default='wla-z80')
    parser.add_argument('--wlalink',default='wlalink')
    args=parser.parse_args()
    def run(d):return prepare(d) if args.prepare else verify(d,args.wla_z80,args.wlalink)
    if args.directory:report=run(args.directory)
    else:
        with tempfile.TemporaryDirectory(prefix='ys_m4_wla_') as d:report=run(d)
    print(report)
if __name__=='__main__':main()
