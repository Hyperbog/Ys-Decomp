#!/usr/bin/env python3
"""External WLA-DX integration for standalone fixed and switchable banks 0,3,7."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
from build_sms_phase14 import ROOT
from whole_bank00 import full_bank as bank00,mixed_source as asm00
from whole_bank03 import full_bank as bank03,mixed_source as asm03
from whole_bank07 import full_bank as bank07,mixed_source as asm07
from wla_whole_bank07 import WLA_HEADER

BANKS={0:(bank00,asm00),3:(bank03,asm03),7:(bank07,asm07)}

def source_fixture(bank,root=ROOT):
    _,source=BANKS[bank]
    header=WLA_HEADER.replace('DEFAULTSLOT 2','DEFAULTSLOT 0')
    header=header.replace('.BANK 7 SLOT 2',f'.BANK {bank} SLOT {0 if bank==0 else 2}')
    origin=0x0000 if bank==0 else 0x8000
    text=source(root)
    found=f'org ${origin:04X}'
    if text.count(found)!=1:raise ValueError('Unexpected source bank origin')
    return header+text.replace(found,f'.ORGA ${origin:04X}',1)

def prepare(directory,root=ROOT):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    hashes={}
    for bank in BANKS:
        src=source_fixture(bank,root)
        (directory/f'bank{bank:02}.asm').write_text(src)
        hashes[bank]=hashlib.sha256(src.encode()).hexdigest()
    (directory/'linkfile').write_text('[objects]\n'+''.join(f'bank{bank:02}.o\n' for bank in BANKS))
    return {'banks':list(BANKS),'fixture_sha256':hashes,'independent_assembly_verified':False}

def verify(directory,assembler='wla-z80',linker='wlalink',root=ROOT):
    if not shutil.which(assembler) or not shutil.which(linker):
        raise FileNotFoundError('Real WLA-DX wla-z80 and wlalink executables required; fixture preparation is not verification')
    directory=Path(directory)
    prepare(directory,root)
    for bank in BANKS:
        subprocess.run([assembler,'-o',f'bank{bank:02}.o',f'bank{bank:02}.asm'],cwd=directory,
                       check=True,timeout=120,capture_output=True,text=True)
    subprocess.run([linker,'-r','linkfile','assembled.rom'],cwd=directory,check=True,
                   timeout=120,capture_output=True,text=True)
    rom=(directory/'assembled.rom').read_bytes()
    if len(rom)<0x20000:raise ValueError('WLA output shorter than bank7')
    for bank,(fn,_) in BANKS.items():
        if rom[bank*0x4000:(bank+1)*0x4000]!=fn(root):raise ValueError(f'External assembly mismatch bank {bank}')
    return {'banks':list(BANKS),'matched_bytes':3*0x4000,'independent_assembly_verified':True}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare',action='store_true')
    group.add_argument('--run',action='store_true')
    p.add_argument('--directory',type=Path)
    p.add_argument('--wla-z80',default='wla-z80')
    p.add_argument('--wlalink',default='wlalink')
    a=p.parse_args()
    def operation(directory):return prepare(directory) if a.prepare else verify(directory,a.wla_z80,a.wlalink)
    if a.directory:result=operation(a.directory)
    else:
        with tempfile.TemporaryDirectory(prefix='ys_m3_wla_') as path:result=operation(path)
    print(('WLA fixtures prepared; NOT externally verified:' if a.prepare else 'External WLA source-match verified:'),result)

if __name__=='__main__':main()
