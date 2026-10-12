#!/usr/bin/env python3
"""Build whole-system reconstruction work queue from *unresolved* static edges.

A candidate is not an instruction proof. No ROM data is copied or decoded.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def build_frontier(graph):
    if graph.get('schema') != 'ys-mapper-aware-evidence-graph-v1':
        raise ValueError('incompatible graph')
    by_target=defaultdict(list)
    ambiguous=defaultdict(list)
    for row in graph['edges']:
        if row['resolution']=='fixed_bank0' and row['to_instruction'] is None:
            by_target[row['to_cpu']].append(row['from'])
        if row['resolution']=='unresolved_mapper_slot':
            ambiguous[row['to_cpu']].append(row['from'])
    targets=[{'physical_bank':0,'cpu':cpu,'incoming_verified_code_sites':sorted(set(sites)),
              'status':'unexamined_target_not_verified_code',
              'instruction_bytes_claimed':0} for cpu,sites in sorted(by_target.items(),key=lambda item:(-len(item[1]),item[0]))]
    unknown=[{'cpu':cpu,'caller_instruction_ids':sorted(set(sites)),
              'status':'mapper_slot_unknown_not_proven_reachable'}
             for cpu,sites in sorted(ambiguous.items())]
    return {'schema':'ys-code-frontier-v1','source_rom_sha256':graph['original_rom_sha256'],
            'priority':'fixed_bank0_code_target_candidate_first',
            'fixed_bank0_targets_without_verified_instruction':targets,
            'mapper_ambiguous_target_sites':unknown,
            'summary':{'missing_fixed_bank0_target_count':len(targets),
                       'missing_fixed_bank0_ref_count':sum(len(v) for v in by_target.values()),
                       'unresolved_mapper_ref_count':sum(len(v) for v in ambiguous.values()),
                       'new_source_backed_bytes':0},
            'qualification':'Candidates are high-priority investigation roots, not new code coverage. Source-only bank 0 is still incomplete.'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--graph',type=Path,default=ROOT/'whole_system/evidence_graph.json')
    p.add_argument('--output',type=Path,default=ROOT/'whole_system/frontier.json')
    p.add_argument('--check',action='store_true')
    args=p.parse_args()
    report=build_frontier(json.loads(args.graph.read_text()))
    if args.check:
        if json.loads(args.output.read_text()) != report:raise ValueError('frontier drift')
    else:
        args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report['summary'],indent=2))

if __name__=='__main__':main()
