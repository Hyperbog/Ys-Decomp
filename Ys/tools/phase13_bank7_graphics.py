#!/usr/bin/env python3
"""Audit bank-7 map-cell graphics, unrolled VDP-side Z80 transfer code.

User-provided ROM stays outside Git. Records are described by digest and length;
the generated source is Z80 mnemonics, never raw proprietary asset payloads.
Static mapper/root evidence, not a runtime emulator execution trace.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from z80_regions import decode
from z80_roundtrip_phase10 import encode, assemble
from rebuild_phase10 import render
from bank_trace_phase8 import ROOTS, walk_bank

ROOT = HERE.parent
ROM_SHA = json.loads((ROOT/'manifest.json').read_text())['sha256']
SOURCE = ROOT/'src'/'phase13'/'bank07_unrolled_vdp.asm'
REPORT = ROOT/'phase13'/'graphics_directory.json'
BANK = 7
BASE = BANK * 0x4000


def word(raw, at):
    return int.from_bytes(raw[at:at+2], 'little')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def generate(raw):
    if len(raw) != 0x40000 or sha(raw) != ROM_SHA:
        raise ValueError('Original Ys SMS ROM fingerprint mismatch')
    bank = raw[BASE:BASE+0x4000]
    # Entry from fixed bank $01C8 -> CPU $8819, and from $0DD7 -> $86C1:
    # bank-7 mapping evidence already checked in Phase 8. Rooted CFG is contiguous.
    code, owner, unresolved = walk_bank(raw, BANK, ROOTS[BANK])
    if unresolved:
        raise AssertionError(f'Bank 7 has unresolved CFG edges: {unresolved}')
    oldset = set(owner)
    assert len(oldset) == 438
    assert oldset == set(range(BASE+0x6C1, BASE+0x877))
    # $8856 reads flags/index from C199, scales it by four, then reads both
    # 16-bit words at $8000+index*4. PUSH DE / RET transfers to the first word.
    assert raw[BASE+0x856:BASE+0x876] == bytes.fromhex(
        '21 99 C1 7E CB BE 87 D0 87 6F 26 80 3E 20 D3 BF '
        '3E 74 D3 BF 0E BE 5E 2C 56 2C 7E 2C 66 6F AF D5')
    assert raw[BASE+0x876] == 0xC9
    # $86C1 stores index=(x&7)+8*(y&7), with bit7 as update-needed flag.
    assert raw[BASE+0x6D2:BASE+0x6E7] == bytes.fromhex(
        'E6 07 07 07 07 5F 3A 82 C1 80 E6 07 B3 21 99 C1 BE C8 F6 80 77')
    # Phase8's bank-7 sprite/map updater reads 64 22-byte records from $8100
    # using the $8729 11-iteration loop, two source bytes per iteration.
    assert raw[BASE+0x71C:BASE+0x724] == bytes.fromhex('26 81 08 87 6F 5E 2C 56')
    assert raw[BASE+0x729:BASE+0x72B] == bytes.fromhex('06 0B')
    assert raw[BASE+0x769:BASE+0x76B] == bytes.fromhex('10 C0')
    assert raw[BASE+0x874] == 0xAF  # XOR A: three OUT writes carry zero plane bytes
    data_dirs=[]
    tile_lengths=[]
    for idx in range(64):
        pos = idx*4
        executable = word(bank,pos)
        payload = word(bank,pos+2)
        assert 0x8180 <= executable <= 0x8300 and (executable-0x8180)%0x40 == 0
        assert 0x8877 <= payload < 0xAFBF
        assert (0x86C0-executable)%8 == 0
        source_bytes = (0x86C0-executable)//8
        assert 120 <= source_bytes <= 168 and source_bytes%8 == 0
        tile_lengths.append(source_bytes)
        secondary = word(bank,0x100+idx*2)
        assert secondary==0xAFBF+idx*22
        data_dirs.append({
            'index':idx,
            'unrolled_entry_cpu':f'{executable:04X}',
            'graphics_source_cpu':f'{payload:04X}',
            'graphics_bytes':source_bytes,
            'expanded_4bpp_bytes':source_bytes*4,
            'mode4_tiles':source_bytes//8,
            'graphics_sha256':sha(bank[payload-0x8000:payload-0x8000+source_bytes]),
            'secondary_record_cpu':f'{secondary:04X}',
            'secondary_record_bytes':22,
            'secondary_sha256':sha(bank[secondary-0x8000:secondary-0x8000+22])
        })
    # Pointer-selected records fill the entire payload interval with no gaps or
    # overlap. This is a stronger condition than merely recognizing non-$FF data.
    ordered=sorted((int(d['graphics_source_cpu'],16),
                    int(d['graphics_source_cpu'],16)+d['graphics_bytes'],
                    d['index']) for d in data_dirs)
    cursor=0x8877
    for lo,hi,idx in ordered:
        assert lo==cursor,f'Graphics record {idx} gap/overlap at {cursor:04X}'
        cursor=hi
    assert cursor==0xAFBF
    assert sum(tile_lengths)==0xAFBF-0x8877==10056
    assert word(bank,0x100)==0xAFBF
    assert int(data_dirs[-1]['secondary_record_cpu'],16)+22==0xB53F
    # Decoder and independent assembler must BOTH reconstruct the 168 8-byte
    # unrolled groups (OUTI; OUT (BE),A x3) and final RET at $86C0.
    pattern=bytes.fromhex('ED A3 D3 BE D3 BE D3 BE')
    assert bank[0x180:0x6C0]==pattern*168
    assert bank[0x6C0]==0xC9
    rows=[]
    cursor=BASE+0x180
    while cursor<BASE+0x6C1:
        cpu=0x8000+cursor-BASE
        end,inst=decode(raw,cursor,(2-BANK)*0x4000)
        assert end<=BASE+0x6C1
        chunk=raw[cursor:end]
        assert encode(inst,cpu)==chunk
        rows.append((cursor,cpu,inst,chunk,'phase13 ROM-backed unrolled VDP'))
        cursor=end
    assert len(rows)==673 and sum(len(r[3]) for r in rows)==1345
    source=render(BANK,rows)
    output,labels=assemble(source)
    assert not labels and len(output)==1345
    for rom_off,cpu,mnemonic,chunk,origin in rows:
        assert bytes(output[p] for p in range(cpu,cpu+len(chunk)))==chunk
    new_code=set(range(BASE+0x180,BASE+0x6C1))
    structured=(set(range(BASE,BASE+0x180))|
                set(range(BASE+0x877, BASE+0x353F)))
    assert len(structured)==256+128+10056+1408==11848
    assert not (structured&new_code or structured&oldset or new_code&oldset)
    assert structured|new_code|oldset==set(range(BASE,BASE+0x353F))
    assert len(structured|new_code|oldset)==13631
    # All record data remains outside repository; merely SHA and length metadata.
    report={
      'schema':'ys-phase13-bank7-graphics-v1',
      'rom_sha256':ROM_SHA,
      'physical_bank':BANK,
      'complete_accounted_span':{'start':'1C000','end_exclusive':'1F53F','bytes':13631,
         'existing_bank7_code_bytes':438,'new_instruction_bytes':1345,
         'new_structured_data_bytes':11848},
      'code':{'start':'1C180','end_exclusive':'1C6C1','instructions':673,
              'bytes':1345,'sha256':sha(raw[BASE+0x180:BASE+0x6C1]),
              'assembly_matches_ROM':True,'external_assembler_verified':False},
      'sections':{
         'grid_directory':{'start':'1C000','end_exclusive':'1C100','entries':64,'entry_width':4,
            'sha256':sha(bank[:0x100])},
         'secondary_directory':{'start':'1C100','end_exclusive':'1C180','entries':64,'entry_width':2,
            'sha256':sha(bank[0x100:0x180])},
         'graphics_source':{'start':'1C877','end_exclusive':'1EFBF','records':64,
            'bytes':10056,'tile_rows':10056,'mode4_tiles':1257,
            'sha256':sha(bank[0x877:0x2FBF])},
         'secondary_records':{'start':'1EFBF','end_exclusive':'1F53F','records':64,
            'width':22,'bytes':1408,'sha256':sha(bank[0x2FBF:0x353F])}
      },
      'transfer':{'destination_control_bytes':['20','74'],'first_control_port':'BF',
         'output_port':'BE','entry_method':'PUSH DE then RET',
         'source_bytes_per_tile':8,'output_bytes_per_source':4,
         'graphics_source_total_bytes':10056,'equivalent_expanded_bytes':40224,
         'plane_values':'one ROM byte followed by three zero bytes',
         'tile_interpretation':'SMS Mode-4 1bpp source expanded to 4bpp VRAM-compatible rows'},
      'length_histogram':{str(length):tile_lengths.count(length) for length in sorted(set(tile_lengths))},
      'graphics_records':data_dirs,
      'new_distinct_classified_bytes':13193,
      'new_distinct_assembler_matched_bytes':1345,
      'new_distinct_structured_data_bytes':11848,
      'cumulative_assembler_matched_bytes':14025,
      'cumulative_reversible_data_bytes':24028,
      'cumulative_combined_reconstruction_bytes':38053,
      'cumulative_candidate_coverage_bytes':58133,
      'cumulative_candidate_coverage_percentage':round(58133/262144*100,4),
      'limitations':['Graphics bytes and secondary records not checked in an emulator',
          'Records are reversibly bounded but not individually labelled for gameplay locations',
          'Assembly matches ROM using in-project encoder, not independent external assembler',
          'The surrounding 438-byte Phase8 code has already been counted',
          'Raw copyright-protected graphics payload bytes are absent from project']
    }
    assert report['sections']['graphics_source']['sha256']==sha(raw[BASE+0x877:BASE+0x2FBF])
    return source,report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('rom',type=Path)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write',action='store_true')
    mode.add_argument('--check',action='store_true')
    args=parser.parse_args()
    source,report=generate(args.rom.read_bytes())
    met=json.dumps(report,indent=2)+'\n'
    if args.write:
        SOURCE.parent.mkdir(parents=True,exist_ok=True)
        REPORT.parent.mkdir(parents=True,exist_ok=True)
        SOURCE.write_text(source)
        REPORT.write_text(met)
    else:
        assert SOURCE.read_text()==source,'Asm changed'
        assert REPORT.read_text()==met,'Metadata changed'
    print(f"PASS Phase13: {report['code']['instructions']} Z80 instructions / 1345 assembled bytes, "
          '11848 structured data bytes, 13631-byte contiguous bank7 span')

if __name__=='__main__':main()
