#!/usr/bin/env python3
"""Whole-System M9: historical regression gates plus banks 9/11/12."""
import argparse,json,sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from run_system_m8_regressions import commands as historical
from run_regressions_phase21 import one_suite,ROOT

def commands(rom):
 yield from historical(rom)
 yield 'wholebank09_11_12_source_only',[sys.executable,str(ROOT/'tools/whole_banks09_11_12.py'),'--verify-mixed','--verify-rom',str(rom)]
 yield 'wholebank09_11_12_tests',[sys.executable,str(ROOT/'tests_whole_banks09_11_12.py'),str(rom)]
 yield 'whole_system_twelve_bank_build',[sys.executable,str(ROOT/'tools/build_system_m9.py'),str(rom),'--check']
 yield 'bank09_bounded_glyph_execution',[sys.executable,str(ROOT/'tools/bank09_glyph_trace.py'),str(rom),'--check']
 yield 'whole_system_twelve_bank_wla_prepare',[sys.executable,str(ROOT/'tools/wla_system_m9.py'),'--prepare']

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('rom',type=Path);p.add_argument('--jobs',type=int,default=4);p.add_argument('--timeout',type=int,default=600)
 p.add_argument('--report',type=Path,default=ROOT/'whole_system/regression_report_m9.json');a=p.parse_args()
 if not a.rom.is_file() or not 1<=a.jobs<=4 or a.timeout<=0:p.error('Invalid ROM or jobs')
 jobs=list(commands(a.rom.resolve()));done={}
 with ThreadPoolExecutor(max_workers=a.jobs) as pool:
  fut={pool.submit(one_suite,j,a.timeout):j[0] for j in jobs}
  for f in as_completed(fut):
   item=f.result();done[item['suite']]=item
   print(item['suite'],item['status'],item['elapsed_seconds'],flush=True)
 report={'schema':'ys-system-m9-regressions-v1','count':len(jobs),
  'passed':sum(done[k]['status']=='passed' for k,_ in jobs),
  'all_passed':all(done[k]['status']=='passed' for k,_ in jobs),
  'cases':[done[k] for k,_ in jobs]}
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n')
 print(f"{report['passed']}/{report['count']} suites passed")
 if not report['all_passed']:raise SystemExit(1)
if __name__=='__main__':main()
