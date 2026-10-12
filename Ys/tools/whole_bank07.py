#!/usr/bin/env python3
"""Source-only physical bank 7 reconstruction. Inferred field names stay conservative.

No game ROM is needed to emit the complete 16-KiB bank or its mixed Z80/DB/DW
source; --capture is an explicit one-time extraction requiring the known ROM.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from build_sms_phase14 import ROOT, SOURCES, EXPECTED_SHA, offset
from z80_roundtrip_phase10 import assemble, encode
from source_tables_phase15 import load_verified_sources
from structured_data_phase16 import load_verified as load_records
from graphics_source_phase17 import load_verified as load_graphics
from z80_regions import decode

BANK=7
CPU_START=0x8000
SIZE=0x4000
TAIL=0xB53F
BASE=0x1C000
FILE=Path('wholebank07/source.json')
ASM=Path('src/wholebank07/late_code.asm')
DIGEST=Path('wholebank07/digests.json')
CODE_RANGES=((0xB53F,0xB596),(0xB9D6,0xBA0F),(0xBA1E,0xBA3B))
OPAQUE=(0xB596,0xB9D6)
PARAMS=(0xBA0F,0xBA1E)
MAP_DIRECTORY=(0xBA3B,0xBA67)
MAP_RECORDS=(0xBA67,0xBDBF)
INDEX=(0xBDBF,0xBDD4)
TEXT_DIRECTORY=(0xBDD4,0xBDFE)
TEXT=(0xBDFE,0xBFD3)
PADDING=(0xBFD3,0xC000)


def digest(bs):return hashlib.sha256(bs).hexdigest()

def word_bytes(vals):
    out=bytearray()
    for v in vals:
        if type(v)!=int or not 0x8000<=v<0xC000:raise ValueError(f'invalid slot-2 target {v}')
        out.extend((v&255,v>>8))
    return bytes(out)

def byte_list(vals):
    if not isinstance(vals,list) or any(type(v)!=int or not 0<=v<=255 for v in vals):
        raise ValueError('Expected list of unsigned bytes')
    return bytes(vals)

def known_bytes(root=ROOT):
    """Aggregate existing bank-7 independent source owners, NOT the game ROM."""
    owners={}
    def claim(part,where):
        for pc,value in part.items():
            if not CPU_START<=pc<0xC000 or type(value)!=int or not 0<=value<256:
                raise ValueError(f'invalid bank 7 source {where} at {pc:04X}')
            if pc in owners:raise ValueError(f'Bank 7 duplicate source owner at {pc:04X}: {where}')
            owners[pc]=value
    for source,bank in SOURCES:
        if bank==BANK:
            code,_=assemble((root/source).read_text())
            claim(code,source)
    claim(load_verified_sources(root)[BANK]['bytes'],'phase15 pointer directories')
    claim(load_records(root)[BANK]['bytes'],'phase16 secondary graphics records')
    claim(load_graphics(root)[BANK]['bytes'],'phase17 pixel records')
    if len(owners)!=13631 or set(owners)!=set(range(CPU_START,TAIL)):
        raise ValueError('Bank-7 existing sources must exactly cover CPU $8000-$B53E')
    return owners

def load_tail(root=ROOT):
    data=json.loads((root/FILE).read_text())
    if data.get('schema')!='ys-bank07-complete-tail-v1':raise ValueError('Unexpected tail schema')
    result={}
    def claim(start,chunk,who):
        for n,v in enumerate(chunk):
            pc=start+n
            if pc in result or not TAIL<=pc<0xC000:raise ValueError(f'Tail overlap/range error: {who} ${pc:04X}')
            result[pc]=v
    # Code is independently assembled from mnemonics; no pre-decoded opcode blobs.
    z80,_=assemble((root/ASM).read_text())
    wanted={i for start,stop in CODE_RANGES for i in range(start,stop)}
    if set(z80)!=wanted:raise ValueError('Tail Z80 source spans/ownership changed')
    for pc,value in z80.items():claim(pc,bytes([value]),'Z80 mnemonic')
    claim(*OPAQUE[:1],bytes.fromhex(data['unresolved_visual_bytes_hex']),'unresolved bytes')
    claim(PARAMS[0],byte_list([x for triple in data['parameter_triples'] for x in triple]),'three-byte parameters')
    ptrs=data['map_pointers']
    if len(ptrs)!=22 or any(type(p)!=int for p in ptrs) or ptrs[0]!=MAP_RECORDS[0] or ptrs[-1]!=0xBDBA or any(a>=b for a,b in zip(ptrs,ptrs[1:])):
        raise ValueError('Invalid 22-entry map-object directory')
    claim(MAP_DIRECTORY[0],word_bytes(ptrs),'22 map pointers')
    groups=data['map_groups']
    if len(groups)!=22:raise ValueError('Expected 22 map groups')
    for i,(p,g) in enumerate(zip(ptrs,groups)):
        if g['start']!=p:raise ValueError('Map group pointer mismatch')
        records=g['records']
        if not isinstance(records,list) or any(len(t)!=4 for t in records):raise ValueError('Expected four-byte map entries')
        raw=byte_list([v for t in records for v in t])
        term=g['terminator_zero']
        if type(term)!=bool:raise ValueError('Invalid map group terminator')
        chunk=raw+(b'\0' if term else b'')
        stop=ptrs[i+1] if i<21 else MAP_RECORDS[1]
        if p+len(chunk)!=stop:raise ValueError(f'Map group {i} boundary mismatch')
        claim(p,chunk,f'map record {i}')
    claim(INDEX[0],byte_list(data['text_selector_symbols']),'selector symbol table')
    titles=data['text_pointers']
    if len(titles)!=21 or any(type(p)!=int for p in titles) or titles[0]!=0xBE10 or titles[-1]!=0xBFC2 or any(a>=b for a,b in zip(titles,titles[1:])):
        raise ValueError('Invalid 21-item text directory')
    claim(TEXT_DIRECTORY[0],word_bytes(titles),'21 text pointers')
    prefix=byte_list(data['text_prefix'])
    if len(prefix)!=titles[0]-TEXT[0]:raise ValueError('Text prefix boundary mismatch')
    claim(TEXT[0],prefix,'text prefix')
    blocks=data['text_blocks']
    if len(blocks)!=len(titles):raise ValueError('Text block count mismatch')
    for i,(p,block) in enumerate(zip(titles,blocks)):
        stop=titles[i+1] if i+1<len(titles) else TEXT[1]
        raw=byte_list(block)
        if len(raw)!=stop-p:raise ValueError(f'Text pointer range mismatch: {i}')
        claim(p,raw,f'text block {i}')
    if data['padding_fill']!=255 or data['padding_length']!=PADDING[1]-PADDING[0]:
        raise ValueError('Unexpected bank-end filler')
    claim(PADDING[0],bytes([255])*data['padding_length'],'bank-end filler')
    if len(result)!=0xC000-TAIL or set(result)!=set(range(TAIL,0xC000)):
        raise ValueError('Incomplete late bank-7 source')
    wanted_digest=json.loads((root/DIGEST).read_text())
    raw=bytes(result[pc] for pc in range(TAIL,0xC000))
    if digest(raw)!=wanted_digest['tail_sha256'] or wanted_digest['tail_size']!=len(raw):
        raise ValueError('Tail source changed without reviewed digest')
    return result

def full_bank(root=ROOT):
    early=known_bytes(root)
    tail=load_tail(root)
    if set(early)&set(tail):raise ValueError('Overlapping bank-7 owners')
    combined=early|tail
    if len(combined)!=SIZE or set(combined)!=set(range(CPU_START,0xC000)):
        raise ValueError('Bank-7 source has a gap')
    raw=bytes(combined[pc] for pc in range(CPU_START,0xC000))
    expected=json.loads((root/DIGEST).read_text())['bank7_sha256']
    if digest(raw)!=expected:raise ValueError('Entire bank-7 source digest drift')
    return raw

def get_code_instructions(root=ROOT):
    result={}
    for path,bank in SOURCES:
        if bank==BANK: files=[root/path]
        else:continue
        for file in files:
            pc=None
            for row in file.read_text().splitlines():
                s=row.split(';',1)[0].strip()
                if not s or s.endswith(':'):continue
                if s.lower().startswith('org '):pc=int(s.split('$',1)[1],16);continue
                blob=encode(s,pc)
                if pc in result:raise ValueError('Duplicate Z80 instruction')
                result[pc]=(s,len(blob));pc+=len(blob)
    for file in [root/ASM]:
        pc=None
        for row in file.read_text().splitlines():
            s=row.split(';',1)[0].strip()
            if not s or s.endswith(':'):continue
            if s.lower().startswith('org '):pc=int(s.split('$',1)[1],16);continue
            blob=encode(s,pc)
            if pc in result:raise ValueError('Duplicate Z80 instruction')
            result[pc]=(s,len(blob));pc+=len(blob)
    return result

def mixed_source(root=ROOT):
    raw=full_bank(root)
    instructions=get_code_instructions(root)
    lines=['; Ys SMS physical bank 7. Standalone source-only 16-KiB reconstruction.',
           '; Code uses Z80 mnemonics; typed data sources are in wholebank07/source.json.',
           '; Unresolved art bytes are consciously preserved, not decoded.','org $8000']
    labels={0x8000:'GraphicsDispatchDirectory',0x8100:'SecondaryRecordDirectory',
            0x8180:'UnrolledGraphicsUploader',0x86C1:'GridGraphicsEngine',
            0x8877:'PixelRecords',0xAFBF:'SecondaryGraphicsRecords',
            0xB53F:'MapInitialization',0xB596:'UnresolvedVisualData',
            0xB9D6:'StateCycleHandler',0xBA0F:'StateCycleTriples',
            0xBA1E:'StateCounters',0xBA3B:'MapObjectDirectory',
            0xBA67:'MapObjectRecords',0xBDBF:'TextSelectorSymbols',
            0xBDD4:'TextPointerDirectory',0xBDFE:'TextPrefix',
            0xBFD3:'BankPadding'}
    pc=0x8000
    data_ends={0x8000:0x8100,0x8100:0x8180,0x8877:0xAFBF,0xAFBF:0xB53F,
               0xB596:0xB9D6,0xBA0F:0xBA1E,0xBA3B:0xBA67,
               0xBA67:0xBDBF,0xBDBF:0xBDD4,0xBDD4:0xBDFE,
               0xBDFE:0xBFD3,0xBFD3:0xC000}
    while pc<0xC000:
        if pc in labels:lines.append(labels[pc]+':')
        if pc in instructions:
            mnemonic,length=instructions[pc]
            assert raw[pc-0x8000:pc-0x8000+length]==encode(mnemonic,pc)
            lines.append('    '+mnemonic)
            pc+=length
            continue
        # Explicit DW only in pointer table regions; other data DB byte-wise.
        if 0x8000<=pc<0x8180 or 0xBA3B<=pc<0xBA67 or 0xBDD4<=pc<0xBDFE:
            limit=0x8100 if pc<0x8100 else 0x8180 if pc<0x8180 else 0xBA67 if pc<0xBA67 else 0xBDFE
            n=min(8,(limit-pc)//2)
            vals=[int.from_bytes(raw[p-0x8000:p-0x8000+2],'little') for p in range(pc,pc+n*2,2)]
            lines.append('    dw '+', '.join(f'${v:04X}' for v in vals))
            pc+=2*n
            continue
        next_label=min((i for i in labels if i>pc),default=0xC000)
        next_instruction=min((i for i in instructions if i>pc),default=0xC000)
        next_bound=min((v for k,v in data_ends.items() if k<=pc<v),default=0xC000)
        step=min(16,next_label-pc,next_instruction-pc,next_bound-pc)
        if step<=0:raise ValueError(f'Unexpected source boundary ${pc:04X}')
        lines.append('    db '+', '.join(f'${b:02X}' for b in raw[pc-0x8000:pc-0x8000+step]))
        pc+=step
    return '\n'.join(lines)+'\n'

def assemble_mixed(source):
    """Check complete printable mixed source using IN-PROJECT assembler (not WLA)."""
    result={};pc=None
    for line in source.splitlines():
        s=line.split(';',1)[0].strip()
        if not s or s.endswith(':'):continue
        if s.lower().startswith('org '):pc=int(s.split('$',1)[1],16);continue
        m=re.fullmatch(r'(db|dw)\s+(.+)',s,re.I)
        if m:
            values=[int(v.strip()[1:],16) for v in m[2].split(',')]
            if m[1].lower()=='db':
                if any(v>255 for v in values):raise ValueError('DB out of range')
                blob=bytes(values)
            else:
                if any(v>65535 for v in values):raise ValueError('DW out of range')
                blob=b''.join(v.to_bytes(2,'little') for v in values)
        else:blob=encode(s,pc)
        for byte in blob:
            if pc in result:raise ValueError(f'Mixed ASM source overlap at {pc:04X}')
            result[pc]=byte;pc+=1
    if set(result)!=set(range(0x8000,0xC000)):
        raise ValueError('Mixed source is not a full 16-KiB bank')
    return bytes(result[pc] for pc in range(0x8000,0xC000))

def capture(rom,root=ROOT):
    if digest(rom)!=EXPECTED_SHA or len(rom)!=0x40000:raise ValueError('Wrong ROM for extraction')
    def part(start,stop):return rom[BASE+start-0x8000:BASE+stop-0x8000]
    if len(known_bytes(root))!=13631:raise ValueError('Invalid Phase21 bank source')
    lines=[]
    for start,stop in CODE_RANGES:
        pc=start
        lines.append(f'org ${start:04X}')
        while pc<stop:
            nxt,txt=decode(rom,BASE+pc-0x8000,-0x14000)
            cp=nxt-BASE+0x8000
            if cp>stop:raise ValueError('Z80 decoder crosses code range')
            if encode(txt,pc)!=part(pc,cp):raise ValueError(f'Decoder/encoder disagrees at {pc:04X}')
            lines.append('    '+txt+f' ; ${pc:04X}')
            pc=cp
    (root/ASM).write_text('\n'.join(lines)+'\n')
    ptrs=[int.from_bytes(part(0xBA3B+i*2,0xBA3D+i*2),'little') for i in range(22)]
    groups=[]
    for i,p in enumerate(ptrs):
        stop=ptrs[i+1] if i<21 else MAP_RECORDS[1]
        raw=part(p,stop)
        terminal=(len(raw)%4)==1
        if len(raw)%4 not in (0,1) or (terminal and raw[-1]!=0):raise ValueError('Map record layout inconsistent')
        vals=raw[:-1] if terminal else raw
        groups.append({'start':p,'records':[list(vals[i:i+4]) for i in range(0,len(vals),4)],
                       'terminator_zero':terminal})
    titles=[int.from_bytes(part(0xBDD4+i*2,0xBDD6+i*2),'little') for i in range(21)]
    data={
      'schema':'ys-bank07-complete-tail-v1',
      'provenance':'ROM-dependent capture performed once; normal output uses source only',
      'unresolved_visual_bytes_hex':part(*OPAQUE).hex(),
      'parameter_triples':[list(part(0xBA0F+i*3,0xBA12+i*3)) for i in range(5)],
      'map_pointers':ptrs,
      'map_groups':groups,
      'text_selector_symbols':list(part(*INDEX)),
      'text_pointers':titles,
      'text_prefix':list(part(TEXT[0],titles[0])),
      'text_blocks':[list(part(p,(titles[i+1] if i+1<len(titles) else TEXT[1]))) for i,p in enumerate(titles)],
      'padding_fill':255,'padding_length':PADDING[1]-PADDING[0]
    }
    (root/FILE).write_text(json.dumps(data,indent=2)+'\n')
    (root/DIGEST).write_text(json.dumps({'bank7_sha256':digest(part(0x8000,0xC000)),
                                    'tail_sha256':digest(part(TAIL,0xC000)),
                                    'tail_size':0xC000-TAIL},indent=2)+'\n')
    return data

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture',type=Path,help='one-time review extraction from user-owned ROM')
    p.add_argument('--out-bank',type=Path,help='write source-only 16KiB bank (outside repo)')
    p.add_argument('--out-asm',type=Path,help='write full mixed Z80/DB/DW source')
    p.add_argument('--verify-rom',type=Path)
    p.add_argument('--verify-mixed',action='store_true')
    a=p.parse_args()
    if a.capture:capture(a.capture.read_bytes())
    bank=full_bank()
    if a.verify_rom:
        rom=a.verify_rom.read_bytes()
        if digest(rom)!=EXPECTED_SHA or rom[BASE:BASE+SIZE]!=bank:
            raise ValueError('Source-only physical bank 7 disagrees with original ROM')
    if a.verify_mixed or a.out_asm:
        asm=mixed_source()
        if assemble_mixed(asm)!=bank:raise ValueError('Mixed code/data source mismatch')
        if a.out_asm:a.out_asm.write_text(asm)
    if a.out_bank:a.out_bank.write_bytes(bank)
    print(f'PASS: complete bank 7: {len(bank)} ROM-independent bytes SHA256={digest(bank)}; +2753 beyond Phase21')

if __name__=='__main__':main()
