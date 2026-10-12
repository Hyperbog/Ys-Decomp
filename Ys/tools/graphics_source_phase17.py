#!/usr/bin/env python3
"""Phase 17 reversible pixel-source reconstruction, independent of ROM at build time.

Capture needs the user-provided ROM; regenerate/verify reads only committed
pixel rows and prior verified pointer/digest ledgers. This embeds derived game
art assets in the project; it is not a source-only ROM or emulator trace.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
from build_sms_phase14 import validated_rom, offset
from mode4_tiles_phase8 import decode_tile, encode_tile
from source_tables_phase15 import assemble_data

ROOT = Path(__file__).resolve().parents[1]
LEDGER = 'phase17/graphics.json'
MODULES = {3: 'src/phase17/bank03_tiles.asm', 7: 'src/phase17/bank07_graphics.asm'}
ROM_SHA = '02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9'


def read_json(root, path):
    return json.loads((root / path).read_text(encoding='utf-8'))


def digest(value):
    return hashlib.sha256(bytes(value)).hexdigest()


def capture(rom, root=ROOT):
    validated_rom(rom)
    refs = read_json(root, 'phase13/graphics_directory.json')['graphics_records']
    bank7 = []
    for ref in refs:
        pc = int(ref['graphics_source_cpu'], 16)
        length = ref['graphics_bytes']
        start = offset(7, pc)
        payload = rom[start:start+length]
        if digest(payload) != ref['graphics_sha256'] or length % 8:
            raise ValueError('bank7 graphics source digest/length mismatch')
        bank7.append({'index':ref['index'], 'cpu':ref['graphics_source_cpu'],
                      'rows': [f'{byte:08b}' for byte in payload]})
    bank3=[]
    for i in range(176):
        start=0xC000+32*i
        pixels=decode_tile(rom[start:start+32])
        bank3.append({'index':i, 'cpu':f'{0x8000+32*i:04X}',
                      'rows':[''.join(f'{v:X}' for v in pixels[y*8:y*8+8]) for y in range(8)]})
    data={'schema':'ys-phase17-graphics-sources-v1', 'rom_sha256':ROM_SHA,
          'bank3_mode4_tiles':bank3, 'bank7_mono_graphics':bank7}
    segments(data,root)
    return data


def segments(data,root=ROOT):
    if data.get('schema')!='ys-phase17-graphics-sources-v1' or data.get('rom_sha256')!=ROM_SHA:
        raise ValueError('wrong graphics ledger schema/ROM identity')
    bank3=data.get('bank3_mode4_tiles',[])
    bank7=data.get('bank7_mono_graphics',[])
    if len(bank3)!=176 or len(bank7)!=64:
        raise ValueError('incorrect graphics record count')
    if [t['index'] for t in bank3]!=list(range(176)) or [r['index'] for r in bank7]!=list(range(64)):
        raise ValueError('out-of-order/duplicated graphics indices')
    parts=[]
    for tile in bank3:
        if tile['cpu']!=f'{0x8000+32*tile["index"]:04X}' or len(tile['rows'])!=8:
            raise ValueError('incorrect bank3 tile address or row count')
        if any(not isinstance(s,str) or not re.fullmatch('[0-9A-F]{8}',s) for s in tile['rows']):
            raise ValueError('invalid 4bpp pixel index row')
        pixels=[int(ch,16) for row in tile['rows'] for ch in row]
        parts.append((3,int(tile['cpu'],16),f'Mode4Tile_{tile["index"]:03d}',encode_tile(pixels)))
    for lo,hi in ((0xC000,0xD000),(0xD000,0xD600)):
        selected=b''.join(blob for bank,pc,_,blob in parts if bank==3 and lo<=offset(bank,pc)<hi)
        entry=next(b for b in read_json(root,'phase8/tile_metadata.json')['blocks'] if int(b['file_start'],16)==lo)
        if len(selected)!=hi-lo or digest(selected)!=entry['sha256']:
            raise ValueError('bank3 graphics block digest mismatch')
    refs=read_json(root,'phase13/graphics_directory.json')['graphics_records']
    spans=[]
    for record,ref in zip(bank7,refs):
        if record['cpu']!=ref['graphics_source_cpu'] or len(record['rows'])!=ref['graphics_bytes']:
            raise ValueError('bank7 graphics pointer/length mismatch')
        if any(not isinstance(s,str) or not re.fullmatch('[01]{8}',s) for s in record['rows']):
            raise ValueError('invalid monochrome bit row')
        payload=bytes(int(s,2) for s in record['rows'])
        if digest(payload)!=ref['graphics_sha256']:
            raise ValueError('bank7 graphics record digest mismatch')
        pc=int(record['cpu'],16)
        spans.append((pc,pc+len(payload)))
        parts.append((7,pc,f'MonoGfx_{record["index"]:02d}',payload))
    ordered=sorted(spans)
    if ordered[0][0]!=0x8877 or ordered[-1][1]!=0xAFBF or any(a[1]!=b[0] for a,b in zip(ordered,ordered[1:])):
        raise ValueError('bank7 records have gaps or overlaps')
    owners=set()
    for bank,pc,_,blob in parts:
        for j in range(len(blob)):
            off=offset(bank,pc+j)
            if off in owners:raise ValueError('overlapping graphics sources')
            owners.add(off)
    if len(owners)!=15688:
        raise ValueError('unexpected total graphics bytes')
    return parts


def generated_sources(data,root=ROOT):
    out={}
    parts=segments(data,root)
    for bank,rel in MODULES.items():
        lines=[f'; Ys SMS bank {bank:02d} — generated from editable 8-pixel source rows.',
               '; These contain proprietary game graphics data from the user-supplied ROM.',
               '; Pixel layout verified against earlier ROM digests; VRAM use not emulator-traced.', '']
        for _,pc,name,payload in sorted((s for s in parts if s[0]==bank),key=lambda s:s[1]):
            lines.extend([f'org ${pc:04X}',name+':'])
            for n in range(0,len(payload),16):
                lines.append('    db '+', '.join(f'${b:02X}' for b in payload[n:n+16]))
            lines.append('')
        out[bank]='\n'.join(lines).rstrip()+'\n'
    return out


def load_verified(root=ROOT):
    data=read_json(root,LEDGER)
    expected=generated_sources(data,root)
    out={}
    for bank,path in MODULES.items():
        if (root/path).read_text(encoding='utf-8')!=expected[bank]:
            raise ValueError('graphics source drift: '+path)
        bytes_by_pc,labels=assemble_data(expected[bank])
        out[bank]={'bytes':bytes_by_pc,'labels':labels,'source':path}
    if sum(len(v['bytes']) for v in out.values())!=15688:
        raise ValueError('assembled graphics total mismatch')
    return out


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--capture',type=Path)
    ap.add_argument('--sync',action='store_true')
    ap.add_argument('--verify',action='store_true')
    a=ap.parse_args()
    if a.capture:
        ROOT.joinpath(LEDGER).write_text(json.dumps(capture(a.capture.read_bytes()),indent=2)+'\n',encoding='utf-8')
    if a.capture or a.sync:
        for bank,source in generated_sources(read_json(ROOT,LEDGER)).items():
            dest=ROOT/MODULES[bank];dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_text(source,encoding='utf-8')
    matched=load_verified()
    print('Phase17 independent graphics source:',sum(len(x['bytes']) for x in matched.values()),'bytes')
if __name__=='__main__':main()
