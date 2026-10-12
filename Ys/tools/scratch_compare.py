#!/usr/bin/env python3
"""Local function/region matching loop for sparse Z80 source.

Inspired by decomp.me's small, iterative comparisons, but runs offline.
This is NOT an external assembler or an emulator. It verifies bytes emitted
by the project's existing restricted Z80 encoder against an identified ROM.
"""
import argparse
import hashlib
import json
from pathlib import Path
from z80_roundtrip_phase10 import assemble

ROM_SHA256 = '02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9'
ROM_LENGTH = 262144
BANK_SIZE = 0x4000


def file_offset(bank, address):
    if not 0 <= bank < ROM_LENGTH // BANK_SIZE:
        raise ValueError('Physical bank must be 0..15')
    slot_start = 0x0000 if bank == 0 else (0x4000 if bank == 1 else 0x8000)
    if not slot_start <= address < slot_start + BANK_SIZE:
        raise ValueError(f'CPU ${address:04X} is not inside bank {bank} slot')
    return bank * BANK_SIZE + (address - slot_start)


def compare(rom, source, bank, max_differences=8):
    if len(rom) != ROM_LENGTH or hashlib.sha256(rom).hexdigest() != ROM_SHA256:
        raise ValueError('Wrong ROM size or SHA-256')
    if max_differences < 1:
        raise ValueError('max_differences must be >= 1')
    built, labels = assemble(source)
    if not built:
        raise ValueError('Source emitted no instructions')
    equal = 0
    errors = []
    count_errors = 0
    # Sort by logical CPU address; mapping is fixed to one physical bank.
    for cpu, generated in sorted(built.items()):
        physical = file_offset(bank, cpu)
        expected = rom[physical]
        if generated == expected:
            equal += 1
            continue
        count_errors += 1
        if len(errors) < max_differences:
            errors.append({
                'cpu_address': f'{cpu:04X}',
                'rom_offset': f'{physical:05X}',
                'expected_opcode': f'{expected:02X}',
                'emitted_opcode': f'{generated:02X}',
            })
    return {
        'schema': 'ys-local-z80-scratch-v1',
        'bank': bank,
        'rom_sha256': ROM_SHA256,
        'assembler': 'in-project restricted Z80 encoder (not external)',
        'emitted_bytes': len(built),
        'matching_bytes': equal,
        'mismatching_bytes': count_errors,
        'exact_match': count_errors == 0,
        'matching_percent_within_source': round(equal * 100 / len(built), 4),
        'label_count': len(labels),
        'differences': errors,
        'limitations': 'A sparse source match does not establish runtime behavior, complete ROM reconstruction, or code/data semantic correctness.'
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom', type=Path, help='Locally supplied original Ys .sms')
    p.add_argument('--source', type=Path, required=True, help='A small Z80 .asm region to match')
    p.add_argument('--bank', type=int, required=True, help='Physical 16-KiB ROM bank, 0..15')
    p.add_argument('--json', type=Path, help='Optional metadata report (contains no ROM payload)')
    p.add_argument('--max-differences', type=int, default=8)
    args = p.parse_args()
    result = compare(args.rom.read_bytes(), args.source.read_text(), args.bank, args.max_differences)
    print(f"Bank {args.bank}: {result['matching_bytes']}/{result['emitted_bytes']} bytes match ({result['matching_percent_within_source']:.2f}%)")
    for d in result['differences']:
        print(f"  ${d['rom_offset']}: expected {d['expected_opcode']}, emitted {d['emitted_opcode']}")
    if args.json:
        args.json.write_text(json.dumps(result, indent=2) + '\n')
    raise SystemExit(0 if result['exact_match'] else 1)


if __name__ == '__main__':
    main()
