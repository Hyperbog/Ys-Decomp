#!/usr/bin/env python3
"""Complete regression suite and whole-bank-level verification gates."""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import json
from pathlib import Path
import sys
from run_regressions_phase21 import commands as old_commands,one_suite,ROOT


def commands(rom):
    yield from old_commands(rom)
    yield 'wholebank07_source_only', [sys.executable,str(ROOT/'tools/whole_bank07.py'),'--verify-mixed']
    yield 'wholebank07_tests',[sys.executable,str(ROOT/'tests_whole_bank07.py'),str(rom)]
    yield 'wholebank07_integrated',[sys.executable,str(ROOT/'tools/build_whole_bank07.py'),str(rom),'--check']
    yield 'wholebank03_source_only',[sys.executable,str(ROOT/'tools/whole_bank03.py'),'--verify-mixed']
    yield 'wholebank03_tests',[sys.executable,str(ROOT/'tests_whole_bank03.py'),str(rom)]
    yield 'whole_system_tests',[sys.executable,str(ROOT/'tests_whole_system.py'),str(rom)]
    yield 'whole_system_overlay',[sys.executable,str(ROOT/'tools/build_whole_system.py'),str(rom),'--check']
    yield 'system_graph_snapshot',[sys.executable,str(ROOT/'tools/build_system_graph.py'),str(rom),'--output',str(ROOT/'whole_system/evidence_graph.json'),'--check']
    yield 'system_graph_tests',[sys.executable,str(ROOT/'tests_system_graph.py'),str(rom)]
    yield 'system_graph_frontier',[sys.executable,str(ROOT/'tools/build_graph_frontier.py'),'--check']

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path)
    p.add_argument('--jobs',type=int,default=4)
    p.add_argument('--timeout',type=int,default=120)
    p.add_argument('--report',type=Path)
    a=p.parse_args()
    if not a.rom.exists() or not 1<=a.jobs<=4 or a.timeout<=0:p.error('Invalid ROM/jobs/timeout')
    jobs=list(commands(a.rom.resolve()))
    found={}
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        futures={pool.submit(one_suite,item,a.timeout):item[0] for item in jobs}
        for future in as_completed(futures):
            result=future.result(); found[result['suite']]=result
            print(result['suite'],result['status'],result['elapsed_seconds'],flush=True)
    result={'schema':'ys-whole-system-regression-v1','count':len(jobs),
            'passed':sum(found[k]['status']=='passed' for k,_ in jobs),
            'all_passed':all(found[k]['status']=='passed' for k,_ in jobs),
            'cases':[found[k] for k,_ in jobs]}
    if a.report:a.report.write_text(json.dumps(result,indent=2)+'\n')
    print(f"{result['passed']}/{result['count']} total suites pass")
    if not result['all_passed']:raise SystemExit(1)
if __name__=='__main__':main()
