#!/usr/bin/env python3
"""Select a bounded, bank-aware research context from verified Z80 CFG evidence.

No guessing aliases in mapper-controlled windows. Output is descriptive static
context, not a runtime trace or proof of function reachability.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAPH = ROOT/'whole_system/evidence_graph.json'
SYMBOLS = ROOT/'phase15/symbols.json'


def query(graph, bank, cpu, *, edge_limit=12, radius=4, symbols=None):
    if graph.get('schema') != 'ys-mapper-aware-evidence-graph-v1':
        raise ValueError('unsupported evidence graph schema')
    if not (0 <= bank < 16 and 0 <= cpu < 0xC000):
        raise ValueError('bank or CPU address out of range')
    if not (0 <= radius <= 20 and 1 <= edge_limit <= 100):
        raise ValueError('context bounds out of range')
    org = 0 if bank == 0 else 0x4000 if bank == 1 else 0x8000
    if not org <= cpu < org+0x4000:
        raise ValueError('physical bank and CPU address do not agree')
    physical = bank*0x4000 + cpu-org
    nid = f'{physical:05X}'
    ins = graph['instructions']
    byid = {n['id']: n for n in ins}
    node = byid.get(nid)
    if node is None:
        return {'target': {'physical_bank': bank, 'cpu': f'{cpu:04X}', 'physical': nid},
                'matched_instruction': False,
                'message': 'No already-verified source instruction starts at this offset; do not decode it speculatively.'}
    block = next(b for b in graph['blocks'] if b['offset'] <= physical < b['offset']+b['byte_count'] and b['bank']==bank)
    peer_ids = [n['id'] for n in ins if n['bank']==bank and block['offset'] <= n['offset'] < block['offset']+block['byte_count']]
    idx = peer_ids.index(nid)
    near = [byid[k] for k in peer_ids[max(0,idx-radius):idx+radius+1]]
    incoming = [e for e in graph['edges'] if e.get('to_instruction') == nid and e['kind'] != 'fallthrough']
    outgoing = [e for e in graph['edges'] if e['from'] == nid]
    block_effects = [e for e in graph['effects'] if e['instruction_id'] in peer_ids]
    named = [s for s in (symbols or {}).get('symbols', [])
             if s.get('address_space') == 'ROM' and s.get('physical_bank') == bank
             and s.get('cpu_address') == f'{cpu:04X}']
    return {'target': {'physical_bank':bank, 'cpu':f'{cpu:04X}', 'physical':nid},
            'matched_instruction':True, 'instruction':node, 'block':block,
            'nearby_instructions':near,
            'incoming_direct_references':incoming[:edge_limit], 'incoming_count':len(incoming),
            'outgoing':outgoing[:edge_limit], 'effects_in_block':block_effects[:edge_limit],
            'symbols_at_entry':named,
            'limitations':['Does not establish runtime reachability.',
                           'Mapper-selected ROM bank is uncertain unless backed by separate evidence.',
                           'Only already-matched instruction starts are indexed.']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--graph',type=Path,default=DEFAULT_GRAPH)
    p.add_argument('--bank',required=True,type=lambda s:int(s,0))
    p.add_argument('--cpu',required=True,type=lambda s:int(s,0))
    p.add_argument('--limit',type=int,default=12)
    p.add_argument('--radius',type=int,default=4)
    p.add_argument('--output',type=Path)
    opts=p.parse_args()
    result=query(json.loads(opts.graph.read_text()),opts.bank,opts.cpu,edge_limit=opts.limit,
                 radius=opts.radius,symbols=json.loads(SYMBOLS.read_text()))
    text=json.dumps(result,indent=2,sort_keys=True)+'\n'
    if opts.output:opts.output.write_text(text)
    print(text,end='')

if __name__=='__main__':main()
