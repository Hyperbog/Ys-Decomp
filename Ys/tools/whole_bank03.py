#!/usr/bin/env python3
"""Source-only physical bank 3 reconstruction, with explicit unresolved visual data.

Previously reconstructed 176 Mode4 tiles and candidate text lanes are reused.
The 60 four-byte index records are pointer-verified against text lane bounds;
actual rendering/control grammar is NOT claimed understood.
"""
import argparse
import hashlib
import json
from pathlib import Path
from build_sms_phase14 import ROOT,EXPECTED_SHA
from graphics_source_phase17 import load_verified as graphics
from phase21_semantic_sources import load_verified as typed_data
from whole_bank07 import assemble_mixed

BANK=3;BASE=0xC000;SIZE=0x4000
GFX=(0x8000,0x9600)
UNRESOLVED=(0x9600,0x9DA3)
DIRECTORY=(0x9DA3,0x9E93)
TEXT_PREFIX=(0x9E93,0x9F00)
TEXT=(0x9F00,0xB8CD)
PADDING=(0xB8CD,0xC000)
JSON=Path('wholebank03/source.json')
DIGEST=Path('wholebank03/digests.json')

def sha(data):return hashlib.sha256(data).hexdigest()

def known_bytes(root=ROOT):
    owners={}
    def claim(table,origin):
        for pc,v in table.items():
            if pc in owners or not 0x8000<=pc<0xC000 or type(v)!=int or not 0<=v<256:
                raise ValueError(f'Bank3 owner overlap/boundary: {origin} at {pc:04X}')
            owners[pc]=v
    claim(graphics(root)[3]['bytes'],'bank3 editable Mode4 pixels')
    bank3={pc:byte for (bank,pc),byte in typed_data(root)[0].items() if bank==3}
    claim(bank3,'Phase21 candidate glyph tokens')
    expected=set(range(*GFX))|set(range(*TEXT))
    if len(owners)!=12237 or set(owners)!=expected:
        raise ValueError('Previously source-backed bank3 coverage drift')
    return owners

def tail_bytes(root=ROOT):
    data=json.loads((root/JSON).read_text())
    if data.get('schema')!='ys-whole-bank03-source-v1':raise ValueError('Invalid bank3 schema')
    un=bytes.fromhex(data['unresolved_visual_bytes_hex'])
    if len(un)!=UNRESOLVED[1]-UNRESOLVED[0]:raise ValueError('Visual data boundaries drift')
    entries=data['text_directory']
    if len(entries)!=60:raise ValueError('Expected 60 bank3 text directory entries')
    fields=bytearray()
    for i,e in enumerate(entries):
        if type(e)!=dict or set(e)!={'parameter0','parameter1','pointer'}:raise ValueError(f'Bad descriptor fields {i}')
        x,y,target=e['parameter0'],e['parameter1'],e['pointer']
        if any(type(v)!=int or not 0<=v<256 for v in (x,y)) or type(target)!=int or not TEXT_PREFIX[0]<=target<TEXT[1]:
            raise ValueError(f'Invalid bank3 text target or descriptor {i}')
        fields.extend((x,y,target&255,target>>8))
    if entries[0]['pointer']!=TEXT_PREFIX[0] or entries[-1]['pointer']!=0xB2D7:
        raise ValueError('Unexpected first/last descriptor anchors')
    prefix=bytes(data['candidate_text_prefix'])
    if len(prefix)!=TEXT_PREFIX[1]-TEXT_PREFIX[0] or any(type(x)!=int or x<0 or x>255 for x in data['candidate_text_prefix']):
        raise ValueError('Bad candidate text prefix')
    if data['padding_fill']!=255 or data['padding_length']!=PADDING[1]-PADDING[0]:
        raise ValueError('Unexpected bank3 padding')
    result={}
    for start,chunk,name in ((UNRESOLVED[0],un,'unresolved'),(DIRECTORY[0],bytes(fields),'directory'),
                             (TEXT_PREFIX[0],prefix,'prefix'),(PADDING[0],b'\xff'*data['padding_length'],'padding')):
        for j,v in enumerate(chunk):
            pc=start+j
            if pc in result:raise ValueError('Bank3 tail overlap '+name)
            result[pc]=v
    wanted=set(range(*UNRESOLVED))|set(range(*DIRECTORY))|set(range(*TEXT_PREFIX))|set(range(*PADDING))
    if set(result)!=wanted or len(result)!=4147:raise ValueError('Bank3 tail missing bytes')
    raw=bytes(result[pc] for pc in sorted(result))
    digs=json.loads((root/DIGEST).read_text())
    if sha(raw)!=digs['new_source_bytes_sha256']:raise ValueError('Bank3 tail source digest drift')
    return result

def full_bank(root=ROOT):
    a=known_bytes(root);b=tail_bytes(root)
    if set(a)&set(b) or len(a)+len(b)!=SIZE:raise ValueError('Bank3 ownership mismatch')
    result=a|b
    if set(result)!=set(range(0x8000,0xC000)):raise ValueError('Source-only bank3 has uncovered addresses')
    raw=bytes(result[pc] for pc in range(0x8000,0xC000))
    if sha(raw)!=json.loads((root/DIGEST).read_text())['bank3_sha256']:
        raise ValueError('Bank3 full source digest drift')
    return raw

def mixed_source(root=ROOT):
    raw=full_bank(root)
    labels={0x8000:'Mode4Tiles',0x9600:'UndecodedVisualStream',
            0x9DA3:'TextDirectory60',0x9E93:'TextPrefixCandidate',
            0x9F00:'ExistingGlyphSlots',0xB8CD:'Bank3FFFiller'}
    lines=['; Ys physical bank 03, all 16384 bytes independently source-backed.',
           '; Visual stream and control-byte semantics remain unresolved.','org $8000']
    pc=0x8000
    while pc<0xC000:
        if pc in labels:lines.append(labels[pc]+':')
        # 60 records: first 2 bytes unresolved parameters + anchored target word.
        if DIRECTORY[0]<=pc<DIRECTORY[1]:
            i=pc-DIRECTORY[0]
            if i%4==0:
                lines.append(f'    db ${raw[pc-0x8000]:02X}, ${raw[pc-0x8000+1]:02X}')
                pc+=2
            else:
                value=int.from_bytes(raw[pc-0x8000:pc-0x8000+2],'little')
                lines.append(f'    dw ${value:04X}')
                pc+=2
        else:
            end=min((a for a in labels if a>pc),default=0xC000)
            n=min(16,end-pc)
            lines.append('    db '+', '.join(f'${x:02X}' for x in raw[pc-0x8000:pc-0x8000+n]))
            pc+=n
    return '\n'.join(lines)+'\n'

def capture(rom,root=ROOT):
    if len(rom)!=0x40000 or sha(rom)!=EXPECTED_SHA:raise ValueError('Wrong source ROM')
    def read(start,stop):return rom[BASE+start-0x8000:BASE+stop-0x8000]
    known_bytes(root)
    records=[]
    for j in range(60):
        s=read(DIRECTORY[0]+4*j,DIRECTORY[0]+4*j+4)
        records.append({'parameter0':s[0],'parameter1':s[1],'pointer':s[2]|(s[3]<<8)})
    data={'schema':'ys-whole-bank03-source-v1',
          'unresolved_visual_bytes_hex':read(*UNRESOLVED).hex(),
          'text_directory':records,'candidate_text_prefix':list(read(*TEXT_PREFIX)),
          'padding_fill':255,'padding_length':PADDING[1]-PADDING[0],
          'note':'60 descriptors with text-bounded pointers, but channel flags/control format not established.'}
    (root/JSON).write_text(json.dumps(data,indent=2)+'\n')
    (root/DIGEST).write_text(json.dumps({
        'bank3_sha256':sha(read(0x8000,0xC000)),
        'new_source_bytes_sha256':sha(read(*UNRESOLVED)+read(*DIRECTORY)+read(*TEXT_PREFIX)+read(*PADDING)),
        'new_source_bytes':4147},indent=2)+'\n')

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
        if sha(rom)!=EXPECTED_SHA or bank!=rom[BASE:BASE+SIZE]:raise ValueError('Bank3 mismatch against ROM')
    if a.verify_mixed or a.out_asm:
        asm=mixed_source()
        if assemble_mixed(asm)!=bank:raise ValueError('Mixed source does not reassemble bank3')
        if a.out_asm:a.out_asm.write_text(asm)
    if a.out_bank:a.out_bank.write_bytes(bank)
    print('PASS: source-only bank3',SIZE,'SHA256',sha(bank),'+4147 source-backed bytes')
if __name__=='__main__':main()
