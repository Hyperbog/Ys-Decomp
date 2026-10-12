#!/usr/bin/env python3
"""Prepare whole-bank 0/1/2/3/4/6/7/8/10 WLA-DX fixtures; no fake verification."""
import argparse
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path
from build_sms_phase14 import ROOT
from wla_system_m7 import fixture as m7fixture
from wla_whole_bank07 import WLA_HEADER
from build_system_m8 import BANKS,complete_banks
from whole_banks08_10 import mixed_source

def fixture(bank,root=ROOT):
    if bank not in (8,10):return m7fixture(bank,root)
    prefix=WLA_HEADER.replace('Physical bank 7','Physical bank '+str(bank)).replace('.BANK 7 SLOT 2',f'.BANK {bank} SLOT 2')
    body=mixed_source(bank,root)
    if body.count('org $8000')!=1:raise ValueError('Bank source origin mismatch')
    return prefix+body.replace('org $8000','.ORGA $8000',1)

def prepare(directory,root=ROOT):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    hashes={}
    for n in BANKS:
        s=fixture(n,root)
        (directory/f'bank{n:02}.asm').write_text(s)
        hashes[str(n)]=hashlib.sha256(s.encode()).hexdigest()
    (directory/'linkfile').write_text('[objects]\n'+''.join(f'bank{n:02}.o\n' for n in BANKS))
    return {'banks':BANKS,'fixture_sha256':hashes,'external_assembler_verified':False}

def verify(directory,assembler='wla-z80',linker='wlalink',root=ROOT):
    if not shutil.which(assembler) or not shutil.which(linker):
        raise FileNotFoundError('Independent WLA-DX wla-z80 and wlalink binaries required')
    directory=Path(directory);prepare(directory,root)
    for n in BANKS:
        subprocess.run([assembler,'-o',f'bank{n:02}.o',f'bank{n:02}.asm'],cwd=directory,
                       check=True,timeout=120,capture_output=True,text=True)
    subprocess.run([linker,'-r','linkfile','nine_banks.rom'],cwd=directory,
                   check=True,timeout=120,capture_output=True,text=True)
    raw=(directory/'nine_banks.rom').read_bytes()
    if len(raw)<0x2c000:raise ValueError('External output too short for bank 10')
    for n,b in complete_banks(root).items():
        if raw[n*0x4000:(n+1)*0x4000]!=b:raise ValueError(f'External bank {n} mismatch')
    return {'banks':BANKS,'matched_bytes':len(BANKS)*0x4000,'external_assembler_verified':True}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--prepare',action='store_true');g.add_argument('--run',action='store_true')
    p.add_argument('--directory',type=Path)
    p.add_argument('--wla-z80',default='wla-z80');p.add_argument('--wlalink',default='wlalink')
    a=p.parse_args()
    if a.directory:print(prepare(a.directory) if a.prepare else verify(a.directory,a.wla_z80,a.wlalink))
    else:
        with tempfile.TemporaryDirectory(prefix='ys_m8_wla_') as d:
            print(prepare(d) if a.prepare else verify(d,a.wla_z80,a.wlalink))
if __name__=='__main__':main()
