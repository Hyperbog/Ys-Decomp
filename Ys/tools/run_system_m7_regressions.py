#!/usr/bin/env python3
"""M7 all historical suites + bank4, collision, seven-bank + WLA gates."""
import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from run_system_m6_regressions import commands as previous_commands
from run_regressions_phase21 import one_suite,ROOT

def commands(rom):
    yield from previous_commands(rom)
    yield 'wholebank04_source_only',[sys.executable,str(ROOT/'tools/whole_bank04.py'),'--verify-mixed','--verify-rom',str(rom)]
    yield 'wholebank04_tests',[sys.executable,str(ROOT/'tests_whole_bank04.py'),str(rom)]
    yield 'whole_system_seven_bank_build',[sys.executable,str(ROOT/'tools/build_system_m7.py'),str(rom),'--check']
    yield 'bank04_collision_runtime',[sys.executable,str(ROOT/'tools/bank04_collision_trace.py'),str(rom),'--check']
    yield 'bank04_static_crossbank_links',[sys.executable,str(ROOT/'tools/bank04_crossbank_ledger.py'),'--check']
    yield 'whole_system_seven_bank_wla_prepare',[sys.executable,str(ROOT/'tools/wla_system_m7.py'),'--prepare']

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path);p.add_argument('--jobs',type=int,default=4)
    p.add_argument('--timeout',type=int,default=180)
    p.add_argument('--report',type=Path,default=ROOT/'whole_system/regression_report_m7.json')
    a=p.parse_args()
    if not a.rom.is_file() or not 1<=a.jobs<=4 or a.timeout<=0:p.error('Invalid ROM/jobs/timeout')
    jobs=list(commands(a.rom.resolve()));done={}
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        futures={pool.submit(one_suite,job,a.timeout):job[0] for job in jobs}
        for f in as_completed(futures):
            item=f.result();done[item['suite']]=item
            print(item['suite'],item['status'],item['elapsed_seconds'],flush=True)
    report={'schema':'ys-system-m7-regressions-v1','count':len(jobs),
       'passed':sum(done[k]['status']=='passed' for k,_ in jobs),
       'all_passed':all(done[k]['status']=='passed' for k,_ in jobs),
       'cases':[done[k] for k,_ in jobs]}
    a.report.write_text(json.dumps(report,indent=2)+'\n')
    print(f"{report['passed']}/{report['count']} suites passed")
    if not report['all_passed']:raise SystemExit(1)
if __name__=='__main__':main()
