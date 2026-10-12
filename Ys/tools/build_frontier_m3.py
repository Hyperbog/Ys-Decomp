#!/usr/bin/env python3
"""Derive fixed-bank0 missing instruction-entry candidates from expanded CFG."""
import argparse
import json
from collections import defaultdict
from pathlib import Path
from build_sms_phase14 import ROOT

def build(graph):
    missing=defaultdict(set)
    existing={int(n['pc'],16) for n in graph['instructions'] if n['bank']==0}
    for edge in graph['edges']:
        if edge.get('resolution')=='fixed_bank0' and edge.get('to_instruction') is None:
            missing[edge['to_cpu']].add(edge['from'])
    rows=[]
    for target,refs in sorted(missing.items()):
        pc=int(target,16)
        rows.append({'cpu':target,'incoming':sorted(refs),
                     'status':'missing_verified_instruction_start',
                     'comment':'Needs overlapping-entry or code/data investigation; not automatically classified'})
    return {'schema':'ys-m3-fixed-bank-frontier-v1',
            'source_graph':'whole_system/evidence_graph_m3.json',
            'missing_fixed_bank0_targets':rows,
            'count':len(rows),
            'previous_m2_frontier_closed':['06E8','0702','0718','0739','07D5'],
            'qualification':'Static branch targets do not imply code starts without independent boundary evidence.'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check',action='store_true')
    p.add_argument('--graph',type=Path,default=ROOT/'whole_system/evidence_graph_m3.json')
    p.add_argument('--output',type=Path,default=ROOT/'whole_system/frontier_m3.json')
    a=p.parse_args();data=build(json.loads(a.graph.read_text()))
    if a.check:
        if json.loads(a.output.read_text())!=data:raise ValueError('M3 frontier snapshot drift')
    else:a.output.write_text(json.dumps(data,indent=2)+'\n')
    print('M3 missing bank0 instruction starts:',data['count'],[r['cpu'] for r in data['missing_fixed_bank0_targets']])
if __name__=='__main__':main()
