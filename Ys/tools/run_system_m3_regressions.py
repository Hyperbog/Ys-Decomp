#!/usr/bin/env python3
"""All historical ROM checks plus fixed-bank-0 closure and 3-bank system graph."""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import sys
from run_whole_system_regressions import commands as historical
from run_regressions_phase21 import one_suite, ROOT

def commands(rom):
    yield from historical(rom)
    yield 'wholebank00_source_only',[sys.executable,str(ROOT/'tools/whole_bank00.py'),'--verify-mixed','--verify-rom',str(rom)]
    yield 'wholebank00_tests',[sys.executable,str(ROOT/'tests_whole_bank00.py'),str(rom)]
    yield 'whole_system_three_bank_build',[sys.executable,str(ROOT/'tools/build_system_m3.py'),str(rom),'--check']
    yield 'whole_system_three_bank_graph',[sys.executable,str(ROOT/'tools/build_system_graph_m3.py'),str(rom),'--check']
    yield 'whole_system_three_bank_frontier',[sys.executable,str(ROOT/'tools/build_frontier_m3.py'),'--check']
    yield 'whole_system_three_bank_wla_prepare',[sys.executable,str(ROOT/'tools/wla_system_m3.py'),'--prepare']

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path)
    p.add_argument('--jobs',type=int,default=4)
    p.add_argument('--timeout',type=int,default=120)
    p.add_argument('--report',type=Path,default=ROOT/'whole_system/regression_report_m3.json')
    a=p.parse_args()
    if not a.rom.exists() or not 1<=a.jobs<=4 or a.timeout<=0:p.error('Invalid ROM/jobs/timeout')
    jobs=list(commands(a.rom.resolve()));found={}
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        futures={pool.submit(one_suite,job,a.timeout):job[0] for job in jobs}
        for future in as_completed(futures):
            item=future.result();found[item['suite']]=item
            print(item['suite'],item['status'],item['elapsed_seconds'],flush=True)
    result={'schema':'ys-system-m3-regressions-v1','count':len(jobs),
            'passed':sum(found[k]['status']=='passed' for k,_ in jobs),
            'all_passed':all(found[k]['status']=='passed' for k,_ in jobs),
            'cases':[found[k] for k,_ in jobs]}
    if a.report:a.report.write_text(json.dumps(result,indent=2)+'\n')
    print(f"{result['passed']}/{result['count']} total suites passed")
    if not result['all_passed']:raise SystemExit(1)

if __name__=='__main__':main()
