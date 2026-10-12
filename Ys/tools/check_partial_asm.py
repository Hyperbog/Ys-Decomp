#!/usr/bin/env python3
"""Verify annotated partial Z80 assembly against ROM-decoded mnemonics.

This is NOT an assembler and does not establish emitted binary equivalence.
Usage: python tools/check_partial_asm.py original.sms [annotated.asm]
"""
import hashlib
import json
from pathlib import Path
import re
import sys

from z80_regions import decode

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ASM = ROOT / 'src/bank02_update.asm'


def check(rom, asm):
    data = rom.read_bytes()
    sha = json.loads((ROOT / 'manifest.json').read_text())['sha256']
    assert hashlib.sha256(data).hexdigest() == sha, 'ROM SHA-256 mismatch'
    pc = None
    symbols = {}
    instructions = []
    for line_no, line in enumerate(asm.read_text().splitlines(), 1):
        line = line.split(';', 1)[0].strip().lower()
        if not line:
            continue
        if line.startswith('org '):
            assert pc is None, f'multiple ORGs, line {line_no}'
            pc = int(line[4:].strip().replace('$', '0x'), 16)
            assert pc == 0x8000, 'source starts outside verified bank-2 region'
            continue
        assert pc is not None, f'no ORG before line {line_no}'
        if line.endswith(':'):
            name = line[:-1]
            assert re.fullmatch(r'[a-z_][a-z_0-9]*', name), 'invalid symbol'
            assert name not in symbols, f'duplicate symbol: {name}'
            symbols[name] = pc
            continue
        end, expected = decode(data, pc)
        assert end <= 0x808F, f'source overruns bounded ROM region at {pc:04X}'
        instructions.append((line_no, pc, line, expected.lower()))
        pc = end
    assert pc == 0x808F, f'source ends at {pc:04X}; expected 808F'
    for line_no, address, line, expected in instructions:
        for label in sorted(symbols, key=len, reverse=True):
            line = re.sub(r'\b' + label + r'\b', f'${symbols[label]:04x}', line)
        normalize = lambda s: re.sub(r'\s+', ' ', re.sub(r'\s*,\s*', ',', s)).strip()
        assert normalize(line) == normalize(expected), (
            f'line {line_no} at {address:04X}: source {line!r} != ROM {expected!r}')
    return len(instructions), len(symbols)


if __name__ == '__main__':
    try:
        if len(sys.argv) not in (2, 3):
            raise ValueError(__doc__)
        asm_path = Path(sys.argv[2]) if len(sys.argv) == 3 else DEFAULT_ASM
        count, labels = check(Path(sys.argv[1]), asm_path)
        print(f'PASS: {count} assembly instructions and {labels} symbols '
              f'checked at bank 2 $8000–$808E (not assembled)')
    except (AssertionError, ValueError, OSError, IndexError) as exc:
        sys.exit(f'FAIL: {exc}')
