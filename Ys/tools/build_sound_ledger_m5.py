#!/usr/bin/env python3
"""ROM-independent sound-engine code -> resource and hardware cross-references."""
import argparse
import json
from pathlib import Path
from build_sms_phase14 import ROOT, SOURCES
from z80_roundtrip_phase10 import encode
from whole_bank02 import full_bank,sha

TABLE_TARGETS={
    0x8A58:'psg_note_periods_73',
    0x8AEA:'fm_note_registers_73',
    0x8B7D:'sequence_directory_17',
    0x8C90:'song_directory_55',
}
PORTS={0x7F:'psg_data',0xF0:'ym2413_register_select',0xF1:'ym2413_register_data'}

def ledger(root=ROOT):
    bank=full_bank(root)
    refs=[];ops=[]
    for source,b in SOURCES:
        if b!=2:continue
        pc=None
        for line in (root/source).read_text().splitlines():
            s=line.split(';',1)[0].strip()
            if not s or s.endswith(':'):continue
            if s.lower().startswith('org '):pc=int(s.split('$',1)[1],16);continue
            if pc is None:raise ValueError('Unanchored audio mnemonic')
            bytes_=encode(s,pc)
            if bank[pc-0x8000:pc-0x8000+len(bytes_)]!=bytes_:raise ValueError('Sound source/ROM identity changed')
            operand=s.lower().replace(' ','')
            if operand.startswith('ldhl,$'):
                try:target=int(operand.partition('$')[2],16)
                except ValueError:target=-1
                if target in TABLE_TARGETS:
                    refs.append({'bank':2,'cpu':f'{pc:04X}','rom_file_offset':f'{2*0x4000+pc-0x8000:05X}',
                                 'table_cpu':f'{target:04X}','table_kind':TABLE_TARGETS[target]})
            if operand.startswith('out($') and operand.endswith('),a'):
                try:port=int(operand[5:-3],16)
                except ValueError:port=-1
                if port in PORTS:
                    ops.append({'bank':2,'cpu':f'{pc:04X}',
                        'rom_file_offset':f'{2*0x4000+pc-0x8000:05X}',
                        'io_port':f'{port:02X}','hardware_role':PORTS[port]})
            pc+=len(bytes_)
    if len(refs)<5 or len(ops)<25:raise ValueError('Sound-engine linkage unexpectedly sparse')
    return {'schema':'ys-m5-static-sound-links-v1','bank2_sha256':sha(bank),
         'evidence':'ROM-matched source mnemonics only; no full music execution trace',
         'lookup_references':refs,'hardware_writes':ops,
         'lookup_reference_count':len(refs),'hardware_write_instruction_count':len(ops),
         'full_audio_runtime_verified':False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check',action='store_true')
    p.add_argument('--report',type=Path,default=ROOT/'wholebank02/static_sound_links.json')
    args=p.parse_args()
    output=ledger()
    if args.check:
        if json.loads(args.report.read_text())!=output:raise ValueError('Sound link ledger drift')
    else:args.report.write_text(json.dumps(output,indent=2)+'\n')
    print('Sound lookups',output['lookup_reference_count'],'hardware output instruction sites',output['hardware_write_instruction_count'])
if __name__=='__main__':main()
