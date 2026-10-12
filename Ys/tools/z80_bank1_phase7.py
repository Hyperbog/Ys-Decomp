#!/usr/bin/env python3
"""Ys SMS Phase 7: ROM-backed, bank-conditional bank-1 CFG and bank-3 survey.

This *does not* establish runtime bank occupancy or encode/decode opaque data.
Only roots independently referenced from earlier fixed-bank ROM instructions
are considered. Never infer a slot-2 physical bank from an arbitrary call.
"""
import argparse
from collections import defaultdict, deque
import hashlib
import json
from pathlib import Path
import sys

from z80_regions import decode
from z80_cfg_phase5 import control_edges, old_classified, analyze as phase5_analyze
from z80_cfg_phase6 import analyze as phase6_analyze

ROOT = Path(__file__).resolve().parents[1]
BANK1_START, BANK1_END = 0x4000, 0x8000
BANK3_START, BANK3_END = 0xC000, 0x10000
DATA_BOUNDARIES = [0xC000, 0xD000, 0xD600, 0xDF00, 0xF8CD]
DATA_NAMES = [
    'Repeated four-byte motifs; likely graphic or color lookup data; format not proven',
    'Graphics-looking packed patterns and structured words; format not proven',
    'Mixed packed payload; no validated internal record grammar',
    'High-entropy symbol/command-like payload; possible encoded game text; format unproven',
]


def prior_code(rom):
    _, earlier = old_classified(rom)
    c5, *_ = phase5_analyze(rom, json.loads((ROOT/'phase5/regions.json').read_text()))
    c6, *_ = phase6_analyze(rom, json.loads((ROOT/'phase6/regions.json').read_text()))
    earlier.update(c5)
    earlier.update(c6)
    return earlier


def anchored_roots(rom):
    refs = defaultdict(set)
    for pc, (end, text) in prior_code(rom).items():
        # Direct control-flow references from the known fixed bank only.
        if pc >= BANK1_START:
            continue
        targets, _ = control_edges(rom, pc, end, text)
        for dest in targets:
            if BANK1_START <= dest < BANK1_END:
                refs[dest].add(pc)
    assert sorted(refs) == [0x42BA, 0x476C, 0x60B5, 0x61AE, 0x6215, 0x64CD], 'Known bank-1 roots changed'
    return {k: sorted(v) for k,v in refs.items()}


def trace(rom):
    roots = anchored_roots(rom)
    q = deque((a, 'prior fixed-bank reference') for a in sorted(roots))
    code, owner, uncertain, incoming = {}, {}, set(), defaultdict(set)
    while q:
        entry, provenance = q.popleft()
        incoming[entry].add(provenance)
        if not BANK1_START <= entry < BANK1_END:
            continue
        if entry in owner:
            assert entry in code, f'Branch enters instruction interior at {entry:04X}'
            continue
        pc = entry
        while BANK1_START <= pc < BANK1_END and pc not in owner:
            end, txt = decode(rom, pc)
            assert end <= BANK1_END, f'Instruction extends outside bank-1 boundary {pc:04X}'
            assert not any(x in owner for x in range(pc,end)), f'Overlapping code at {pc:04X}'
            code[pc] = (end,txt)
            owner.update((x,pc) for x in range(pc,end))
            dests, fallthrough = control_edges(rom,pc,end,txt)
            for dest in dests:
                if BANK1_START <= dest < BANK1_END:
                    q.append((dest, f'branch at {pc:04X}'))
                elif 0 <= dest < 0x4000:
                    # Fixed bank available independently of slot-1 mapping.
                    continue
                else:
                    uncertain.add(f'{pc:04X} -> CPU {dest:04X}, slot-2 bank unknown')
            if not fallthrough:
                break
            pc=end
        if pc >= BANK1_END:
            uncertain.add(f'Fallthrough beyond bank-1 boundary at {pc:04X}')
    assert len(code) == 376 and len(owner) == 763, 'Bank-1 CFG changed; investigate before snapshot update'
    return roots, code, owner, sorted(uncertain)


def bank3_survey(rom):
    assert len(rom) == 262144
    # The bank-3 tail is a contiguous, unmistakable 0xFF pad run. Discover
    # it independently and reject any mismatch with the reported boundary.
    ptr = BANK3_END
    while ptr > BANK3_START and rom[ptr-1] == 0xFF:
        ptr -= 1
    assert ptr == DATA_BOUNDARIES[-1], f'Bank-3 padding boundary changed: {ptr:05X}'
    assert BANK3_END-ptr == 1843
    blocks=[]
    for a,b,name in zip(DATA_BOUNDARIES[:-1], DATA_BOUNDARIES[1:], DATA_NAMES):
        blob=rom[a:b]
        blocks.append({
            'offset_start':f'{a:05X}', 'offset_end_exclusive':f'{b:05X}',
            'size':len(blob), 'status':'provisional_opaque_data',
            'sha256':hashlib.sha256(blob).hexdigest(),
            'ff_bytes':blob.count(255),
            'byte_values_distinct':len(set(blob)),
            'notes':name,
        })
    return blocks, BANK3_END-ptr


def generate(rom):
    sha=hashlib.sha256(rom).hexdigest()
    assert sha==json.loads((ROOT/'manifest.json').read_text())['sha256'], 'Source ROM SHA-256 mismatch'
    roots,code,owner,unresolved=trace(rom)
    blocks,padding=bank3_survey(rom)
    all_prior=set(range(0x102))
    for p in (2,3,4):
        cfg=json.loads((ROOT/f'phase{p}/regions.json').read_text())
        for r in cfg['code']:
            all_prior.update(range(int(r['start'],16),int(r['end_exclusive'],16)))
        for r in cfg['data']:
            a=int(r['start'],16)
            all_prior.update(range(a,a+len(bytes.fromhex(r['hex']))))
    for p in (5,6):
        cfg=json.loads((ROOT/f'phase{p}/regions.json').read_text())
        if p==5:c,o,d,*_=phase5_analyze(rom,cfg)
        else:c,o,d,*_=phase6_analyze(rom,cfg)
        all_prior.update(o)
        all_prior.update(x for b in d for x in range(b[0],b[1]))
    assert len(all_prior)==21523, 'Earlier phase union has changed'
    region=set(x for b in blocks for x in range(int(b['offset_start'],16),int(b['offset_end_exclusive'],16)))
    assert len(region)==14541 and len(region & all_prior)==0
    assert len(set(owner)&all_prior)==0 and not set(owner)&region
    code_lines=[
        '; Phase 7: conservative bank-1 Z80 CFG from six prior fixed-bank references.',
        '; Mapping is CONDITIONAL on bank 1 being present at CPU $4000-$7FFF.',
        '; Not assembled, execution-traced, or a validated full-function map.',
        '; ROM    CPU   bytes               Z80',
    ]
    for pc,(end,instr) in sorted(code.items()):
        code_lines.append(f'{pc:05X} {pc:04X}  {rom[pc:end].hex(" ").upper():<19} {instr}')
    code_lines += ['', '; Provisional bank-3 opaque segments are separately SHA-256 anchored; bytes omitted.']
    for b in blocks:
        code_lines.append(f'; {b["offset_start"]}–{int(b["offset_end_exclusive"],16)-1:05X}: {b["size"]} bytes — {b["notes"]}')
    report={
        'source_sha256':sha,
        'interpretation':'Bank-1 CFG is conditional on mapper state; bank-3 non-padding spans are provisional opaque data, NOT a decoded graphics/text grammar',
        'bank1_direct_roots':{f'{k:04X}':[f'{x:04X}' for x in v] for k,v in roots.items()},
        'bank1_new_instructions':len(code),
        'bank1_new_instruction_bytes':len(owner),
        'bank1_code_sha256':hashlib.sha256(bytes(rom[x] for x in sorted(owner))).hexdigest(),
        'bank3_provisional_data_bytes':len(region),
        'bank3_segments':blocks,
        'bank3_ff_padding_excluded':padding,
        'phase7_candidate_total_new':len(owner)+len(region),
        'earlier_phase_1_to_6_classified':len(all_prior),
        'candidate_cumulative_coverage':len(all_prior)+len(owner)+len(region),
        'candidate_coverage_percent':round((len(all_prior)+len(owner)+len(region))/len(rom)*100,3),
        'unresolved_slot2_edges':unresolved,
        'not_proven':['bank-1 runtime occupancy at each caller',
                      'meaning or format of bank-3 data',
                      'byte-identical assembler output','emulator execution equivalence'],
    }
    return '\n'.join(code_lines)+'\n',json.dumps(report,indent=2)+'\n',report


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('rom',type=Path)
    x=ap.add_mutually_exclusive_group(required=True)
    x.add_argument('--write',action='store_true')
    x.add_argument('--check',action='store_true')
    a=ap.parse_args()
    rom=a.rom.read_bytes()
    listing,coverage,stats=generate(rom)
    dst=ROOT/'phase7'
    if a.write:
        (dst/'code.lst').write_text(listing)
        (dst/'coverage.json').write_text(coverage)
    else:
        assert (dst/'code.lst').read_text()==listing, 'Phase7 listing changed'
        assert (dst/'coverage.json').read_text()==coverage, 'Phase7 report changed'
    print('PASS Phase7: %d bank-1 instruction bytes + %d provisional bank-3 data bytes = %d new; %d cumulative candidate bytes' %
        (stats['bank1_new_instruction_bytes'],stats['bank3_provisional_data_bytes'],
         stats['phase7_candidate_total_new'],stats['candidate_cumulative_coverage']))

if __name__ == '__main__':
    try:main()
    except (AssertionError,ValueError,IndexError,OSError) as ex:sys.exit('FAIL Phase7: '+str(ex))
