#!/usr/bin/env python3
"""Phase 16: schema-driven ROM record source. Capture requires a reference ROM;
rebuild needs ONLY committed JSON. These are transformed game data, not emulator traces.
"""
import argparse
import hashlib
import json
from pathlib import Path
from source_tables_phase15 import assemble_data
from build_sms_phase14 import validated_rom, offset

ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/'phase16/records.json'
MODULES={4:'src/phase16/bank04_records.asm',6:'src/phase16/bank06_records.asm',7:'src/phase16/bank07_secondary.asm'}

def digest(data):return hashlib.sha256(bytes(data)).hexdigest()
def read_json(relative):return json.loads((ROOT/relative).read_text())
def ihex(s):return int(s,16)

def capture(rom):
    validated_rom(rom)
    b6=read_json('phase11/bank6_records.json')
    b7=read_json('phase13/graphics_directory.json')
    p12=read_json('phase12/sprite_pipeline.json')
    p8=read_json('phase8/mapper_audit.json')['bank4_indexed_table']
    result={'schema':'ys-phase16-record-sources-v1','rom_sha256':digest(rom),'bank6_sprite_records':[],
            'bank7_secondary_records':[], 'sprite_offset_tables':[], 'bank4_index_records':[]}
    for entry in b6['records_by_directory_index']:
        st,en=ihex(entry['rom_start']),ihex(entry['rom_end_exclusive'])
        v=rom[st:en]; count=v[0]
        if len(v)!=1+3*count or count!=entry['elements'] or digest(v)!=entry['sha256']:raise ValueError('bank6 record mismatch')
        result['bank6_sprite_records'].append({'index':entry['index'],'cpu':entry['cpu_address'],
           'delta_y':list(v[1:1+count]), 'delta_x_and_tile':[[v[1+count+i*2],v[2+count+i*2]] for i in range(count)]})
    a=rom[0x18080:0x19932]
    if digest(a)!=b6['record_payload_sha256']:raise ValueError('bank6 aggregate mismatch')
    for entry in b7['graphics_records']:
        st=ihex(entry['secondary_record_cpu'])-0x8000+0x1c000
        v=rom[st:st+22]
        if len(v)!=22 or digest(v)!=entry['secondary_sha256']:raise ValueError('bank7 record mismatch')
        result['bank7_secondary_records'].append({'index':entry['index'], 'cpu':entry['secondary_record_cpu'],
                          'pairs':[[v[i],v[i+1]] for i in range(0,22,2)]})
    for name in ('fourteen_sprite_offsets','sixteen_sprite_offsets'):
        ent=p12['data_spans'][name];st,en=ihex(ent['start']),ihex(ent['end_exclusive'])
        if digest(rom[st:en])!=ent['sha256']:raise ValueError('sprite offset table mismatch')
        result['sprite_offset_tables'].append({'name':name,'cpu':f'{st-0x18000+0x8000:04X}',
                                                'pairs':[[rom[i],rom[i+1]] for i in range(st,en,2)]})
    st,en=ihex(p8['physical_start']),ihex(p8['physical_end_exclusive'])
    if en-st!=124 or digest(rom[st:en])!=p8['sha256']:raise ValueError('bank4 indexed table mismatch')
    result['bank4_index_records']=[list(rom[i:i+4]) for i in range(st,en,4)]
    return result

def segments(data):
    if data.get('schema')!='ys-phase16-record-sources-v1':raise ValueError('unknown data schema')
    if len(data['bank6_sprite_records'])!=64 or len(data['bank7_secondary_records'])!=64:return _bad('incorrect directory sizes')
    b6=read_json('phase11/bank6_records.json')['records_by_directory_index']
    b7=read_json('phase13/graphics_directory.json')['graphics_records']
    p12=read_json('phase12/sprite_pipeline.json')['data_spans']
    for name,records in [('bank6_sprite_records',b6),('bank7_secondary_records',b7)]:
        if sorted(e['index'] for e in data[name])!=list(range(64)):_bad('duplicate/out-of-range indices')
    entries=[]
    for e in data['bank6_sprite_records']:
        index=e['index']; count=len(e['delta_y']); rec=b6[index]
        if not (0<count<=255) or len(e['delta_x_and_tile'])!=count:_bad('bank6 count mismatch')
        v=[count]+e['delta_y']+[n for pair in e['delta_x_and_tile'] for n in checked_pair(pair)]
        if len(v)!=rec['bytes'] or e['cpu']!=rec['cpu_address'] or digest(v)!=rec['sha256']:_bad('bank6 payload mismatch')
        entries.append((6,ihex(e['cpu']),f'SpriteRecord_{index:02d}',v))
    for e in data['bank7_secondary_records']:
        idx=e['index']; rec=b7[idx]
        if len(e['pairs'])!=11:_bad('bank7 pair count mismatch')
        v=[n for pair in e['pairs'] for n in checked_pair(pair)]
        if len(v)!=22 or e['cpu']!=rec['secondary_record_cpu'] or digest(v)!=rec['secondary_sha256']:_bad('bank7 secondary mismatch')
        entries.append((7,ihex(e['cpu']),f'SecondaryRecord_{idx:02d}',v))
    expected={'fourteen_sprite_offsets':(0x9b29,p12['fourteen_sprite_offsets']),
              'sixteen_sprite_offsets':(0x9b7c,p12['sixteen_sprite_offsets'])}
    if {e['name'] for e in data['sprite_offset_tables']}!=set(expected):_bad('sprite offset table identity mismatch')
    for e in data['sprite_offset_tables']:
        pc,ref=expected[e['name']]
        if len(e['pairs'])*2!=ref['bytes']:_bad('offset table size mismatch')
        v=[n for pair in e['pairs'] for n in checked_pair(pair)]
        if ihex(e['cpu'])!=pc or digest(v)!=ref['sha256']:_bad('offset source mismatch')
        entries.append((6,pc,e['name'],v))
    if len(data['bank4_index_records'])!=31:_bad('bank4 table count mismatch')
    v=[n for quad in data['bank4_index_records'] for n in checked_quad(quad)]
    ref=read_json('phase8/mapper_audit.json')['bank4_indexed_table']
    if len(v)!=124 or digest(v)!=ref['sha256']:_bad('bank4 table checksum mismatch')
    entries.append((4,0x8000,'Bank04FourByteRecords',v))
    positions=set()
    for bank,pc,name,v in entries:
        for i in range(len(v)):
            at=offset(bank,pc+i)
            if at in positions:_bad(f'overlapping structured data at {at:05X}')
            positions.add(at)
    if len(positions)!=7902:_bad('unanticipated structured coverage')
    return entries

def _bad(message):raise ValueError(message)
def checked_pair(p):
    if not isinstance(p,list) or len(p)!=2:_bad('invalid two-byte pair')
    return [checked_byte(x) for x in p]
def checked_quad(p):
    if not isinstance(p,list) or len(p)!=4:_bad('invalid four-byte record')
    return [checked_byte(x) for x in p]
def checked_byte(x):
    if type(x)!=int or not 0<=x<256:_bad('invalid data byte')
    return x

def generate_sources(data):
    by_bank={bank:[] for bank in MODULES}
    for bank,pc,name,values in sorted(segments(data),key=lambda e:(e[0],e[1])):
        lines=[f'org ${pc:04X}',name+':']
        for n in range(0,len(values),16):
            lines.append('    db '+', '.join(f'${b:02X}' for b in values[n:n+16]))
        by_bank[bank].extend(lines+[''])
    return {bank:'; Ys phase 16 structured source bank %02d. Generated from semantic record arrays.\n'%bank+
            '; Names and field boundaries are inferred, not original developer symbols.\n\n'+
            '\n'.join(lines).rstrip()+'\n' for bank,lines in by_bank.items()}

def load_verified(root=ROOT):
    data=json.loads((root/'phase16/records.json').read_text())
    if data.get('rom_sha256')!=read_json('manifest.json')['sha256']:_bad('ROM source mismatch')
    sources=generate_sources(data)
    ret={}
    for bank,rel in MODULES.items():
        if (root/rel).read_text()!=sources[bank]:_bad('structured source drift '+rel)
        code,labels=assemble_data(sources[bank])
        ret[bank]={'bytes':code,'labels':labels,'source':rel}
    return ret

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture',type=Path,help='extract semantic arrays from original ROM (development only)')
    p.add_argument('--sync',action='store_true',help='regenerate DB source from committed JSON')
    p.add_argument('--verify',action='store_true')
    a=p.parse_args()
    if a.capture:
        data=capture(a.capture.read_bytes()); segments(data)
        LEDGER.parent.mkdir(exist_ok=True)
        LEDGER.write_text(json.dumps(data,indent=2)+'\n')
    if a.sync or a.capture:
        for bank,text in generate_sources(json.loads(LEDGER.read_text())).items():
            target=ROOT/MODULES[bank];target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(text)
    verified=load_verified()
    print('Structured source matched:',sum(len(v['bytes']) for v in verified.values()),'bytes; banks',list(verified))
if __name__=='__main__':main()
