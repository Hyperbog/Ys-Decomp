#!/usr/bin/env python3
"""Phase 11: ROM-grounded sparse Z80 assembly and reversible data auditing.

Not a full ROM rebuild, external assembler, or runtime execution proof.
No original ROM bytes or graphic pixel arrays are written to the project.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
from collections import defaultdict
if __package__:
    from .z80_regions import decode
    from .z80_roundtrip_phase10 import assemble, encode
    from .rebuild_phase10 import read_listings, render
    from .bank_trace_phase8 import walk_bank
    from .mode4_tiles_phase8 import BLOCKS, decode_tile, encode_tile
else:
    from z80_regions import decode
    from z80_roundtrip_phase10 import assemble, encode
    from rebuild_phase10 import read_listings, render
    from bank_trace_phase8 import walk_bank
    from mode4_tiles_phase8 import BLOCKS, decode_tile, encode_tile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'phase11'
ASM=ROOT/'src'/'phase11_roundtrip'
ROM_SHA=json.loads((ROOT/'manifest.json').read_text())['sha256']
BOOT=re.compile(r'^([0-9A-F]{4})\s+((?:[0-9A-F]{2}\s+)+?)\s{2,}(.+)$')


def older_rows(rom):
    rows=[]
    for line in (ROOT/'src/bank00_boot.lst').read_text().splitlines():
        m=BOOT.match(line)
        if not m:continue
        off=int(m[1],16)
        raw=bytes.fromhex(m[2])
        text=m[3].strip().split(';',1)[0].strip()
        if text.startswith(('db ', 'dw ')) or 'db ' in text or not re.match(r'^[a-z]',text):
            continue
        end,disasm=decode(rom,off)
        assert rom[off:end]==raw and end==off+len(raw), f'Boot listing mismatch {off:04X}'
        rows.append((off,off,disasm,raw,'src/bank00_boot.lst'))
    for n in (2,3,4):
        conf=json.loads((ROOT/f'phase{n}/regions.json').read_text())
        for segment in conf['code']:
            start=int(segment['start'],16)
            stop=int(segment['end_exclusive'],16)
            bank=int(segment['bank'])
            slot=int(segment['slot'])
            p=start
            while p<stop:
                end,disasm=decode(rom,p,(slot-bank)*0x4000)
                assert end<=stop, f'Phase {n} region crosses at {p:05X}'
                cpu=p if p<0x8000 else 0x8000+(p&0x3fff)
                rows.append((p,cpu,disasm,rom[p:end],f'phase{n}/regions.json'))
                p=end
    return rows


def bank6_rows(rom):
    # The mapper is selected in these fixed-bank routines and is not changed
    # between the $FFFF write and the CPU slot-2 CALL or JP. Provenance is
    # local to the caller and does not assert runtime execution.
    a=rom[0x26EF:0x2710]
    b=rom[0x2BEF:0x2C05]
    assert b'\x3e\x06\x32\xff\xff' in a and b'\xcd\x32\x99' in a
    assert b'\x3e\x06\x32\xff\xff' in b and b'\xc3\x66\x99' in b
    code,owners,uncertain=walk_bank(rom,6,{0x9932:['bank0 direct call'],0x9966:['bank0 direct jump']})
    assert not uncertain
    result=[]
    for pos,(end,inst) in sorted(code.items()):
        result.append((pos,0x8000+(pos&0x3fff),inst,rom[pos:end],'bank6 rooted CFG'))
    return result


def data_audit(rom):
    # 64 entries, individually addressable by index in bank6 $9932.  $9934
    # doubles A, $9936 places the result at the base of the $8000 pointer
    # table, and $9939-$993B loads the little-endian destination.
    entry=0x19932
    assert rom[entry:entry+13]==bytes.fromhex('3A 99 C1 87 6F 26 80 7E 2C 66 6F 46 48')
    table=rom[0x18000:0x18080]
    targets=[int.from_bytes(table[i:i+2],'little') for i in range(0,len(table),2)]
    assert len(targets)==64 and all(0x8000<=t<0x9932 for t in targets)
    assert len(set(targets))==64
    # Value at $8080 is not a valid pointer: precise 128-byte boundary.
    assert int.from_bytes(rom[0x18080:0x18082],'little')>=0xc000
    return {
        'bank':6,'rom_begin':'18000','rom_end_exclusive':'18080',
        'cpu_begin':'8000','record_width':2,'entries':64,
        'unique_destinations':len(set(targets)),
        'minimum_target':f'{min(targets):04X}', 'maximum_target':f'{max(targets):04X}',
        'sha256':hashlib.sha256(table).hexdigest(),
        'targets_sha256':hashlib.sha256(b''.join(v.to_bytes(2,'little') for v in targets)).hexdigest(),
        'interpretation':'64 little-endian pointers indexed through bank6 $9932; destination payload schema unknown',
        'limitation':'No independently established maximum allowed runtime index or interpretation of payloads'
    }


def graphics_audit(rom):
    pieces=[]
    for lo,hi in BLOCKS:
        data=rom[lo:hi]
        tiles=[decode_tile(data[i:i+32]) for i in range(0,len(data),32)]
        pixels=sum((tile for tile in tiles),[])
        assert all(0<=pixel<=15 for pixel in pixels)
        rebuild=b''.join(encode_tile(t) for t in tiles)
        assert rebuild==data
        pieces.append(dict(rom_start=f'{lo:05X}',rom_end_exclusive=f'{hi:05X}',
            tiles=len(tiles),bytes=len(data),sha256=hashlib.sha256(rebuild).hexdigest()))
    return pieces


def inventory(rom):
    assert len(rom)==0x40000 and hashlib.sha256(rom).hexdigest()==ROM_SHA
    original=read_listings()
    expanded=older_rows(rom)
    expanded+=bank6_rows(rom)
    combined=original+expanded
    occupied={}
    for off,cpu,inst,raw,name in combined:
        assert 0<=off<0x40000 and raw
        assert cpu==(off if off<0x8000 else 0x8000+(off&0x3fff))
        assert encode(inst,cpu)==raw==rom[off:off+len(raw)], (name,hex(off),inst)
        end,decoder_text=decode(rom,off,0 if off<0x8000 else (2-(off>>14))*0x4000)
        assert end==off+len(raw),f'Decoder boundary mismatch {off:05X}'
        for i in range(off,off+len(raw)):
            assert i not in occupied, f'Overlapping code at {i:05X}: {name} vs {occupied[i]}'
            occupied[i]=name
    return combined,occupied,original,expanded


def report_and_sources(rom,write=False):
    rows,owners,original,added=inventory(rom)
    banks=defaultdict(list)
    for row in rows:banks[row[0]//0x4000].append(row)
    stats=[]
    for bank,entries in sorted(banks.items()):
        entries.sort()
        src=render(bank,entries)
        path=ASM/f'bank{bank:02d}.asm'
        if write:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(src)
        else:assert path.read_text()==src,f'Source snapshot changed: {path}'
        code,labels=assemble(path.read_text())
        assert not labels
        assert len(code)==sum(len(entry[3]) for entry in entries)
        for off,cpu,inst,raw,origin in entries:
            assert bytes(code[pc] for pc in range(cpu,cpu+len(raw)))==raw,f'Assembler changed: {off:05X}'
        stats.append(dict(bank=bank,instructions=len(entries),code_bytes=len(code),
                          first_offset=f'{entries[0][0]:05X}',last_offset=f'{entries[-1][0]+len(entries[-1][3])-1:05X}'))
    tiles=graphics_audit(rom)
    pointer=data_audit(rom)
    tile_offsets={i for t in tiles for i in range(int(t['rom_start'],16),int(t['rom_end_exclusive'],16))}
    ptr_offsets=set(range(0x18000,0x18080))
    assert not owners.keys()&tile_offsets and not owners.keys()&ptr_offsets
    code_bytes=set(owners)
    phase9=set().union(*(set(range(a,b)) for a,b in (
        (0x05F2,0x0624),(0x06C1,0x06D4),(0x06D4,0x06E8),(0x0BA1,0x0BB7))))
    assert phase9 <= code_bytes, 'Previously matched Phase9 routine missing from assembled union'
    additional=set().union(tile_offsets,ptr_offsets)
    report=dict(schema='ys-phase11-v1',rom_sha256=ROM_SHA,
        source='Sparse Z80 ASM generated from audited disassembly; original commercial ROM not embedded',
        external_assembler_verified=False,
        baseline_phase10b_instructions=len(original),
        baseline_phase10b_code_bytes=sum(len(x[3]) for x in original),
        additional_instructions=len(added),additional_code_bytes=sum(len(x[3]) for x in added),
        cumulative_code_instruction_count=len(rows),
        cumulative_distinct_assembler_matched_code_bytes=len(code_bytes),
        code_banks=stats,
        pointer_table=pointer,
        reversible_tile_blocks=tiles,
        separate_reencoded_data_bytes=len(additional),
        combined_distinct_code_and_reencoded_data_bytes=len(code_bytes|additional),
        new_candidate_classification_bytes=403+128,
        total_candidate_coverage_bytes=37748+403+128,
        scope='Cumulative matched code excludes raw original-ROM fill; graphics reencoding is independent of assembler, not execution verified',
        limitations=['Sparse assembly does not reproduce complete bank images or entire ROM',
            'No external assembler or emulator trace','Tile pixel interpretation does not establish runtime VRAM usage',
            'Additional bank6 code is statically rooted; pointer payloads remain unknown'])
    return json.dumps(report,indent=2)+'\n',report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('rom',type=Path)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write',action='store_true')
    mode.add_argument('--check',action='store_true')
    a=parser.parse_args()
    rom=a.rom.read_bytes()
    report,stats=report_and_sources(rom,write=a.write)
    path=OUT/'report.json'
    if a.write:
        OUT.mkdir(parents=True,exist_ok=True)
        path.write_text(report)
    else:assert path.read_text()==report,'Report snapshot differs'
    print(f"PASS Phase11: {stats['cumulative_code_instruction_count']} assembled instructions / "
          f"{stats['cumulative_distinct_assembler_matched_code_bytes']} code bytes; "
          f"{stats['separate_reencoded_data_bytes']} reversible data bytes; "
          f"{stats['combined_distinct_code_and_reencoded_data_bytes']} combined unique bytes")

if __name__=='__main__':main()
