#!/usr/bin/env python3
"""Build a bank-aware *static evidence* graph from already ROM-matched Z80 sources.

No speculative linear disassembly. All instructions are independently checked
against the supplied ROM byte offsets before entering the graph. Targets in
mapper-controlled slots are candidates, not proven runtime bank assignments.
This is NOT a full-system emulator trace, type/SSA inference, or source build.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
sys.path.insert(0, str(ROOT.parent))
from shared_decomp.evidence import validate_graph  # noqa: E402
from build_sms_phase14 import SOURCES, offset, validated_rom, EXPECTED_SHA  # noqa: E402
from z80_roundtrip_phase10 import encode  # noqa: E402
from z80_regions import decode  # noqa: E402

BANK_SIZE = 0x4000
MODULES = tuple(SOURCES) + (('src/wholebank07/late_code.asm', 7),)
CONTROL = {'jr', 'djnz', 'jp', 'call', 'ret', 'reti', 'retn', 'rst', 'halt'}
CONDITIONS = {'nz', 'z', 'nc', 'c', 'po', 'pe', 'p', 'm'}
HEX = re.compile(r'^\$([0-9a-f]{1,4})$', re.I)
ORG = re.compile(r'^org\s+\$([0-9a-f]{4})\b', re.I)
ADDR = re.compile(r'\(\$([0-9a-f]{4})\)', re.I)
PORT = re.compile(r'^(in|out)\s+.*?\(\$([0-9a-f]{2})\)', re.I)


def parse_source(path, bank, rom):
    """Strictly parse a mnemonic-only source module and check every byte."""
    pc = None
    for line_no, line in enumerate(path.read_text().splitlines(), 1):
        s = line.split(';', 1)[0].strip()
        if not s or s.endswith(':'):
            continue
        mo = ORG.fullmatch(s)
        if mo:
            pc = int(mo.group(1), 16)
            continue
        if pc is None or re.match(r'^(db|dw|ds|incbin|org)\b', s, re.I):
            raise ValueError(f'{path}:{line_no}: invalid instruction-only source')
        emitted = encode(s, pc)
        if not emitted:
            raise ValueError(f'{path}:{line_no}: empty encoding')
        at = offset(bank, pc)
        if at + len(emitted) > (bank + 1) * BANK_SIZE:
            raise ValueError(f'{path}:{line_no}: instruction crosses physical bank')
        expected = rom[at:at + len(emitted)]
        if expected != emitted:
            raise ValueError(f'{path}:{line_no}: original ROM mismatch at {at:05X}')
        end, _ = decode(rom, at, pc - at)
        if end - at != len(emitted):
            raise ValueError(f'{path}:{line_no}: decoder disagrees on instruction length at {at:05X}')
        yield {'id': f'{at:05X}', 'bank': bank, 'pc': f'{pc:04X}',
               'offset': at, 'size': len(emitted), 'asm': s.lower(),
               'source': str(path.relative_to(ROOT)), 'line': line_no}
        pc += len(emitted)


def flow(node):
    """Return (edge kind, target CPU or None, conditional, fallthrough)."""
    words = node['asm'].split(None, 1)
    op = words[0]
    if op not in CONTROL:
        return None, None, False, True
    operand = words[1].strip() if len(words) > 1 else ''
    if op in ('reti', 'retn', 'halt'):
        return op, None, False, False
    if op == 'ret':
        return 'return', None, operand in CONDITIONS, operand in CONDITIONS
    if op == 'jp' and operand.startswith('('):
        return 'indirect_jump', None, False, False
    tail = operand.split(',')[-1].strip()
    match = HEX.fullmatch(tail)
    conditional = op == 'djnz' or (',' in operand and operand.split(',')[0].strip() in CONDITIONS)
    if op == 'rst':
        conditional = False
    if not match:
        raise ValueError(f'unhandled control target at {node["id"]}: {node["asm"]}')
    target = int(match.group(1), 16)
    if op == 'rst':
        return 'call', target, False, True
    if op == 'call':
        return 'call', target, conditional, True
    return 'branch', target, conditional, conditional


def io_effects(node):
    asm = node['asm']
    effects = []
    match = PORT.match(asm)
    if match:
        effects.append({'kind': 'io_write' if match.group(1) == 'out' else 'io_read', 'port': match.group(2).upper()})
    if asm.startswith(('outi', 'otir', 'outd', 'otdr')):
        effects.append({'kind': 'io_write', 'port': 'C', 'port_source': 'dynamic_register'})
    if asm.startswith(('ini', 'inir', 'ind', 'indr')):
        effects.append({'kind': 'io_read', 'port': 'C', 'port_source': 'dynamic_register'})
    if asm.startswith('out (c),'):
        effects.append({'kind': 'io_write', 'port': 'C', 'port_source': 'dynamic_register'})
    if asm.startswith('in ') and '(c)' in asm:
        effects.append({'kind': 'io_read', 'port': 'C', 'port_source': 'dynamic_register'})
    if asm.startswith('ld '):
        m = re.match(r'^ld\s+([^,]+),(.+)$', asm)
        if m:
            left, right = m.group(1).strip(), m.group(2).strip()
            write = ADDR.fullmatch(left)
            read = ADDR.fullmatch(right)
            for hit, kind in ((write, 'absolute_memory_write'), (read, 'absolute_memory_read')):
                if hit:
                    cpu = int(hit.group(1), 16)
                    effects.append({'kind': kind, 'cpu_address': f'{cpu:04X}',
                                    'address_class': 'ram_or_mapper' if cpu >= 0xC000 else 'rom_window',
                                    **({'mapper_register': True} if kind == 'absolute_memory_write' and 0xFFFC <= cpu <= 0xFFFF else {})})
    return effects


def hints():
    path = ROOT/'phase15/symbols.json'
    data = json.loads(path.read_text())
    lookup = {}
    for item in data['references']:
        if 'static_target_bank_candidate' in item:
            key = (item['from_bank'], int(item['from_cpu'], 16), int(item['target_cpu'], 16))
            lookup[key] = (item['static_target_bank_candidate'], item.get('static_bank_evidence'))
    return lookup


def build(rom, *, modules=MODULES):
    validated_rom(rom)
    instructions = {}
    bytes_owned = {}
    for relative, bank in modules:
        for n in parse_source(ROOT/relative, bank, rom):
            if n['offset'] in instructions:
                raise ValueError(f'overlapping instruction starts: {n["id"]}')
            for i in range(n['offset'], n['offset'] + n['size']):
                if i in bytes_owned:
                    raise ValueError(f'overlap at {i:05X} (previous {bytes_owned[i]:05X})')
                bytes_owned[i] = n['offset']
            instructions[n['offset']] = n
    known = set(instructions)
    hint_map = hints()
    edges = []
    leaders = set()
    effect_rows = []
    for p, n in sorted(instructions.items()):
        prev = p - 1
        if prev not in bytes_owned or bytes_owned[prev] + instructions[bytes_owned[prev]]['size'] != p:
            leaders.add(p)
        cpu = int(n['pc'], 16)
        after_cpu = cpu + n['size']
        after_offset = p + n['size']
        kind, target, conditional, falls = flow(n)
        n['flow_type'] = kind or 'sequential'
        e = io_effects(n)
        if e:
            effect_rows.append({'instruction_id': n['id'], 'effects': e})
        if target is not None:
            target_bank = None
            resolution = 'unresolved_mapper_slot'
            evidence = None
            if target < 0x4000:
                target_bank, resolution = 0, 'fixed_bank0'
            elif target >= 0xC000:
                resolution = 'non_rom_address'
            else:
                hint = hint_map.get((n['bank'], cpu, target))
                if hint and target >= 0x8000:
                    target_bank, resolution, evidence = hint[0], 'static_mapper_candidate', hint[1]
                elif (0x4000 <= target < 0x8000 and n['bank'] == 1) or (0x8000 <= target < 0xC000 and n['bank'] >= 2):
                    target_bank, resolution = n['bank'], 'same_image_candidate'
            dest = None
            if target_bank is not None:
                try:
                    proposed = offset(target_bank, target)
                except ValueError:
                    proposed = None
                if proposed in known:
                    dest = f'{proposed:05X}'
                    # Every local branch/call destination starts a block.
                    if target_bank == n['bank']:
                        leaders.add(proposed)
            edges.append({'from': n['id'], 'kind': kind, 'to_cpu': f'{target:04X}',
                          'to_bank_candidate': target_bank, 'to_instruction': dest,
                          'resolution': resolution, 'mapping_evidence': evidence,
                          'conditional': conditional})
        if kind in ('return', 'reti', 'retn', 'indirect_jump', 'halt'):
            edges.append({'from': n['id'], 'kind': kind, 'to_cpu': None, 'to_instruction': None,
                          'resolution': 'non_static_exit', 'conditional': conditional})
        if falls:
            if after_offset in known and (after_cpu < 0x4000 if n['bank'] == 0 else after_cpu < (0x8000 if n['bank'] == 1 else 0xC000)):
                edges.append({'from': n['id'], 'kind': 'fallthrough', 'to_cpu': f'{after_cpu:04X}',
                              'to_bank_candidate': n['bank'], 'to_instruction': f'{after_offset:05X}',
                              'resolution': 'contiguous_instruction', 'conditional': False})
                if kind is not None:
                    leaders.add(after_offset)
            else:
                edges.append({'from': n['id'], 'kind': 'unresolved_fallthrough', 'to_cpu': f'{after_cpu & 0xFFFF:04X}',
                              'to_bank_candidate': n['bank'], 'to_instruction': None,
                              'resolution': 'not_in_verified_code', 'conditional': False})
    # A basic block includes straight-line instructions up to a leader or control terminator.
    blocks = []
    current = None
    for p, node in sorted(instructions.items()):
        if current is None or p in leaders or current['last_offset'] + current['last_size'] != p:
            if current is not None:
                current.pop('last_offset'); current.pop('last_size'); blocks.append(current)
            current = {'id': node['id'], 'bank': node['bank'], 'cpu_start': node['pc'],
                       'offset': p, 'instruction_count': 0, 'byte_count': 0, 'last_offset': p, 'last_size': 0}
        current['instruction_count'] += 1
        current['byte_count'] += node['size']
        current['last_offset'], current['last_size'] = p, node['size']
        # Block termination is explicit; otherwise a jump can land after a dead predecessor.
        if node['flow_type'] != 'sequential':
            current.pop('last_offset'); current.pop('last_size'); blocks.append(current)
            current = None
    if current is not None:
        current.pop('last_offset'); current.pop('last_size'); blocks.append(current)
    block_for = {}
    for b in blocks:
        for pos in sorted(p for p in known if b['offset'] <= p < b['offset'] + b['byte_count']):
            if instructions[pos]['bank'] == b['bank']:
                block_for[pos] = b['id']
    # Block spans are contiguous and no bytes can be owned twice.
    if len(block_for) != len(known):
        raise ValueError('basic block partition invalid')
    for edge in edges:
        edge['from_block'] = block_for[int(edge['from'], 16)]
        edge['to_block'] = block_for[int(edge['to_instruction'], 16)] if edge.get('to_instruction') else None
    topology = validate_graph([instructions[p] for p in sorted(instructions)], blocks, edges, len(rom))
    if not topology['valid']:
        raise ValueError(f'graph topology invalid: {topology["errors"][:5]}')
    bank_stats = []
    for bank in range(16):
        ns = [x for x in instructions.values() if x['bank'] == bank]
        bs = [x for x in blocks if x['bank'] == bank]
        bank_stats.append({'bank': bank, 'instruction_count': len(ns), 'verified_code_bytes': sum(x['size'] for x in ns),
                           'basic_blocks': len(bs), 'static_edges': sum(x['from_block'] in {b['id'] for b in bs} for x in edges)})
    direct_counts = dict(sorted(Counter(e['resolution'] for e in edges).items()))
    report = {'schema': 'ys-mapper-aware-evidence-graph-v1', 'original_rom_sha256': EXPECTED_SHA,
              'scope': 'Only instruction positions supplied by already-ROM-verified assembly sources; no speculative code discovery',
              'summary': {'verified_instruction_count': len(instructions), 'verified_instruction_bytes': len(bytes_owned),
                          'basic_blocks': len(blocks), 'edges': len(edges), 'portable_topology_validated': topology['valid'], 'hardware_or_absolute_memory_instruction_sites': len(effect_rows),
                          'edge_resolution_counts': direct_counts},
              'banks': bank_stats, 'instructions': [instructions[p] for p in sorted(instructions)],
              'blocks': blocks, 'edges': edges, 'effects': effect_rows,
              'limitations': ['Same-image edges are static candidates, not mapper-state proof.',
                              'External emulator traces and independent assemblers have not been run.',
                              'CFG covers verified Z80 assembly only, not all ROM content.',
                              'Flow edges are syntax-derived and do not imply runtime reachability.']}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    report = build(args.rom.read_bytes())
    if args.output:
        if args.check:
            if json.loads(args.output.read_text()) != report:
                raise ValueError('evidence graph differs from committed snapshot')
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    print(json.dumps(report['summary'], sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
