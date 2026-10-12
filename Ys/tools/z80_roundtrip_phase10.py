#!/usr/bin/env python3
"""Independent instruction-to-opcode Z80 encoder for ROM-sourced assembly.

NOT an external assembler. Does not read original ROM to generate instructions;
ROM supplied only for verification. Unsupported opcodes fail closed.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REG = ('b','c','d','e','h','l','(hl)','a')
RP = ('bc','de','hl','sp')
STACK = ('bc','de','hl','af')
CC = ('nz','z','nc','c','po','pe','p','m')
ALU = ('add a,','adc a,','sub ','sbc a,','and ','xor ','or ','cp ')
ROT = ('rlca','rrca','rla','rra','daa','cpl','scf','ccf')
SHIFT = ('rlc','rrc','rl','rr','sla','sra','sll','srl')
# Encoding spec: literal opcodes and operand insertion tuples (width, source-index).
OPS = defaultdict(list)


def canonical(text):
    # Preserve the opcode/operand boundary: RLD must not alias RL D.
    fields = text.lower().strip().split(None, 1)
    return fields[0] + (' ' + ''.join(fields[1].split()) if len(fields) > 1 else '')


def add(txt, code, *fields):
    OPS[canonical(txt)].append((tuple(code), tuple(fields)))

def initialize():
    for code in range(256):
        x,y,z = code >> 6,(code >> 3)&7,code&7
        p,q = y >> 1,y&1
        spec=[]; txt=None
        if x==0:
            if z==0:
                if y==0: txt='nop'
                elif y==1:txt="ex af,af'"
                else:
                    txt=('djnz ','jr ','jr nz,','jr z,','jr nc,','jr c,')[y-2]+'%'
                    spec=[('r',0)]
            elif z==1:
                txt=f'add hl,{RP[p]}' if q else f'ld {RP[p]},%'
                if not q:spec=[('w',0)]
            elif z==2:
                target=('(bc)','(de)','(%)','(%)')[p]
                if p<2:txt=f'ld {"a,"+target if q else target+",a"}'
                elif p==2:txt=f'ld {"hl,"+target if q else target+",hl"}'
                else:txt=f'ld {"a,"+target if q else target+",a"}'
                if p>=2:spec=[('w',0)]
            elif z==3:txt=f'{"dec" if q else "inc"} {RP[p]}'
            elif z in (4,5):txt=f'{"inc" if z==4 else "dec"} {REG[y]}'
            elif z==6:txt=f'ld {REG[y]},%';spec=[('b',0)]
            else:txt=ROT[y]
        elif x==1:
            txt='halt' if code==0x76 else f'ld {REG[y]},{REG[z]}'
        elif x==2:txt=ALU[y]+REG[z]
        else:
            if z==0:txt=f'ret {CC[y]}'
            elif z==1:
                txt=f'pop {STACK[p]}' if not q else ('ret','exx','jp (hl)','ld sp,hl')[p]
            elif z==2:txt=f'jp {CC[y]},%';spec=[('w',0)]
            elif z==3:
                if y==0:txt='jp %';spec=[('w',0)]
                elif y==2:txt='out (%),a';spec=[('b',0)]
                elif y==3:txt='in a,(%)';spec=[('b',0)]
                elif y==4:txt='ex (sp),hl'
                elif y==5:txt='ex de,hl'
                elif y==6:txt='di'
                elif y==7:txt='ei'
            elif z==4:txt=f'call {CC[y]},%';spec=[('w',0)]
            elif z==5:
                if not q:txt=f'push {STACK[p]}'
                elif p==0:txt='call %';spec=[('w',0)]
            elif z==6:txt=ALU[y]+'%';spec=[('b',0)]
            else:txt=f'rst %';spec=[('rst',0)]
        if txt is None:continue
        add(txt, [code], *spec)
        # DD/FD reinterpret ONLY instructions involving H/L/(HL).
        indexable=(x==0 and (((z==1 and (p==2 or q==1)) or (z in (2,3) and p==2)) or (z in (4,5,6) and y in (4,5,6)))) or (x==1 and code!=0x76 and (y in (4,5,6) or z in (4,5,6))) or (x==2 and z in (4,5,6)) or (x==3 and ((z==1 and p==2) or (z==3 and y==4) or (z==5 and not q and p==2)))
        if not indexable:continue
        for idx,prefix in [('ix',0xdd),('iy',0xfd)]:
            # Protect the mnemonic, transforming operand registers only.
            head,_,args=txt.partition(' ')
            if not args:continue
            replace=lambda m: {'hl':idx,'h':idx+'h','l':idx+'l'}[m.group(0)]
            args=re.sub(r'\bhl\b|\bh\b|\bl\b',replace,args)
            disp=('('+idx+')') in args
            if disp:args=args.replace('('+idx+')','('+idx+'@)')
            fields=[('d',0)]+[(kind,at+1) for kind,at in spec] if disp else spec
            add(head+' '+args, [prefix,code], *fields)
    for code in range(256):
        x,y,z=code>>6,(code>>3)&7,code&7
        txt=(f'{SHIFT[y]} {REG[z]}' if x==0 else
             f'bit {y},{REG[z]}' if x==1 else
             f'{"res" if x==2 else "set"} {y},{REG[z]}')
        add(txt,[0xcb,code])
        for idx,prefix in [('ix',0xdd),('iy',0xfd)]:
            dest=f'({idx}@)'
            if x==0: t=f'{SHIFT[y]} {dest}'
            elif x==1:t=f'bit {y},{dest}'
            else:t=f'{"res" if x==2 else "set"} {y},{dest}'
            if z!=6 and x!=1:t+=f',{REG[z]}'
            if z!=6 and x==1:continue
            # DD CB displacement opcode, not DD CB opcode displacement.
            add(t,[prefix,0xcb,code],('d',0))
    ed_block=('ldi','cpi','ini','outi','ldd','cpd','ind','outd',
              'ldir','cpir','inir','otir','lddr','cpdr','indr','otdr')
    for code in range(256):
        x,y,z=code>>6,(code>>3)&7,code&7
        p,q=y>>1,y&1
        txt=None; spec=[]
        if x==1:
            if z==0:txt=f'in {REG[y]},(c)' if y!=6 else 'in (c)'
            elif z==1:txt=f'out (c),{REG[y]}' if y!=6 else 'out (c),0'
            elif z==2:txt=f'{"adc" if q else "sbc"} hl,{RP[p]}'
            elif z==3:
                txt=f'ld {RP[p]},(%)' if q else f'ld (%),{RP[p]}'
                spec=[('w',0)]
            elif z==4:txt='neg'
            elif z==5:txt='reti' if y==1 else 'retn'
            elif z==6:txt=f'im {(0,0,1,2,0,0,1,2)[y]}'
            elif z==7 and y<6:
                txt=('ld i,a','ld r,a','ld a,i','ld a,r','rrd','rld')[y]
        elif x==2 and z<=3 and y>=4:txt=ed_block[(y-4)*4+z]
        if txt:add(txt,[0xed,code],*spec)

initialize()

def normalized(s):
    s=canonical(s)
    s=re.sub(r'\$[a-f0-9]+|\bloc_[a-f0-9]+\b','%',s)
    return re.sub(r'\b(ix|iy)([+-]\d+)',lambda m:m[1]+'@',s)

def operands(s):
    s=''.join(s.lower().split())
    return re.findall(r'\$[a-f0-9]+|\bloc_[a-f0-9]+\b|(?<=ix)[+-]\d+|(?<=iy)[+-]\d+',s)

def encode(s,pc,labels=None):
    choices=OPS.get(normalized(s),[])
    if not choices:raise ValueError(f'Unsupported instruction: {pc:04X}: {s}')
    vals=operands(s); labels=labels or {}
    def numeric(t):
        if t.startswith('$'):return int(t[1:],16)
        if t in labels:return labels[t]
        if t.startswith(('ix','iy')):raise ValueError(t)
        if t[0] in '+-':return int(t)
        if t.startswith('loc_'):return None
        raise ValueError('Unknown operand: '+t)
    for opbytes,fields in choices:
        value=bytearray(opbytes)
        # DD CB displacement must be inserted before last opcode.
        ddcb=len(value)==3 and value[1]==0xcb
        if ddcb:value=value[:2]
        for field,index in fields:
            n=numeric(vals[index]);n=0 if n is None else n
            if field=='rst':
                if n != opbytes[0]-0xc7:break
                continue
            if field=='r':
                n=((n-pc-2+32768)&65535)-32768
                if not -128<=n<=127:raise ValueError(f'Out-of-range relative target at {pc:04X}: {s}')
            if field=='d' and not -128<=n<=127:raise ValueError('Index displacement out of range')
            if field in ('b','w') and not 0<=n< (256 if field=='b' else 65536):raise ValueError('Immediate out of range')
            value.extend([n&255] if field in ('b','d','r') else [n&255,(n>>8)&255])
        else:
            if ddcb:
                value.append(opbytes[-1])
            return bytes(value)
    raise ValueError('No matching encoding '+s)

def assemble(source):
    # Each section: org establishes CPU PC; ROM physical mapping handled by caller.
    lines=[];labels={};pc=None
    for row,line in enumerate(source.splitlines(),1):
        t=line.split(';',1)[0].strip()
        if not t:continue
        if t.lower().startswith('org '):pc=int(t[4:].strip().replace('$','0x'),16);lines.append(('org',pc,row))
        elif t.endswith(':'):
            if pc is None:raise ValueError('Label outside section')
            name=t[:-1].lower()
            if name in labels:raise ValueError('Duplicate label: '+name)
            labels[name]=pc;lines.append(('label',name,row))
        else:
            if pc is None:raise ValueError('Code before org')
            bs=encode(t,pc);lines.append(('code',t,row));pc+=len(bs)
    out={};pc=None
    for kind,value,row in lines:
        if kind=='org':pc=value
        if kind!='code':continue
        chunk=encode(value,pc,labels)
        for offset,byte in enumerate(chunk):
            if pc+offset in out:raise ValueError(f'Overlapping code at {pc+offset:04X}')
            out[pc+offset]=byte
        pc+=len(chunk)
    return out,labels

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('file',type=Path)
    ns=p.parse_args()
    code,labels=assemble(ns.file.read_text())
    print(f'{ns.file}: {len(code)} assembled bytes; {len(labels)} labels')
