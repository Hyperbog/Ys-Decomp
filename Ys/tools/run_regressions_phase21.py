#!/usr/bin/env python3
"""Run the Ys decomp regression history with phase-specific command contracts.

Phase 14/15 unittest runners obtain their ROM fixture internally; all other
phase runners accept the explicit ROM path. Runs each suite with its own
execution timeout so a long suite cannot prevent status for the others.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]


def commands(rom):
    yield 'phase1', [sys.executable, str(ROOT/'tests_check.py'), str(rom)]
    for i in range(2,22):
        arguments=[] if i in (14,15) else [str(rom)]
        yield f'phase{i}', [sys.executable, str(ROOT/f'tests_phase{i}.py'), *arguments]
        if i==11:
            yield 'phase11b', [sys.executable, str(ROOT/'tests_phase11b.py'), str(rom)]
    yield 'scratch_workflow', [sys.executable, str(ROOT/'tests_scratch_workflow.py'), str(rom)]
    yield 'full_rom_overlay', [sys.executable, str(ROOT/'tools/build_phase21.py'), str(rom), '--check']


def one_suite(item, seconds):
    name,command=item
    start=time.monotonic()
    try:
        result=subprocess.run(command, cwd=ROOT.parent,
                stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                text=True,timeout=seconds)
        status='passed' if result.returncode==0 else 'failed'
        output=result.stdout[-1500:]
    except subprocess.TimeoutExpired as exception:
        status='timeout'
        captured=exception.stdout or b''
        output=(captured.decode('utf-8','replace') if isinstance(captured,bytes)
                else captured)[-1500:]
    except Exception as exception:
        status='runner_error'
        output=repr(exception)
    return {'suite':name,'status':status,
            'elapsed_seconds':round(time.monotonic()-start,3),
            'output_tail':output}


def run(rom, seconds=120, selected=None, jobs=1):
    wanted=[item for item in commands(rom) if not selected or item[0] in selected]
    if jobs==1:
        cases=[]
        for item in wanted:
            result=one_suite(item,seconds)
            cases.append(result)
            print(f'{result["suite"]}: {result["status"]} ({result["elapsed_seconds"]:.1f}s)',flush=True)
    else:
        found={}
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            futures={pool.submit(one_suite,item,seconds):item[0] for item in wanted}
            for future in as_completed(futures):
                result=future.result()
                found[result['suite']]=result
                print(f'{result["suite"]}: {result["status"]} ({result["elapsed_seconds"]:.1f}s)',flush=True)
        cases=[found[item[0]] for item in wanted] # deterministic JSON ordering
    return {'schema':'ys-phase21-regression-runner-v1',
            'jobs':jobs,
            'all_selected_passed':bool(cases) and all(e['status']=='passed' for e in cases),
            'cases':cases}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom',type=Path)
    parser.add_argument('--timeout',type=int,default=120,
                        help='per-suite timeout in seconds')
    parser.add_argument('--jobs',type=int,default=1,help='independent suites to run concurrently (1-4)')
    parser.add_argument('--suite',action='append',
                        help='optional suite name, repeat to run a subset')
    parser.add_argument('--report',type=Path,
                        help='optional JSON file with case results')
    args=parser.parse_args()
    if args.timeout<=0:
        parser.error('timeout must be positive')
    if not 1<=args.jobs<=4:
        parser.error('jobs must be between 1 and 4')
    if not args.rom.is_file():
        parser.error('ROM does not exist')
    requested=set(args.suite or [])
    known={name for name,_ in commands(args.rom)}
    if requested-known:
        parser.error('unknown suite names: '+', '.join(sorted(requested-known)))
    result=run(args.rom.resolve(),args.timeout,requested or None,args.jobs)
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(result,indent=2)+'\n')
    print(f'{sum(e["status"]=="passed" for e in result["cases"])}'
          f'/{len(result["cases"])} suites passed')
    if not result['all_selected_passed']:
        sys.exit(1)


if __name__=='__main__':
    main()
