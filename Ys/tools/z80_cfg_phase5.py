#!/usr/bin/env python3
"""Conservative bank-aware Z80 control-flow snapshot for Ys SMS Phase 5.

Trace explicitly rooted code only. A bank-0 caller does NOT prove which ROM
bank is mapped at CPU $8000, so its slot-2 calls are never traversed.
Unresolved branches, indirect jumps, and out-of-window paths are recorded;
these code listings do not constitute emulator execution or assembled output.
"""
import argparse
from collections import defaultdict, deque
import hashlib
import json
from pathlib import Path
import sys

from z80_regions import decode

ROOT = Path(__file__).resolve().parents[1]
CODE_WINDOWS = ((0x0260, 0x0749), (0x0BEF, 0x2002), (0x8329, 0x8A58))
CONDITIONAL_JP = frozenset((0xC2, 0xCA, 0xD2, 0xDA, 0xE2, 0xEA, 0xF2, 0xFA))
CONDITIONAL_CALL = frozenset((0xC4, 0xCC, 0xD4, 0xDC, 0xE4, 0xEC, 0xF4, 0xFC))
CONDITIONAL_RET = frozenset((0xC0, 0xC8, 0xD0, 0xD8, 0xE0, 0xE8, 0xF0, 0xF8))
RELATIVE = frozenset((0x10, 0x18, 0x20, 0x28, 0x30, 0x38))
RETURN_ED = frozenset((0x45, 0x4D, 0x55, 0x5D, 0x65, 0x6D, 0x75, 0x7D))


def inside_window(offset):
    return any(a <= offset < z for a, z in CODE_WINDOWS)


def cpu_slot(addr):
    if 0 <= addr < 0x4000:
        return 0
    if 0x8000 <= addr < 0xC000:
        return 2
    return -1


def control_edges(rom, offset, next_offset, text):
    """Return (targets, can_fall_through); targets are CPU addresses.

    No interpretation is made of computed JP (HL/IX/IY) destinations.
    """
    op = rom[offset]
    if op in (0xDD, 0xFD):
        op = rom[offset+1]
    if op in RELATIVE:
        dest = int(text.rsplit('$', 1)[-1], 16)
        return (dest,), op != 0x18
    if op == 0xC3 or op in CONDITIONAL_JP:
        return (rom[next_offset-2] | (rom[next_offset-1] << 8),), op != 0xC3
    if op == 0xCD or op in CONDITIONAL_CALL:
        return (rom[next_offset-2] | (rom[next_offset-1] << 8),), True
    if op & 0xC7 == 0xC7:
        return (op & 0x38,), True
    if op in CONDITIONAL_RET:
        return (), True
    if op in (0xC9, 0xE9, 0x76):
        return (), False
    if op == 0xED and rom[offset+1] in RETURN_ED:
        return (), False
    return (), True


def old_classified(rom):
    """All Phase 1–4 accounted bytes; previously bounded code instruction map."""
    occupied = set(range(0x102))  # Phase 1 includes padding and data.
    previous_code = {}
    for phase in (2, 3, 4):
        cfg = json.loads((ROOT/f'phase{phase}/regions.json').read_text())
        for r in cfg['code']:
            a, z = int(r['start'], 16), int(r['end_exclusive'], 16)
            occupied.update(range(a, z))
            p = a
            while p < z:
                nxt, txt = decode(rom, p, (r['slot'] - r['bank']) * 0x4000)
                assert nxt <= z, f'Previous Phase {phase} instruction crosses boundary'
                previous_code[p] = (nxt, txt)
                p = nxt
        for d in cfg['data']:
            a = int(d['start'], 16)
            occupied.update(range(a, a + len(bytes.fromhex(d['hex']))))
    assert len(occupied) == 2068, f'Phase 1–4 coverage changed: {len(occupied)}'
    return occupied, previous_code


def analyze(rom, cfg):
    old, known_code = old_classified(rom)
    data_regions = []
    data_offsets = set()
    for d in cfg['data']:
        a, z = int(d['start'], 16), int(d['end_exclusive'], 16)
        assert a < z and not data_offsets.intersection(range(a, z))
        assert not old.intersection(range(a, z)), f'Data overlaps previously classified: {a:05X}'
        assert hashlib.sha256(rom[a:z]).hexdigest() == d['sha256'], f'Data digest mismatch: {a:05X}'
        data_offsets.update(range(a, z))
        data_regions.append((a, z, d['name']))

    # Root evidence: explicit decoder entries, the verified dispatch pointer
    # table ($8600-$8627), and direct jumps in pre-existing bounded code.
    roots = set(int(s, 16) for s in cfg['entrypoints'])
    table = rom[0x8600:0x8628]
    assert len(table) == 40 and 0x8600 in data_offsets
    targets = [int.from_bytes(table[i:i+2], 'little') for i in range(0, 40, 2)]
    assert all(0x8329 <= dest < 0x8A58 for dest in targets), 'Dispatcher target out of window'
    roots.update(targets)
    previous_edges = set()
    for pc, (end, text) in known_code.items():
        dests, _ = control_edges(rom, pc, end, text)
        for dest in dests:
            # Do not assume the bank-2 mapping for a caller in fixed bank 0.
            if inside_window(dest) and dest not in old and not (pc < 0x4000 and dest >= 0x8000):
                previous_edges.add(dest)
    roots.update(previous_edges)

    queue = deque((address, 'root') for address in sorted(roots) if inside_window(address))
    code = {}
    owner = {}
    incoming = defaultdict(set)
    unresolved = set()
    errors = []
    while queue:
        origin, reason = queue.popleft()
        incoming[origin].add(reason)
        if origin in old or not inside_window(origin):
            continue
        if origin in data_offsets:
            errors.append(f'Code target into anchored data: {origin:05X}')
            continue
        if origin in owner:
            if origin not in code:
                errors.append(f'Branch into middle of instruction: {origin:05X}')
            continue
        pc = origin
        while inside_window(pc):
            if pc in old or pc in code:
                break
            if pc in owner:
                errors.append(f'Overlapping code landing: {pc:05X}')
                break
            if pc in data_offsets:
                errors.append(f'Fallthrough enters anchored data: {pc:05X}')
                break
            end, txt = decode(rom, pc)
            if not inside_window(end-1):
                unresolved.add(f'Window boundary at {pc:05X}, ends {end:05X}')
                break
            overlap = [p for p in range(pc, end) if p in old or p in data_offsets or p in owner]
            if overlap:
                errors.append(f'Instruction overlap at {pc:05X}, prior byte {overlap[0]:05X}')
                break
            code[pc] = (end, txt)
            for p in range(pc, end):
                owner[p] = pc
            dests, fallthrough = control_edges(rom, pc, end, txt)
            for dest in dests:
                if cpu_slot(dest) == -1:
                    unresolved.add(f'Unmapped target: {pc:05X} -> CPU {dest:04X}')
                elif pc < 0x4000 and dest >= 0x8000:
                    unresolved.add(f'Unknown slot-2 bank: {pc:05X} -> CPU {dest:04X}')
                elif inside_window(dest) and dest not in old:
                    queue.append((dest, f'{pc:05X}'))
                elif dest not in old:
                    unresolved.add(f'Outside Phase 5 window: {pc:05X} -> CPU {dest:04X}')
            if not fallthrough:
                break
            pc = end
        if not inside_window(pc) and pc != origin:
            unresolved.add(f'Linear path reached Phase 5 window boundary at {pc:05X}')
    if errors:
        raise AssertionError('; '.join(sorted(set(errors))[:8]))
    if owner.keys() & data_offsets or owner.keys() & old:
        raise AssertionError('New code overlaps old classification or anchored data')
    return code, owner, data_regions, incoming, sorted(unresolved)


def output(rom, cfg):
    code, owner, data, incoming, unresolved = analyze(rom, cfg)
    lines = ['; Phase 5: anchored, bank-aware recursive Z80 listing',
             '; STATIC reachability only. NOT execution-traced or assembler-verified.',
             '; ROM offset  CPU addr  ROM bytes          decoded instruction', '']
    for pc, (end, mnemonic) in sorted(code.items()):
        cpu = pc   # only file banks 0 and 2 mapped into their matching slots
        bytestr = rom[pc:end].hex(' ').upper()
        lines.append(f'{pc:05X} {cpu:04X}  {bytestr:<19} {mnemonic}')
    lines += ['', '; ANCHORED NON-CODE TABLES (byte digests in regions.json)']
    for a, z, name in data:
        lines.append(f'; {a:05X}-{z-1:05X} ({z-a} bytes): {name}')
        for p in range(a, z, 16):
            lines.append(f'{p:05X} DATA  {rom[p:min(p+16,z)].hex(" ").upper()}')
    lines.append('')
    listing = '\n'.join(lines)
    bank0 = sum(p < 0x4000 for p in owner)
    bank2 = len(owner) - bank0
    info = {
        'scope': 'ROM-anchored static Z80 disassembly; not binary-rebuilt or runtime-confirmed',
        'rom_sha256': hashlib.sha256(rom).hexdigest(),
        'new_instruction_count': len(code),
        'new_code_bytes': len(owner),
        'new_code_bank0_bytes': bank0,
        'new_code_bank2_bytes': bank2,
        'new_data_bytes': sum(z-a for a, z, _ in data),
        'new_total_bytes': len(owner) + sum(z-a for a, z, _ in data),
        'cumulative_distinct_bytes': 2068+len(owner)+sum(z-a for a, z, _ in data),
        'unresolved_edges': unresolved,
        'seed_addresses': [f'{s:04X}' for s in sorted({int(s,16) for s in cfg['entrypoints']})],
        'dispatcher_targets_8600': [f'{int.from_bytes(rom[x:x+2],"little"):04X}' for x in range(0x8600,0x8628,2)],
        'code_byte_sha256': hashlib.sha256(bytes(rom[p] for p in sorted(owner))).hexdigest(),
        'data_byte_sha256': hashlib.sha256(bytes(rom[p] for d in data for p in range(d[0],d[1]))).hexdigest(),
    }
    return listing, json.dumps(info, indent=2)+'\n', info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write', action='store_true')
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    manifest = json.loads((ROOT/'manifest.json').read_text())
    assert hashlib.sha256(rom).hexdigest() == manifest['sha256'], 'Original ROM SHA-256 mismatch'
    cfg = json.loads((ROOT/'phase5/regions.json').read_text())
    listing, report, stats = output(rom, cfg)
    snapshot = ROOT/'phase5/code.lst'
    stats_path = ROOT/'phase5/coverage.json'
    if args.write:
        snapshot.write_text(listing)
        stats_path.write_text(report)
    else:
        assert snapshot.read_text() == listing, 'Phase 5 listing is not an exact byte/text match'
        assert stats_path.read_text() == report, 'Phase 5 coverage report changed'
    print(f"PASS Phase 5: {stats['new_instruction_count']} instructions, "
          f"{stats['new_code_bytes']} code bytes + {stats['new_data_bytes']} data bytes "
          f"= {stats['new_total_bytes']} new; cumulative {stats['cumulative_distinct_bytes']}")


if __name__ == '__main__':
    try:
        main()
    except (AssertionError, OSError, ValueError, IndexError) as exc:
        sys.exit(f'FAIL Phase 5: {exc}')
