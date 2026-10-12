#!/usr/bin/env python3
"""M12 system regressions; optionally require real Emulicious independent assembly."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import sys

from run_system_m10_regressions import commands as historical
from run_regressions_phase21 import ROOT,one_suite


def commands(rom,jar=None):
    yield from historical(rom)
    yield 'emulicious_assembler_m12_tests',[sys.executable,str(ROOT/'tests_emulicious_assembler_m12.py')]
    if jar is not None:
        yield 'emulicious_assembler_m12_external',[
            sys.executable,str(ROOT/'tools/verify_emulicious_assembler_m12.py'),
            '--jar',str(jar.resolve()),'--reference-rom',str(rom.resolve()),
            '--report',str(ROOT/'whole_system/emulicious_assembler_report_m12.json')]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom',type=Path)
    parser.add_argument('--external-jar',type=Path,
                        help='Require Emulicious.jar for an actual external Z80 assembly comparison')
    parser.add_argument('--jobs',type=int,default=4)
    parser.add_argument('--timeout',type=int,default=600)
    parser.add_argument('--report',type=Path,default=ROOT/'whole_system/regression_report_m12.json')
    args=parser.parse_args()
    if not args.rom.is_file() or not 1<=args.jobs<=4 or args.timeout<=0:
        parser.error('Invalid input ROM, jobs or timeout')
    if args.external_jar is not None and not args.external_jar.is_file():
        parser.error('External Emulicious.jar does not exist')
    jobs=list(commands(args.rom,args.external_jar))
    cases={}
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures={pool.submit(one_suite,job,args.timeout):job[0] for job in jobs}
        for future in as_completed(futures):
            result=future.result()
            cases[result['suite']]=result
            print(result['suite'],result['status'],result['elapsed_seconds'],flush=True)
    passed=sum(cases[name]['status']=='passed' for name,_ in jobs)
    report={'schema':'ys-system-m12-regressions-v1','count':len(jobs),
            'passed':passed,'all_passed':passed==len(jobs),
            'external_emulicious_assembler_required':args.external_jar is not None,
            'cases':[cases[name] for name,_ in jobs]}
    args.report.parent.mkdir(exist_ok=True,parents=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(f'{passed}/{len(jobs)} suites passed',flush=True)
    if passed!=len(jobs):raise SystemExit(1)

if __name__=='__main__':main()
