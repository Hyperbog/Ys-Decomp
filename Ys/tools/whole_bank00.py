#!/usr/bin/env python3
"""Ys fixed bank 0: independent source-only build with ROM-anchored candidate code.

Only --capture requires the user-owned ROM; normal builds use committed assembly,
field-records and explicit unresolved spans. Byte closure is not semantic closure.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from build_sms_phase14 import ROOT, SOURCES, EXPECTED_SHA
from source_tables_phase15 import load_verified_sources
from structured_data_phase16 import load_verified as load16
from phase21_semantic_sources import load_verified as load21
from z80_roundtrip_phase10 import assemble, encode
from z80_regions import decode

BASE=0; SIZE=0x4000
SOURCE=Path('wholebank00/source.json')
ASM=Path('src/wholebank00/new_code.asm')
DIGEST=Path('wholebank00/digests.json')
# Manually delimited instruction spans after ROM and fixed-reference inspection.
# They are byte-exact Z80 but are not all gameplay-executed/semantically analyzed.
CODE_SPANS=(
    (0x0288,0x0389),(0x06E8,0x0749),(0x07D5,0x0801),
    (0x0B4E,0x0B56),(0x0B5A,0x0B64),(0x0BB7,0x0BC5),(0x0C3E,0x0C4A),
    (0x0FFD,0x1988),(0x1ED4,0x1F9A),(0x1F9A,0x1FD4),(0x2673,0x267B),
    (0x28CE,0x2A64),(0x2B7D,0x2BCF),(0x2C05,0x2C24),
    (0x2DB6,0x2E2A),(0x2E2A,0x2E3D),(0x2E3D,0x2F2A),(0x3032,0x3194),
    (0x31AE,0x329C),(0x32BB,0x333B),(0x3355,0x3415),
    (0x3637,0x3652),(0x3713,0x3725),(0x3741,0x3744),
    (0x37E2,0x3C88),(0x3C88,0x3CB3),(0x3DCC,0x3DFB),(0x3E4D,0x3E77),
    (0x3E8E,0x3E91),(0x3E9B,0x3EE7),(0x3EF6,0x3EFC),(0x3F06,0x3F0C),
    (0x3F70,0x3F88),(0x3FA0,0x3FC3),(0x3FD1,0x3FFF))
# Pointer tables with verified contiguous word boundaries. No assumptions about
# mapper-controlled targets when the CPU word falls into $4000-$BFFF.
POINTER_TABLES={
    (0x01AC,0x01B4):'bootstrap_dispatch_4',
    (0x01EB,0x01FD):'bootstrap_routines_9',
    (0x0FF7,0x0FFD):'object_setup_dispatch_3',
    (0x1988,0x19CC):'actor_handler_dispatch_34',
    (0x1EA8,0x1ED4):'graphics_upload_dispatch_22',
    (0x2533,0x2585):'nine_byte_resource_directory_41',
    (0x367A,0x3682):'state_handler_dispatch_4',
    (0x369D,0x36A3):'state_handler_dispatch_3a',
    (0x36E3,0x36E9):'state_handler_dispatch_3b',
    (0x3774,0x37C4):'scenario_dispatch_40',
    (0x2BCF,0x2BF1):'sprite_ram_buffer_pointers_17',
    (0x3F88,0x3FA0):'endgame_local_dispatch_12',
    (0x3FC3,0x3FD1):'endgame_branch_dispatch_7',
}
KNOWN_POINTER_TARGETS={
 'nine_byte_resource_directory_41': (0x2585,0x2674),
 'actor_handler_dispatch_34': (0x0FFD,0x1988),
 'graphics_upload_dispatch_22':(0x1ED4,0x1F9A),
}

def sha(b):return hashlib.sha256(b).hexdigest()

def existing(root=ROOT):
    found={}
    def claim(address,value,owner):
        if not 0<=address<SIZE or address in found or type(value)!=int or not 0<=value<=255:
            raise ValueError(f'Old bank0 owner conflict at {address:04X}: {owner}')
        found[address]=value
    for src,bank in SOURCES:
        if bank==0:
            code,_=assemble((root/src).read_text())
            for pc,value in code.items():claim(pc,value,src)
    for bank,v in load_verified_sources(root).items():
        if bank==0:
            for pc,value in v['bytes'].items():claim(pc,value,'phase15 tables')
    for bank,v in load16(root).items():
        if bank==0:
            for pc,value in v['bytes'].items():claim(pc,value,'phase16 records')
    for (bank,pc),value in load21(root)[0].items():
        if bank==0:claim(pc,value,'phase21 records')
    if len(found)!=8242:raise ValueError('Original bank0 source ownership changed')
    return found

def parsed_new_instructions(root=ROOT):
    source=(root/ASM).read_text()
    result,labels=assemble(source)
    wanted={pc for start,stop in CODE_SPANS for pc in range(start,stop)}
    if set(result)!=wanted:raise ValueError('New Z80 regions have gaps/overlaps')
    # Strictly ensure only instructions in declared spans (not a DB byte shell).
    instructions={};pc=None
    for line in source.splitlines():
        stripped=line.split(';',1)[0].strip()
        if not stripped or stripped.endswith(':'):continue
        if stripped.lower().startswith('org '):
            pc=int(stripped.split('$',1)[1],16)
            if pc not in {a for a,_ in CODE_SPANS}:raise ValueError('Unexpected Z80 ORG')
            continue
        if pc is None or re.match(r'^(db|dw|ds|incbin)\b',stripped,re.I):
            raise ValueError('New Z80 listing must be real mnemonics')
        raw=encode(stripped,pc)
        if pc in instructions or any(i not in wanted for i in range(pc,pc+len(raw))):
            raise ValueError('Z80 instruction ownership invalid')
        instructions[pc]=(stripped,len(raw))
        pc+=len(raw)
    return result,instructions

def data_chunks(root=ROOT):
    obj=json.loads((root/SOURCE).read_text())
    if obj.get('schema')!='ys-whole-bank00-v1':raise ValueError('Bank0 source schema mismatch')
    chunks={};details={};cursor=0
    for entry in obj['segments']:
        start=entry['start'];end=entry['end'];kind=entry['kind'];name=entry['name']
        if type(start)!=int or type(end)!=int or not 0<=start<end<=SIZE or start in chunks:
            raise ValueError('Bad bank0 data segment bounds')
        if kind=='fill_ff':
            if entry['value']!=255 or entry['count']!=end-start:raise ValueError('Padding boundaries drift')
            b=b'\xff'*(end-start)
        elif kind=='ascii':
            b=entry['text'].encode('ascii')
            if len(b)!=end-start:raise ValueError('Title length changed')
        elif kind=='pointer_words':
            words=entry['words']
            if len(words)*2!=end-start or any(type(w)!=int or not 0<=w<=0xFFFF for w in words):
                raise ValueError('Pointer count/value invalid')
            if (start,end) not in POINTER_TABLES or name!=POINTER_TABLES[(start,end)]:
                raise ValueError('Undocumented pointer directory')
            if name in KNOWN_POINTER_TARGETS:
                low,high=KNOWN_POINTER_TARGETS[name]
                if any(not low<=w<high for w in words):raise ValueError('Pointer directory target out of inferred range')
            b=b''.join(w.to_bytes(2,'little') for w in words)
        elif kind=='unresolved':
            b=bytes.fromhex(entry['hex'])
        else:raise ValueError('Unsupported bank0 source field type: '+kind)
        if len(b)!=end-start:raise ValueError('Bank0 segment length changed')
        for i,value in enumerate(b):
            pc=start+i
            if pc in chunks:raise ValueError('Data overlap')
            chunks[pc]=value
        details[start]=(end,kind,name)
    return chunks,details

def full_bank(root=ROOT):
    prior=existing(root); code,_=parsed_new_instructions(root);data,details=data_chunks(root)
    if set(prior)&set(code) or set(prior)&set(data) or set(code)&set(data):
        raise ValueError('Bank0 ownership collision')
    combined=prior|code|data
    if len(combined)!=SIZE or set(combined)!=set(range(SIZE)):
        raise ValueError(f'Bank0 is not complete: {len(combined)} owned bytes')
    bank=bytes(combined[i] for i in range(SIZE))
    hashes=json.loads((root/DIGEST).read_text())
    if sha(bank)!=hashes['bank_sha256'] or sha(bytes(code[i] for i in sorted(code)))!=hashes['new_code_sha256'] or sha(bytes(data[i] for i in sorted(data)))!=hashes['new_data_sha256']:
        raise ValueError('Bank0 source fingerprint mismatch')
    if len(code)!=hashes['new_code_bytes'] or len(data)!=hashes['new_data_bytes']:
        raise ValueError('Bank0 source accounting changed')
    return bank

def original_instructions(root=ROOT):
    out={}
    for src,bank in SOURCES:
        if bank!=0:continue
        pc=None
        for line in (root/src).read_text().splitlines():
            s=line.split(';',1)[0].strip()
            if not s or s.endswith(':'):continue
            if s.lower().startswith('org '):pc=int(s.split('$',1)[1],16);continue
            raw=encode(s,pc)
            if pc in out:raise ValueError('Existing Z80 instruction collision')
            out[pc]=(s,len(raw));pc+=len(raw)
    return out

def mixed_source(root=ROOT):
    raw=full_bank(root)
    instructions=original_instructions(root)|parsed_new_instructions(root)[1]
    _,types=data_chunks(root)
    lines=['; Ys fixed bank 0: source-only 16384-byte reconstruction.',
           '; Full byte parity does not imply resolved graphics/data semantics.',
           'org $0000']
    pc=0
    while pc<SIZE:
        if pc in types:
            end,kind,name=types[pc]
            lines.append(f'; {name}: {kind}, ${pc:04X}-${end-1:04X}')
        if pc in instructions:
            s,length=instructions[pc]
            if raw[pc:pc+length]!=encode(s,pc):raise ValueError('Mixed instruction drift')
            lines.append('    '+s);pc+=length
            continue
        entry=next(((start,end,kind) for start,(end,kind,name) in types.items() if start<=pc<end),None)
        next_code=min((x for x in instructions if x>pc),default=SIZE)
        if entry and entry[2]=='pointer_words':
            step=min(8,(entry[1]-pc)//2)
            if step:
                vals=[int.from_bytes(raw[p:p+2],'little') for p in range(pc,pc+2*step,2)]
                lines.append('    dw '+', '.join(f'${w:04X}' for w in vals));pc+=2*step;continue
        next_data=min((x for x in types if x>pc),default=SIZE)
        next_end=entry[1] if entry else SIZE
        n=min(16,next_code-pc,next_data-pc,next_end-pc)
        if n<=0:raise ValueError(f'Unexpected bank0 mixed source boundary ${pc:04X}')
        lines.append('    db '+', '.join(f'${v:02X}' for v in raw[pc:pc+n]));pc+=n
    return '\n'.join(lines)+'\n'

def assemble_mixed_fixed(source):
    """Independent parser for a complete bank0 mixed DB/DW/Z80 listing."""
    out={};pc=None
    for line in source.splitlines():
        s=line.split(';',1)[0].strip()
        if not s or s.endswith(':'):continue
        if s.lower().startswith('org '):pc=int(s.split('$',1)[1],16);continue
        m=re.fullmatch(r'(db|dw)\s+(.+)',s,re.I)
        if m:
            values=[int(x.strip()[1:],16) for x in m[2].split(',')]
            if m[1].lower()=='db':
                if any(not 0<=v<=255 for v in values):raise ValueError('DB bounds')
                blob=bytes(values)
            else:
                if any(not 0<=v<=65535 for v in values):raise ValueError('DW bounds')
                blob=b''.join(v.to_bytes(2,'little') for v in values)
        else:blob=encode(s,pc)
        for value in blob:
            if pc in out:raise ValueError(f'Mixed bank0 ownership overlap ${pc:04X}')
            out[pc]=value;pc+=1
    if set(out)!=set(range(SIZE)):raise ValueError('Mixed bank0 source missing bytes')
    return bytes(out[i] for i in range(SIZE))


def capture(rom,root=ROOT):
    if len(rom)!=0x40000 or sha(rom)!=EXPECTED_SHA:raise ValueError('Wrong Ys ROM for capture')
    prior=existing(root)
    code_lines=['; Byte-verified Z80 instructions; semantics partly uninvestigated.']
    code={}
    for start,end in CODE_SPANS:
        code_lines.append(f'org ${start:04X}')
        pc=start
        while pc<end:
            stop,s=decode(rom,pc,0)
            if stop>end or rom[pc:stop]!=encode(s,pc):raise ValueError(f'Unroundtrippable instruction at ${pc:04X}')
            code_lines.append('    '+s)
            for i in range(pc,stop):
                if i in code or i in prior:raise ValueError('Capture overlaps previous source')
                code[i]=rom[i]
            pc=stop
    (root/ASM).parent.mkdir(parents=True,exist_ok=True)
    (root/ASM).write_text('\n'.join(code_lines)+'\n')
    data={i for i in range(SIZE) if i not in prior and i not in code}
    ranges=[];start=None
    for pc in range(SIZE+1):
        allowed=pc in data
        if allowed and start is None:start=pc
        if not allowed and start is not None:ranges.append((start,pc));start=None
    entries=[]
    for start,end in ranges:
        b=rom[start:end]
        kind='unresolved';name=f'unresolved_{start:04X}';extras={'hex':b.hex()}
        if all(v==255 for v in b):
            kind='fill_ff';name=f'padding_{start:04X}';extras={'value':255,'count':len(b)}
        elif (start,end) in POINTER_TABLES:
            kind='pointer_words';name=POINTER_TABLES[(start,end)]
            extras={'words':[int.from_bytes(b[i:i+2],'little') for i in range(0,len(b),2)]}
        elif (start,end)==(0x0782,0x079A):
            kind='ascii';name='cartridge_title';extras={'text':b.decode('ascii')}
        entries.append({'start':start,'end':end,'kind':kind,'name':name,**extras})
    (root/SOURCE).parent.mkdir(parents=True,exist_ok=True)
    (root/SOURCE).write_text(json.dumps({'schema':'ys-whole-bank00-v1','segments':entries,
        'note':'Unresolved byte data is reversible but not claimed decoded; Z80 ranges inferred and independently round-tripped.'},indent=2)+'\n')
    data_bytes=bytes(rom[i] for i in sorted(data))
    (root/DIGEST).write_text(json.dumps({'bank_sha256':sha(rom[:SIZE]),
          'new_code_sha256':sha(bytes(code[i] for i in sorted(code))),
          'new_data_sha256':sha(data_bytes),
          'new_code_bytes':len(code),'new_data_bytes':len(data),
          'new_structured_bytes':sum(e['end']-e['start'] for e in entries if e['kind']!='unresolved'),
          'unresolved_bytes':sum(e['end']-e['start'] for e in entries if e['kind']=='unresolved')},indent=2)+'\n')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture',type=Path)
    p.add_argument('--verify-rom',type=Path)
    p.add_argument('--verify-mixed',action='store_true')
    p.add_argument('--out-asm',type=Path)
    a=p.parse_args()
    if a.capture:capture(a.capture.read_bytes())
    blob=full_bank()
    if a.verify_rom:
        rom=a.verify_rom.read_bytes()
        if len(rom)!=0x40000 or sha(rom)!=EXPECTED_SHA or blob!=rom[:SIZE]:raise ValueError('Bank0 ROM mismatch')
    if a.verify_mixed or a.out_asm:
        asm=mixed_source()
        if assemble_mixed_fixed(asm)!=blob:raise ValueError('Bank0 mixed-source independent assembly mismatch')
        if a.out_asm:a.out_asm.write_text(asm)
    print('PASS: source-only fixed bank0',len(blob),'bytes SHA256',sha(blob))

if __name__=='__main__':main()
