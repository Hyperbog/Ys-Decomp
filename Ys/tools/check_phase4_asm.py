#!/usr/bin/env python3
"""Check exact Z80 text and symbol placement in $81D9-$8203 (not assembly)."""
import hashlib
import json
from pathlib import Path
import re
import sys
from z80_regions import decode

ROOT = Path(__file__).resolve().parents[1]
ASM = ROOT / 'src/bank02_sound_dispatch.asm'
START, END = 0x81D9, 0x8204


def check(rom, source):
    data = rom.read_bytes()
    assert hashlib.sha256(data).hexdigest() == json.loads(
        (ROOT / 'manifest.json').read_text())['sha256'], 'ROM fingerprint mismatch'
    pc = None
    labels = {}
    instructions = []
    for no, raw in enumerate(source.read_text().splitlines(), 1):
        line = raw.split(';', 1)[0].strip().lower()
        if not line:
            continue
        if line.startswith('org '):
            assert pc is None and int(line[4:].strip().replace('$', '0x'), 16) == START, f'incorrect ORG on line {no}'
            pc = START
            continue
        assert pc is not None, f'missing ORG before line {no}'
        if line.endswith(':'):
            name = line[:-1]
            assert re.fullmatch(r'[a-z_][a-z_0-9]*', name), f'invalid label on line {no}'
            assert name not in labels, f'duplicate label {name}'
            labels[name] = pc
            continue
        nxt, expected = decode(data, pc)
        assert nxt <= END, f'instruction overruns $8203 at line {no}'
        instructions.append((no, pc, line, expected.lower()))
        pc = nxt
    assert pc == END, f'incomplete source: stopped at {pc:04X}'
    assert labels.get('sound_processpendingcommand') == START
    assert labels.get('sound_bc_bd') == 0x81F5
    for no, addr, actual, expected in instructions:
        for label in sorted(labels, key=len, reverse=True):
            actual = re.sub(r'\b' + label + r'\b', f'${labels[label]:04x}', actual)
        norm = lambda s: re.sub(r'\s+', ' ', re.sub(r'\s*,\s*', ',', s)).strip()
        assert norm(actual) == norm(expected), f'line {no} at {addr:04X}: {actual!r} != {expected!r}'
    return len(instructions), len(labels)


if __name__ == '__main__':
    try:
        if len(sys.argv) not in (2, 3):
            raise ValueError('Usage: check_phase4_asm.py original.sms [source.asm]')
        n, m = check(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) == 3 else ASM)
        print(f'PASS: {n} instructions and {m} symbols match ROM $81D9–$8203 (not assembled)')
    except (AssertionError, ValueError, OSError, IndexError) as exc:
        sys.exit(f'FAIL: {exc}')
