#!/usr/bin/env python3
"""Prepare WLA-DX fixtures for independent assembly of BOTH complete banks.

--prepare does NOT validate assembler bytes; --run fails closed if external
WLA-DX binaries are unavailable or the resulting two bank slices differ.
"""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
from build_sms_phase14 import ROOT
from whole_bank03 import full_bank as bank03,mixed_source as asm03
from whole_bank07 import full_bank as bank07,mixed_source as asm07
from wla_whole_bank07 import WLA_HEADER

def fixture_text(source,bank):
    header=WLA_HEADER.replace('.BANK 7 SLOT 2',f'.BANK {bank} SLOT 2')
    return header+source.replace('org $8000','.ORGA $8000',1)

def prepare(directory,root=ROOT):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    for bank,source in ((3,asm03(root)),(7,asm07(root))):
        (directory/f'bank{bank:02}.asm').write_text(fixture_text(source,bank))
    (directory/'linkfile').write_text('[objects]\nbank03.o\nbank07.o\n')
    return {'module_count':2,'source_only_banks':[3,7],
            'source_sha256':{str(bank):hashlib.sha256((directory/f'bank{bank:02}.asm').read_bytes()).hexdigest()
                             for bank in (3,7)},'externally_assembled':False}

def verify(directory,assembler='wla-z80',linker='wlalink',root=ROOT):
    if not shutil.which(assembler) or not shutil.which(linker):
        raise FileNotFoundError('External WLA-DX wla-z80/wlalink are required; fixture preparation is NOT an independent check')
    directory=Path(directory)
    prepare(directory,root)
    for b in (3,7):
        subprocess.run([assembler,'-o',f'bank{b:02}.o',f'bank{b:02}.asm'],cwd=directory,
                       check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    subprocess.run([linker,'-r','linkfile','compare.rom'],cwd=directory,
                   check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    image=(directory/'compare.rom').read_bytes()
    if len(image)<0x20000:raise AssertionError('WLA output too short')
    matched={}
    for b,expected in ((3,bank03(root)),(7,bank07(root))):
        actual=image[b*16384:(b+1)*16384]
        if actual!=expected:raise AssertionError(f'WLA-DX independent bank{b} mismatch')
        matched[b]=hashlib.sha256(actual).hexdigest()
    return {'externally_assembled':True,'banks':[3,7], 'matched_bytes':32768,
            'digests':matched}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--prepare',action='store_true')
    g.add_argument('--run',action='store_true')
    p.add_argument('--wla-z80',default='wla-z80')
    p.add_argument('--wlalink',default='wlalink')
    p.add_argument('--directory',type=Path)
    a=p.parse_args()
    def invoke(directory):return prepare(directory) if a.prepare else verify(directory,a.wla_z80,a.wlalink)
    if a.directory:result=invoke(a.directory)
    else:
        with tempfile.TemporaryDirectory(prefix='ys_whole_system_wla_') as path:result=invoke(path)
    print(('PREPARED; NOT independently verified:' if a.prepare else 'WLA-DX VERIFIED:'),result)
if __name__=='__main__':main()
