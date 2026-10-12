#!/usr/bin/env python3
"""Rebuild Ys bank0 resource records, bank2 audio descriptors and bank3 glyph lanes.

Normal build reads only checked-in JSON, never the cartridge. --extract is an
explicit, developer-only conversion from a SHA-approved user-owned ROM.

Be conservative: alphabetic glyph slot notation is NOT a decrypted script;
non-glyph bytes remain opaque control operands. Audio stream bodies are not
recovered by this tool, and must remain ROM fallback.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'phase21/source.json'
ROM_DIGEST = json.loads((ROOT / 'manifest.json').read_text())['sha256']
BASE0, N0 = 0x2585, 23
SONG_DIR, SONG_COUNT = 0x8C90, 55
REGULAR_START, REGULAR_COUNT, REGULAR_SIZE = 0xAA77, 21, 37
LATE_START, LATE_END, LATE_FIRST_INDEX = 0xB319, 0xB6E8, 31
TEXT_START, TEXT_END = 0xDF00, 0xF8CD
GLYPH_MIN, GLYPH_MAX = 0xC3, 0xDC
RECOGNIZED = {0xE7:'gap_e7', 0xFE:'marker_fe', 0xFF:'marker_ff'}
BACK = {v:k for k,v in RECOGNIZED.items()}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parsed_record(data):
    if len(data) != 9: raise ValueError('Audio channel must have nine bytes')
    return {'parameters':list(data[:3]), 'stream_pointer':int.from_bytes(data[3:5],'little'),
            'flags':list(data[5:])}


def extracted(rom):
    if sha(rom) != ROM_DIGEST: raise ValueError('Original ROM identity mismatch')
    directory=[int.from_bytes(rom[SONG_DIR+2*i:SONG_DIR+2*i+2],'little') for i in range(SONG_COUNT)]
    regular=[]
    for i in range(REGULAR_COUNT):
        cpu=REGULAR_START+i*REGULAR_SIZE
        if directory[i]!=cpu or rom[cpu]!=4:raise ValueError('Regular descriptor alignment broken')
        regular.append({'address':cpu, 'channels':[parsed_record(rom[cpu+1+j*9:cpu+10+j*9]) for j in range(4)]})
    late=[]
    for i in range(LATE_FIRST_INDEX,SONG_COUNT):
        cpu=directory[i]
        stop=directory[i+1] if i+1<SONG_COUNT else LATE_END
        n=rom[cpu]
        if n not in (1,2) or cpu< LATE_START or stop> LATE_END or cpu+1+9*n>stop:
            raise ValueError('Variable descriptor bounds invalid')
        late.append({'index':i, 'address':cpu, 'next_address':stop,
                     'channels':[parsed_record(rom[cpu+1+9*j:cpu+10+9*j]) for j in range(n)]})
    # These nine-byte records are addressed by the established 41-entry
    # directory at $2533. Fields are NOT assigned invented semantics.
    resource=[{'index':i, 'bytes':list(rom[BASE0+9*i:BASE0+9*i+9])} for i in range(N0)]
    spans=[]; i=TEXT_START
    while i<TEXT_END:
        b=rom[i]
        if GLYPH_MIN<=b<=GLYPH_MAX:
            j=i
            while j<TEXT_END and GLYPH_MIN<=rom[j]<=GLYPH_MAX:j+=1
            spans.append({'op':'glyph_slots_0_to_25','slots':[v-GLYPH_MIN for v in rom[i:j]]})
            i=j
        elif b in RECOGNIZED:
            spans.append({'op':RECOGNIZED[b]});i+=1
        else:
            j=i
            while j<TEXT_END and not(GLYPH_MIN<=rom[j]<=GLYPH_MAX or rom[j] in RECOGNIZED):j+=1
            spans.append({'op':'unresolved','bytes':list(rom[i:j])});i=j
    return {'schema':'ys-phase21-typed-audio-and-glyph-lanes-v1',
            'provenance':{'source_rom_sha256':ROM_DIGEST,
             'note':'Glyph slots are numeric byte positions, not decoded plaintext; unresolved tokens are opaque.'},
            'bank0_indexed_records':resource,'bank2_song_directory':directory,
            'bank2_regular_descriptors':regular, 'bank2_variable_descriptors':late,
            'bank3_candidate_glyph_stream':spans}


def check_byte(v):
    if type(v) is not int or not 0<=v<=255:raise ValueError(f'Not an 8-bit value: {v}')
    return v


def check_word(v):
    if type(v) is not int or not 0<=v<=65535:raise ValueError(f'Not a 16-bit word: {v}')
    return v


def bytearray_map(bank, start, data):
    if not (0 <= bank < 16):raise ValueError('Bad bank')
    return {(bank, start+i):check_byte(v) for i,v in enumerate(data)}


def assemble_channel(c):
    prefix=c['parameters']; suffix=c['flags']; ptr=check_word(c['stream_pointer'])
    if len(prefix)!=3 or len(suffix)!=4:raise ValueError('Channel field sizes differ from ROM grammar')
    return bytes([*(check_byte(x) for x in prefix),ptr&255,ptr>>8,
                  *(check_byte(x) for x in suffix)])


def assemble(data):
    if data['schema']!='ys-phase21-typed-audio-and-glyph-lanes-v1':raise ValueError('Unknown source schema')
    if data['provenance']['source_rom_sha256']!=ROM_DIGEST:raise ValueError('Provenance ROM mismatch')
    result={}; typed={}; counts={}
    def put(bank,start,content,name):
        if not (bank==0 and 0<=start<0x4000 or bank==2 and 0x8000<=start<0xc000 or bank==3 and 0x8000<=start<0xc000):
            raise ValueError('Mapped source address outside physical ROM bank')
        new=bytearray_map(bank,start,content)
        if any(p in result for p in new):raise ValueError('Overlapping phase21 source ownership')
        result.update(new)
        typed.setdefault(name,{}).update(new)
    res=data['bank0_indexed_records']
    if len(res)!=N0 or any(r['index']!=i or len(r['bytes'])!=9 for i,r in enumerate(res)):
        raise ValueError('Bank0 indexed nine-byte records invalid')
    for i,r in enumerate(res):put(0,BASE0+9*i,r['bytes'],'resource_records')
    ptr=data['bank2_song_directory']
    if len(ptr)!=SONG_COUNT:raise ValueError('Song directory must have 55 pointers')
    for v in ptr:
        check_word(v)
        if not 0x8000<=v<0xC000:raise ValueError('Song pointer not in bank2 slot')
    put(2,SONG_DIR,b''.join(v.to_bytes(2,'little') for v in ptr),'song_directory')
    reg=data['bank2_regular_descriptors']
    if len(reg)!=REGULAR_COUNT:raise ValueError('Regular descriptor count differs')
    for i,r in enumerate(reg):
        start=REGULAR_START+i*REGULAR_SIZE
        if r['address']!=start or ptr[i]!=start or len(r['channels'])!=4:
            raise ValueError('Misaligned regular descriptor')
        for c in r['channels']:
            if not 0x8D40<=c['stream_pointer']<0xB319:raise ValueError('Regular descriptor stream outside known event span')
        put(2,start,bytes([4])+b''.join(assemble_channel(c) for c in r['channels']),'regular_descriptors')
    late=data['bank2_variable_descriptors']
    if len(late)!=SONG_COUNT-LATE_FIRST_INDEX:raise ValueError('Variable descriptor count differs')
    for j,r in enumerate(late):
        i=LATE_FIRST_INDEX+j;start=ptr[i];stop=ptr[i+1] if i<SONG_COUNT-1 else LATE_END
        channels=r['channels']; head_end=start+1+9*len(channels)
        if not( r['index']==i and r['address']==start and r['next_address']==stop
                and len(channels) in (1,2) and LATE_START<=start<stop<=LATE_END
                and head_end<=stop):raise ValueError('Variable descriptor boundary or count mismatch')
        for c in channels:
            if not head_end<=c['stream_pointer']<stop:
                raise ValueError('Variable descriptor stream points outside own record trailer')
        put(2,start,bytes([len(channels)])+b''.join(assemble_channel(c) for c in channels),'variable_headers')
    # Require contiguous directory sequence; this proof is what makes the
    # 24 variable headers stronger than speculative byte grouping.
    if [r['address'] for r in late]!=ptr[LATE_FIRST_INDEX:]:raise ValueError('Variable headers do not follow directory')
    stream=bytearray()
    for token in data['bank3_candidate_glyph_stream']:
        op=token['op']
        if op=='glyph_slots_0_to_25':
            slots=token['slots']
            if not slots or any(type(v) is not int or not 0<=v<=25 for v in slots):raise ValueError('Invalid glyph slot')
            stream.extend(GLYPH_MIN+v for v in slots)
        elif op in BACK:stream.append(BACK[op])
        elif op=='unresolved':
            vals=token['bytes']
            if not vals or any(GLYPH_MIN<=check_byte(v)<=GLYPH_MAX or v in RECOGNIZED for v in vals):
                raise ValueError('Opaque run contains an identified candidate glyph/control')
            stream.extend(vals)
        else:raise ValueError(f'Unknown glyph-stream token: {op}')
    if len(stream)!=TEXT_END-TEXT_START:raise ValueError('Bank3 glyph stream length mismatch')
    put(3,0x8000+TEXT_START-0xC000,stream,'candidate_glyph_stream')
    expected={'resource_records':207,'song_directory':110,'regular_descriptors':777,
              'variable_headers':357,'candidate_glyph_stream':6605}
    counts={k:len(v) for k,v in typed.items()}
    if counts!=expected:raise ValueError(f'Incorrect region ownership sizes: {counts}')
    if len(result)!=sum(expected.values()):raise ValueError('Phase21 region overlap detected')
    return result,counts


def load_verified(root=ROOT):
    data=json.loads((root/'phase21/source.json').read_text(encoding='utf-8'))
    result,counts=assemble(data)
    digest=sha(bytes(v for _,v in sorted(result.items())))
    expected=json.loads((root/'phase21/digests.json').read_text())
    if digest!=expected['combined_source_sha256'] or counts!=expected['region_bytes']:
        raise ValueError('Phase21 source hash/metadata drift')
    return result,counts,digest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--extract',type=Path,help='One-time extraction from user ROM (never needed by normal build)')
    p.add_argument('--verify',action='store_true')
    a=p.parse_args()
    if a.extract:
        data=extracted(a.extract.read_bytes())
        source,counts=assemble(data)
        SRC.write_text(json.dumps(data,indent=1)+'\n')
        digest=sha(bytes(v for _,v in sorted(source.items())))
        (ROOT/'phase21/digests.json').write_text(json.dumps({'combined_source_sha256':digest,'region_bytes':counts},indent=2)+'\n')
        print('Created source from approved user ROM:',counts)
    if a.verify or not a.extract:
        positions,counts,digest=load_verified()
        print('Verified phase21 original-ROM-independent source emission:',len(positions),'bytes',counts,digest)

if __name__=='__main__':main()
