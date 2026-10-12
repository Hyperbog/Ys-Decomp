#!/usr/bin/env python3
"""Physical bank 6: ROM-independent 16-KiB source rebuild.

Explicitly separate existing sprite engine, graphics byte lanes, bounded
count-prefixed triplet layouts, tile indices and fill. Capturing a dataset
requires the owner-provided ROM. Normal source build NEVER opens a ROM.
"""
import argparse
import hashlib
import json
from pathlib import Path
from build_sms_phase14 import ROOT, SOURCES, EXPECTED_SHA
from z80_roundtrip_phase10 import assemble
from source_tables_phase15 import load_verified_sources
from structured_data_phase16 import load_verified
from whole_bank07 import assemble_mixed

BANK=6
CPU=0x8000
SIZE=0x4000
KNOWN_END=0x9C18
PIXEL=(0x9C18,0xB908)
ID_PRE=(0xB908,0xB9C8)
DIR_A=(0xB9C8,0xB9D0)
LAYOUT_A=((0xB9D0,0xB9F8),(0xB9F8,0xBA23),(0xBA23,0xBA4B))
ID_MID=(0xBA4B,0xBA5B)
DIR_B=(0xBA5B,0xBA63)
LAYOUT_B=((0xBA63,0xBA7C),(0xBA7C,0xBA9B),(0xBA9B,0xBABA),(0xBABA,0xBAD9))
ID_TAIL=(0xBAD9,0xBFF9)
FILL=(0xBFF9,0xC000)
DATA=Path('wholebank06/source.json')
DIGEST=Path('wholebank06/digests.json')
ASM=Path('src/wholebank06/bank06_complete.asm')

def sha(data):return hashlib.sha256(data).hexdigest()

def known_bytes(root=ROOT):
    rows={}
    def put(pc,v,origin):
        if pc in rows or not CPU<=pc<KNOWN_END or type(v)!=int or not 0<=v<=255:
            raise ValueError(f'Prior bank6 ownership conflict {origin} ${pc:04X}')
        rows[pc]=v
    for source,bank in SOURCES:
        if bank==BANK:
            decoded,_=assemble((root/source).read_text())
            for pc,v in decoded.items():put(pc,v,source)
    for caller in (load_verified_sources,load_verified):
        for pc,v in caller(root)[BANK]['bytes'].items():put(pc,v,caller.__name__)
    if len(rows)!=7192 or set(rows)!=set(range(CPU,KNOWN_END)):
        raise ValueError('Earlier verified bank6 source ownership changed')
    return rows

def expand_lanes(rows,start,end,label):
    if not isinstance(rows,list) or len(rows)*8!=end-start:
        raise ValueError(f'{label}: expected exact eight-byte lanes')
    output=bytearray()
    for lane in rows:
        if not isinstance(lane,list) or len(lane)!=8 or any(type(v)!=int or not 0<=v<256 for v in lane):
            raise ValueError(f'{label}: invalid lane')
        output.extend(lane)
    return bytes(output)

def parse_layouts(records,bounds,label):
    if not isinstance(records,list) or len(records)!=len(bounds):raise ValueError(label+' record count')
    output=[]
    for item,(start,end) in zip(records,bounds):
        if type(item)!=dict or set(item)!={'start','triplets'} or item['start']!=start:
            raise ValueError(label+' record start')
        triples=item['triplets']
        if not isinstance(triples,list) or len(triples)>255 or 1+3*len(triples)!=end-start:
            raise ValueError(label+' count and triplet span')
        flat=bytearray([len(triples)])
        for rec in triples:
            if not isinstance(rec,list) or len(rec)!=3 or any(type(x)!=int or not 0<=x<256 for x in rec):
                raise ValueError(label+' invalid sprite triplet')
            flat.extend(rec)
        output.append(bytes(flat))
    return output

def parse_pointer_directory(values,expected,target_bounds,label):
    if type(values)!=list or values!=expected:
        raise ValueError(label+' directory pointer ordering/alias drift')
    if any(not target_bounds[0]<=p<target_bounds[1] for p in values):raise ValueError(label+' pointer out of bounds')
    return b''.join(p.to_bytes(2,'little') for p in values)

def new_chunks(root=ROOT):
    meta=json.loads((root/DATA).read_text())
    if meta.get('schema')!='ys-wholebank06-v1':raise ValueError('Bank6 source schema drift')
    first=expand_lanes(meta['graphics_byte_lanes_8'],*PIXEL,'graphics lanes')
    index0=expand_lanes(meta['tile_indices_before_layouts_8'],*ID_PRE,'tile index header')
    index1=expand_lanes(meta['tile_indices_between_layouts_8'],*ID_MID,'tile index middle')
    index2=expand_lanes(meta['tile_indices_after_layouts_8'],*ID_TAIL,'tile index tail')
    group_a=parse_layouts(meta['sprite_layouts_a'],LAYOUT_A,'sprite A')
    group_b=parse_layouts(meta['sprite_layouts_b'],LAYOUT_B,'sprite B')
    dir_a=parse_pointer_directory(meta['layout_directory_a'],[0xB9D0,0xB9F8,0xBA23,0xB9F8],(0xB9D0,0xBA4B),'A')
    dir_b=parse_pointer_directory(meta['layout_directory_b'],[0xBA63,0xBA7C,0xBA9B,0xBABA],(0xBA63,0xBAD9),'B')
    if meta['ff_padding_count']!=7:raise ValueError('Bank6 FF padding size drift')
    parts=[(PIXEL[0],first,'unresolved graphics bytes in eight-byte lanes'),
           (ID_PRE[0],index0,'tile indices A'),(DIR_A[0],dir_a,'layout pointers A')]
    parts.extend((a,raw,'sprite layout A') for (a,b),raw in zip(LAYOUT_A,group_a))
    parts.extend([(ID_MID[0],index1,'tile indices middle'),(DIR_B[0],dir_b,'layout pointers B')])
    parts.extend((a,raw,'sprite layout B') for (a,b),raw in zip(LAYOUT_B,group_b))
    parts.extend([(ID_TAIL[0],index2,'tile indices tail'),(FILL[0],b'\xff'*7,'padding')])
    result={};ownership=[]
    for start,chunk,label in parts:
        for i,v in enumerate(chunk):
            address=start+i
            if address in result or not KNOWN_END<=address<0xC000:raise ValueError('Bank6 source overlap '+label)
            result[address]=v
        ownership.append({'start':start,'end_exclusive':start+len(chunk),'type':label,'bytes':len(chunk)})
    if len(result)!=9192 or set(result)!=set(range(KNOWN_END,0xC000)):
        raise ValueError('Bank6 source data incomplete')
    raw=bytes(result[pc] for pc in range(KNOWN_END,0xC000))
    if sha(raw)!=json.loads((root/DIGEST).read_text())['new_bytes_sha256']:
        raise ValueError('Bank6 source data digest mismatch')
    return result,ownership

def full_bank(root=ROOT):
    old=known_bytes(root);new,_=new_chunks(root)
    if set(old)&set(new) or len(old)+len(new)!=SIZE:raise ValueError('Bank6 source ownership overlap')
    b=bytes((old|new)[pc] for pc in range(CPU,0xC000))
    if sha(b)!=json.loads((root/DIGEST).read_text())['bank06_sha256']:
        raise ValueError('Bank6 full-image digest mismatch')
    return b

def mixed_source(root=ROOT):
    raw=full_bank(root)
    parsed={}
    from z80_roundtrip_phase10 import encode
    for source,bank in SOURCES:
        if bank!=BANK:continue
        pc=None
        for line in (root/source).read_text().splitlines():
            s=line.split(';',1)[0].strip()
            if not s or s.endswith(':'):continue
            if s.lower().startswith('org '):pc=int(s.split('$',1)[1],16);continue
            if pc is None:raise ValueError('Unanchored bank6 instruction')
            b=encode(s,pc)
            if pc in parsed:raise ValueError('Duplicate bank6 code')
            parsed[pc]=(s,len(b));pc+=len(b)
    labels={0x8000:'SpriteRecordPointers',0x8080:'SpriteCountRecords',0x9932:'ProduceSpriteBuffer',
            0x9A77:'ObjectRecordPointers',0x9A99:'SpriteHandlerDirectory',
            0x9C18:'SpriteGraphicsByteLanes',0xB908:'TileIndicesA',0xB9C8:'SpriteLayoutPointersA',
            0xB9D0:'SpriteLayoutA0',0xB9F8:'SpriteLayoutA1',0xBA23:'SpriteLayoutA2',
            0xBA4B:'TileIndicesMiddle',0xBA5B:'SpriteLayoutPointersB',
            0xBA63:'SpriteLayoutB0',0xBA7C:'SpriteLayoutB1',0xBA9B:'SpriteLayoutB2',0xBABA:'SpriteLayoutB3',
            0xBAD9:'TileIndicesTail',0xBFF9:'FFPadding'}
    dirs={DIR_A,DIR_B}
    words={p for a,b in dirs for p in range(a,b,2)}
    lines=['; Ys SMS physical bank 06 — standalone source-only 16-KiB assembly.',
           '; Sprite triplet fields and tile indices preserved; raw graphics encoding remains undecoded.',
           'org $8000']
    pc=CPU
    while pc<0xC000:
        if pc in labels:lines.append(labels[pc]+':')
        if pc in parsed:
            s,n=parsed[pc];lines.append('    '+s);pc+=n;continue
        if pc in words:
            word=int.from_bytes(raw[pc-CPU:pc-CPU+2],'little')
            lines.append(f'    dw ${word:04X}');pc+=2;continue
        stop=min((p for p in labels if p>pc),default=0xC000)
        next_code=min((p for p in parsed if p>pc),default=0xC000)
        step=min(8,stop-pc,next_code-pc)
        if step<=0:raise ValueError('Bank06 assembly boundary error')
        lines.append('    db '+', '.join(f'${v:02X}' for v in raw[pc-CPU:pc-CPU+step]));pc+=step
    return '\n'.join(lines)+'\n'

def capture(rom,root=ROOT):
    if len(rom)!=0x40000 or sha(rom)!=EXPECTED_SHA:raise ValueError('Invalid ROM fingerprint')
    b=rom[BANK*SIZE:(BANK+1)*SIZE]
    def read(a,e):return b[a-CPU:e-CPU]
    def lanes(a,e):return [list(read(i,i+8)) for i in range(a,e,8)]
    def layout(a,e):
        raw=read(a,e);count=raw[0]
        if 1+3*count!=len(raw):raise ValueError(f'Layout count disagrees with bound at {a:04X}')
        return {'start':a,'triplets':[list(raw[i:i+3]) for i in range(1,len(raw),3)]}
    def ptrs(a,e):return [int.from_bytes(read(i,i+2),'little') for i in range(a,e,2)]
    meta={'schema':'ys-wholebank06-v1',
          'graphics_byte_lanes_8':lanes(*PIXEL),
          'tile_indices_before_layouts_8':lanes(*ID_PRE),
          'layout_directory_a':ptrs(*DIR_A),
          'sprite_layouts_a':[layout(a,e) for a,e in LAYOUT_A],
          'tile_indices_between_layouts_8':lanes(*ID_MID),
          'layout_directory_b':ptrs(*DIR_B),
          'sprite_layouts_b':[layout(a,e) for a,e in LAYOUT_B],
          'tile_indices_after_layouts_8':lanes(*ID_TAIL),
          'ff_padding_count':7,
          'evidence_note':'Count-prefixed sprite triplets and two pointer directories have exact boundaries. Eight-byte visual lanes are byte-preserving grouping only, NOT a proven pixel encoding.'}
    (root/DATA).parent.mkdir(parents=True,exist_ok=True)
    (root/DATA).write_text(json.dumps(meta,separators=(',',':'))+'\n')
    (root/DIGEST).write_text(json.dumps({'bank06_sha256':sha(b),
        'new_bytes_sha256':sha(read(KNOWN_END,0xC000)),
        'new_bytes':9192,'prior_bytes':7192,'source_only_complete':True},indent=2)+'\n')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture',type=Path)
    p.add_argument('--verify-rom',type=Path)
    p.add_argument('--verify-mixed',action='store_true')
    p.add_argument('--out-bank',type=Path)
    p.add_argument('--out-asm',type=Path)
    a=p.parse_args()
    if a.capture:capture(a.capture.read_bytes())
    bank=full_bank()
    if a.verify_rom:
        rom=a.verify_rom.read_bytes()
        if len(rom)!=0x40000 or sha(rom)!=EXPECTED_SHA or rom[BANK*SIZE:(BANK+1)*SIZE]!=bank:
            raise ValueError('Bank6 original ROM mismatch')
    if a.out_asm:a.out_asm.write_text(mixed_source())
    if a.verify_mixed:
        asm=mixed_source();rebuilt=assemble_mixed(asm)
        if rebuilt!=bank:raise ValueError('Mixed assembler byte mismatch')
        if (ROOT/ASM).read_text()!=asm:raise ValueError('Committed bank6 ASM snapshot drift')
    if a.out_bank:a.out_bank.write_bytes(bank)
    print(f'Bank6 source-only {len(bank)} bytes SHA256 {sha(bank)}')
if __name__=='__main__':main()
