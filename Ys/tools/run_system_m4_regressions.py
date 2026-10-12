#!/usr/bin/env python3
"""All M3 historical suites plus bank6 and 4-bank whole-ROM proof gates."""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import sys
from run_system_m3_regressions import commands as old_commands
from run_regressions_phase21 import one_suite,ROOT

def commands(rom):
    yield from old_commands(rom)
    yield 'wholebank06_source_only',[sys.executable,str(ROOT/'tools/whole_bank06.py'),'--verify-mixed','--verify-rom',str(rom)]
    yield 'wholebank06_tests',[sys.executable,str(ROOT/'tests_whole_bank06.py'),str(rom)]
    yield 'whole_system_four_bank_build',[sys.executable,str(ROOT/'tools/build_system_m4.py'),str(rom),'--check']
    yield 'wholebank06_asset_ledger',[sys.executable,str(ROOT/'tools/build_sprite_asset_ledger_m4.py'),'--check']
    yield 'whole_system_four_bank_wla_prepare',[sys.executable,str(ROOT/'tools/wla_system_m4.py'),'--prepare']

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path)
    p.add_argument('--jobs',type=int,default=4)
    p.add_argument('--timeout',type=int,default=120)
    p.add_argument('--report',type=Path,default=ROOT/'whole_system/regression_report_m4.json')
    a=p.parse_args()
    if not a.rom.is_file() or not 1<=a.jobs<=4 or a.timeout<=0:p.error('Invalid ROM/jobs/timeout')
    jobs=list(commands(a.rom.resolve()))
    done={}
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        futures={pool.submit(one_suite,job,a.timeout):job[0] for job in jobs}
        for future in as_completed(futures):
            item=future.result();done[item['suite']]=item
            print(item['suite'],item['status'],item['elapsed_seconds'],flush=True)
    summary={'schema':'ys-system-m4-regressions-v1','count':len(jobs),
        'passed':sum(done[k]['status']=='passed' for k,_ in jobs),
        'all_passed':all(done[k]['status']=='passed' for k,_ in jobs),
        'cases':[done[k] for k,_ in jobs]}
    if a.report:a.report.write_text(json.dumps(summary,indent=2)+'\n')
    print(f"{summary['passed']}/{summary['count']} suites passed")
    if not summary['all_passed']:raise SystemExit(1)
if __name__=='__main__':main()
