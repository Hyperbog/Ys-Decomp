#!/usr/bin/env python3
"""Historical M4 suites plus complete sound bank and five-bank system gates."""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import sys
from run_system_m4_regressions import commands as old_commands
from run_regressions_phase21 import one_suite,ROOT

def commands(rom):
    yield from old_commands(rom)
    yield 'wholebank02_source_only',[sys.executable,str(ROOT/'tools/whole_bank02.py'),'--verify-mixed','--verify-rom',str(rom)]
    yield 'wholebank02_tests',[sys.executable,str(ROOT/'tests_whole_bank02.py'),str(rom)]
    yield 'whole_system_five_bank_build',[sys.executable,str(ROOT/'tools/build_system_m5.py'),str(rom),'--check']
    yield 'whole_system_five_bank_sound_links',[sys.executable,str(ROOT/'tools/build_sound_ledger_m5.py'),'--check']
    yield 'whole_system_five_bank_wla_prepare',[sys.executable,str(ROOT/'tools/wla_system_m5.py'),'--prepare']

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path)
    p.add_argument('--jobs',type=int,default=4)
    p.add_argument('--timeout',type=int,default=120)
    p.add_argument('--report',type=Path,default=ROOT/'whole_system/regression_report_m5.json')
    args=p.parse_args()
    if not args.rom.is_file() or not 1<=args.jobs<=4 or args.timeout<=0:p.error('Invalid ROM/jobs/timeout')
    cases=list(commands(args.rom.resolve()));done={}
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures={pool.submit(one_suite,item,args.timeout):item[0] for item in cases}
        for f in as_completed(futures):
            result=f.result();done[result['suite']]=result
            print(result['suite'],result['status'],result['elapsed_seconds'],flush=True)
    result={'schema':'ys-system-m5-regressions-v1','count':len(cases),
         'passed':sum(done[name]['status']=='passed' for name,_ in cases),
         'all_passed':all(done[name]['status']=='passed' for name,_ in cases),
         'cases':[done[name] for name,_ in cases]}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+'\n')
    print(f"{result['passed']}/{result['count']} suites passed")
    if not result['all_passed']:raise SystemExit(1)
if __name__=='__main__':main()
