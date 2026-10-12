#!/usr/bin/env python3
"""ROM-independent verified bank1 -> bank4 collision caller dependency ledger."""
import argparse
import json
from pathlib import Path
from build_sms_phase14 import ROOT
from whole_bank01 import full_bank as bank01
from whole_bank04 import full_bank as bank04

CALLS=((0x47C2,14),(0x486C,14),(0x48DF,13))

def build(root=ROOT):
    caller=bank01(root);target=bank04(root)
    if target[0x7C:0xA2]!=bytes.fromhex('87876f26807e2cdd8611d0b92807d0863812b8380f2c7edd8610d0bb2806d02c863801ba3fc9'):
        raise ValueError('Bank4 collision instruction fingerprint drift')
    records=[{'record':i,'offset':i*4,'cpu_address':f'{0x8000+4*i:04X}',
              'y_offset_raw':target[4*i],'y_extent_raw':target[4*i+1],
              'x_offset_raw':target[4*i+2],'x_extent_raw':target[4*i+3]} for i in range(31)]
    references=[]
    for pc,delta in CALLS:
        idx=pc-0x4000
        if (caller[idx:idx+3]!=b'\xcd\x7c\x80' or
            caller[idx-3:idx]!=bytes([0xDD,0x7E,delta])):
            raise ValueError(f'Bank1 collision caller opcode changed at {pc:04X}')
        if caller[idx+3]!=0xD9:raise ValueError('Collision caller does not EXX after return')
        references.append({'from_bank':1,'from_cpu':f'{pc:04X}',
            'opcode':'CD7C80','target_cpu':'807C','target_bank_candidate':4,
            'actor_index_offset_in_ix':delta,
            'mapping_status':'bank4_candidate_not_runtime_proven',
            'returned_carry_examined_by_caller':True})
    return {'schema':'ys-bank04-crossbank-static-links-v1',
            'routine_cpu':'807C','routine_bank':4,
            'box_count':31,'records':records,'call_references':references,
            'table_index_calculation':'A*4 into $8000 using ADD A,A twice; valid actor table index 0..30',
            'mapper_proven_at_calls':False,
            'scope':'Caller opcodes and descriptors are ROM-matched project source; dynamic mapper state unknown.'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check',action='store_true')
    p.add_argument('--report',type=Path,default=ROOT/'wholebank04/crossbank_links.json')
    a=p.parse_args();r=build()
    if a.check:
        if r!=json.loads(a.report.read_text()):raise ValueError('Crossbank links snapshot mismatch')
    else:a.report.write_text(json.dumps(r,indent=2)+'\n')
    print('Three bank1 collision call sites and 31 box descriptors validated')
if __name__=='__main__':main()
