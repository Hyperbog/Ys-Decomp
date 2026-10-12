#!/usr/bin/env python3
"""Independent Z80 instruction matching with Emulicious's assembler.Z80Assembler.

Generates an instruction worklist from all 16 checked-in mixed source banks.
The project's known encoder is used ONLY to locate instruction boundaries;
Emulicious selects opcodes and encodes each mnemonic independently. Results
are checked against the source-only reconstructed cartridge and (optionally)
the original ROM. Unsupported syntax is explicitly reported, never skipped as
matched code. No emulator JAR, ROM, or executable is added to the Git tree.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from build_system_m10 import build
from z80_roundtrip_phase10 import encode

EXPECTED = '02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9'
JAVA_SOURCE = Path(__file__).with_name('EmuliciousZ80EncoderM12.java')


def enumerate_instructions(root=ROOT):
    """Yield (physical ROM address, CPU PC, source mnemonic); fail on layout drift."""
    addresses=set()
    instructions=[]
    for bank in range(16):
        path=root/'src'/f'wholebank{bank:02}'/f'bank{bank:02}_complete.asm'
        pc=None
        for line_number, line in enumerate(path.read_text().splitlines(),1):
            s=line.split(';',1)[0].strip()
            if not s or s.endswith(':'): continue
            org=re.fullmatch(r'org\s+\$([0-9a-fA-F]+)',s,re.I)
            if org:
                pc=int(org.group(1),16)
                continue
            if pc is None:raise ValueError(f'{path}:{line_number}: missing origin')
            directive=re.fullmatch(r'(db|dw)\s+(.+)',s,re.I)
            if directive:
                fields=[v.strip() for v in directive.group(2).split(',')]
                if any(not re.fullmatch(r'\$[0-9a-fA-F]+',v) for v in fields):
                    raise ValueError(f'{path}:{line_number}: unsupported data expression')
                size=len(fields)*(1 if directive.group(1).lower()=='db' else 2)
            else:
                size=len(encode(s,pc))
                phys=bank*0x4000+(pc-(0 if bank==0 else 0x4000 if bank==1 else 0x8000))
                instructions.append((phys,pc,s,bank,line_number))
            base=0 if bank==0 else 0x4000 if bank==1 else 0x8000
            if not base<=pc<base+0x4000 or pc+size>base+0x4000:
                raise ValueError(f'{path}:{line_number}: crosses bank boundary')
            start=bank*0x4000+pc-base
            for p in range(start,start+size):
                if p in addresses:raise ValueError(f'{path}:{line_number}: duplicate physical address {p:X}')
                addresses.add(p)
            pc+=size
        if len([x for x in addresses if bank*0x4000<=x<(bank+1)*0x4000])!=0x4000:
            raise ValueError(f'Physical bank {bank} incomplete')
    return instructions


def audit_responses(worklist, lines, image):
    """Fail closed on misaligned replies, invalid hex and external mismatches."""
    if len(lines)!=len(worklist):
        raise AssertionError(f'Emulicious response count {len(lines)} != {len(worklist)}')
    matched=0; mismatches=[]; unsupported=[]; total_bytes=0
    for (offset,pc,mnemonic,bank,line),reply in zip(worklist,lines):
        prefix,sep,result=reply.partition('\t')
        if not sep or prefix.upper()!=f'{pc:04X}':
            raise AssertionError(f'Malformed/misaligned assembler response: {reply}')
        expected=encode(mnemonic,pc)
        total_bytes+=len(expected)
        if result.startswith('ERROR:'):
            unsupported.append({'bank':bank,'address':f'{pc:04X}','instruction':mnemonic,'error':result})
            continue
        try:actual=bytes.fromhex(result)
        except ValueError as e:raise AssertionError(f'Invalid external hex: {reply}') from e
        if actual!=image[offset:offset+len(expected)] or len(actual)!=len(expected):
            mismatches.append({'bank':bank,'address':f'{pc:04X}', 'instruction':mnemonic,
                               'external':actual.hex().upper(),'reference':image[offset:offset+len(expected)].hex().upper()})
            continue
        matched+=len(actual)
    return matched,mismatches,unsupported,total_bytes


def run(jar:Path, *, reference:Path|None=None, root=ROOT):
    if not jar.is_file():raise FileNotFoundError(f'Emulicious JAR not found: {jar}')
    image,_=build(root)
    if hashlib.sha256(image).hexdigest()!=EXPECTED:raise AssertionError('source-only build mismatch')
    if reference is not None and (len(reference.read_bytes())!=len(image) or
                              hashlib.sha256(reference.read_bytes()).hexdigest()!=EXPECTED):
        raise ValueError('Original reference ROM hash mismatch')
    worklist=enumerate_instructions(root)
    with tempfile.TemporaryDirectory(prefix='ys_emulicious_assembler_') as td:
        directory=Path(td)
        subprocess.run(['javac','-cp',str(jar),'-d',td,str(JAVA_SOURCE)],check=True,
                       capture_output=True,text=True,timeout=30)
        requests=''.join(f'{pc:04X}\t{mnemonic}\n' for _,pc,mnemonic,_,_ in worklist)
        completed=subprocess.run(['java','-cp',f'{jar}:{td}','EmuliciousZ80EncoderM12'],
                                 input=requests,check=True,capture_output=True,text=True,
                                 timeout=120)
    summary=audit_responses(worklist, completed.stdout.splitlines(), image)
    matched,mismatches,unsupported,total_bytes=summary
    return {'schema':'ys-external-emulicious-z80-assembler-m12-v1',
            'assembler':'Emulicious built-in Z80Assembler',
            'jar_sha256':hashlib.sha256(jar.read_bytes()).hexdigest(),
            'source_cartridge_sha256':EXPECTED,'all_16_banks_source_only':True,
            'instructions_submitted':len(worklist),
            'instruction_bytes_examined':total_bytes,
            'externally_matched_instruction_bytes':matched,
            'unsupported_instruction_count':len(unsupported),
            'mismatching_instruction_count':len(mismatches),
            'unsupported_samples':unsupported[:30],
            'mismatch_samples':mismatches[:30],
            'independent_full_cartridge_link_passed':False,
            'independent_wla_dx_passed':False}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--jar',required=True,type=Path)
    ap.add_argument('--reference-rom',type=Path)
    ap.add_argument('--report',type=Path)
    opts=ap.parse_args()
    result=run(opts.jar,reference=opts.reference_rom)
    print(json.dumps(result,indent=2))
    if opts.report:
        opts.report.parent.mkdir(exist_ok=True,parents=True)
        opts.report.write_text(json.dumps(result,indent=2)+'\n')
    if result['mismatching_instruction_count']:raise SystemExit('External assembly mismatches detected')
    if result['unsupported_instruction_count']:raise SystemExit('External assembler does not support all instruction syntaxes')

if __name__=='__main__':main()
