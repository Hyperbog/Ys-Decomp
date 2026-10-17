#!/usr/bin/env python3
"""PC-45: source-backed 41-entry Ys resource/dispatch route audit.

The fields below are interpreted only where fixed-bank Z80 proves a use.
Neither directory indices nor compression pointers identify a game scene.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROM_SHA = '02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9'
DIRECTORY, RECORDS, DISPATCH = 0x2533, 0x2585, 0x205A
COUNT, UNIQUE, WIDTH = 41, 23, 9
# Independently observed fixed-bank original opcode fragments; checking these
# does not claim that every record is reached in an original execution.
LOADER_OPCODES = {
    0x1FE3: '3a81c1', 0x1FE6: '213325', 0x1FE9: 'df',
    0x1FEB: '32ffff', 0x202B: '7e', 0x202C: '3293c1',
    0x2030: '7e', 0x2031: '3294c1', 0x2035: '7e',
    0x2036: 'e60f', 0x2038: '321dc1', 0x203B: 'af',
    0x203C: 'cb7e', 0x203E: '2801', 0x2040: '3c',
    0x2041: '3298c1', 0x2044: 'af', 0x2045: 'cb76',
    0x2047: '2801', 0x2049: '3c', 0x204A: '329ac1',
    0x204F: '32ffff', 0x2052: '3a81c1', 0x2055: '215a20',
    0x2058: 'cf',
}


def strict_json(path):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'duplicate JSON key: {key}')
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding='utf-8'),
                      object_pairs_hook=unique_pairs)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def word_bytes(words):
    if any(type(x) is not int or not 0 <= x <= 65535 for x in words):
        raise ValueError('Invalid directory/dispatch word')
    return b''.join(w.to_bytes(2, 'little') for w in words)


def analyze(bank, phase21, phase6, regions, rom=None, pc44=None):
    """Returns an address/flag report; never mutates supplied ROM or sources."""
    segments = [s for s in bank['segments']
                if s.get('name') == 'nine_byte_resource_directory_41']
    if bank['schema'] != 'ys-whole-bank00-v1' or len(segments) != 1:
        raise ValueError('Bank0 record directory source changed')
    segment = segments[0]
    if (segment['start'], segment['end'], segment['kind']) != (
            DIRECTORY, RECORDS, 'pointer_words'):
        raise ValueError('Resource directory bounds/type mismatch')
    words = segment['words']
    if type(words) is not list or len(words) != COUNT:
        raise ValueError('Resource directory count mismatch')
    # 23 unique records, then 18 aliases of the last record. Their
    # alignment and aliases are observed data, NOT guessed scene IDs.
    expected = [RECORDS + WIDTH * min(i, UNIQUE - 1) for i in range(COUNT)]
    if words != expected:
        raise ValueError('Resource indices no longer match 23 bounded records')
    directory = word_bytes(words)

    if (phase21['schema'] != 'ys-phase21-typed-audio-and-glyph-lanes-v1'
            or phase21['provenance']['source_rom_sha256'] != ROM_SHA):
        raise ValueError('Typed record provenance mismatch')
    rows = phase21['bank0_indexed_records']
    if type(rows) is not list or len(rows) != UNIQUE:
        raise ValueError('Nine-byte resource count changed')
    records = []
    for i, record in enumerate(rows):
        if type(record) is not dict or set(record) != {'index', 'bytes'} or record['index'] != i:
            raise ValueError('Record index/schema mismatch')
        data = record['bytes']
        if (type(data) is not list or len(data) != WIDTH or
                any(type(v) is not int or not 0 <= v <= 255 for v in data)):
            raise ValueError('Invalid nine-byte record')
        if any(data[j] not in range(16) for j in (0, 3)):
            raise ValueError('Unmappable cartridge bank')
        if any(not 0x8000 <= (data[j] | data[j + 1] << 8) < 0xC000
               for j in (1, 4)):
            raise ValueError('Resource pointer outside mapper slot 2')
        # Based on bank0 $1FEA-$2058: two source banks/pointers,
        # two raw state bytes, one bitfield with three proven uses.
        flags = data[8]
        records.append({
            'address': f'{RECORDS + WIDTH * i:04X}',
            'first_bank': data[0],
            'first_cpu_pointer': f'{data[1] | data[2] << 8:04X}',
            'second_bank': data[3],
            'second_cpu_pointer': f'{data[4] | data[5] << 8:04X}',
            'C193': data[6], 'C194': data[7],
            'C11D_masked': flags & 0x0F,
            'C198': int(bool(flags & 0x80)),
            'C19A': int(bool(flags & 0x40)),
            'unresolved_flags_4_5': flags & 0x30,
        })
    payload = bytes(v for row in rows for v in row['bytes'])

    raw_targets = phase6['dispatch_tables']['205A']
    if type(raw_targets) is not list or len(raw_targets) != COUNT:
        raise ValueError('41-way state dispatch changed')
    if any(type(s) is not str or len(s) != 4 or
           any(c not in '0123456789ABCDEF' for c in s) for s in raw_targets):
        raise ValueError('Dispatch entry encoding changed')
    targets = [int(s, 16) for s in raw_targets]
    if any(not 0x2000 <= pc <= 0x251E for pc in targets):
        raise ValueError('Dispatch destination outside confirmed routines')
    dispatch_bytes = word_bytes(targets)

    canonical = {(int(s['start'], 16), int(s['end_exclusive'], 16)): s['sha256']
                 for s in regions['data']}
    for span, actual in [((DIRECTORY, RECORDS), directory),
                         ((RECORDS, RECORDS + UNIQUE * WIDTH), payload),
                         ((DISPATCH, DISPATCH + COUNT * 2), dispatch_bytes)]:
        if digest(actual) != canonical[span]:
            raise ValueError(f'Source digest mismatch in ${span[0]:04X}')

    if rom is not None:
        if len(rom) != 262144 or digest(rom) != ROM_SHA:
            raise ValueError('Wrong original reconstructed ROM')
        for address, actual in ((DIRECTORY, directory), (RECORDS, payload),
                                (DISPATCH, dispatch_bytes)):
            if rom[address:address + len(actual)] != actual:
                raise ValueError(f'Source/ROM mismatch at ${address:04X}')
        for pc, hexbytes in LOADER_OPCODES.items():
            data = bytes.fromhex(hexbytes)
            if rom[pc:pc + len(data)] != data:
                raise ValueError(f'Original loader opcode mismatch at ${pc:04X}')

    if pc44 is not None:
        if pc44.get('schema') != 'ys-pc44-physical-c198-writes-v1':
            raise ValueError('PC-44 source trace schema mismatch')
        seen = [e for e in pc44['events'] if e['pc'] == '2041']
        if len(seen) != 1 or seen[0]['hl'] != '258D':
            raise ValueError('PC-44 record pointer provenance changed')
        if (seen[0]['source_at_hl'] != rows[0]['bytes'][8] or
                seen[0]['after'] != records[0]['C198']):
            raise ValueError('PC-44 observed flag disagrees with source record')

    routes = [{'selector': i, 'record_index': min(i, UNIQUE - 1),
               'record_address': f'{words[i]:04X}',
               'handler_pc': f'{targets[i]:04X}',
               'C198': records[min(i, UNIQUE - 1)]['C198'],
               'C19A': records[min(i, UNIQUE - 1)]['C19A']}
              for i in range(COUNT)]
    return {
        'schema': 'ys-pc45-source-resource-routes-v1',
        'source_rom_sha256': ROM_SHA,
        'source_region_hashes': {'directory': digest(directory),
                                 'records': digest(payload),
                                 'handlers': digest(dispatch_bytes)},
        'directory_entries': COUNT, 'unique_records': UNIQUE,
        'record_bytes': len(payload), 'directory_bytes': len(directory),
        'handler_bytes': len(dispatch_bytes),
        'record_flags_c198_one': sum(r['C198'] for r in records),
        'record_flags_c19a_one': sum(r['C19A'] for r in records),
        'records': records, 'routes': routes,
        'scope': 'source layout and proven field consumers only; not game-state reachability',
    }


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--root', type=Path, default=ROOT)
    cli.add_argument('--rom', type=Path, help='optional original or source-rebuilt 256 KiB ROM')
    cli.add_argument('--pc44-writes', type=Path, help='optional verified PC-44 write trace')
    cli.add_argument('--out', type=Path, help='optional deterministic analysis (outside Git)')
    args = cli.parse_args()
    root = args.root
    report = analyze(strict_json(root / 'Ys/wholebank00/source.json'),
                     strict_json(root / 'Ys/phase21/source.json'),
                     strict_json(root / 'Ys/phase6/coverage.json'),
                     strict_json(root / 'Ys/phase6/regions.json'),
                     args.rom.read_bytes() if args.rom else None,
                     strict_json(args.pc44_writes) if args.pc44_writes else None)
    if args.out:
        args.out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('PASS PC-45: 41 directory/handler routes; 23 typed original records; '
          '207 record bytes; 3 flag-bit7, 1 flag-bit6; ' +
          ('ROM MATCH' if args.rom else 'source hashes matched'))


if __name__ == '__main__':
    try:
        main()
    except (KeyError, ValueError, TypeError, OSError, AssertionError) as error:
        raise SystemExit(f'FAIL PC-45: {error}') from error
