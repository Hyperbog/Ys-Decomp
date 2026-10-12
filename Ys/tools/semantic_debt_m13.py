#!/usr/bin/env python3
"""Audit semantic reconstruction of all 16 source-only SMS bank listings.

Counts bytes from the committed human-readable assembly (never guesses semantic
completion from ROM parity). Labels containing unresolved/undecoded are a *lower
bound* on semantic debt; anonymous DB/DW data is separately exposed.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
try:
    from .z80_roundtrip_phase10 import encode
    from .build_sms_phase14 import ROOT
except ImportError:
    from z80_roundtrip_phase10 import encode
    from build_sms_phase14 import ROOT

LABEL=re.compile(r'^([A-Za-z_][\w.]*)\s*:$')
DATA=re.compile(r'^(db|dw)\s+(.+)$',re.I)
ORG=re.compile(r'^org\s+\$([0-9a-f]+)$',re.I)
UNCERTAIN=re.compile(r'(unresolved|undecoded|opaque|candidate|unknown)',re.I)

def analyze_bank(bank,root=ROOT):
    path=root/f'src/wholebank{bank:02}/bank{bank:02}_complete.asm'
    if not path.is_file():raise ValueError(f'Bank {bank} source missing')
    offset=0 if bank==0 else (0x4000 if bank==1 else 0x8000)
    pc=None;active=None;spans=[];seen=set();bytes_by_kind={'mnemonic':0,'db':0,'dw':0}; uncertain=[]
    for lineno,line in enumerate(path.read_text().splitlines(),1):
        s=line.split(';',1)[0].strip()
        if not s:continue
        match=ORG.fullmatch(s)
        if match:
            pc=int(match[1],16)
            if pc!=offset:
                raise ValueError(f'Unexpected ORG bank {bank} line {lineno}')
            continue
        match=LABEL.fullmatch(s)
        if match:
            if pc is None:raise ValueError('Label before ORG')
            active=match[1]
            continue
        if pc is None:raise ValueError('Code before ORG')
        match=DATA.fullmatch(s)
        if match:
            kind=match[1].lower()
            items=[v.strip() for v in match[2].split(',')]
            if not items or any(not re.fullmatch(r'\$[0-9a-fA-F]+',i) for i in items):
                raise ValueError(f'Nonliteral data bank {bank} line {lineno}')
            vals=[int(v[1:],16) for v in items]
            if any(v>(255 if kind=='db' else 65535) for v in vals):raise ValueError('Data width overflow')
            raw=bytes(vals) if kind=='db' else b''.join(v.to_bytes(2,'little') for v in vals)
        else:
            kind='mnemonic';raw=encode(s,pc)
        if len(raw)==0:raise ValueError('Empty source instruction/data')
        if pc<offset or pc+len(raw)>offset+0x4000:
            raise ValueError(f'Out-of-bank source bank {bank} line {lineno}')
        for i in range(pc,pc+len(raw)):
            if i in seen:raise ValueError(f'Overlapping source bank {bank} at ${i:04X}')
            seen.add(i)
        row={'cpu_start':pc,'bytes':len(raw),'kind':kind,'label':active}
        spans.append(row)
        bytes_by_kind[kind]+=len(raw)
        if active and UNCERTAIN.search(active):uncertain.append(row)
        pc+=len(raw)
    if seen!=set(range(offset,offset+0x4000)):raise ValueError(f'Bank {bank} source contains gaps')
    ambiguous=sum(r['bytes'] for r in uncertain)
    anonymous_data=sum(r['bytes'] for r in spans if r['kind']!='mnemonic' and not r['label'])
    groups=[]
    for row in spans:
        if not row['label'] or not UNCERTAIN.search(row['label']):continue
        if groups and groups[-1]['label']==row['label'] and groups[-1]['end_cpu_exclusive']==row['cpu_start']:
            groups[-1]['end_cpu_exclusive']+=row['bytes'];groups[-1]['bytes']+=row['bytes']
        else:groups.append({'label':row['label'],'start_cpu':row['cpu_start'],'end_cpu_exclusive':row['cpu_start']+row['bytes'],'bytes':row['bytes']})
    return {'bank':bank,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'mnemonic_bytes':bytes_by_kind['mnemonic'],'db_bytes':bytes_by_kind['db'],
            'dw_bytes':bytes_by_kind['dw'],'explicitly_uncertain_bytes_lower_bound':ambiguous,
            'unlabeled_data_bytes':anonymous_data,'explicitly_uncertain_regions':groups}

def make_report(root=ROOT):
    banks=[analyze_bank(n,root) for n in range(16)]
    return {'schema':'ys-semantic-debt-m13-v1','classification':'explicit-label-based lower bound; NOT definitive semantic decoding',
            'bank_count':16,'cartridge_bytes':0x40000,
            'mnemonic_bytes':sum(x['mnemonic_bytes'] for x in banks),
            'data_directive_bytes':sum(x['db_bytes']+x['dw_bytes'] for x in banks),
            'explicitly_uncertain_bytes_lower_bound':sum(x['explicitly_uncertain_bytes_lower_bound'] for x in banks),
            'banks':banks}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,default=ROOT/'whole_system/semantic_debt_m13.json')
    ap.add_argument('--check',action='store_true')
    a=ap.parse_args()
    r=make_report()
    if a.check:
        if json.loads(a.out.read_text())!=r:raise ValueError('Semantic-debt report changed')
    else:
        a.out.parent.mkdir(exist_ok=True,parents=True);a.out.write_text(json.dumps(r,indent=2)+'\n')
    print('Mnemonic bytes:',r['mnemonic_bytes'],'DB/DW bytes:',r['data_directive_bytes'], 'explicit uncertainty lower bound:',r['explicitly_uncertain_bytes_lower_bound'])
if __name__=='__main__':main()
