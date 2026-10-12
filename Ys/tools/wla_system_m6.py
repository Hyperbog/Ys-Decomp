#!/usr/bin/env python3
"""Prepare/check WLA-DX six-bank sources. Preparation is NOT independent assembly."""
import argparse
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path
from build_sms_phase14 import ROOT
from build_system_m6 import BANKS,complete_banks
from wla_system_m5 import fixture as m5fixture
from wla_whole_bank07 import WLA_HEADER
from whole_bank01 import mixed_source

def fixture(bank,root=ROOT):
    if bank!=1:return m5fixture(bank,root)
    header=WLA_HEADER.replace('DEFAULTSLOT 2','DEFAULTSLOT 1').replace('.BANK 7 SLOT 2','.BANK 1 SLOT 1')
    source=mixed_source(root)
    if source.count('org $4000')!=1:raise ValueError('Bank1 WLA origin drift')
    return header+source.replace('org $4000','.ORGA $4000',1)

def prepare(directory,root=ROOT):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    hashes={}
    for n in BANKS:
        text=fixture(n,root)
        (directory/f'bank{n:02}.asm').write_text(text)
        hashes[str(n)]=hashlib.sha256(text.encode()).hexdigest()
    (directory/'linkfile').write_text('[objects]\n'+''.join(f'bank{n:02}.o\n' for n in BANKS))
    return {'banks':BANKS,'fixture_sha256':hashes,'external_assembler_verified':False}

def verify(directory,assembler='wla-z80',linker='wlalink',root=ROOT):
    if not shutil.which(assembler) or not shutil.which(linker):
        raise FileNotFoundError('Independent assembler check requires real wla-z80 and wlalink')
    directory=Path(directory);prepare(directory,root)
    for n in BANKS:
        subprocess.run([assembler,'-o',f'bank{n:02}.o',f'bank{n:02}.asm'],
                       cwd=directory,check=True,timeout=120,capture_output=True,text=True)
    subprocess.run([linker,'-r','linkfile','six_banks.rom'],
                   cwd=directory,check=True,timeout=120,capture_output=True,text=True)
    img=(directory/'six_banks.rom').read_bytes()
    if len(img)<0x20000:raise ValueError('WLA output shorter than expected six-bank physical interval')
    for n,b in complete_banks(root).items():
        if img[n*0x4000:(n+1)*0x4000]!=b:
            raise ValueError(f'Independent Z80 assembler mismatch bank {n}')
    return {'banks':BANKS,'matched_bytes':len(BANKS)*0x4000,'external_assembler_verified':True}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--prepare',action='store_true');g.add_argument('--run',action='store_true')
    p.add_argument('--directory',type=Path)
    p.add_argument('--wla-z80',default='wla-z80');p.add_argument('--wlalink',default='wlalink')
    a=p.parse_args()
    if a.directory:print(prepare(a.directory) if a.prepare else verify(a.directory,a.wla_z80,a.wlalink))
    else:
        with tempfile.TemporaryDirectory(prefix='ys_m6_wla_') as d:
            print(prepare(d) if a.prepare else verify(d,a.wla_z80,a.wlalink))
if __name__=='__main__':main()
