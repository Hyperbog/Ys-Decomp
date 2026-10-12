#!/usr/bin/env python3
"""Execute ROM bank4 Z80 collision predicate at CPU $807C on synthetic states.

Emulates ONLY the instructions actually present in this routine. Carries an
independent field-level predicate as a cross-check. Not full-game emulation.
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from build_sms_phase14 import ROOT,EXPECTED_SHA

BASE=0x10000

def collision_reference(record,index_y,index_x,c,b,e,d):
    """Independent Z80 arithmetic/branch semantics, not emulated instructions."""
    y0,ylen,x0,xlen=record
    ysum=y0+index_y
    if ysum<256:return False
    y=ysum&255
    if y!=c:
        if y>=c:return False
        if y+ylen>=256 or ((y+ylen)&255)<b:return False
    xsum=x0+index_x
    if xsum<256:return False
    x=xsum&255
    if x==e:return True
    if x>=e:return False
    return x+xlen<256 and ((x+xlen)&255)>=d

class CollisionMachine:
    def __init__(self,rom,table_index,origin_y,origin_x,c,b,e,d):
        self.rom=rom
        self.pc=0x807C
        self.a=table_index;self.b=b;self.c=c;self.d=d;self.e=e
        self.h=self.l=0;self.ix=0xC300
        self.origin_y=origin_y;self.origin_x=origin_x
        self.carry=False;self.zero=False
        self.steps=0;self.exit_pc=None;self.table_reads=[]
    def mem(self,address):
        if address==self.ix+17:return self.origin_y
        if address==self.ix+16:return self.origin_x
        if 0x8000<=address<0xC000:
            return self.rom[BASE+address-0x8000]
        raise ValueError(f'Unexpected bank4 collision memory read {address:04X}')
    def fetch(self):
        if not 0x807C<=self.pc<=0x80A1:
            raise ValueError(f'Left collision routine at {self.pc:04X}')
        v=self.mem(self.pc);self.pc+=1;return v
    def add(self,val):
        v=self.a+val;self.carry=v>255;self.a=v&255;self.zero=self.a==0
    def cp(self,val):
        self.carry=self.a<val;self.zero=self.a==val
    def run(self):
        for _ in range(80):
            ins=self.pc;op=self.fetch();self.steps+=1
            if op==0x87:self.add(self.a) # ADD A,A
            elif op==0x6F:self.l=self.a
            elif op==0x26:self.h=self.fetch()
            elif op==0x7E:
                addr=self.h<<8|self.l;self.a=self.mem(addr);self.table_reads.append(addr)
            elif op==0x2C:
                self.l=(self.l+1)&255;self.zero=self.l==0 # carry unchanged
            elif op==0xDD:
                if self.fetch()!=0x86:raise ValueError('Unexpected DD collision opcode')
                disp=self.fetch();val=self.mem(self.ix+(disp if disp<128 else disp-256));self.add(val)
            elif op==0xD0: # RET NC
                if not self.carry:self.exit_pc=ins;return False
            elif op==0xB9:self.cp(self.c)
            elif op==0xB8:self.cp(self.b)
            elif op==0xBB:self.cp(self.e)
            elif op==0xBA:self.cp(self.d)
            elif op==0x28: # JR Z
                disp=self.fetch()
                if self.zero:self.pc=(self.pc+(disp if disp<128 else disp-256))&0xFFFF
            elif op==0x38: # JR C
                disp=self.fetch()
                if self.carry:self.pc=(self.pc+(disp if disp<128 else disp-256))&0xFFFF
            elif op==0x86:
                addr=self.h<<8|self.l;self.add(self.mem(addr));self.table_reads.append(addr)
            elif op==0x3F:self.carry=not self.carry # CCF; zero unchanged
            elif op==0xC9:self.exit_pc=ins;return self.carry
            else:raise ValueError(f'Unsupported bank4 collision opcode {op:02X} at {ins:04X}')
        raise ValueError('Bank4 collision routine exceeded instruction budget')

def trace(rom):
    if len(rom)!=0x40000 or hashlib.sha256(rom).hexdigest()!=EXPECTED_SHA:
        raise ValueError('Original ROM fingerprint mismatch')
    table=rom[BASE:BASE+124]
    if len(table)!=31*4:raise AssertionError('Collision table not 31 records')
    counts=Counter();cases=0;positive=0;steps=0;out=hashlib.sha256()
    for i in range(31):
        record=table[i*4:i*4+4]
        y0,ylen,x0,xlen=record
        for seed in range(16):
            oy=(seed*17+33)&255;ox=(seed*29+51)&255
            ya=(y0+oy)&255;xa=(x0+ox)&255
            # Include branch-boundary probes, zero/equality, and false pathways.
            for variant in range(8):
                c=(ya+(variant%3))&255
                b=(ya+ylen-1+((variant//3)%3))&255
                e=(xa+(variant%3))&255
                d=(xa+xlen-1+((variant//3)%3))&255
                m=CollisionMachine(rom,i,oy,ox,c,b,e,d)
                actual=m.run();expected=collision_reference(record,oy,ox,c,b,e,d)
                if actual!=expected:
                    raise AssertionError(f'Collision mismatch record {i} seed {seed} variant {variant}: {actual}/{expected}')
                if any(not 0x8000<=p<0x807C for p in m.table_reads):
                    raise AssertionError('Collision table read outside descriptor range')
                cases+=1;positive+=actual;steps+=m.steps;counts[f'{m.exit_pc:04X}']+=1
                out.update(bytes([i,seed,variant,int(actual),m.steps,m.exit_pc&255,m.exit_pc>>8]))
    return {'schema':'ys-bank04-bounded-collision-v1','case_count':cases,
        'descriptor_records':31,'origin_seed_count':16,'boundary_variants':8,
        'collision_positive_cases':positive,'collision_negative_cases':cases-positive,
        'executed_opcodes_total_with_repeats':steps,'return_sites':dict(sorted(counts.items())),
        'outcome_trace_sha256':out.hexdigest(),
        'limitations':['Runs actual bank-4 collision instruction bytes on seeded registers and IX memory.',
        'Independent direct predicate checks arithmetic and carry behavior; synthetic state only.',
        'Does not establish game-state call paths, actor coordinate units, or whole-system runtime.']}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path);p.add_argument('--check',action='store_true')
    p.add_argument('--report',type=Path,default=ROOT/'wholebank04/collision_report.json')
    a=p.parse_args();report=trace(a.rom.read_bytes())
    if a.check:
        if json.loads(a.report.read_text())!=report:raise ValueError('Collision report snapshot drift')
    else:a.report.parent.mkdir(exist_ok=True,parents=True);a.report.write_text(json.dumps(report,indent=2)+'\n')
    print(report)
if __name__=='__main__':main()
