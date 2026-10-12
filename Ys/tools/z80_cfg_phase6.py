#!/usr/bin/env python3
"""Ys SMS phase 6: bounded fixed-bank CFG with separate ROM-data anchors.

Run --write to generate deterministic snapshots; --check validates them.
Requires the exact original ROM. This is static location/type classification,
not a sound-stream semantic decoder or assembled source equivalence test.
"""
import argparse
from collections import defaultdict, deque
import hashlib
import json
from pathlib import Path
import sys

from z80_regions import decode
from z80_cfg_phase5 import (old_classified, analyze as phase5_analyze,
                             control_edges, CONDITIONAL_CALL)

ROOT = Path(__file__).resolve().parents[1]
WINDOWS = ((0x0A00, 0x0BC5), (0x2002, 0x4000))


def inside(offset):
    return any(lo <= offset < hi for lo, hi in WINDOWS)


def previous(rom):
    """Obtain the verified phases 1–5 byte map; don't reuse guessed edges."""
    old, previous_code = old_classified(rom)
    phase5_cfg = json.loads((ROOT/'phase5/regions.json').read_text())
    c5, own5, d5, _, _ = phase5_analyze(rom, phase5_cfg)
    old.update(own5)
    old.update(i for lo, hi, _ in d5 for i in range(lo, hi))
    assert len(old) == 7002, f'Prior classified union changed: {len(old)}'
    previous_code.update(c5)
    return old, previous_code


def indexed_dispatch(rom, cfg):
    table_roots = set()
    details = {}
    for table in cfg['dispatch_tables']:
        lo = int(table['start'], 16)
        hi = int(table['end_exclusive'], 16)
        assert (hi-lo) % 2 == 0
        targets = [int.from_bytes(rom[p:p+2], 'little') for p in range(lo,hi,2)]
        assert all(0x2002 <= x < 0x4000 for x in targets), f'Bad target in {lo:04X}'
        details[f'{lo:04X}'] = [f'{x:04X}' for x in targets]
        table_roots.update(targets)
    return table_roots, details


def analyze(rom, cfg):
    occupied, prev_code = previous(rom)
    data = []
    data_bytes = set()
    for item in cfg['data']:
        lo = int(item['start'],16)
        hi = int(item['end_exclusive'],16)
        assert 0 <= lo < hi <= len(rom)
        assert hashlib.sha256(rom[lo:hi]).hexdigest() == item['sha256'], f'Data digest mismatch {lo:05X}'
        span = set(range(lo,hi))
        assert not occupied.intersection(span), f'Previous classification overlaps data {lo:05X}'
        assert not data_bytes.intersection(span), f'Data ranges overlap {lo:05X}'
        data_bytes.update(span)
        data.append((lo,hi,item['name'],item['confidence']))
    dispatch, directory = indexed_dispatch(rom,cfg)
    roots = set(int(x,16) for x in cfg['entrypoints']) | dispatch
    unresolved = set()
    for pc, (end, instruction) in prev_code.items():
        targets, _ = control_edges(rom,pc,end,instruction)
        for target in targets:
            if 0x4000 <= target:
                if pc < 0x4000:
                    unresolved.add(f'Prior bank0 caller {pc:04X} -> mapped CPU {target:04X}; bank unknown')
                continue
            if inside(target) and target not in occupied:
                roots.add(target)
    code = {}
    ownership = {}
    errors = []
    queue = deque((s,'seed') for s in sorted(roots))
    while queue:
        pc, origin = queue.popleft()
        if not inside(pc) or pc in occupied:
            continue
        if pc in data_bytes:
            errors.append(f'Instruction entry into anchored data {pc:05X} via {origin}')
            continue
        if pc in ownership:
            if pc not in code:
                errors.append(f'Entry {pc:05X} inside instruction at {ownership[pc]:05X}')
            continue
        while inside(pc) and pc not in occupied and pc not in ownership:
            if pc in data_bytes:
                errors.append(f'Fallthrough into anchored data at {pc:05X}')
                break
            try:
                end, text = decode(rom,pc)
            except (ValueError,IndexError) as exc:
                errors.append(f'Decoder stopped at {pc:05X}: {exc}')
                break
            if not inside(end-1):
                unresolved.add(f'Instruction at {pc:05X} crosses analysis boundary')
                break
            overlap = [x for x in range(pc,end) if x in data_bytes or x in occupied or x in ownership]
            if overlap:
                errors.append(f'Instruction {pc:05X} overlaps previously typed byte {overlap[0]:05X}')
                break
            code[pc] = (end,text)
            ownership.update((i,pc) for i in range(pc,end))
            targets, fallthrough = control_edges(rom,pc,end,text)
            for target in targets:
                if 0x4000 <= target:
                    unresolved.add(f'Bank0 instruction {pc:04X} -> bank-dependent CPU {target:04X}')
                elif inside(target) and target not in occupied:
                    queue.append((target,f'{pc:05X}'))
                elif target not in occupied:
                    unresolved.add(f'Outside Phase6 windows {pc:04X} -> CPU {target:04X}')
            if not fallthrough:
                break
            pc = end
        if not inside(pc):
            unresolved.add(f'Fallthrough exited Phase6 window at {pc:05X}')
    assert not errors, '; '.join(sorted(set(errors))[:12])
    assert not ownership.keys() & data_bytes
    assert not ownership.keys() & occupied
    return code, ownership, data, directory, sorted(unresolved)


def output(rom, cfg):
    code, owner, data, directory, unresolved = analyze(rom,cfg)
    lines = ['; Ys SMS Phase 6: ROM-backed bounded fixed-bank Z80 listing',
             '; Offsets/bytes verified. Sound stream semantics not yet decoded.',
             '; file   CPU   bytes               Z80', '']
    for pc,(end, instruction) in sorted(code.items()):
        lines.append(f'{pc:05X} {pc:04X}  {rom[pc:end].hex(" ").upper():<19} {instruction}')
    lines.append('')
    lines.append('; AUDIO AND DISPATCH DATA REGIONS (digest-checked, opaque where noted)')
    for lo, hi, name, confidence in data:
        lines.append(f'; {lo:05X}-{hi-1:05X}: {hi-lo} bytes [{confidence}] {name}')
        # Deliberately omit commercial music payload bytes from committed files.
        # Exact data bytes are available only from the user's private ROM.
    lines.append('')
    stats = {
      'rom_sha256': hashlib.sha256(rom).hexdigest(),
      'scope': 'Static CFG plus bounded opaque ROM-data sections; no runtime or build equivalence',
      'new_instruction_count': len(code),
      'new_code_bytes': len(owner),
      'new_data_bytes': sum(hi-lo for lo,hi,_,_ in data),
      'new_total_bytes': len(owner)+sum(hi-lo for lo,hi,_,_ in data),
      'cumulative_distinct_bytes': 7002+len(owner)+sum(hi-lo for lo,hi,_,_ in data),
      'dispatch_tables': directory,
      'classified_data_regions': [{'start':f'{lo:05X}', 'end_exclusive':f'{hi:05X}',
          'size':hi-lo,'confidence':conf} for lo,hi,_,conf in data],
      'unresolved_edges': unresolved,
      'code_bytes_sha256': hashlib.sha256(bytes(rom[i] for i in sorted(owner))).hexdigest(),
      'data_bytes_sha256': hashlib.sha256(bytes(rom[i] for lo,hi,_,_ in data for i in range(lo,hi))).hexdigest(),
    }
    return '\n'.join(lines), json.dumps(stats,indent=2)+'\n', stats


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write',action='store_true')
    mode.add_argument('--check',action='store_true')
    args=p.parse_args()
    rom=args.rom.read_bytes()
    digest=json.loads((ROOT/'manifest.json').read_text())['sha256']
    assert hashlib.sha256(rom).hexdigest()==digest,'Source ROM hash mismatch'
    cfg=json.loads((ROOT/'phase6/regions.json').read_text())
    listing,report,stats=output(rom,cfg)
    listing_path=ROOT/'phase6/code.lst'
    report_path=ROOT/'phase6/coverage.json'
    if args.write:
        listing_path.write_text(listing)
        report_path.write_text(report)
    else:
        assert listing_path.read_text()==listing, 'Code listing is not reproducible'
        assert report_path.read_text()==report, 'Coverage JSON is not reproducible'
    print('PASS Phase6: %d new instructions; %d code + %d data = %d new bytes; %d cumulative' %
        (stats['new_instruction_count'],stats['new_code_bytes'],stats['new_data_bytes'],
         stats['new_total_bytes'],stats['cumulative_distinct_bytes']))

if __name__=='__main__':
    try:
        main()
    except (AssertionError, OSError, ValueError, IndexError) as exc:
        sys.exit(f'FAIL Phase6: {exc}')
