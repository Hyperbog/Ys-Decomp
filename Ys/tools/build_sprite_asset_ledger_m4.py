#!/usr/bin/env python3
"""Generate ROM-independent sprite graphics/layout ownership and consumer evidence.

Consumer references originate from already ROM-matched fixed-bank assembly.
Literal addresses do NOT by themselves prove runtime mapper state.
"""
import argparse
import json
from pathlib import Path
from build_sms_phase14 import ROOT
from whole_bank06 import DATA, LAYOUT_A,LAYOUT_B,new_chunks

OUT=ROOT/'wholebank06/asset_ledger.json'
def build(root=ROOT):
    meta=json.loads((root/DATA).read_text())
    _,segments=new_chunks(root)
    sources=[]
    for name in ('src/wholebank00/new_code.asm',):
        for idx,line in enumerate((root/name).read_text().splitlines(),1):
            source=line.split(';',1)[0].strip().lower()
            for addr,purpose in (('$9c18','visual-data entry'),('$ba5b','sprite-layout pointer directory')):
                if source==f'ld hl,{addr}':
                    sources.append({'source':name,'line':idx,'asm':source,
                                    'address':addr[1:].upper(),
                                    'target_bank_candidate':6,
                                    'confidence':'instruction literal only; bank mapper state unverified',
                                    'context':purpose})
    if len(sources)!=2:raise ValueError('Expected two anchored fixed-bank asset references')
    counts=[len(v['triplets']) for v in meta['sprite_layouts_a']+meta['sprite_layouts_b']]
    if counts!=[13,14,13,8,10,10,10]:raise ValueError('Sprite layout shape drift')
    return {'schema':'ys-bank6-sprite-asset-ledger-v1',
        'bank':6,'source_only_bytes':16384,
        'previously_source_backed_bytes':7192,
        'newly_source_backed_bytes':9192,
        'unresolved_visual_bytes':7408,
        'indexed_tile_bytes':1520,
        'layout_pointer_bytes':16,
        'layout_count_bytes_plus_triplets':241,
        'padding_bytes':7,
        'layout_record_counts':counts,'layout_total_triplets':sum(counts),
        'layout_directories':{'A':meta['layout_directory_a'],'B':meta['layout_directory_b']},
        'fixed_bank_literals':sources,
        'source_segments':segments,
        'confidence_notes':['Sprite count-prefix and three-byte record sizing are mechanically verified.',
            'Graphics byte lanes are storage subdivisions; original pixel-bit interpretation remains uncertain.',
            'Bank 0 contains instructions loading these two bank6 asset addresses. Active bank6 mapping at the call sites is not proven by the literal alone.']}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check',action='store_true')
    ap.add_argument('--output',type=Path,default=OUT)
    a=ap.parse_args();report=build()
    if a.check:
        if json.loads(a.output.read_text())!=report:raise ValueError('Bank6 asset ledger changed')
    else:a.output.write_text(json.dumps(report,indent=2)+'\n')
    print('Bank6 graphic lanes',report['unresolved_visual_bytes'],'layout triplets',report['layout_total_triplets'],
          'fixed-bank asset-address literals',len(report['fixed_bank_literals']))
if __name__=='__main__':main()
