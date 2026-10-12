#!/usr/bin/env python3
"""Whole-system source-verified ROM overlay: independent banks 0,2,3,6,7."""
import argparse
import hashlib
import json
from pathlib import Path
from build_sms_phase14 import ROOT,validated_rom
from build_system_m4 import build as previous_build,complete_banks as old_banks,SOURCE_BYTES as OLD
from whole_bank02 import full_bank as bank02,new_data,decoded_code

SIZE=0x4000
NEW=12599
SOURCED=OLD+NEW
BANKS=[0,2,3,6,7]

def sha(b):return hashlib.sha256(b).hexdigest()

def complete_banks(root=ROOT):
    b=old_banks(root)
    b[2]=bank02(root)
    if sorted(b)!=BANKS or any(len(x)!=SIZE for x in b.values()):raise ValueError('Five-bank source ownership drift')
    return b

def build(rom,root=ROOT):
    validated_rom(rom)
    baseline,prior=previous_build(rom,root)
    audio=bank02(root)
    start=2*SIZE
    if baseline[start:start+SIZE]!=audio or rom[start:start+SIZE]!=audio:
        raise ValueError('Bank2 source-only ROM mismatch')
    out=bytearray(baseline);out[start:start+SIZE]=audio
    if bytes(out)!=rom:raise ValueError('Whole-ROM byte identity mismatch')
    rows=[]
    for r in prior['per_bank']:
        n=r['bank'];count=r['source_backed_bytes']+(NEW if n==2 else 0)
        if (count==SIZE)!=(n in BANKS):raise ValueError('Five-bank closure ledger disagrees')
        rows.append({'bank':n,'source_backed_bytes':count,
            'original_rom_fallback_bytes':SIZE-count,'source_only_complete':count==SIZE,
            'sha256':sha(out[n*SIZE:(n+1)*SIZE])})
    if len(rows)!=16 or sum(x['source_backed_bytes'] for x in rows)!=SOURCED:
        raise ValueError('Five-bank source byte count drift')
    _,inventory=new_data(root)
    code=decoded_code(root)
    return bytes(out),{'schema':'ys-whole-system-five-banks-v1',
        'rom_sha256':sha(out),'rom_bytes':len(out),'bank_count':16,
        'source_only_complete_banks':BANKS,'complete_source_only_bank_bytes':5*SIZE,
        'prior_source_backed_bytes':OLD,'new_source_backed_bytes':NEW,
        'new_bank2_z80_instruction_bytes':len(code),
        'new_bank2_data_bytes':NEW-len(code),'source_backed_bytes':SOURCED,
        'source_backed_pct':round(SOURCED*100/len(out),4),
        'original_rom_fallback_bytes':len(out)-SOURCED,
        'bank2_new_data_segments':inventory,
        'variable_song_event_record_count':24,
        'psg_note_register_words':73,'fm_note_register_words':73,
        'sequence_directory_words':17,'shape_directory_words':5,
        'source_only_complete_rom':False,'external_wla_dx_verified':False,
        'full_emulator_verified':False,'sound_engine_fully_semantically_decoded':False,
        'per_bank':rows,'limitations':[
            'Five banks reconstruct without original ROM; eleven remaining banks still require original-ROM fallback.',
            'Most bank2 event payloads and late-bank data remain byte-preserving but semantically unresolved.',
            'No complete musical playback/emulator trace has been performed, and external WLA-DX has not executed.']}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',nargs='?',type=Path)
    p.add_argument('--standalone-banks',action='store_true')
    p.add_argument('--output-directory',type=Path)
    p.add_argument('--out',type=Path)
    p.add_argument('--check',action='store_true')
    p.add_argument('--report',type=Path,default=ROOT/'whole_system/build_report_m5.json')
    args=p.parse_args()
    if args.standalone_banks:
        bs=complete_banks()
        if args.output_directory:
            args.output_directory.mkdir(parents=True,exist_ok=True)
            for n,b in bs.items():(args.output_directory/f'bank{n:02}.bin').write_bytes(b)
        for n,b in sorted(bs.items()):print(f'Bank {n:02} source-only {len(b)} bytes SHA256 {sha(b)}')
        return
    if args.rom is None:p.error('Full ROM overlay requires the locally owned original ROM')
    if args.out and args.out.resolve()==args.rom.resolve():p.error('Refusing to overwrite user ROM')
    rebuilt,report=build(args.rom.read_bytes())
    if args.check:
        if json.loads(args.report.read_text())!=report:raise ValueError('M5 bank ledger changed')
    else:args.report.write_text(json.dumps(report,indent=2)+'\n')
    if args.out:args.out.write_bytes(rebuilt)
    print('Complete source-only banks',report['source_only_complete_banks'],
          'source-backed',SOURCED,'fallback',report['original_rom_fallback_bytes'],
          'full sha256',report['rom_sha256'])
if __name__=='__main__':main()
