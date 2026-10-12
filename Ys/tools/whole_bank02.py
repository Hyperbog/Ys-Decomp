#!/usr/bin/env python3
"""Ys SMS physical bank 2: ROM-independent sound-bank byte reconstruction.

Normal generation uses committed assembly/typed resources; only --capture reads
an approved original ROM. Unidentified event bytes are preserved as explicit
*unresolved* data, never claimed to be decoded music commands.
"""
import argparse
import hashlib
import json
from pathlib import Path
from build_sms_phase14 import ROOT, SOURCES, EXPECTED_SHA
from build_phase21 import old_positions
from phase21_semantic_sources import load_verified, SONG_DIR, SONG_COUNT, LATE_START, LATE_END
from z80_roundtrip_phase10 import assemble, encode
from whole_bank07 import assemble_mixed

BANK=2; CPU=0x8000; SIZE=0x4000; BOTTOM=0xC000
DATA=Path('wholebank02/source.json')
DIGEST=Path('wholebank02/digests.json')
CODE=Path('src/wholebank02/additional_code.asm')
ASM=Path('src/wholebank02/bank02_complete.asm')
CODE_RANGES=((0x837B,0x837F),(0x85FC,0x8600),(0x88D8,0x88DC),(0x88E2,0x88E6))
PSG=(0x8A58,0x8AEA)
FM=(0x8AEA,0x8B7C)
SEQ_PTRS=(0x8B7D,0x8B9F)
SEQ_DATA=(0x8B9F,0x8C2F)
SHAPE_PTRS=(0x8C2F,0x8C39)
SHAPE_PREFIX=(0x8C39,0x8C39)
SHAPE_DATA=(0x8C39,0x8C90)
PRIOR=3785
NEW=12599


def sha(data):return hashlib.sha256(data).hexdigest()

def known(root=ROOT):
    """Reuse already checked Phase 1-21 source ownership for this bank."""
    offsets=old_positions(root)
    from_phase21=load_verified(root)[0]
    positions={a-2*SIZE+CPU for a in offsets if 2*SIZE<=a<3*SIZE}
    original={}
    for source,bank in SOURCES:
        if bank==BANK:
            decoded,_=assemble((root/source).read_text())
            for pc,val in decoded.items():
                if pc in original:raise ValueError(f'Bank2 prior ASM overlap ${pc:04X}')
                original[pc]=val
    # recover early source data via identical ownership tested in phase17's map
    from source_tables_phase15 import load_verified_sources
    from structured_data_phase16 import load_verified as load16
    from graphics_source_phase17 import load_verified as load17
    for fn in (load_verified_sources,load16,load17):
        mapping=fn(root)
        if BANK in mapping:
            for pc,v in mapping[BANK]['bytes'].items():
                if pc in original:raise ValueError('Earlier source overlap')
                original[pc]=v
    for (bank,pc),val in from_phase21.items():
        if bank==BANK:
            if pc in original:raise ValueError('Phase21 overlap')
            original[pc]=val
    if set(original)!=positions|{pc for bank,pc in from_phase21 if bank==BANK}:
        raise ValueError('Bank2 prior ownership does not agree with overlay')
    if len(original)!=PRIOR:raise ValueError(f'Bank2 previous source byte count drift: {len(original)}')
    return original


def byte_list(items,name):
    if not isinstance(items,list) or any(type(i)!=int or not 0<=i<=255 for i in items):
        raise ValueError('Bad unsigned bytes in '+name)
    return bytes(items)


def words(items,start,stop,name,lo=None,hi=None):
    if not isinstance(items,list) or len(items)*2!=stop-start or any(type(i)!=int or not 0<=i<=65535 for i in items):
        raise ValueError('Bad little-endian words: '+name)
    if lo is not None and any(not lo<=i<hi for i in items):raise ValueError('Out of range pointers: '+name)
    return b''.join(w.to_bytes(2,'little') for w in items)


def decoded_code(root=ROOT):
    data,_=assemble((root/CODE).read_text())
    expected={p for a,b in CODE_RANGES for p in range(a,b)}
    if set(data)!=expected:raise ValueError('Missing bank2 mnemonic instructions')
    cursor=None
    for line in (root/CODE).read_text().splitlines():
        s=line.split(';',1)[0].strip()
        if not s or s.endswith(':'):continue
        if s.lower().startswith('org '):
            cursor=int(s.split('$',1)[1],16)
            if cursor not in {a for a,b in CODE_RANGES}:raise ValueError('Unanchored bank2 code')
        else:
            if cursor is None or s.lower().startswith(('db ','dw ','ds ')):raise ValueError('Only mnemonic instructions allowed')
            cursor+=len(encode(s,cursor))
    return data


def new_data(root=ROOT):
    m=json.loads((root/DATA).read_text())
    if m.get('schema')!='ys-wholebank02-sound-v1':raise ValueError('Bad sound bank source schema')
    old=known(root)
    chunks={};inventory=[]
    def put(a,b,blob,name):
        if len(blob)!=b-a or a<CPU or b>BOTTOM or a>=b:raise ValueError('Sound data region boundary: '+name)
        for i,v in enumerate(blob):
            pc=a+i
            if pc in old or pc in chunks:raise ValueError(f'Sound bank source overlap {name} ${pc:04X}')
            chunks[pc]=v
        inventory.append({'cpu_start':a,'cpu_end_exclusive':b,'bytes':len(blob),'kind':name})
    put(0x81B1,0x81D9,byte_list(m['init_register_sequence'],'init_register_sequence'),'unresolved_init_sequence')
    put(0x8600,0x8628,words(m['dispatch_targets'],0x8600,0x8628,'dispatch',0x8000,0x9000),'sound_dispatch_words_20')
    put(0x8878,0x8883,byte_list(m['channel_constants'],'channel_constants'),'unresolved_channel_constants')
    put(*PSG,words(m['psg_note_periods'],*PSG,'PSG periods'),'psg_note_periods_73_words')
    put(*FM,words(m['fm_note_registers'],*FM,'FM words'),'fm_note_registers_73_words')
    if m['sequence_sentinel']!=255:raise ValueError('Sound sequence sentinel drift')
    put(0x8B7C,0x8B7D,b'\xff','lookup_sentinel')
    ptr=m['sequence_pointers'];seq_end=SEQ_DATA[1]
    if len(ptr)!=17 or ptr[0]!=SEQ_DATA[0] or ptr[-1]>=seq_end or any(p>=q for p,q in zip(ptr,ptr[1:])):
        raise ValueError('Sound sequence pointer ordering')
    put(*SEQ_PTRS,words(ptr,*SEQ_PTRS,'sequence directory',*SEQ_DATA),'sequence_directory_17')
    if len(m['sequences'])!=len(ptr):raise ValueError('Sequence record count')
    for i,entry in enumerate(m['sequences']):
        stop=ptr[i+1] if i+1<len(ptr) else seq_end
        if entry['start']!=ptr[i]:raise ValueError('Sequence pointer mismatch')
        put(ptr[i],stop,byte_list(entry['bytes'],'sequence'),'unresolved_sequence_'+str(i))
    shp=m['shape_pointers']; shp_end=SHAPE_DATA[1]
    if len(shp)!=5 or shp[0]!=SHAPE_DATA[0] or any(p>=q for p,q in zip(shp,shp[1:])):
        raise ValueError('Shape pointer ordering')
    put(*SHAPE_PTRS,words(shp,*SHAPE_PTRS,'shape pointers',*SHAPE_DATA),'shape_directory_5')
    if len(m['shapes'])!=len(shp):raise ValueError('Shape record count')
    for i,entry in enumerate(m['shapes']):
        stop=shp[i+1] if i+1<len(shp) else shp_end
        if entry['start']!=shp[i]:raise ValueError('Shape pointer mismatch')
        put(shp[i],stop,byte_list(entry['bytes'],'shape'),'unresolved_shape_'+str(i))
    for field,a,b,name in (
        ('event_and_instrument_bytes_hex',0x8CFE,0xAA77,'unresolved_sound_tables_and_events'),
        ('event_stream_bytes_hex',0xAD80,0xB319,'unresolved_audio_event_streams'),
        ('post_song_data_hex',0xB6E8,0xBE57,'unresolved_post_song_data')):
        put(a,b,bytes.fromhex(m[field]),name)
    # Preserve each of the 24 bounded song payloads separately, keyed by its
    # already-source-backed one/two-channel header and next directory entry.
    from_phase21=json.loads((root/'phase21/source.json').read_text())['bank2_variable_descriptors']
    variable=m['variable_event_bodies']
    if len(variable)!=24 or len(from_phase21)!=24:raise ValueError('Variable song count')
    for j,(r,ref) in enumerate(zip(variable,from_phase21)):
        start=ref['address']+1+9*len(ref['channels']);end=ref['next_address']
        if r['index']!=31+j or r['start']!=start or r['end_exclusive']!=end or not start<end:
            raise ValueError('Variable song event boundaries drift')
        for channel in ref['channels']:
            if not start<=channel['stream_pointer']<end:raise ValueError('Channel stream outside variable song body')
        put(start,end,byte_list(r['unresolved_event_bytes'],'song event body'),f'unresolved_song_event_{j+31:02d}')
    if m['bank_end_ff_count']!=425:raise ValueError('Sound bank FF filler size changed')
    put(0xBE57,0xC000,b'\xff'*425,'ff_padding')
    expected={p for a,b in CODE_RANGES for p in range(a,b)}
    if set(chunks)&expected:raise ValueError('Bank2 code/data collision')
    if len(chunks)!=NEW-len(expected):raise ValueError(f'Bank2 new data length drift {len(chunks)}')
    hashes=json.loads((root/DIGEST).read_text())
    raw=bytes(chunks[p] for p in sorted(chunks))
    if sha(raw)!=hashes['new_data_sha256']:raise ValueError('Sound bank data source digest drift')
    return chunks,inventory


def full_bank(root=ROOT):
    prior=known(root);code=decoded_code(root);data,_=new_data(root)
    if any(set(a)&set(b) for a,b in ((prior,code),(prior,data),(code,data))):raise ValueError('Bank2 source overlap')
    merged=prior|code|data
    if len(merged)!=SIZE or set(merged)!=set(range(CPU,BOTTOM)):
        raise ValueError(f'Bank2 source-only missing bytes, have {len(merged)}')
    result=bytes(merged[p] for p in range(CPU,BOTTOM))
    hashes=json.loads((root/DIGEST).read_text())
    if sha(result)!=hashes['bank_sha256'] or sha(bytes(code[p] for p in sorted(code)))!=hashes['new_code_sha256']:
        raise ValueError('Bank2 complete byte digest drift')
    return result


def mixed_source(root=ROOT):
    raw=full_bank(root)
    instructions={}
    for path,bank in SOURCES:
        if bank!=BANK:continue
        pc=None
        for line in (root/path).read_text().splitlines():
            s=line.split(';',1)[0].strip()
            if not s or s.endswith(':'):continue
            if s.lower().startswith('org '):pc=int(s.split('$',1)[1],16);continue
            if pc is None:raise ValueError('Unanchored old sound code')
            blob=encode(s,pc)
            if pc in instructions:raise ValueError('Bank2 duplicate Z80 instruction')
            instructions[pc]=(s,len(blob));pc+=len(blob)
    pc=None
    for line in (root/CODE).read_text().splitlines():
        s=line.split(';',1)[0].strip()
        if not s or s.endswith(':'):continue
        if s.lower().startswith('org '):pc=int(s.split('$',1)[1],16);continue
        blob=encode(s,pc)
        if pc in instructions:raise ValueError('Bank2 new code duplicate')
        instructions[pc]=(s,len(blob));pc+=len(blob)
    label_list={0x8000:'SoundFrameUpdate',0x81B1:'SoundInitRegisterSequence',0x8600:'SoundDispatchTargets',
       0x8878:'ChannelConstants',0x8A58:'PSGNotePeriodWords',0x8AEA:'FMNoteRegisterWords',
       0x8B7C:'LookupSentinel',0x8B7D:'SequencePointerDirectory17',0x8B9F:'SequenceRecords',
       0x8C2F:'ShapePointerDirectory5',0x8C39:'ShapeRecords',
       0x8C90:'SongDirectory55',0x8CFE:'UnresolvedSoundTablesAndEvents',
       0xAA77:'RegularSongDescriptors21',0xAD80:'UnresolvedSongEventArea',
       0xB319:'VariableSongHeaders24',0xB6E8:'UndecodedSoundTrailingData',
       0xBE57:'SoundBankEndPadding'}
    for r in json.loads((root/DATA).read_text())['variable_event_bodies']:
        label_list[r['start']]=f'Song{r["index"]:02d}UnresolvedEvents'
    word_starts=set(range(*PSG,2))|set(range(*FM,2))|set(range(*SEQ_PTRS,2))|set(range(*SHAPE_PTRS,2))|set(range(0x8600,0x8628,2))|set(range(*((0x8C90,0x8CFE)),2))
    lines=['; Ys SMS bank 02: source-only reconstruction with ROM-independent typed song data.',
           '; Unresolved sound command streams are byte-preserving, NOT decoded audio semantics.',
           'org $8000']
    pc=CPU
    while pc<BOTTOM:
        if pc in label_list:lines.append(label_list[pc]+':')
        if pc in instructions:
            mnemonic,n=instructions[pc];lines.append('    '+mnemonic);pc+=n;continue
        if pc in word_starts:
            w=int.from_bytes(raw[pc-CPU:pc-CPU+2],'little')
            lines.append(f'    dw ${w:04X}');pc+=2;continue
        next_bound=min([p for p in label_list if p>pc]+[p for p in instructions if p>pc]+[p for p in word_starts if p>pc]+[BOTTOM])
        n=min(12,next_bound-pc)
        if n<1:raise ValueError('Bank2 mixed assembly boundary conflict')
        lines.append('    db '+', '.join(f'${v:02X}' for v in raw[pc-CPU:pc-CPU+n]));pc+=n
    return '\n'.join(lines)+'\n'


def capture(rom,root=ROOT):
    if len(rom)!=0x40000 or sha(rom)!=EXPECTED_SHA:raise ValueError('Incorrect source ROM SHA256')
    data=rom[2*SIZE:3*SIZE]
    def read(a,b):return data[a-CPU:b-CPU]
    def wordlist(a,b):return [int.from_bytes(read(p,p+2),'little') for p in range(a,b,2)]
    def sliced(ptr,stop):return [{'start':p,'bytes':list(read(p,ptr[i+1] if i+1<len(ptr) else stop))} for i,p in enumerate(ptr)]
    songs=json.loads((root/'phase21/source.json').read_text())['bank2_variable_descriptors']
    new={
        'schema':'ys-wholebank02-sound-v1',
        'init_register_sequence':list(read(0x81B1,0x81D9)),
        'dispatch_targets':wordlist(0x8600,0x8628),
        'channel_constants':list(read(0x8878,0x8883)),
        'psg_note_periods':wordlist(*PSG),
        'fm_note_registers':wordlist(*FM),
        'sequence_sentinel':read(0x8B7C,0x8B7D)[0],
        'sequence_pointers':wordlist(*SEQ_PTRS),
        'sequences':sliced(wordlist(*SEQ_PTRS),SEQ_DATA[1]),
        'shape_pointers':wordlist(*SHAPE_PTRS),
        'shapes':sliced(wordlist(*SHAPE_PTRS),SHAPE_DATA[1]),
        'event_and_instrument_bytes_hex':read(0x8CFE,0xAA77).hex(),
        'event_stream_bytes_hex':read(0xAD80,0xB319).hex(),
        'variable_event_bodies':[{'index':r['index'],'start':r['address']+1+9*len(r['channels']),
          'end_exclusive':r['next_address'],
          'unresolved_event_bytes':list(read(r['address']+1+9*len(r['channels']),r['next_address']))} for r in songs],
        'post_song_data_hex':read(0xB6E8,0xBE57).hex(),
        'bank_end_ff_count':425,
        'evidence_note':'PSG/FM note periods are named from matching engine references; command streams are unresolved. Music header pointers are validated by Phase21. Exact bank source build does not certify audio playback.'}
    (root/DATA).parent.mkdir(parents=True,exist_ok=True)
    (root/DATA).write_text(json.dumps(new,indent=1)+'\n')
    prior=known(root);new_code=decoded_code(root)
    # Hash data captured from ROM ranges not yet claimed by prior sources/code.
    positions=set(range(CPU,BOTTOM))-set(prior)-set(new_code)
    new_data=bytes(read(pc,pc+1)[0] for pc in sorted(positions))
    dig={'bank_sha256':sha(data),'new_code_sha256':sha(bytes(new_code[p] for p in sorted(new_code))),
         'new_data_sha256':sha(new_data),'prior_source_bytes':len(prior),
         'new_code_bytes':len(new_code),'new_data_bytes':len(new_data),
         'new_source_bytes':len(new_code)+len(new_data)}
    (root/DIGEST).write_text(json.dumps(dig,indent=2)+'\n')
    return dig


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture',type=Path)
    p.add_argument('--verify-rom',type=Path)
    p.add_argument('--verify-mixed',action='store_true')
    p.add_argument('--out-bank',type=Path)
    a=p.parse_args()
    if a.capture:print('Source extracted:',capture(a.capture.read_bytes()))
    blob=full_bank()
    if a.verify_mixed:
        asm=mixed_source()
        if assemble_mixed(asm)!=blob:raise ValueError('Independent mixed-source bank2 assembly mismatch')
        print('Bank2 Z80/DB/DW mixed source matches',len(blob),'bytes')
    if a.verify_rom:
        full=a.verify_rom.read_bytes()
        if len(full)!=0x40000 or sha(full)!=EXPECTED_SHA or blob!=full[2*SIZE:3*SIZE]:raise ValueError('Bank2 ROM mismatch')
    if a.out_bank:a.out_bank.write_bytes(blob)
    print('Source-only bank2',len(blob),'bytes SHA256',sha(blob))
if __name__=='__main__':main()
