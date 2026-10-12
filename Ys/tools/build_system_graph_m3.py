#!/usr/bin/env python3
"""ROM-verified cross-bank Z80 graph including newly assembled fixed bank0."""
import argparse
import json
from pathlib import Path
from build_sms_phase14 import ROOT, SOURCES
from build_system_graph import build as baseline_build

MODULES=tuple(SOURCES)+(('src/wholebank07/late_code.asm',7),('src/wholebank00/new_code.asm',0))

def build(rom):
    report=baseline_build(rom,modules=MODULES)
    report['schema']='ys-system-graph-three-complete-banks-v1'
    report['scope']='All known Z80 mnemonic-source regions, including new bank0 linear-disassembly candidates. Syntax and byte checks are not dynamic proof.'
    report['limitations'].append('New bank0 code segments were bounded by manual inspection; not all code reaches gameplay execution.')
    if report['banks'][0]['verified_code_bytes']!=7935+6518:raise ValueError('Bank0 graph code-byte ledger drift')
    if report['summary']['verified_instruction_bytes']!=14198+6518:raise ValueError('System graph source coverage drift')
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path)
    p.add_argument('--output',type=Path,default=ROOT/'whole_system/evidence_graph_m3.json')
    p.add_argument('--check',action='store_true')
    a=p.parse_args()
    result=build(a.rom.read_bytes())
    if a.check:
        if json.loads(a.output.read_text())!=result:raise ValueError('Graph snapshot differs')
    else:a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result['summary'],indent=2))

if __name__=='__main__':main()
