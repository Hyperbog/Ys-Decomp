#!/usr/bin/env python3
"""Strict, standalone two-pass Z80 subset assembler for Phase 9 modules.

Supports only explicitly whitelisted instructions in src/phase9_vdp.asm.
This encoder does not use the ROM/disassembler for byte generation. It
validates exact original bytes afterwards; NOT a general Z80 assembler.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
SHA=json.loads((ROOT/'manifest.json').read_text())['sha256']
SOURCE=ROOT/'src/phase9_vdp.asm'
SINGLE={
  'nop':0x00,'inc b':0x04,'dec a':0x3d,'dec c':0x0d,'inc hl':0x23,
  'ld a,b':0x78,'ld a,c':0x79,'ld a,h':0x7c,'ld a,l':0x7d,
  'ld b,c':0x41,'ld a,(hl)':0x7e,'or a':0xb7,'xor a':0xaf,
  'push af':0xf5,'pop af':0xf1,'ret':0xc9,'ret z':0xc8,
}
ED={'outi':0xa3}
R_IMM={'a':0x3e,'b':0x06,'c':0x0e}
R_INDIRECT={'a':0x3a,'hl':0x2a}
R_STORE={'a':0x32}
BR={'djnz':0x10,'jr nz,':0x20,'jr z,':0x28}


def number(s,symbols):
    s=s.strip()
    if s in symbols:return symbols[s]
    folded={key.lower():value for key,value in symbols.items()}
    if s.lower() in folded:return folded[s.lower()]
    if s.startswith('$'):return int(s[1:],16)
    if s.isdecimal():return int(s)
    raise ValueError(f'Undefined operand/symbol {s!r}')


def encode(instr,pc,labels,unknown=False):
    """Return opcode bytes; zeros stand in for not-yet-resolved labels in pass1."""
    s=' '.join(instr.lower().split())
    def n(s,width):
        if unknown and s not in labels and not s.startswith('$') and not s.isdecimal(): return bytes(width)
        v=number(s,labels)
        if not 0<=v<1<<(8*width):raise ValueError(f'out-of-range operand: {s}')
        return v.to_bytes(width,'little')
    if s in SINGLE:return bytes([SINGLE[s]])
    if s in ED:return bytes([0xed,ED[s]])
    if s in ('out ($be),a','out ($bf),a'):
        return bytes([0xd3,int(s[6:8],16)])
    if s=='rst $28':return b'\xef'
    m=re.fullmatch(r'ld ([a-z]+),\((\$[0-9a-f]+)\)',s)
    if m and m[1] in R_INDIRECT:
        return bytes([R_INDIRECT[m[1]]])+n(m[2],2)
    m=re.fullmatch(r'ld \((\$[0-9a-f]+)\),([a-z]+)',s)
    if m and m[2] in R_STORE:
        return bytes([R_STORE[m[2]]])+n(m[1],2)
    m=re.fullmatch(r'ld ([a-z]+),(.+)',s)
    if m:
        reg,val=m.groups()
        if reg in R_IMM:return bytes([R_IMM[reg]])+n(val,1)
        if reg=='bc':return b'\x01'+n(val,2)
        if reg=='hl':return b'\x21'+n(val,2)
    for branch,opcode in BR.items():
        prefix=branch if branch.endswith(',') else branch+' '
        if s.startswith(prefix):
            target=s[len(prefix):].strip()
            if unknown and target not in labels:return bytes([opcode,0])
            to=number(target,labels)
            disp=to-(pc+2)
            if not -128<=disp<=127:raise ValueError(f'JR out of range {pc:04X} -> {target}')
            return bytes([opcode,disp&255])
    raise ValueError(f'Unsupported instruction at {pc:04X}: {instr}')


def parse(src):
    lines=[];global_label=''
    for num,line in enumerate(src.splitlines(),1):
        line=line.split(';',1)[0].strip()
        if not line:continue
        if line.endswith(':'):
            symbol=line[:-1]
            if symbol.startswith('.'):
                if not global_label:raise ValueError('Local label without global scope')
                symbol=global_label+symbol
            else:global_label=symbol
            lines.append((num,'label',symbol))
        elif line.lower().startswith('org '):lines.append((num,'org',line[4:].strip()))
        else:
            for k in ('.BlockLoop','.ByteLoop','.NoExtraBlock','.PendingCopy','.WordLoop'):
                line=line.replace(k,global_label+k)
            lines.append((num,'code',line))
    return lines


def assemble(src):
    lines=parse(src)
    labels={};pc=None
    for num,kind,payload in lines:
        if kind=='org':pc=number(payload,labels)
        elif kind=='label':
            if payload in labels:raise ValueError(f'Duplicate label {payload}')
            labels[payload]=pc
        else:
            if pc is None:raise ValueError('Code appears before org')
            pc+=len(encode(payload,pc,labels,unknown=True))
    memory={};pc=None;spans=[];begin=None
    for num,kind,payload in lines:
        if kind=='org':
            if begin is not None:spans.append((begin,pc))
            pc=number(payload,labels);begin=pc
        elif kind=='code':
            bs=encode(payload,pc,labels)
            for i,b in enumerate(bs):
                if pc+i in memory:raise ValueError(f'Overlapping assembly at {pc+i:04X}')
                memory[pc+i]=b
            pc+=len(bs)
    if begin is not None:spans.append((begin,pc))
    return memory,spans,labels


def analyze(rom):
    assert hashlib.sha256(rom).hexdigest()==SHA, 'ROM fingerprint mismatch'
    memory,spans,labels=assemble(SOURCE.read_text())
    assert spans==[(0x05F2,0x0624),(0x06C1,0x06D4),(0x06D4,0x06E8),(0x0BA1,0x0BB7)]
    for p,b in memory.items():
        assert rom[p]==b,f'Assembler mismatch at ${p:04X}: built ${b:02X}, source ${rom[p]:02X}'
    blocks=[]
    for start,end in spans:
        code=bytes(memory[p] for p in range(start,end))
        blocks.append({'start':f'{start:04X}','end_exclusive':f'{end:04X}',
                       'bytes':len(code),'sha256':hashlib.sha256(code).hexdigest(),
                       'matches_rom':True})
    out={'assembler':'independent restricted two-pass encoder, NOT external full-Z80 assembler',
         'source_sha256':SHA,'source_asm':'src/phase9_vdp.asm',
         'total_assembled_bytes':len(memory), 'span_count':len(spans),
         'symbol_count':len(labels), 'sections':blocks,
         'limitation':'Three disjoint VDP components plus the uploader; no full ROM build, emulator trace or timing parity'}
    return json.dumps(out,indent=2)+'\n',out,memory


def main():
    p=argparse.ArgumentParser()
    p.add_argument('rom',type=Path)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write',action='store_true')
    mode.add_argument('--check',action='store_true')
    a=p.parse_args()
    content,report,_=analyze(a.rom.read_bytes())
    dest=ROOT/'phase9/assembly_report.json'
    if a.write:dest.write_text(content)
    else:assert dest.read_text()==content,'Assembly metadata changed'
    print(f'PASS Phase9 assembly: {report["total_assembled_bytes"]} bytes emitted and matched, {report["symbol_count"]} labels')

if __name__=='__main__':
    try:main()
    except (AssertionError,ValueError,IndexError,OSError) as ex:sys.exit('FAIL Phase9 assembler: '+str(ex))
