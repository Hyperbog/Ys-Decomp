#!/usr/bin/env python3
"""Prepare/check third-party WLA-DX comparison for the ENTIRE source-only bank 7.

--prepare explicitly does NOT verify third-party assembler output. In --run
mode WLA-DX must actually exist or the command fails without claiming success.
"""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
from build_sms_phase14 import ROOT
from whole_bank07 import mixed_source, full_bank

WLA_HEADER='''; Physical bank 7 complete independent assembly fixture
.MEMORYMAP
 DEFAULTSLOT 2
 SLOT 0 START $0000 SIZE $4000
 SLOT 1 START $4000 SIZE $4000
 SLOT 2 START $8000 SIZE $4000
.ENDME
.ROMBANKMAP
 BANKSTOTAL 16
 BANKSIZE $4000
 BANKS 16
.ENDRO
.BANK 7 SLOT 2
'''

def fixture_text(root=ROOT):
    source=mixed_source(root)
    lines=[]
    for line in source.splitlines():
        line=line.replace('org $8000','.ORGA $8000') if line.strip().lower()=='org $8000' else line
        lines.append(line)
    if sum('.ORGA $8000' in s for s in lines)!=1:raise ValueError('Invalid WLA source origin')
    return WLA_HEADER+'\n'.join(lines)+'\n'

def prepare(path,root=ROOT):
    path=Path(path);path.mkdir(parents=True,exist_ok=True)
    asm=fixture_text(root)
    (path/'bank07.asm').write_text(asm)
    (path/'linkfile').write_text('[objects]\nbank07.o\n')
    return {'source_file':'bank07.asm','linkfile':'linkfile',
            'source_sha256':hashlib.sha256(asm.encode()).hexdigest(),
            'expected_bank_bytes':16384,'externally_verified':False}

def check(directory,assembler='wla-z80',linker='wlalink',root=ROOT):
    if not shutil.which(assembler) or not shutil.which(linker):
        raise FileNotFoundError('Cannot independently validate: wla-z80 AND wlalink are required')
    directory=Path(directory)
    prepare(directory,root)
    subprocess.run([assembler,'-o','bank07.o','bank07.asm'],cwd=directory,check=True,
                   stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    subprocess.run([linker,'-r','linkfile','rom_output.bin'],cwd=directory,check=True,
                   stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    image=(directory/'rom_output.bin').read_bytes()
    if len(image)<0x20000:raise AssertionError('WLA output shorter than bank-7 physical interval')
    got=image[0x1c000:0x20000]
    if got!=full_bank(root):
        raise AssertionError('Independent WLA-DX bank-7 output mismatch')
    return {'externally_verified':True,'bytes':len(got),
            'bank_sha256':hashlib.sha256(got).hexdigest()}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare',action='store_true')
    mode.add_argument('--run',action='store_true')
    p.add_argument('--wla-z80',default='wla-z80')
    p.add_argument('--wlalink',default='wlalink')
    p.add_argument('--directory',type=Path)
    a=p.parse_args()
    if a.directory:
        result=prepare(a.directory) if a.prepare else check(a.directory,a.wla_z80,a.wlalink)
    else:
        with tempfile.TemporaryDirectory(prefix='ys_wholebank07_wla_') as t:
            result=prepare(t) if a.prepare else check(t,a.wla_z80,a.wlalink)
    print('PREPARED, NOT independently assembled:' if a.prepare else 'INDEPENDENT WLA-DX PASSED:',result)

if __name__=='__main__':main()
