#!/usr/bin/env python3
"""WLA-DX seven-bank fixtures; external verification requires actual binaries."""
import argparse
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path
from build_sms_phase14 import ROOT
from build_system_m7 import BANKS,complete_banks
from wla_system_m6 import fixture as m6fixture
from wla_whole_bank07 import WLA_HEADER
from whole_bank04 import mixed_source

def fixture(bank,root=ROOT):
    if bank!=4:return m6fixture(bank,root)
    header=WLA_HEADER.replace('.BANK 7 SLOT 2','.BANK 4 SLOT 2')
    body=mixed_source(root)
    if body.count('org $8000')!=1:raise ValueError('Bank4 source origin drift')
    return header+body.replace('org $8000','.ORGA $8000',1)

def prepare(directory,root=ROOT):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    hashes={}
    for n in BANKS:
        source=fixture(n,root)
        (directory/f'bank{n:02}.asm').write_text(source)
        hashes[str(n)]=hashlib.sha256(source.encode()).hexdigest()
    (directory/'linkfile').write_text('[objects]\n'+''.join(f'bank{n:02}.o\n' for n in BANKS))
    return {'banks':BANKS,'fixture_sha256':hashes,'external_assembler_verified':False}

def verify(directory,assembler='wla-z80',linker='wlalink',root=ROOT):
    if not shutil.which(assembler) or not shutil.which(linker):
        raise FileNotFoundError('Real WLA-DX wla-z80 and wlalink required')
    directory=Path(directory);prepare(directory,root)
    for n in BANKS:
        subprocess.run([assembler,'-o',f'bank{n:02}.o',f'bank{n:02}.asm'],
                       cwd=directory,check=True,timeout=120,capture_output=True,text=True)
    subprocess.run([linker,'-r','linkfile','seven_banks.rom'],
                   cwd=directory,check=True,timeout=120,capture_output=True,text=True)
    image=(directory/'seven_banks.rom').read_bytes()
    if len(image)<0x20000:raise ValueError('External WLA output shorter than seven-bank physical interval')
    for n,b in complete_banks(root).items():
        if image[n*0x4000:(n+1)*0x4000]!=b:raise ValueError(f'External assembler mismatch bank {n}')
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
        with tempfile.TemporaryDirectory(prefix='ys_m7_wla_') as d:
            print(prepare(d) if a.prepare else verify(d,a.wla_z80,a.wlalink))
if __name__=='__main__':main()
