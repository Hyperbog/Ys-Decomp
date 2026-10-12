#!/usr/bin/env python3
"""Source-only closure of SMS bank 8 (script/lookup) and 10 (dialogue/number output).

Normal build reads project sources ONLY. --capture requires fingerprinted owner ROM.
Preserved opaque resources must never be reported as decoded game scripting.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from build_sms_phase14 import ROOT, SOURCES, EXPECTED_SHA
from z80_roundtrip_phase10 import assemble, encode
from z80_regions import decode

CPU=0x8000; END=0xC000; SIZE=0x4000
KNOWN={8:(0xBEE8,0xBF72),10:(0xBEF7,0xBF42)}
NEW_CODE=(0xBFB6,0xBFDC)
B8_SCRIPT=(0x8000,0xBEE8)
B8_LOOKUP=(0xBF72,0xBFB6)
B8_TRAILER=(0xBFDC,0xBFF1)
B10_MAIN=(0x8000,0xBE70)
B10_DIR=(0xBE70,0xBE86)
B10_WORDS=(0xBE86,0xBEF7)
B10_TRAILER=(0xBF42,0xBFFD)
PADS={8:(0xBFF1,0xC000),10:(0xBFFD,0xC000)}

def sha(x):return hashlib.sha256(x).hexdigest()
def path(bank):return Path(f'wholebank{bank:02}/source.json')
def digestpath(bank):return Path(f'wholebank{bank:02}/digests.json')
def asmpath(bank):return Path(f'src/wholebank{bank:02}/bank{bank:02}_complete.asm')

def existing(bank,root=ROOT):
    o={}
    for src,n in SOURCES:
        if n==bank:
            b,_=assemble((root/src).read_text())
            for pc,v in b.items():
                if pc in o:raise ValueError('Existing Z80 source overlap')
                o[pc]=v
    a,z=KNOWN[bank]
    if set(o)!=set(range(a,z)):raise ValueError(f'Bank{bank} previous ownership drift')
    return o

def new_code(root=ROOT):
    s=(root/'src/wholebank08/extra_code.asm').read_text()
    data,_=assemble(s)
    if set(data)!=set(range(*NEW_CODE)):raise ValueError('Bank8 additional code not complete')
    lines=instruction_index(s)
    if set(lines)==set() or sum(n for _,n in lines.values())!=NEW_CODE[1]-NEW_CODE[0]:
        raise ValueError('Bank8 additional source must be mnemonic instructions')
    return data

def instruction_index(s):
    out={};p=None
    for line in s.splitlines():
        x=line.split(';',1)[0].strip()
        if not x or x.endswith(':'):continue
        if x.lower().startswith('org '):p=int(x.split('$',1)[1],16);continue
        if p is None or re.match(r'^(db|dw|ds|incbin)\b',x,re.I):raise ValueError('Mnemonic source only')
        n=len(encode(x,p))
        if p in out:raise ValueError('Repeated instruction')
        out[p]=(x,n);p+=n
    return out

def opaque_chunks(entries,a,z,name):
    if type(entries)!=list or not entries:raise ValueError(name+' blocks missing')
    out=bytearray();last=a
    for obj in entries:
        if type(obj)!=dict or set(obj)!={'start','hex'} or type(obj['start'])!=int or obj['start']!=last:
            raise ValueError(name+' chunk non-contiguous or wrong schema')
        try:b=bytes.fromhex(obj['hex'])
        except ValueError:raise ValueError(name+' bad byte encoding')
        if not 1<=len(b)<=256:raise ValueError(name+' chunk invalid length')
        out.extend(b);last+=len(b)
    if last!=z:raise ValueError(name+' gap at end')
    return bytes(out)

def chunks_from_rom(bank,bounds,blob):
    a,z=bounds
    return [{'start':p,'hex':blob[p-CPU:min(p+256,z)-CPU].hex()} for p in range(a,z,256)]

def new_bytes(bank,root=ROOT):
    obj=json.loads((root/path(bank)).read_text())
    if obj.get('schema')!=f'ys-bank{bank:02}-source-v1':raise ValueError('Unsupported schema')
    regions=[]
    def add(a,data,kind):
        if any(not type(v)==int or not 0<=v<256 for v in data):raise ValueError('Bad '+kind+' values')
        regions.append((a,bytes(data),kind))
    if bank==8:
        add(B8_SCRIPT[0],opaque_chunks(obj['unresolved_script_region'],*B8_SCRIPT,'script'),'unresolved game-script/resource data')
        lookup=obj['lookup_tables']
        if type(lookup)!=dict or set(lookup)!={'offset_y_6','offset_x_6','single_byte','records_11x5'}:
            raise ValueError('Bank8 lookup format')
        if any(type(lookup[k])!=list or len(lookup[k])!=6 for k in ('offset_y_6','offset_x_6')):
            raise ValueError('Bank8 6-byte offset table length')
        if type(lookup['single_byte'])!=int or not 0<=lookup['single_byte']<=255:
            raise ValueError('Bank8 singleton field')
        records=lookup['records_11x5']
        if type(records)!=list or len(records)!=11 or any(type(row)!=list or len(row)!=5 for row in records):
            raise ValueError('Bank8 11x5 descriptor array invalid')
        add(B8_LOOKUP[0],lookup['offset_y_6']+lookup['offset_x_6']+[lookup['single_byte']]+[x for row in records for x in row], 'bank8 lookup offsets and 11x5 indexed records')
        add(B8_TRAILER[0],obj['undecoded_trailing_bytes'],'unresolved bank8 trailer')
    elif bank==10:
        add(B10_MAIN[0],opaque_chunks(obj['unresolved_resource_region'],*B10_MAIN,'resource'),'unresolved bank10 resource body')
        strings=obj['text_directory']
        if type(strings)!=dict or set(strings)!={'pointers','terminated_records'}:
            raise ValueError('Bank10 terminated string directory schema')
        ptrs=strings['pointers'];records=strings['terminated_records']
        if type(ptrs)!=list or len(ptrs)!=11 or type(records)!=list or len(records)!=9:
            raise ValueError('Bank10 pointer or record count')
        starts=[];p=B10_WORDS[0];payload=bytearray()
        for rec in records:
            if type(rec)!=dict or set(rec)!={'start','encoded'} or rec['start']!=p:raise ValueError('Bank10 string record start')
            encoded=rec['encoded']
            if type(encoded)!=list or any(type(v)!=int or not 0<=v<255 for v in encoded):
                raise ValueError('Bank10 string tokens must not include terminator')
            starts.append(p);payload.extend(encoded);payload.append(255);p+=len(encoded)+1
        if p!=B10_WORDS[1] or ptrs!=starts+[starts[0],starts[-1]]:
            raise ValueError('Bank10 directory targets/aliases changed')
        add(B10_DIR[0],[x for w in ptrs for x in (w&255,w>>8)],'11 pointer words including two aliases')
        add(B10_WORDS[0],payload,'nine terminated encoded text strings')
        add(B10_TRAILER[0],opaque_chunks(obj['undecoded_trailing_region'],*B10_TRAILER,'trailer'), 'unresolved bank10 tail')
    else:raise ValueError('Supported banks only 8 and 10')
    a,z=PADS[bank]
    if obj.get('padding')!={'start':a,'count':z-a,'value':255}:raise ValueError('Bank padding drift')
    add(a,[255]*(z-a),'bank-end FF padding')
    result={};ledger=[]
    for start,data,kind in regions:
        if not CPU<=start<END or start+len(data)>END:raise ValueError('Data out of bank')
        for off,value in enumerate(data):
            p=start+off
            if p in result:raise ValueError('Source data overlap')
            result[p]=value
        ledger.append({'start':start,'end_exclusive':start+len(data),'kind':kind,'bytes':len(data)})
    old=existing(bank,root);new=new_code(root) if bank==8 else {}
    if (set(result)&set(old)) or (set(result)&set(new)) or (set(old)&set(new)) or set(result)|set(old)|set(new)!=set(range(CPU,END)):
        raise ValueError('Whole-bank ownership gap or conflict')
    refs=json.loads((root/digestpath(bank)).read_text())
    if sha(bytes(result[k] for k in sorted(result)))!=refs['new_data_sha256']:
        raise ValueError('New data checksum drift')
    return result,ledger

def full_bank(bank,root=ROOT):
    original=existing(bank,root);data,_=new_bytes(bank,root);extra=new_code(root) if bank==8 else {}
    a=original|extra|data
    image=bytes(a[i] for i in range(CPU,END))
    if len(image)!=SIZE or sha(image)!=json.loads((root/digestpath(bank)).read_text())['bank_sha256']:
        raise ValueError('Bank source checksum drift')
    return image

def mixed_source(bank,root=ROOT):
    image=full_bank(bank,root)
    ins={}
    for rel,n in SOURCES:
        if n==bank:
            ins.update(instruction_index((root/rel).read_text()))
    if bank==8:ins.update(instruction_index((root/'src/wholebank08/extra_code.asm').read_text()))
    labels={8:{0x8000:'UnresolvedBank8Script',0xBEE8:'InitializeSystemState',0xBF72:'IndexedOffsetTables',
                0xBF7F:'FiveByteRecords11',0xBFB6:'ReadStateLookup',0xBFDC:'UnresolvedBank8Trailer',0xBFF1:'Bank8Padding'},
            10:{0x8000:'UnresolvedBank10Resources',0xBE70:'TextDirectory11',0xBE86:'EncodedStringRecords9',
                0xBEF7:'DisplayDecimalNumber',0xBF42:'UnresolvedBank10Trailer',0xBFFD:'Bank10Padding'}}[bank]
    words=set(range(*B10_DIR,2)) if bank==10 else set()
    lines=[f'; Ys SMS physical bank {bank} — source-only binary closure, not complete semantic decompilation.',
           '; Opaque bytes are unresolved project-source arrays. Never claim game encoding decoded.', 'org $8000']
    p=CPU
    while p<END:
        if p in labels:lines.append(labels[p]+':')
        if p in ins:
            line,n=ins[p];lines.append('    '+line);p+=n;continue
        if p in words:
            word=int.from_bytes(image[p-CPU:p-CPU+2],'little');lines.append(f'    dw ${word:04X}');p+=2;continue
        bound=min([t for t in ins if t>p]+[t for t in labels if t>p]+[t for t in words if t>p]+[END])
        n=min(16,bound-p)
        if n<1:raise ValueError('Mixed source emission stuck')
        lines.append('    db '+', '.join(f'${v:02X}' for v in image[p-CPU:p-CPU+n]));p+=n
    return '\n'.join(lines)+'\n'

def assemble_mixed(source):
    vals={};p=None
    for line in source.splitlines():
        x=line.split(';',1)[0].strip()
        if not x or x.endswith(':'):continue
        if x.lower().startswith('org '):p=int(x.split('$',1)[1],16);continue
        m=re.fullmatch(r'(db|dw)\s+(.+)',x,re.I)
        if m:
            digits=[int(y.strip()[1:],16) for y in m[2].split(',')]
            if m[1].lower()=='db':
                if any(not 0<=v<256 for v in digits):raise ValueError('DB invalid')
                blob=bytes(digits)
            else:blob=b''.join(w.to_bytes(2,'little') for w in digits)
        else:blob=encode(x,p)
        for value in blob:
            if p in vals:raise ValueError('Mixed source overlaps')
            vals[p]=value;p+=1
    if set(vals)!=set(range(CPU,END)):raise ValueError('Mixed source bank coverage incomplete')
    return bytes(vals[p] for p in range(CPU,END))

def capture(rom,root=ROOT):
    if len(rom)!=0x40000 or sha(rom)!=EXPECTED_SHA:raise ValueError('Wrong fingerprint for capture')
    for bank in [8,10]:
        image=rom[bank*SIZE:(bank+1)*SIZE]
        for p,v in existing(bank,root).items():
            if image[p-CPU]!=v:raise ValueError('Existing bank source mismatch')
        if bank==8:
            s=['; Additional bank8 system lookup code anchored at $BFB6.', 'org $BFB6'];p=NEW_CODE[0]
            while p<NEW_CODE[1]:
                a,z=decode(rom,bank*SIZE+p-CPU,CPU-bank*SIZE)
                if a>bank*SIZE+NEW_CODE[1]-CPU:raise ValueError('Instruction crosses declared bound')
                line=encode(z,p)
                if line!=rom[bank*SIZE+p-CPU:a]:raise ValueError('Encoder disagrees with new Z80')
                s.append('    '+z);p+=len(line)
            (root/'src/wholebank08').mkdir(parents=True,exist_ok=True)
            (root/'src/wholebank08/extra_code.asm').write_text('\n'.join(s)+'\n')
            lookup=image[B8_LOOKUP[0]-CPU:B8_LOOKUP[1]-CPU]
            src={'schema':'ys-bank08-source-v1','unresolved_script_region':chunks_from_rom(bank,B8_SCRIPT,image),
                 'lookup_tables':{'offset_y_6':list(lookup[:6]),'offset_x_6':list(lookup[6:12]),
                                  'single_byte':lookup[12],'records_11x5':[list(lookup[i:i+5]) for i in range(13,68,5)]},
                 'undecoded_trailing_bytes':list(image[B8_TRAILER[0]-CPU:B8_TRAILER[1]-CPU]),
                 'padding':{'start':PADS[bank][0],'count':PADS[bank][1]-PADS[bank][0],'value':255}}
        else:
            ptrs=[int.from_bytes(image[p-CPU:p-CPU+2],'little') for p in range(*B10_DIR,2)]
            records=[];p=B10_WORDS[0]
            while p<B10_WORDS[1]:
                term=image.index(255,p-CPU,B10_WORDS[1]-CPU)+CPU
                records.append({'start':p,'encoded':list(image[p-CPU:term-CPU])});p=term+1
            src={'schema':'ys-bank10-source-v1','unresolved_resource_region':chunks_from_rom(bank,B10_MAIN,image),
                 'text_directory':{'pointers':ptrs,'terminated_records':records},
                 'undecoded_trailing_region':chunks_from_rom(bank,B10_TRAILER,image),
                 'padding':{'start':PADS[bank][0],'count':PADS[bank][1]-PADS[bank][0],'value':255}}
        (root/path(bank)).parent.mkdir(parents=True,exist_ok=True)
        (root/path(bank)).write_text(json.dumps(src,separators=(',',':'))+'\n')
        # New data is all bytes NOT part of earlier canonical or newly coded instructions.
        known=set(existing(bank,root));additional=set(new_code(root)) if bank==8 else set()
        data=bytes(image[p-CPU] for p in range(CPU,END) if p not in known|additional)
        (root/digestpath(bank)).write_text(json.dumps({'bank_sha256':sha(image),'new_data_sha256':sha(data),
             'original_code_bytes':len(known),'additional_code_bytes':len(additional),
             'new_data_bytes':len(data)},indent=2)+'\n')
        if full_bank(bank,root)!=image:raise ValueError('Bank capture did not recompile exactly')
        (root/asmpath(bank)).parent.mkdir(parents=True,exist_ok=True)
        (root/asmpath(bank)).write_text(mixed_source(bank,root))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture',type=Path);p.add_argument('--verify-rom',type=Path)
    p.add_argument('--verify-mixed',action='store_true')
    a=p.parse_args()
    if a.capture:capture(a.capture.read_bytes())
    for n in (8,10):
        b=full_bank(n)
        if a.verify_mixed:
            s=mixed_source(n)
            if s!=(ROOT/asmpath(n)).read_text() or assemble_mixed(s)!=b:
                raise ValueError(f'Bank{n} canonical mixed assembly mismatch')
        if a.verify_rom:
            rom=a.verify_rom.read_bytes()
            if len(rom)!=0x40000 or sha(rom)!=EXPECTED_SHA or rom[n*SIZE:(n+1)*SIZE]!=b:
                raise ValueError(f'Bank{n} original ROM mismatch')
        print(f'Bank{n:02} source-only: 16384 bytes; sha256 {sha(b)}')
if __name__=='__main__':main()
