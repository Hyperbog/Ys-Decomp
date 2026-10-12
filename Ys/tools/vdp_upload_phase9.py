#!/usr/bin/env python3
"""Phase 9: ROM-anchored bank-3 -> Mode-4 VDP expansion at CPU $0BA1.

The uploader emits each source byte followed by zero, for 16*C source
bytes. Parse four caller argument triples from *instruction bytes*, not
from notes or a generated listing. No emulator timing claim is made.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = json.loads((ROOT/'manifest.json').read_text())['sha256']
# Pre-call immediate operand locations; each call has LD HL,nn / LD DE,nn / LD C,n.
CALLS = [
    (0x1DC0,0x1DC3,0x1DC6,0x1DC8),
    (0x3C94,0x3C97,0x3C9A,0x3C9C),
    (0x3C9F,0x3CA2,0x3CA5,0x3CA7),
    (0x3D8F,0x3D92,0x3D95,0x3D97),
]
UPLOADER_ROM = bytes.fromhex('3e 03 32 ff ff ef 06 10 7e d3 be 23 af 00 d3 be 10 f6 0d 20 f1 c9')


def w(rom,p):return int.from_bytes(rom[p:p+2],'little')


def analyze(rom):
    assert hashlib.sha256(rom).hexdigest()==SOURCE_SHA, 'ROM fingerprint differs'
    assert rom[0xBA1:0xBB7]==UPLOADER_ROM, 'Uploader instruction encoding changed'
    assert rom[0x28:0x30]==bytes.fromhex('f3 7b d3 bf 7a d3 bf fb'), 'RST28 VDP command sequence changed'
    rows=[]
    union=set()
    for hlp,dep,cp,call in CALLS:
        assert rom[hlp] == 0x21 and dep==hlp+3, 'LD HL,nn expected'
        assert rom[dep] == 0x11 and cp==dep+3, 'LD DE,nn expected'
        assert rom[cp] == 0x0E and call==cp+2, 'LD C,n expected'
        assert rom[call:call+3] == bytes.fromhex('cd a1 0b'), 'CALL uploader expected'
        hl,de,count=w(rom,hlp+1),w(rom,dep+1),rom[cp+1]
        assert 0x8000<=hl<0xC000 and de&0xC000 == 0x4000, 'Unsupported ROM/VDP source mode'
        start = 3*0x4000 + hl - 0x8000
        end = start + count*16
        assert 0xC000<=start<end<=0x10000, 'Source exceeds bank3'
        source=rom[start:end]
        output=bytes(c for v in source for c in (v,0))
        assert len(output)==count*32
        assert output[1::2]==bytes(len(source)) and output[::2]==source
        # These are 32-byte SMS Mode-4 destination tiles, with planes 1/3 zero.
        assert all(output[y+1]==0 and output[y+3]==0 for y in range(0,len(output),4))
        vram_address=de & 0x3fff
        assert vram_address+len(output)<=0x4000
        union.update(range(start,end))
        rows.append({
            'call_cpu':f'{call:04X}', 'source_cpu':f'{hl:04X}',
            'source_physical_start':f'{start:05X}', 'source_end_exclusive':f'{end:05X}',
            'source_bytes':len(source), 'vdp_command':f'{de:04X}',
            'vram_start':f'{vram_address:04X}',
            'vram_end_exclusive':f'{vram_address+len(output):04X}',
            'mode4_output_tiles':count,'vdp_output_bytes':len(output),
            'source_sha256':hashlib.sha256(source).hexdigest(),
            'vdp_output_sha256':hashlib.sha256(output).hexdigest(),
        })
    first,last=min(union),max(union)+1
    assert len(rows)==4 and first==0xD14A and last==0xD5EA and len(union)==1184
    assert union==set(range(first,last))
    # Every source byte was already within Phase7/Phase8 survey; no new footprint.
    assert all(0xD000<=p<0xD600 for p in union)
    result={
        'source_sha256':SOURCE_SHA,
        'code_anchor':'0BA1..0BB6: selects $FFFF=3; RST $28; C iterations of 16 source bytes, each output to $BE with an interleaved zero',
        'vdp_uploads':rows,
        'total_source_bytes_with_repeats':sum(r['source_bytes'] for r in rows),
        'distinct_source_bytes':len(union),
        'source_union_start':f'{first:05X}', 'source_union_end_exclusive':f'{last:05X}',
        'total_vdp_output_bytes_with_repeats':sum(r['vdp_output_bytes'] for r in rows),
        'distinct_new_rom_bytes':0,
        'scope':'Static callsite arguments and emitted byte stream; no emulator timing/graphics palette confirmation',
        'correction':'Phase8 native-4bpp interpretation is not established for source spans expanded at runtime; they should be described as 16-byte source tile streams',
    }
    return json.dumps(result,indent=2)+'\n',result


def main():
    p=argparse.ArgumentParser()
    p.add_argument('rom',type=Path)
    x=p.add_mutually_exclusive_group(required=True)
    x.add_argument('--write',action='store_true')
    x.add_argument('--check',action='store_true')
    args=p.parse_args()
    out,info=analyze(args.rom.read_bytes())
    dest=ROOT/'phase9/vdp_uploads.json'
    if args.write:dest.write_text(out)
    else:assert dest.read_text()==out,'VDP report changed'
    print('PASS Phase9: 4 upload sites, 1184 distinct source bytes,',info['total_vdp_output_bytes_with_repeats'],'mode4 VDP bytes')

if __name__=='__main__':
    try:main()
    except (AssertionError,ValueError,IndexError,OSError) as e:sys.exit('FAIL Phase9 '+str(e))
