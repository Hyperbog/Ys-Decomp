#!/usr/bin/env python3
"""Source-backed static bank-1 control/hardware reference ledger.

This does not certify mapper occupancy, hardware timing, or gameplay execution.
"""
import argparse
import json
import re
from pathlib import Path
from build_sms_phase14 import ROOT, SOURCES
from whole_bank01 import BANK, CODE, instruction_index, full_bank, sha

PORTS={0xBE:'VDP data',0xBF:'VDP control',0x7F:'PSG',0xF0:'YM2413 register',0xF1:'YM2413 data'}

def create(root=ROOT):
    bank=full_bank(root)
    entries={}
    for path,b in SOURCES:
        if b!=BANK:continue
        for pc,(mnemonic,length) in instruction_index((root/path).read_text()).items():
            if pc in entries:raise ValueError('Duplicate bank1 static instruction')
            entries[pc]=(mnemonic,length,'previous')
    for pc,(mnemonic,length) in instruction_index((root/CODE).read_text()).items():
        if pc in entries:raise ValueError('Duplicate new bank1 static instruction')
        entries[pc]=(mnemonic,length,'m6 candidate')
    from z80_roundtrip_phase10 import encode
    branches=[];hardware=[];abs_writes=[]
    for pc,(m,n,confidence) in sorted(entries.items()):
        if encode(m,pc)!=bank[pc-0x4000:pc-0x4000+n]:
            raise ValueError(f'Bank1 static opcode digest failure {pc:04X}')
        s=m.lower().strip()
        k=re.match(r'(call|jp|jr|djnz)\b.*?\$([0-9a-f]{4})\s*$',s)
        if k:
            target=int(k[2],16)
            status=('bank0_fixed' if target<0x4000 else
                    'candidate_bank1_mapper_conditional' if target<0x8000 else
                    'slot2_mapper_unknown' if target<0xC000 else 'ram_target')
            branches.append({'at':pc,'instruction':m,'target':target,'mapping':status,'source':confidence})
        port=re.match(r'^(out|in)\s+\(\$([0-9a-f]{2})\)',s)
        if port:
            num=int(port[2],16)
            hardware.append({'at':pc,'instruction':m,'port':num,'device':PORTS.get(num,'other / unknown')})
        if re.match(r'^ld\s+\(\$ffff\),a$',s):
            abs_writes.append({'at':pc,'instruction':m,'meaning':'Sega mapper page 2 (candidate hardware semantics)'})
    return {'schema':'ys-bank1-static-links-v1','physical_bank':1,
        'bank_sha256':sha(bank),'instruction_sites':len(entries),
        'instruction_bytes':sum(n for m,n,c in entries.values()),
        'direct_control_refs':len(branches),
        'io_port_instructions':len(hardware),'mapper_register_writes':len(abs_writes),
        'branches':branches,'hardware_ports':hardware,'mapper_writes':abs_writes,
        'provenance':'Static disassembly only; no dynamic mapper or scene runtime trace.',
        'full_semantic_decode':False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check',action='store_true')
    p.add_argument('--output',type=Path,default=ROOT/'wholebank01/static_control_links.json')
    a=p.parse_args();out=create()
    if a.check:
        if json.loads(a.output.read_text())!=out:raise ValueError('Bank1 static ledger drift')
    else:a.output.write_text(json.dumps(out,indent=2)+'\n')
    print('Bank1 static instruction sites',out['instruction_sites'],
       'branch targets',out['direct_control_refs'],'port operations',out['io_port_instructions'],
       'mapper-write sites',out['mapper_register_writes'])
if __name__=='__main__':main()
