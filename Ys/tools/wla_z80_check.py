#!/usr/bin/env python3
"""Prepare and optionally execute an INDEPENDENT WLA-DX Z80 comparison.

The test fixture is generated from checked-in assembly text, never from
source ROM bytes. `--run` invokes third-party executables if available;
`--prepare` only validates and prepares the fixture and is NOT validation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = json.loads((ROOT / 'manifest.json').read_text())['sha256']
SOURCE = ROOT / 'src/phase13/bank07_unrolled_vdp.asm'
START = 0x1C180
LENGTH = 1345

HEADER = '''; Ys SMS independent bank-7 verification fixture (not full-game source)
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

def make_source(text):
    lines=text.splitlines()
    org=[n for n,s in enumerate(lines) if s.strip().lower().startswith('org $')]
    if len(org)!=1 or '$8180' not in lines[org[0]].lower():
        raise ValueError('Unexpected bank-7 module origin')
    body=[line for line in lines if not line.lstrip().startswith(';')]
    body=[line.replace('org $8180','.ORGA $8180',1) for line in body]
    if sum('outi' in line.lower().split(';')[0] for line in body)!=168:
        # 1345 bytes / 8 byte pattern has 168 OUTIs plus one RET
        raise ValueError('Unexpected unrolled graphics transfer instruction count')
    if sum('out ($BE),a' in line for line in body)!=504:
        raise ValueError('Unexpected unrolled VDP output instruction count')
    if sum(line.strip().split(';')[0].strip().lower()=='ret' for line in body)!=1:
        raise ValueError('Unexpected unrolled VDP routine terminator')
    return HEADER+'\n'.join(body)+'\n'

def prepare(directory):
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    asm=make_source(SOURCE.read_text())
    (directory/'bank07.asm').write_text(asm)
    (directory/'linkfile').write_text('[objects]\nbank07.o\n')
    return {'asm_sha256':hashlib.sha256(asm.encode()).hexdigest(),
            'module_bytes':LENGTH,'physical_offset':f'{START:05X}'}

def independent_check(rom, directory, assembler='wla-z80', linker='wlalink'):
    if not shutil.which(assembler) or not shutil.which(linker):
        raise FileNotFoundError('WLA-DX wla-z80 and wlalink must be installed for independent verification')
    prepare(directory)
    subprocess.run([assembler,'-o','bank07.o','bank07.asm'],cwd=directory,check=True,capture_output=True,text=True)
    subprocess.run([linker,'-r','linkfile','comparison.rom'],cwd=directory,check=True,capture_output=True,text=True)
    output=(Path(directory)/'comparison.rom').read_bytes()
    expected=rom[START:START+LENGTH]
    actual=output[START:START+LENGTH]
    if len(actual)!=LENGTH:
        raise AssertionError(f'WLA output too short for the bank-7 module ({len(actual)} bytes)')
    if actual!=expected:
        mismatch=next(i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b)
        raise AssertionError(f'External WLA mismatch at ROM {START+mismatch:05X}: generated {actual[mismatch]:02X} expected {expected[mismatch]:02X}')
    return {'result':'passed','external_assembler':'wla-z80','external_linker':'wlalink',
            'matched_bytes':LENGTH,'start':f'{START:05X}',
            'matched_sha256':hashlib.sha256(actual).hexdigest()}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path)
    p.add_argument('--prepare',action='store_true',help='only produce WLA-DX input; not external verification')
    p.add_argument('--wla-z80',default='wla-z80')
    p.add_argument('--wlalink',default='wlalink')
    a=p.parse_args()
    rom=a.rom.read_bytes()
    if hashlib.sha256(rom).hexdigest()!=EXPECTED:raise SystemExit('Wrong source ROM SHA-256')
    with tempfile.TemporaryDirectory(prefix='ys_wla_') as td:
        if a.prepare:
            print('PREPARED (not independently assembled):',json.dumps(prepare(td)))
            return
        try:r=independent_check(rom,td,a.wla_z80,a.wlalink)
        except FileNotFoundError as e:raise SystemExit(str(e))
        print('INDEPENDENT WLA-DX PASS:',json.dumps(r))
if __name__=='__main__':main()
