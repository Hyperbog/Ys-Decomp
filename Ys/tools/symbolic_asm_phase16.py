#!/usr/bin/env python3
"""Named symbolic views of existing verified Z80 modules, with strict EQU resolution.
Not new code coverage. Keeps canonical instruction sources unchanged.
"""
import argparse
import json
import re
from pathlib import Path
from z80_roundtrip_phase10 import assemble
ROOT=Path(__file__).resolve().parents[1]
MODULES={
  'src/phase11_roundtrip/bank00.asm':'src/phase16/bank00_symbolic.asm',
  'src/phase11_roundtrip/bank06.asm':'src/phase16/bank06_symbolic.asm',
  'src/phase12/bank06_sprite_handlers.asm':'src/phase16/bank06_handlers_symbolic.asm',
}
CONSTANTS={
  'MapperSlot2':0xFFFF,
  'MapperControl':0xFFFC,
  'SpriteYBuffer':0xDD00,
  'SpriteXTileBuffer':0xDD40,
  'WorkRecordBase':0xC200,
  'SpriteRecordConsumer':0x9932,
  'SpriteObjectHandler':0x9AF6,
  'SpriteHandlerDirectory':0x9A99,
}
EQU=re.compile(r'^([A-Za-z_][A-Za-z_0-9]*)\s+equ\s+\$([0-9A-Fa-f]{1,4})$',re.I)
IDENT=re.compile(r'(?<![A-Za-z_0-9])([A-Za-z_][A-Za-z_0-9]*)(?![A-Za-z_0-9])')

def resolve(text):
    eq={};out=[]
    for line in text.splitlines():
        code,comment=(line.split(';',1)+[''])[:2]
        t=code.strip()
        m=EQU.fullmatch(t)
        if m:
            if m[1].lower() in eq:raise ValueError('duplicate symbolic constant')
            eq[m[1].lower()]=int(m[2],16)
            continue
        if not t or t.lower().startswith('org ') or t.endswith(':'):
            out.append(line);continue
        # Only replace named constants, leaving mnemonics, registers, and local labels intact.
        def repl(m):
            name=m[1].lower()
            return f'${eq[name]:04X}' if name in eq else m[0]
        resolved=IDENT.sub(repl,code)
        out.append(resolved+(' ;'+comment if ';' in line else ''))
    return '\n'.join(out)+'\n'

def symbolic_source(original):
    symbolic=[];used=set()
    for line in original.splitlines():
        code=line.split(';',1)[0].strip()
        if not code or code.lower().startswith('org ') or code.endswith(':'):
            symbolic.append(line);continue
        head,*tail=line.split(';',1)
        for name,num in CONSTANTS.items():
            pattern=r'(?<![0-9A-Za-z_])\$'+f'{num:04X}'+r'(?![0-9A-Fa-f])'
            head,count=re.subn(pattern,name,head,flags=re.I)
            if count:used.add(name)
        symbolic.append(head+(' ;'+tail[0] if tail else ''))
    hdr=['; Symbolic Phase 16 view; original sources remain canonical.',
         '; EQU constants are expanded to literal addresses before restricted assembly.']
    hdr +=[f'{name} equ ${CONSTANTS[name]:04X}' for name in sorted(used)]
    return '\n'.join(hdr+['']+symbolic)+'\n'

def verify(root=ROOT):
    stats={}
    for original,derived in MODULES.items():
        canonical=(root/original).read_text()
        expected=symbolic_source(canonical)
        if (root/derived).read_text()!=expected:raise ValueError('symbolic source drift: '+derived)
        base,_=assemble(canonical)
        built,_=assemble(resolve(expected))
        if base!=built:raise ValueError('symbolic assembly differs: '+derived)
        stats[derived]={'bytes':len(built),'symbolic_bindings':sum(1 for name in CONSTANTS if re.search(r'\b'+name+r'\b',expected) and f'{name} equ' in expected)}
    return stats

def main():
    p=argparse.ArgumentParser();p.add_argument('--sync',action='store_true');p.add_argument('--verify',action='store_true')
    a=p.parse_args()
    if a.sync:
        for old,new in MODULES.items():
            path=ROOT/new;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(symbolic_source((ROOT/old).read_text()))
    print(json.dumps(verify(),indent=2))
if __name__=='__main__':main()
