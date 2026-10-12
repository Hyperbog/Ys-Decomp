#!/usr/bin/env python3
"""Generate and independently verify bank-separated source from audited Z80 listings.

The emitted ASM has instruction mnemonics, not embedded ROM opcode bytes.
Bank mapping uses the physical ROM offsets in each listing. Instructions remain
statically inferred until emulator execution corroborates their functions.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re

if __package__:
    from .z80_roundtrip_phase10 import assemble, encode
else:
    from z80_roundtrip_phase10 import assemble, encode

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'src' / 'phase10_roundtrip'
REPORT = ROOT / 'phase10' / 'roundtrip_report.json'
LISTINGS = (
    'phase5/code.lst', 'phase6/code.lst',
    'phase7/code.lst', 'phase8/banked_code.lst',
)
LINE = re.compile(
    r'^([0-9A-F]{5})\s+([0-9A-F]{4})\s+'
    r'((?:[0-9A-F]{2}\s+)+?)\s{2,}(\S.*)$', re.I)


def cpu_address(offset):
    """SMS fixed slots 0/1 and switchable 16-KiB slot 2."""
    return offset if offset < 0x8000 else 0x8000 + (offset & 0x3FFF)


def read_listings(root=ROOT):
    rows = []
    used = set()
    for name in LISTINGS:
        count = 0
        for line in (root / name).read_text().splitlines():
            m = LINE.match(line)
            if not m:
                continue
            offset, pc = int(m[1], 16), int(m[2], 16)
            expected, mnemonic = bytes.fromhex(m[3]), m[4].strip()
            assert cpu_address(offset) == pc, f'Incorrect mapper address: {name}: {offset:05X}'
            assert offset + len(expected) <= 0x40000, f'Out of ROM: {name}: {offset:05X}'
            span = set(range(offset, offset + len(expected)))
            assert not (used & span), f'Overlapping instruction: {name}: {offset:05X}'
            used.update(span)
            rows.append((offset, pc, mnemonic, expected, name))
            count += 1
        assert count, f'Empty listing: {name}'
    return sorted(rows)


def grouped(rows):
    banks = defaultdict(list)
    for row in rows:
        banks[row[0] >> 14].append(row)
    return dict(sorted(banks.items()))


def render(bank, rows):
    lines = [f'; Ys SMS: physical ROM bank {bank:02d}, 16-KiB banking',
             '; Generated from ROM-checked mnemonic listings, not original bytes.',
             '; A matching build is not proof these paths execute at runtime.', '']
    pc = None
    for offset, address, text, raw, source in rows:
        if pc != address:
            lines.append(f'org ${address:04X} ; physical ROM ${offset:05X}')
        lines.append(f'    {text:<25} ; ROM ${offset:05X} ({source})')
        pc = address + len(raw)
    return '\n'.join(lines) + '\n'


def compare(rom, root=ROOT, source=SOURCE, require_sources=True):
    rows = read_listings(root)
    banks = grouped(rows)
    assembled = set()
    stats = []
    for bank, items in banks.items():
        path = source / f'bank{bank:02d}.asm'
        generated = render(bank, items)
        if require_sources:
            assert path.read_text() == generated, f'Source differs: {path}'
        code, labels = assemble(path.read_text() if require_sources else generated)
        assert not labels, 'Symbolic labels not used in this generated source set'
        bank_bytes = 0
        for offset, pc, inst, from_listing, listing in items:
            # Three independent equality gates: encoder, listing, actual ROM.
            emitted = encode(inst, pc)
            assert emitted == from_listing, f'Listing/encoder mismatch ${offset:05X}: {inst}'
            assert emitted == rom[offset:offset+len(emitted)], f'ROM mismatch ${offset:05X}'
            assembled_at = bytes(code[a] for a in range(pc, pc+len(emitted)))
            assert assembled_at == emitted, f'ASM mismatch ${offset:05X}'
            for j in range(len(emitted)):
                assembled.add(offset+j)
            bank_bytes += len(emitted)
        assert len(code) == bank_bytes, f'Unexpected assembled bytes in bank {bank}'
        stats.append(dict(bank=bank, instructions=len(items), matched_bytes=bank_bytes,
                          first_offset=f'{items[0][0]:05X}',
                          last_offset=f'{items[-1][0]+len(items[-1][3])-1:05X}',
                          source=str(path.relative_to(root))))
    assert len(assembled) == sum(s['matched_bytes'] for s in stats)
    phase9 = set().union(*(set(range(a,b)) for a,b in (
        (0x05F2,0x0624), (0x06C1,0x06D4), (0x06D4,0x06E8), (0x0BA1,0x0BB7))))
    return dict(schema='ys-z80-phase10b-v1',
                rom_sha256=hashlib.sha256(rom).hexdigest(),
                inputs=list(LISTINGS),
                assembler='independent in-project Z80 mnemonic encoder; not an external assembler',
                matching_instructions=len(rows),
                newly_assembled_distinct_bytes=len(assembled),
                previously_assembled_phase9_bytes=len(phase9),
                phase9_overlap=len(assembled & phase9),
                total_distinct_assembler_matched_bytes=len(assembled | phase9),
                source_banks=stats,
                caveat='Existing decoded instruction classifications; no new ROM coverage or full ROM rebuild.')


def generate(rom, root=ROOT, source=SOURCE):
    manifest = json.loads((root/'manifest.json').read_text())
    assert len(rom) == 0x40000 and hashlib.sha256(rom).hexdigest() == manifest['sha256'], 'ROM fingerprint mismatch'
    source.mkdir(parents=True, exist_ok=True)
    for bank, rows in grouped(read_listings(root)).items():
        (source / f'bank{bank:02d}.asm').write_text(render(bank, rows))
    result = compare(rom, root, source)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    parser.add_argument('--write', action='store_true', help='write ASM source and reference report')
    parser.add_argument('--check', action='store_true', help='verify existing source and reference report')
    ns = parser.parse_args()
    rom = ns.rom.read_bytes()
    if ns.write:
        report = generate(rom)
        REPORT.write_text(json.dumps(report, indent=2) + '\n')
    else:
        manifest = json.loads((ROOT/'manifest.json').read_text())
        assert len(rom) == 0x40000 and hashlib.sha256(rom).hexdigest() == manifest['sha256'], 'ROM fingerprint mismatch'
        report = compare(rom)
        if ns.check:
            assert REPORT.read_text() == json.dumps(report, indent=2) + '\n', 'Report differs'
    print(f"MATCH {report['matching_instructions']} instructions / "
          f"{report['newly_assembled_distinct_bytes']} bytes; "
          f"cumulative unique {report['total_distinct_assembler_matched_bytes']} bytes")


if __name__ == '__main__':
    main()
