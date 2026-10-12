#!/usr/bin/env python3
"""Whole-system M8 regression: all historical gates + banks 8/10."""
import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from run_system_m7_regressions import commands as historical
from run_regressions_phase21 import one_suite,ROOT

def commands(rom):
    yield from historical(rom)
    yield 'wholebank08_and10_source_only',[sys.executable,str(ROOT/'tools/whole_banks08_10.py'),'--verify-mixed','--verify-rom',str(rom)]
    yield 'wholebank08_and10_tests',[sys.executable,str(ROOT/'tests_whole_banks08_10.py'),str(rom)]
    yield 'whole_system_nine_bank_build',[sys.executable,str(ROOT/'tools/build_system_m8.py'),str(rom),'--check']
    yield 'bank10_decimal_bounded_execution',[sys.executable,str(ROOT/'tools/bank10_decimal_trace.py'),'--check']
    yield 'bank08_10_static_mapper_links',[sys.executable,str(ROOT/'tools/bank08_10_crossbank.py'),'--check']
    yield 'whole_system_nine_bank_wla_prepare',[sys.executable,str(ROOT/'tools/wla_system_m8.py'),'--prepare']

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path);p.add_argument('--jobs',type=int,default=4)
    p.add_argument('--timeout',type=int,default=240)
    p.add_argument('--report',type=Path,default=ROOT/'whole_system/regression_report_m8.json')
    a=p.parse_args()
    if not a.rom.is_file() or not 1<=a.jobs<=4 or a.timeout<=0:p.error('Invalid ROM or jobs')
    jobs=list(commands(a.rom.resolve()));done={}
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        futures={pool.submit(one_suite,job,a.timeout):job[0] for job in jobs}
        for future in as_completed(futures):
            item=future.result();done[item['suite']]=item
            print(item['suite'],item['status'],item['elapsed_seconds'],flush=True)
    report={'schema':'ys-system-m8-regressions-v1','count':len(jobs),
        'passed':sum(done[k]['status']=='passed' for k,_ in jobs),
        'all_passed':all(done[k]['status']=='passed' for k,_ in jobs),
        'cases':[done[k] for k,_ in jobs]}
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(report,indent=2)+'\n')
    print(f"{report['passed']}/{report['count']} suites passed")
    if not report['all_passed']:raise SystemExit(1)
if __name__=='__main__':main()
