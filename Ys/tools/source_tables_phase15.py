#!/usr/bin/env python3
"""Generate and assemble Ys SMS source-backed DB/DW tables, without reading a ROM.

Only pointer tables whose values are supported by existing committed ledgers
and the already-published cartridge header are included. Their source files
can be assembled without possessing the game's ROM. Raw graphics, sprites,
and audio streams are deliberately NOT embedded in this repository.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    0: 'src/phase15/bank00_tables.asm',
    1: 'src/phase15/bank01_header.asm',
    6: 'src/phase15/bank06_tables.asm',
    7: 'src/phase15/bank07_tables.asm',
}


def metadata(root=ROOT):
    read = lambda file: json.loads((root / file).read_text(encoding='utf-8'))
    state = read('phase6/coverage.json')['dispatch_tables']
    bank6 = read('phase11/bank6_records.json')['records_by_directory_index']
    sprite = read('phase12/sprite_pipeline.json')
    bank7 = read('phase13/graphics_directory.json')['graphics_records']
    header = bytes.fromhex(read('manifest.json')['header_bytes'])
    assert len(header) == 16 and header[:8] == b'TMR SEGA'
    assert len(bank6) == len(bank7) == 64
    assert all(r['index'] == i for i, r in enumerate(bank6))
    assert all(r['index'] == i for i, r in enumerate(bank7))
    assert len(state['205A']) == 41 and len(state['2C24']) == 9
    return {
        0: [(0x205A, 'GameStateDispatch', [int(x, 16) for x in state['205A']], 'dw'),
            (0x2C24, 'SceneDispatch', [int(x, 16) for x in state['2C24']], 'dw')],
        1: [(0x7FF0, 'SegaCartridgeHeader', list(header), 'db')],
        6: [(0x8000, 'SpriteRecordDirectory', [int(r['cpu_address'], 16) for r in bank6], 'dw'),
            (0x9A77, 'ObjectWorkDirectory', list(range(0xC200, 0xC501, 0x30)), 'dw'),
            (0x9A99, 'SpriteHandlerDirectory', [int(x, 16) for x in sprite['handler_dispatch']['targets']], 'dw')],
        7: [(0x8000, 'GraphicsDispatchDirectory',
             [int(v, 16) for r in bank7 for v in (r['unrolled_entry_cpu'], r['graphics_source_cpu'])], 'dw'),
            (0x8100, 'SecondaryRecordDirectory',
             [int(r['secondary_record_cpu'], 16) for r in bank7], 'dw')],
    }


def generated_sources(root=ROOT):
    result = {}
    for bank, sections in metadata(root).items():
        lines = [f'; Ys SMS physical ROM bank {bank:02d}; source-only reconstructed pointers/header',
                 '; Values derived from reviewed phase ledgers, not from ROM at assembly time.', '']
        for start, name, entries, directive in sections:
            lines += [f'org ${start:04X}', name + ':']
            for at in range(0, len(entries), 8):
                lines.append('    ' + directive + ' ' + ', '.join(
                    f'${v:04X}' if directive == 'dw' else f'${v:02X}'
                    for v in entries[at:at + 8]))
            lines.append('')
        result[bank] = '\n'.join(lines).rstrip() + '\n'
    return result


def assemble_data(source):
    """Minimal independent DB/DW assembler: no instruction encoder or input ROM."""
    emitted = {}
    labels = {}
    pc = None
    for index, line in enumerate(source.splitlines(), 1):
        text = line.split(';', 1)[0].strip()
        if not text:
            continue
        m = re.fullmatch(r'org\s+\$([0-9a-fA-F]{1,4})', text, re.IGNORECASE)
        if m:
            pc = int(m[1], 16)
            continue
        if re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*:', text):
            if pc is None or text[:-1] in labels:
                raise ValueError(f'invalid/duplicate label line {index}')
            labels[text[:-1]] = pc
            continue
        m = re.fullmatch(r'(db|dw)\s+(.+)', text, re.IGNORECASE)
        if not m or pc is None:
            raise ValueError(f'invalid data source line {index}: {text}')
        mode = m[1].lower()
        for value in m[2].split(','):
            value = value.strip()
            if not re.fullmatch(r'\$[0-9a-fA-F]{1,4}', value):
                raise ValueError(f'invalid literal line {index}: {value}')
            number = int(value[1:], 16)
            if number > (0xFF if mode == 'db' else 0xFFFF):
                raise ValueError(f'out of range at line {index}')
            for byte in ([number] if mode == 'db' else [number & 0xFF, number >> 8]):
                if pc in emitted:
                    raise ValueError(f'overlapping source tables CPU ${pc:04X}')
                emitted[pc] = byte
                pc += 1
    return emitted, labels


def load_verified_sources(root=ROOT):
    expected = generated_sources(root)
    return_result = {}
    for bank, relative in SOURCES.items():
        file = root / relative
        actual = file.read_text(encoding='utf-8')
        if actual != expected[bank]:
            raise ValueError(f'structured table source drift: {relative}')
        emitted, labels = assemble_data(actual)
        return_result[bank] = {'bytes': emitted, 'labels': labels,
                               'sha256': hashlib.sha256(actual.encode()).hexdigest(),
                               'relative': relative}
    return return_result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sync', action='store_true', help='write reproducible table assembly files')
    parser.add_argument('--verify', action='store_true', help='verify committed table sources')
    args = parser.parse_args()
    if args.sync:
        for bank, text in generated_sources().items():
            target = ROOT / SOURCES[bank]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding='utf-8')
            print('Wrote', target.relative_to(ROOT))
    if args.verify or not args.sync:
        tables = load_verified_sources()
        for bank, info in tables.items():
            print(f'Bank {bank:02}: {len(info["bytes"])} source-generated bytes; {len(info["labels"])} labels')


if __name__ == '__main__':
    main()
