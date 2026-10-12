#!/usr/bin/env python3
"""Whole physical bank 4, ROM-independent build; conservative source ownership.

The 502 x 32-byte groups are a reversible 4-byte-lane *hypothesis*, NOT
verified VDP tiles. Collision-box table $8000-$807B is the known consumer of
bank4 code $807C-$80A1. Never infer unknown data semantics from round-trips.
"""
import argparse
import hashlib
import json
from pathlib import Path
from build_sms_phase14 import ROOT, SOURCES, EXPECTED_SHA
from z80_roundtrip_phase10 import assemble, encode
from structured_data_phase16 import load_verified
from whole_bank07 import assemble_mixed

BANK=4; BASE=0x10000; FIRST=0x8000; END=0xC000
KNOWN_END=0x80A2
LANES=(0x80A2,0xBF62) # 502 * 32 bytes. Boundary is organizational, not known tile address.
TRAILER=(0xBF62,0xBFB8)
FILL=(0xBFB8,0xC000)
SOURCE=Path('wholebank04/source.json')
DIGEST=Path('wholebank04/digests.json')
ASM=Path('src/wholebank04/bank04_complete.asm')

def sha(data):return hashlib.sha256(data).hexdigest()

def existing(root=ROOT):
    old={}
    for rel,bank in SOURCES:
        if bank!=BANK:continue
        code,_=assemble((root/rel).read_text())
        for pc,v in code.items():
            if pc in old:raise ValueError('Duplicate bank4 instructions')
            old[pc]=v
    records=load_verified(root)[4]['bytes']
    for pc,v in records.items():
        if pc in old:raise ValueError('Duplicate bank4 records')
        old[pc]=v
    if len(old)!=162 or set(old)!=set(range(FIRST,KNOWN_END)):
        raise ValueError('Bank4 previously reconstructed source drift')
    return old

def new_chunks(root=ROOT):
    src=json.loads((root/SOURCE).read_text())
    if src.get('schema')!='ys-bank04-source-v1':raise ValueError('Invalid bank4 source schema')
    tiles=src['candidate_32byte_groups']
    if not isinstance(tiles,list) or len(tiles)!=502:
        raise ValueError('Bank4 requires exactly 502 organizational 32-byte groups')
    lanes=bytearray()
    for tile in tiles:
        if not isinstance(tile,list) or len(tile)!=8:raise ValueError('Bank4 eight-row grouping drift')
        for row in tile:
            if not isinstance(row,list) or len(row)!=4 or any(type(v)!=int or not 0<=v<256 for v in row):
                raise ValueError('Bank4 four-lane group fields invalid')
            lanes.extend(row)
    if len(lanes)!=LANES[1]-LANES[0]:raise ValueError('Bank4 grouped data length mismatch')
    trailer=src['undecoded_trailer']
    if not isinstance(trailer,list) or len(trailer)!=TRAILER[1]-TRAILER[0] or any(type(v)!=int or not 0<=v<256 for v in trailer):
        raise ValueError('Bank4 undecoded trailer invalid')
    if src['ff_padding']!={'start':FILL[0],'count':FILL[1]-FILL[0],'value':255}:
        raise ValueError('Bank4 bank-end fill drift')
    parts=[(LANES[0],bytes(lanes),'candidate graphics 4-byte lanes (NOT confirmed tiles)'),
           (TRAILER[0],bytes(trailer),'unresolved trailer'),
           (FILL[0],bytes([255])*(FILL[1]-FILL[0]),'72-byte FF pad')]
    result={};inventory=[]
    for start,chunk,meaning in parts:
        for i,v in enumerate(chunk):
            pc=start+i
            if pc in result or not KNOWN_END<=pc<END:raise ValueError('Overlapping bank4 data')
            result[pc]=v
        inventory.append({'start':start,'end_exclusive':start+len(chunk),'meaning':meaning,'bytes':len(chunk)})
    if set(result)!=set(range(KNOWN_END,END)) or len(result)!=16222:
        raise ValueError('Bank4 source data does not cover the entire tail')
    data=bytes(result[pc] for pc in range(KNOWN_END,END))
    if sha(data)!=json.loads((root/DIGEST).read_text())['new_data_sha256']:
        raise ValueError('Bank4 source data content fingerprint failed')
    return result,inventory

def full_bank(root=ROOT):
    known=existing(root);new,_=new_chunks(root)
    if set(known)&set(new) or len(known)+len(new)!=0x4000:
        raise ValueError('Bank4 owner overlap')
    result=bytes((known|new)[i] for i in range(FIRST,END))
    if sha(result)!=json.loads((root/DIGEST).read_text())['bank_sha256']:
        raise ValueError('Bank4 complete image digest mismatch')
    return result

def mixed_source(root=ROOT):
    raw=full_bank(root)
    # Prefer actual previous Z80 mnemonic source; other owned bytes are DB lanes.
    code={}
    for rel,bank in SOURCES:
        if bank!=BANK:continue
        pc=None
        for line in (root/rel).read_text().splitlines():
            s=line.split(';',1)[0].strip()
            if not s or s.endswith(':'):continue
            if s.lower().startswith('org '):pc=int(s.split('$',1)[1],16);continue
            if pc is None:raise ValueError('Bank4 Z80 missing origin')
            n=len(encode(s,pc))
            if pc in code:raise ValueError('Bank4 overlapping mnemonics')
            code[pc]=(s,n);pc+=n
    labels={0x8000:'CollisionBoxDescriptors31',0x807C:'CheckCollisionAgainstBox',
            0x80A2:'UndecodedFourByteLanes502Groups',0xBF62:'UndecodedBankTrailer',
            0xBFB8:'Bank4FFPadding'}
    lines=['; SMS physical bank 04 — 16KiB source-only, not completely decoded.',
           '; The 502 x 32-byte group boundaries are a reversible organizational hypothesis.',
           '; Only $8000-$807B is a proven four-field descriptor table with a Z80 consumer.',
           'org $8000']
    pc=FIRST
    while pc<END:
        if pc in labels:lines.append(labels[pc]+':')
        if pc in code:
            s,n=code[pc];lines.append('    '+s);pc+=n;continue
        stop=min([i for i in labels if i>pc]+[i for i in code if i>pc]+[END])
        step=min(16,stop-pc)
        if step<=0:raise ValueError('Invalid bank4 mixed boundary')
        lines.append('    db '+', '.join(f'${x:02X}' for x in raw[pc-FIRST:pc-FIRST+step]));pc+=step
    return '\n'.join(lines)+'\n'

def capture(rom,root=ROOT):
    if len(rom)!=0x40000 or sha(rom)!=EXPECTED_SHA:raise ValueError('Incorrect ROM fingerprint')
    known=existing(root)
    if any(rom[BASE+pc-FIRST]!=v for pc,v in known.items()):
        raise ValueError('Bank4 prior source disagrees with owner ROM')
    bank=rom[BASE:BASE+0x4000]
    def chunk(a,z):return bank[a-FIRST:z-FIRST]
    blocks=[]
    data=chunk(*LANES)
    for i in range(0,len(data),32):
        blocks.append([list(data[i+j:i+j+4]) for j in range(0,32,4)])
    source={'schema':'ys-bank04-source-v1','candidate_32byte_groups':blocks,
            'undecoded_trailer':list(chunk(*TRAILER)),
            'ff_padding':{'start':FILL[0],'count':FILL[1]-FILL[0],'value':255},
            'provenance':'Known ROM fingerprint; candidate graphical grouping does not establish pixel format or VRAM tile boundaries.'}
    (root/SOURCE).parent.mkdir(parents=True,exist_ok=True)
    (root/SOURCE).write_text(json.dumps(source,separators=(',',':'))+'\n')
    (root/DIGEST).write_text(json.dumps({'bank_sha256':sha(bank),
        'new_data_sha256':sha(chunk(KNOWN_END,END)),
        'existing_source_bytes':len(known),'new_source_bytes':len(chunk(KNOWN_END,END)),
        'four_byte_lane_group_count':len(blocks),'candidate_lane_bytes':len(data),
        'unresolved_trailer_bytes':TRAILER[1]-TRAILER[0],
        'ff_padding_bytes':FILL[1]-FILL[0]},indent=2)+'\n')
    if full_bank(root)!=bank:raise ValueError('Bank4 capture failed independent rebuild')
    (root/ASM).parent.mkdir(parents=True,exist_ok=True)
    (root/ASM).write_text(mixed_source(root))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture',type=Path);p.add_argument('--verify-rom',type=Path)
    p.add_argument('--verify-mixed',action='store_true');p.add_argument('--out-bank',type=Path)
    a=p.parse_args()
    if a.capture:capture(a.capture.read_bytes())
    b=full_bank()
    if a.verify_rom:
        rom=a.verify_rom.read_bytes()
        if len(rom)!=0x40000 or sha(rom)!=EXPECTED_SHA or rom[BASE:BASE+0x4000]!=b:
            raise ValueError('Bank4 ROM mismatch')
    if a.verify_mixed:
        s=mixed_source()
        if s!=(ROOT/ASM).read_text() or assemble_mixed(s)!=b:
            raise ValueError('Bank4 assembly/source drift')
    if a.out_bank:a.out_bank.write_bytes(b)
    print('Bank4 independent full image',len(b),'SHA256',sha(b))
if __name__=='__main__':main()
