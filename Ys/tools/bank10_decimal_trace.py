#!/usr/bin/env python3
"""Bounded execution of original bank10 decimal-to-VDP routine $BEF8-$BF41.

Starts after unmodeled RST $28 setup at $BEF7. This is not full SMS emulation.
"""
import argparse
import hashlib
import json
from pathlib import Path
from build_sms_phase14 import ROOT,EXPECTED_SHA
from whole_banks08_10 import full_bank

def execute(bank,value,separator=0x5E):
    if len(bank)!=0x4000 or not 0<=value<=0xFFFF:raise ValueError('Invalid decimal run')
    regs={'pc':0xBEF8,'hl':value,'de':0,'a':0,'b':0,'carry':False}
    stack=[];writes=[];trace=[]
    def fetch():
        pc=regs['pc']
        if not 0xBEF8<=pc<0xBF42:raise ValueError(f'Execution escaped decimal routine {pc:04X}')
        x=bank[pc-0x8000];regs['pc']=pc+1;return x
    def word():return fetch()|(fetch()<<8)
    for _ in range(1500):
        pc=regs['pc'];op=fetch();trace.append(pc)
        if op==0x06:regs['b']=fetch()
        elif op==0x11:regs['de']=word()
        elif op==0x19:
            raw=regs['hl']+regs['de'];regs['carry']=raw>65535;regs['hl']=raw&65535
        elif op==0x04:regs['b']=(regs['b']+1)&255
        elif op==0x05:regs['b']=(regs['b']-1)&255
        elif op==0x38:
            d=fetch();d=d if d<128 else d-256
            if regs['carry']:regs['pc']=(regs['pc']+d)&65535
        elif op==0xED:
            op2=fetch()
            if op2!=0x52:raise ValueError('Unsupported ED opcode')
            v=regs['hl']-regs['de']-int(regs['carry']);regs['carry']=v<0;regs['hl']=v&65535
        elif op==0xCD:
            dest=word()
            if dest!=0xBF35:raise ValueError('Unexpected call target')
            stack.append(regs['pc']);regs['pc']=dest
        elif op==0x45:regs['b']=regs['hl']&255
        elif op==0x3E:regs['a']=fetch()
        elif op==0x80:
            v=regs['a']+regs['b'];regs['a']=v&255;regs['carry']=v>255
        elif op==0xD3:
            port=fetch()
            if port!=0xBE:raise ValueError('Unexpected I/O port')
            writes.append(regs['a'])
        elif op==0x3A:
            addr=word()
            if addr!=0xC026:raise ValueError('Unexpected RAM access')
            regs['a']=separator
        elif op==0x00:pass
        elif op==0xC9:
            if stack:regs['pc']=stack.pop()
            else:
                expected=b''.join(bytes((ord(v),separator)) for v in f'{value:05d}')
                if bytes(writes)!=expected:
                    raise AssertionError(f'Incorrect decimal output for {value}: {bytes(writes).hex()} vs {expected.hex()}')
                return {'value':value,'port_bytes':len(writes),'steps':len(trace),'output_sha256':hashlib.sha256(bytes(writes)).hexdigest()}
        else:raise ValueError(f'Unsupported opcode {op:02X} at {pc:04X}')
    raise ValueError('Decimal interpreter step limit')

def trace():
    bank=full_bank(10)
    samples=sorted(set([0,1,9,10,99,100,999,1000,9999,10000,65535]+[n*257 for n in range(256) if n*257<=65535]))
    digest=hashlib.sha256();maxsteps=0
    for v in samples:
        out=execute(bank,v)
        digest.update(bytes([v&255,v>>8]));digest.update(bytes.fromhex(out['output_sha256']))
        maxsteps=max(maxsteps,out['steps'])
    return {'schema':'ys-bank10-decimal-bounded-v1','tested_values':len(samples),
      'start_pc':'BEF8','subroutine':'BF35','port':'BE',
      'bytes_per_value':10,'max_instructions_per_case':maxsteps,
      'output_sha256':digest.hexdigest(),
      'limitations':['First byte RST $28 at $BEF7 and its fixed-bank handler are excluded.',
        'No VDP address/control behavior modeled; only byte writes to port BE.',
        'Original bank10 instruction bytes are executed with manually supplied HL and C026 state.']}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check',action='store_true');p.add_argument('--report',type=Path,default=ROOT/'wholebank10/decimal_trace.json')
    a=p.parse_args();result=trace()
    if a.check:
        if json.loads(a.report.read_text())!=result:raise ValueError('Decimal trace regression drift')
    else:a.report.write_text(json.dumps(result,indent=2)+'\n')
    print('Decimal bounded execution PASS',result)
if __name__=='__main__':main()
