#!/usr/bin/env python3
"""Source-only rebuild of physical bank 1 ($4000-$7FFF).

Normal build reads *only* repository sources. A separate --capture mode uses a
fingerprinted, user-provided ROM to convert currently unresolved spans into
explicit source records. Static Z80 candidates are not execution-certified.
"""
import argparse
import hashlib
import json
from pathlib import Path
from build_sms_phase14 import ROOT, SOURCES, EXPECTED_SHA
from z80_roundtrip_phase10 import assemble, encode
from source_tables_phase15 import load_verified_sources
import re

BANK=1; START=0x4000; END=0x8000; SIZE=0x4000
SOURCE=Path('wholebank01/source.json')
DIGEST=Path('wholebank01/digests.json')
CODE=Path('src/wholebank01/anchored_code.asm')
ASSEMBLY=Path('src/wholebank01/bank01_complete.asm')
POINTERS=((0x4C03,0x4C13,'scene_subroutine_directory_8'),
          (0x6028,0x602C,'scene_setup_directory_2'))
FF_START=0x7E9C; FF_END=0x7FF0

def sha(b):return hashlib.sha256(b).hexdigest()

def existing(root=ROOT):
    found={}
    for rel,bank in SOURCES:
        if bank!=BANK:continue
        d,_=assemble((root/rel).read_text())
        for pc,v in d.items():
            if pc in found:raise ValueError('Duplicate prior bank1 code byte')
            found[pc]=v
    for pc,v in load_verified_sources(root)[BANK]['bytes'].items():
        if pc in found:raise ValueError('Bank1 code/header overlap')
        found[pc]=v
    if len(found)!=779 or any(not START<=p<END for p in found):
        raise ValueError('Bank1 prior source ownership drift')
    return found

def instruction_index(text):
    starts={};pc=None
    for line in text.splitlines():
        s=line.split(';',1)[0].strip()
        if not s or s.endswith(':'):continue
        if s.lower().startswith('org '):
            pc=int(s.split('$',1)[1],16)
        else:
            if pc is None or s.lower().startswith(('db ','dw ','ds ')):
                raise ValueError('Bank1 expected mnemonic-only instruction module')
            if pc in starts:raise ValueError('Bank1 duplicate instruction start')
            n=len(encode(s,pc))
            starts[pc]=(s,n)
            pc+=n
    return starts

def new_code(root=ROOT):
    text=(root/CODE).read_text(); d,_=assemble(text)
    idx=instruction_index(text)
    claimed={a+i for a,(_,n) in idx.items() for i in range(n)}
    if set(d)!=claimed or len(d)!=1717:
        raise ValueError('Bank1 new code source boundaries drift')
    if set(d)&set(existing(root)):
        raise ValueError('Bank1 new and old code overlap')
    if sha(bytes(d[p] for p in sorted(d)))!=json.loads((root/DIGEST).read_text())['new_code_sha256']:
        raise ValueError('Bank1 new code source SHA drift')
    return d

def new_data(root=ROOT):
    m=json.loads((root/SOURCE).read_text())
    if m.get('schema')!='ys-bank01-source-v1':raise ValueError('Bank1 source schema')
    old=existing(root);code=new_code(root);claimed=set(old)|set(code)
    out={};inventory=[]
    def put(start,raw,name):
        if not raw or start<START or start+len(raw)>END:raise ValueError('Bank1 source chunk boundary '+name)
        for i,v in enumerate(raw):
            p=start+i
            if p in claimed or p in out:raise ValueError('Bank1 data/code overlap '+name)
            out[p]=v
        inventory.append({'start':start,'end_exclusive':start+len(raw),'kind':name,'bytes':len(raw)})
    if len(m['pointer_directories'])!=len(POINTERS):raise ValueError('Bank1 pointer directory count')
    for (a,b,name),meta in zip(POINTERS,m['pointer_directories']):
        v=meta['targets']
        if meta['name']!=name or meta['start']!=a or len(v)!=(b-a)//2 or any(type(x)!=int or not 0x4000<=x<0x7E9C for x in v):
            raise ValueError('Bank1 pointer directory '+name)
        if name=='scene_subroutine_directory_8' and (v[0]!=0x4C13 or v[1]!=0x4C13 or any(not 0x4C13<=q<0x4C80 for q in v)):
            raise ValueError('Bank1 first directory target anchors')
        if name=='scene_setup_directory_2' and v!=[0x602C,0x6043]:
            raise ValueError('Bank1 setup directory anchors')
        put(a,b''.join(x.to_bytes(2,'little') for x in v),name)
    if m['ff_filler']!={'start':FF_START,'count':FF_END-FF_START,'value':255}:
        raise ValueError('Bank1 FF padding changed')
    put(FF_START,b'\xff'*(FF_END-FF_START),'bank_end_ff_filler')
    items=m['unresolved_spans']
    if type(items)!=list or not items:raise ValueError('Bank1 empty unresolved regions')
    prev=START-1
    for i,obj in enumerate(items):
        if type(obj)!=dict or set(obj)!={'start','bytes_hex'}:raise ValueError('Bank1 unresolved schema')
        p=obj['start']
        if type(p)!=int or p<=prev:raise ValueError('Unsorted unresolved spans')
        raw=bytes.fromhex(obj['bytes_hex'])
        if len(raw)>256:raise ValueError('Oversized unresolved span')
        put(p,raw,'unresolved_span_'+str(i));prev=p
    if set(old)|set(code)|set(out)!=set(range(START,END)):
        raise ValueError('Bank1 source-only partition incomplete')
    if sha(bytes(out[p] for p in sorted(out)))!=json.loads((root/DIGEST).read_text())['new_data_sha256']:
        raise ValueError('Bank1 data source SHA drift')
    return out,inventory

def full_bank(root=ROOT):
    a=existing(root);b=new_code(root);c,_=new_data(root)
    if len(a)+len(b)+len(c)!=SIZE or set(a)&set(b) or (set(a)|set(b))&set(c):
        raise ValueError('Bank1 owners overlap')
    blob=bytes((a|b|c)[p] for p in range(START,END))
    if sha(blob)!=json.loads((root/DIGEST).read_text())['bank_sha256']:
        raise ValueError('Bank1 bank SHA drift')
    return blob

def mixed_source(root=ROOT):
    raw=full_bank(root)
    # Previous assembly from source plus new candidate-code instructions.
    instr={}
    for rel,bank in SOURCES:
        if bank!=BANK:continue
        instr.update(instruction_index((root/rel).read_text()))
    for p,v in instruction_index((root/CODE).read_text()).items():
        if p in instr:raise ValueError('Bank1 instruction overlap')
        instr[p]=v
    ptr=set(p for a,b,_ in POINTERS for p in range(a,b,2))
    labels={0x4000:'SceneControlEntry',0x4C03:'SceneSubroutineDirectory8',
      0x6028:'SceneSetupDirectory2',0x6800:'UndecodedSceneData',
      FF_START:'Bank1Padding340',0x7FF0:'SMSHeader'}
    lines=['; Ys bank 1: byte-complete source reconstruction, not full semantic recovery.',
           '; Unknown data has explicit source ownership and is not marked as decoded code.',
           'org $4000']
    pc=START
    while pc<END:
        if pc in labels:lines.append(labels[pc]+':')
        if pc in instr:
            s,n=instr[pc];lines.append('    '+s);pc+=n;continue
        if pc in ptr:
            v=int.from_bytes(raw[pc-START:pc-START+2],'little')
            lines.append(f'    dw ${v:04X}');pc+=2;continue
        limit=min([p for p in instr if p>pc]+[p for p in ptr if p>pc]+[p for p in labels if p>pc]+[END])
        n=min(16,limit-pc)
        if n<=0:raise ValueError('Bank1 mixed emission boundary')
        lines.append('    db '+', '.join(f'${v:02X}' for v in raw[pc-START:pc-START+n]));pc+=n
    return '\n'.join(lines)+'\n'

def assemble_bank01_mixed(source):
    result={};pc=None
    for line in source.splitlines():
        s=line.split(';',1)[0].strip()
        if not s or s.endswith(':'):continue
        if s.lower().startswith('org '):pc=int(s.split('$',1)[1],16);continue
        m=re.fullmatch(r'(db|dw)\s+(.+)',s,re.I)
        if m:
            values=[int(v.strip()[1:],16) for v in m[2].split(',')]
            if m[1].lower()=='db':
                if any(v>255 for v in values):raise ValueError('Bank1 DB out of range')
                blob=bytes(values)
            else:blob=b''.join(v.to_bytes(2,'little') for v in values)
        else:blob=encode(s,pc)
        for byte in blob:
            if pc in result:raise ValueError('Bank1 mixed source overlap')
            result[pc]=byte;pc+=1
    if set(result)!=set(range(START,END)):raise ValueError('Bank1 mixed assembly incomplete')
    return bytes(result[p] for p in range(START,END))

def capture(rom,root=ROOT):
    if len(rom)!=0x40000 or sha(rom)!=EXPECTED_SHA:raise ValueError('Incorrect original ROM')
    # Capture is explicitly separate from normal source-only builds.
    old=existing(root)
    code,_=assemble((root/CODE).read_text())
    if len(code)!=1717 or set(code)&set(old):raise ValueError('Unexpected new code ownership')
    for pc,v in (old|code).items():
        if rom[pc]!=v:raise ValueError(f'Bank1 known source mismatch ${pc:04X}')
    ptr=[];structured=set()
    for a,b,name in POINTERS:
        vals=[int.from_bytes(rom[p:p+2],'little') for p in range(a,b,2)]
        ptr.append({'name':name,'start':a,'targets':vals})
        structured.update(range(a,b))
    structured.update(range(FF_START,FF_END))
    if rom[FF_START:FF_END]!=b'\xff'*(FF_END-FF_START):raise ValueError('Bank1 padding fingerprint')
    remain=sorted(set(range(START,END))-set(old)-set(code)-structured)
    spans=[];i=0
    while i<len(remain):
        start=remain[i];j=i+1
        while j<len(remain) and remain[j]==remain[j-1]+1 and j-i<256:j+=1
        spans.append({'start':start,'bytes_hex':bytes(rom[p] for p in remain[i:j]).hex()});i=j
    obj={'schema':'ys-bank01-source-v1','pointer_directories':ptr,
         'ff_filler':{'start':FF_START,'count':FF_END-FF_START,'value':255},
         'unresolved_spans':spans,
         'note':'Unresolved spans may include code, data and mixed sprite/control sequences. Bytes are source-backed, semantics not certified.'}
    out=root/SOURCE;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(obj,indent=2)+'\n')
    data,_=new_data_capture_bytes(rom,old,code,structured)
    dig={'bank_sha256':sha(rom[START:END]),'new_code_sha256':sha(bytes(code[p] for p in sorted(code))),
         'new_data_sha256':sha(data),'previous_source_bytes':len(old),'new_code_bytes':len(code),
         'new_data_bytes':len(data),'unresolved_bytes':len(remain),'pointer_bytes':sum(b-a for a,b,_ in POINTERS),
         'padding_bytes':FF_END-FF_START,'unresolved_span_count':len(spans)}
    (root/DIGEST).write_text(json.dumps(dig,indent=2)+'\n')
    return dig

def new_data_capture_bytes(rom,old,code,structured):
    remaining=sorted(set(range(START,END))-set(old)-set(code))
    return bytes(rom[p] for p in remaining),remaining

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture',type=Path);p.add_argument('--verify-rom',type=Path)
    p.add_argument('--verify-mixed',action='store_true');p.add_argument('--out-bank',type=Path)
    args=p.parse_args()
    if args.capture:print('Captured bank1 source',capture(args.capture.read_bytes()))
    blob=full_bank()
    if args.verify_mixed:
        if assemble_bank01_mixed(mixed_source())!=blob:raise ValueError('Bank1 mixed source assembly differs')
    if args.verify_rom:
        ref=args.verify_rom.read_bytes()
        if len(ref)!=0x40000 or sha(ref)!=EXPECTED_SHA or blob!=ref[START:END]:
            raise ValueError('Bank1 source/original ROM differs')
    if args.out_bank:args.out_bank.write_bytes(blob)
    print('Source-only bank 1',len(blob),'bytes SHA256',sha(blob))
if __name__=='__main__':main()
