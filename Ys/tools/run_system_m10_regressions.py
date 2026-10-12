#!/usr/bin/env python3
"""M10: independently executed, reportable project-wide regression gates."""
import argparse,json,sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from run_system_m9_regressions import commands as historical
from run_regressions_phase21 import one_suite,ROOT

def commands(rom):
 yield from historical(rom)
 yield 'wholebank05_13_14_15_source_roundtrip',[sys.executable,str(ROOT/'tools/whole_banks05_13_14_15.py'),'--verify-mixed','--verify-rom',str(rom)]
 yield 'wholebank05_13_14_15_tests',[sys.executable,str(ROOT/'tests_whole_banks05_13_14_15.py'),str(rom)]
 yield 'source_only_full_rom_rebuild',[sys.executable,str(ROOT/'tools/build_system_m10.py'),'--check','--verify-rom',str(rom)]
 yield 'complete_16_bank_wla_prepare',[sys.executable,str(ROOT/'tools/wla_system_m10.py'),'--prepare']

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('rom',type=Path);p.add_argument('--jobs',type=int,default=4);p.add_argument('--timeout',type=int,default=600)
 p.add_argument('--report',type=Path,default=ROOT/'whole_system/regression_report_m10.json');a=p.parse_args()
 if not a.rom.is_file() or not 1<=a.jobs<=4 or a.timeout<=0:p.error('Invalid input ROM or job concurrency')
 jobs=list(commands(a.rom.resolve()));done={}
 with ThreadPoolExecutor(max_workers=a.jobs) as pool:
  fut={pool.submit(one_suite,j,a.timeout):j[0] for j in jobs}
  for f in as_completed(fut):
   row=f.result();done[row['suite']]=row
   print(row['suite'],row['status'],row['elapsed_seconds'],flush=True)
 report={'schema':'ys-system-m10-regressions-v1','count':len(jobs),
  'passed':sum(done[n]['status']=='passed' for n,_ in jobs),
  'all_passed':all(done[n]['status']=='passed' for n,_ in jobs),
  'cases':[done[n] for n,_ in jobs]}
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n')
 print(f"{report['passed']}/{report['count']} suites passed")
 if not report['all_passed']:raise SystemExit(1)
if __name__=='__main__':main()
