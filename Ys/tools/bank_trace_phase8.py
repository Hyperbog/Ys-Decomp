#!/usr/bin/env python3
"""Phase 8: ROM-backed Sega mapper edge evidence and rooted slot-2 CFG.

This is path-local static evidence, not an emulator trace. Claims of a known
bank must come from immediate mapper writes or a documented same-routine path.
"""
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import sys

from z80_regions import decode
from z80_cfg_phase5 import old_classified, control_edges
from z80_cfg_phase5 import analyze as analyze5
from z80_cfg_phase6 import analyze as analyze6
from z80_bank1_phase7 import trace as analyze7

ROOT = Path(__file__).resolve().parents[1]
ROM_SHA = json.loads((ROOT/'manifest.json').read_text())['sha256']
# Root provenance deliberately explicit. The $47xx edges are conditional on
# entry through bank1 $476C, which writes bank 4 to $FFFF before those calls.
ROOTS = {
    4: {0x807C: ['bank1 $476C sets $FFFF=04 at $4773, calls at $47C2/$486C/$48DF']},
    7: {
        0x86C1: ['fixed $0DD5/$0DD7/$0DDA and $275F/$2761/$2764: bank 07'],
        0x8819: ['fixed $01C6/$01C8/$01CB: bank 07'],
        0x8856: ['fixed $26DD/$26DF/$26E2: bank 07'],
    },
    8: {0xBEE8: ['fixed $0FB1/$0FB3/$0FB6: bank 08']},
    10: {0xBEF7: ['fixed $3E86/$3E88/$3E8B: bank 0A']},
    12: {0x9EFC: ['fixed $3DC1/$3DC3/$3DC6: bank 0C']},
}


def known_instructions(rom):
    _, code = old_classified(rom)
    code.update(analyze5(rom, json.loads((ROOT/'phase5/regions.json').read_text()))[0])
    code.update(analyze6(rom, json.loads((ROOT/'phase6/regions.json').read_text()))[0])
    code.update(analyze7(rom)[1])
    return code


def mapper_audit(rom, code):
    by_end = {end: start for start, (end, _) in code.items()}
    audit=[]
    for pc, (end, _) in sorted(code.items()):
        if rom[pc:end] != b'\x32\xff\xff':
            continue
        prev = by_end.get(pc)
        value = rom[prev + 1] if prev is not None and rom[prev:pc] == b'\x3e' + bytes([rom[prev+1]]) else None
        next_i = code.get(end)
        next_direct = None
        if next_i is not None and rom[end] in (0xCD,0xC3):
            target=int.from_bytes(rom[end+1:end+3], 'little')
            if 0x8000 <= target < 0xC000:
                next_direct = f'{target:04X}'
        audit.append({'write_offset': f'{pc:05X}', 'bank_immediately_loaded':value,
                      'immediate_slot2_call_or_jump':next_direct})
    return audit


def walk_bank(rom, bank, roots):
    """Decode only slot-2-local paths; stop before mapper-changing instructions.

    A CALL to fixed bank may itself switch the slot-2 bank; we do not follow
    it into the callee and mark the downstream bank state as a caveat.
    """
    start = bank * 0x4000
    limit = start + 0x4000
    def physical(cpu): return start + cpu - 0x8000
    q = deque(sorted(roots))
    code, owners, uncertain = {}, {}, set()
    while q:
        cpu=q.popleft()
        if not 0x8000 <= cpu < 0xC000:continue
        pos=physical(cpu)
        while start <= pos < limit and pos not in owners:
            end, asm=decode(rom,pos,(2-bank)*0x4000)
            if end > limit: raise AssertionError(f'Bank {bank} crosses end at {pos:05X}')
            if any(p in owners for p in range(pos,end)):
                raise AssertionError(f'Bank {bank} overlaps instruction at {pos:05X}')
            code[pos]=(end,asm)
            owners.update((p,pos) for p in range(pos,end))
            # Slot2 remapping invalidates the current physical interpretation.
            if rom[pos:end] == b'\x32\xff\xff':
                uncertain.add(f'bank {bank} changes $FFFF at CPU {0x8000+pos-start:04X}; stop')
                break
            targets, follows=control_edges(rom,pos,end,asm)
            for t in targets:
                if 0x8000 <= t < 0xC000:
                    q.append(t)
                elif 0x4000 <= t < 0x8000:
                    uncertain.add(f'bank {bank} CPU {0x8000+pos-start:04X} -> slot1 ${t:04X} unresolved')
                elif t >= 0xC000:
                    uncertain.add(f'bank {bank} CPU {0x8000+pos-start:04X} -> RAM ${t:04X}')
            # Do not infer that fixed-bank calls preserve the mapper.
            if rom[pos] in (0xCD,0xC4,0xCC,0xD4,0xDC,0xE4,0xEC,0xF4,0xFC):
                if targets and targets[0] < 0x4000:
                    uncertain.add(f'bank {bank} CPU {0x8000+pos-start:04X} calls fixed ${targets[0]:04X}; mapper on return not dynamically verified')
            if not follows:break
            pos=end
        if pos in owners and pos not in code:
            raise AssertionError(f'Branch into instruction middle {pos:05X}')
    return code, owners, sorted(uncertain)


def generate(rom):
    assert hashlib.sha256(rom).hexdigest()==ROM_SHA, 'Wrong source ROM'
    prior=known_instructions(rom)
    audit=mapper_audit(rom,prior)
    # Mandatory exact, adjacent reset-to-call anchors; control-flow free here.
    for write,bank,call,dest in [(0x0DD7,7,0x0DDA,0x86C1),
                                 (0x0C4F,2,0x0C52,0x8803),
                                 (0x1D87,2,0x1D8A,0x8803),
                                 (0x01C8,7,0x01CB,0x8819),
                                 (0x026DF,7,0x026E2,0x8856),
                                 (0x02761,7,0x02764,0x86C1),
                                 (0x0FB3,8,0x0FB6,0xBEE8),
                                 (0x03DC3,12,0x03DC6,0x9EFC),
                                 (0x03E88,10,0x03E8B,0xBEF7)]:
        assert rom[write-2:write] == bytes([0x3E,bank])
        assert rom[write:write+3] == b'\x32\xff\xff'
        assert rom[call] in (0xC3,0xCD) and rom[call+1:call+3] == dest.to_bytes(2,'little')
    assert rom[0x4771:0x4776] == b'\x3e\x04\x32\xff\xff'
    for pc in (0x47C2,0x486C,0x48DF):
        assert rom[pc:pc+3] == b'\xcd\x7c\x80'
    lines=['; Phase 8: conditionally mapped slot-2 CFG; ROM bytes checked, no emulator execution',
           '; OFFSET CPU  BYTES               Z80']
    bank_reports={}
    total_owners=set()
    for bank in sorted(ROOTS):
        code,owner,uncertain=walk_bank(rom,bank,ROOTS[bank])
        assert not (total_owners & set(owner))
        total_owners.update(owner)
        lines.append(f'; BANK {bank} $8000–$BFFF: root(s) '+', '.join(f'${x:04X}' for x in ROOTS[bank]))
        for p,(end,inst) in sorted(code.items()):
            addr=0x8000+(p-bank*0x4000)
            lines.append(f'{p:05X} {addr:04X}  {rom[p:end].hex(" ").upper():<19} {inst}')
        bank_reports[str(bank)]={
            'roots':{f'{k:04X}':v for k,v in ROOTS[bank].items()},
            'instructions':len(code),'bytes':len(owner),
            'code_sha256':hashlib.sha256(bytes(rom[p] for p in sorted(owner))).hexdigest(),
            'uncertainties':uncertain,
        }
    # CPU $8000 in bank 4 is addressed by A*4 in $807C-$8082. The
    # bounded prefix before the first decoded instruction contains 31 x 4-byte
    # records; the format/meaning of fields is not yet determined.
    assert rom[0x1007C:0x10082] == bytes.fromhex('87 87 6F 26 80 7E')
    lookup = rom[0x10000:0x1007C]
    assert len(lookup) == 31*4
    table_metadata={
        'physical_start':'10000','physical_end_exclusive':'1007C',
        'cpu_start':'8000','records':31,'record_size':4,'bytes':len(lookup),
        'sha256':hashlib.sha256(lookup).hexdigest(),
        'indexing_evidence':'Bank4 $807C-$8082 doubles A twice, then dereferences $8000+A*4',
        'limitation':'Only the bounded prefix before code at $807C is counted; data semantics and valid indices unresolved',
    }
    reports={
      'source_sha256':ROM_SHA, 'status':'Static mapper-context reconstruction; not runtime-proven',
      'mapper_write_count':len(audit),
      'mapper_writes_with_adjacent_immediate_bank':sum(x['bank_immediately_loaded'] is not None for x in audit),
      'mapper_audit':audit,'banked_code':bank_reports,
      'new_distinct_code_bytes':len(total_owners),
      'bank4_indexed_table':table_metadata,
      'new_distinct_code_plus_table_bytes':len(total_owners)+len(lookup),
      'cumulative_candidate_coverage_bytes':36827+len(total_owners)+len(lookup),
      'new_distinct_instruction_starts':sum(x['instructions'] for x in bank_reports.values()),
      'caveat':'Branch entry must be reached with its advertised bank mapped; fixed-bank calls may change mapper state; no execution trace.'
    }
    return '\n'.join(lines)+'\n',json.dumps(reports,indent=2)+'\n',reports


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('rom',type=Path)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write',action='store_true')
    mode.add_argument('--check',action='store_true')
    args=parser.parse_args()
    listing,coverage,rep=generate(args.rom.read_bytes())
    out=ROOT/'phase8'
    if args.write:
        (out/'banked_code.lst').write_text(listing)
        (out/'mapper_audit.json').write_text(coverage)
    else:
        assert (out/'banked_code.lst').read_text()==listing
        assert (out/'mapper_audit.json').read_text()==coverage
    print(f"PASS Phase8 bank traces: {rep['new_distinct_code_bytes']} code bytes, "
          f"{rep['mapper_write_count']} mapper writes audited")

if __name__=='__main__':
    try:main()
    except (AssertionError,ValueError,IndexError,OSError) as ex:sys.exit('FAIL Phase8: '+str(ex))
