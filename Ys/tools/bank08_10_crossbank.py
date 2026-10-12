#!/usr/bin/env python3
"""Fixed-bank mapper/branch evidence for bank8 and bank10 code entries.

Only contiguous ROM-backed LD A,n; LD ($FFFF),A; CALL/JP patterns qualify.
Not a gameplay mapper trace.
"""
import argparse
import hashlib
import json
from pathlib import Path
from build_sms_phase14 import ROOT,EXPECTED_SHA
from whole_bank00 import full_bank as bank00
from whole_banks08_10 import full_bank as complete_bank

PATTERNS=[(0x0FB1,8,'call',0xBEE8),(0x38C4,10,'jp',0xBF16),(0x3E86,10,'jp',0xBEF7)]

def ledger():
    bank=bank00();out=[]
    for pc,index,kind,target in PATTERNS:
        opcode={'call':0xCD,'jp':0xC3}[kind]
        expected=bytes((0x3E,index,0x32,0xFF,0xFF,opcode,target&255,target>>8))
        if bank[pc:pc+len(expected)]!=expected:
            raise ValueError(f'Unexpected fixed-bank mapper/transfer sequence at {pc:04X}')
        # Confirm mapper target is genuinely reconstructed source data.
        target_bank=complete_bank(index)
        op=target_bank[target-0x8000]
        out.append({'fixed_bank_pc':f'{pc:04X}','mapper_register':'FFFF',
                    'mapper_value':index,'control_transfer':kind,'target_cpu':f'{target:04X}',
                    'physical_target':f'{index*0x4000+target-0x8000:05X}',
                    'target_first_opcode':f'{op:02X}',
                    'evidence':'contiguous fixed-bank instructions; not emulator-derived mapper state'})
    return {'schema':'ys-bank08-10-static-mapper-links-v1','references':out,
      'count':len(out),'limitations':['Sequences are static candidates, not gameplay execution traces.',
       'Effects of any intervening interrupt or external mapper changes not modeled.']}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check',action='store_true');p.add_argument('--report',type=Path,default=ROOT/'whole_system/m8_mapper_links.json')
    a=p.parse_args();r=ledger()
    if a.check:
        if r!=json.loads(a.report.read_text()):raise ValueError('Mapper evidence ledger drift')
    else:a.report.write_text(json.dumps(r,indent=2)+'\n')
    print('M8 fixed-bank mapper sites',r['count'])
if __name__=='__main__':main()
