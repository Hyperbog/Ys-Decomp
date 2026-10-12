#!/usr/bin/env python3
"""Recover Ys SMS bank-6's 64 indexed, count-delimited records.

Physical offsets are ROM offsets (0x18000 + CPU address - 0x8000).
Emit metadata only, never the copyrighted record payloads.  Every payload
has a reversible structural decode; field meanings are deliberately unnamed.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM_SHA = json.loads((ROOT / 'manifest.json').read_text())['sha256']
START = 0x18000
TABLE_END = 0x18080
PAYLOAD_START = 0x18080
PAYLOAD_END = 0x19932
BANK6_BASE = 0x18000
CPU_BASE = 0x8000
N_RECORDS = 64


def cpu_to_file(cpu):
    assert CPU_BASE <= cpu < 0xC000
    return BANK6_BASE + cpu - CPU_BASE


def decode_payload(raw):
    """A count, count one-byte entries, and count adjacent byte pairs."""
    if not raw:
        raise ValueError('Empty record')
    count = raw[0]
    if len(raw) != 1 + 3 * count:
        raise ValueError(f'Incorrect record size: count={count}, bytes={len(raw)}')
    x_offsets = tuple(raw[1:1 + count])
    paired = tuple((raw[1 + count + 2 * i], raw[2 + count + 2 * i])
                   for i in range(count))
    return count, x_offsets, paired


def encode_payload(fields):
    count, offsets, pairs = fields
    if not 0 <= count <= 255 or len(offsets) != count or len(pairs) != count:
        raise ValueError('Malformed decoded record')
    if any(len(pair) != 2 for pair in pairs):
        raise ValueError('Malformed element pair')
    return bytes([count, *offsets, *(byte for pair in pairs for byte in pair)])


def emulate_record_buffers(fields, base_first=0, base_second=0):
    """Reproduce the two bounded copy loops at bank6 CPU $9944-$9960.

    The accumulator is loaded once before each loop. Each first-group byte
    changes the running accumulator, as does the first byte of each later
    pair. The pair's second byte is copied unchanged by LDI.
    """
    n, first, pairs = fields
    a = base_first & 0xff
    output_first = bytearray()
    for delta in first:
        a = (a + delta) & 0xff
        output_first.append(a)
    a = base_second & 0xff
    output_second = bytearray()
    for delta, literal in pairs:
        a = (a + delta) & 0xff
        output_second.extend((a,literal))
    if len(output_first) != n or len(output_second) != 2*n:
        raise ValueError('Consumer emulation output length mismatch')
    return bytes(output_first), bytes(output_second)


def extract(rom):
    if len(rom) != 0x40000:
        raise ValueError('Expected 256-KiB SMS ROM')
    # This is the instruction sequence at $9932 that fetches indexed words
    # from CPU $8000, reads a count, and then uses the two RAM destinations.
    expected = bytes.fromhex('3A 99 C1 87 6F 26 80 7E 2C 66 6F 46 48')
    if rom[0x19932:0x19932 + len(expected)] != expected:
        raise ValueError('Consumer code at bank6:$9932 changed')
    pointers = [int.from_bytes(rom[START + 2*i:START + 2*i+2], 'little')
                for i in range(N_RECORDS)]
    if len(set(pointers)) != N_RECORDS:
        raise ValueError('Pointer directory contains duplicate destinations')
    if min(pointers) != 0x8080 or max(pointers) >= 0x9932:
        raise ValueError('Directory bounds invalid')
    records = []
    for index, pointer in enumerate(pointers):
        pos = cpu_to_file(pointer)
        n = rom[pos]
        end = pos + 1 + 3 * n
        if end > PAYLOAD_END:
            raise ValueError(f'Record {index} crosses consumer code')
        blob = rom[pos:end]
        fields = decode_payload(blob)
        if encode_payload(fields) != blob:
            raise ValueError(f'Record {index} fails exact reverse encoding')
        records.append({'directory_index': index, 'cpu_address': pointer,
                        'offset': pos, 'end': end, 'count': n,
                        'sha256': hashlib.sha256(blob).hexdigest(),
                        'decoded': fields,
                        'zero_origin_hash': hashlib.sha256(b''.join(emulate_record_buffers(fields))).hexdigest()})
    by_position = sorted(records, key=lambda item: item['offset'])
    if by_position[0]['offset'] != PAYLOAD_START:
        raise ValueError('Gap before first record')
    for a, b in zip(by_position, by_position[1:]):
        if a['end'] != b['offset']:
            raise ValueError(f'Record gap/overlap {a["end"]:05X} != {b["offset"]:05X}')
    if by_position[-1]['end'] != PAYLOAD_END:
        raise ValueError('Record stream does not reach $9932')
    if sum(row['end']-row['offset'] for row in records) != PAYLOAD_END-PAYLOAD_START:
        raise ValueError('Payload coverage mismatch')
    return records


def metadata(rom):
    records = extract(rom)
    counts = Counter(r['count'] for r in records)
    # Distinct offset coverage excludes the table, already classified in 11A.
    return {
        'schema': 'ys-phase11b-records-v1',
        'source_rom_sha256': ROM_SHA,
        'bank': 6,
        'pointer_table_file_range': ['18000','18080'],
        'pointer_table_bytes_previously_classified': 128,
        'record_data_file_range': ['18080','19932'],
        'new_structured_data_bytes': PAYLOAD_END-PAYLOAD_START,
        'record_count': len(records),
        'record_length_formula': '1 + 3 * count',
        'count_histogram': {str(key):counts[key] for key in sorted(counts)},
        'record_byte_count_range': [min(r['end']-r['offset'] for r in records),
                                    max(r['end']-r['offset'] for r in records)],
        'record_payload_sha256': hashlib.sha256(rom[PAYLOAD_START:PAYLOAD_END]).hexdigest(),
        'record_layout': {
            'byte_0': 'count',
            'bytes_1_through_count': 'first byte-array, count bytes',
            'remaining_2xcount': 'count pairs: running delta and literal byte',
            'consumer_output': 'first count bytes are running sums of first group plus ($C210); next 2*count bytes are running sums of each pair first byte plus ($C211), interleaved with copied literal pair second bytes',
            'consumer': 'bank 6 CPU $9932 reads record and copies/transforms into RAM destinations via ($C028) and ($C02A)',
            'semantic_status': 'fields have no confirmed gameplay names; mapping is statically inferred, not emulator traced'
        },
        'records_by_directory_index': [{
            'index': r['directory_index'],
            'cpu_address': f'{r["cpu_address"]:04X}',
            'rom_start': f'{r["offset"]:05X}',
            'rom_end_exclusive': f'{r["end"]:05X}',
            'elements': r['count'],
            'bytes': r['end']-r['offset'],
            'sha256': r['sha256'],
            'consumer_zero_origin_sha256': r['zero_origin_hash']
        } for r in records]
    }


def check_snapshot(rom, snapshot):
    if hashlib.sha256(rom).hexdigest() != ROM_SHA:
        raise ValueError('ROM SHA-256 mismatch')
    actual = metadata(rom)
    if actual != snapshot:
        raise ValueError('Committed record ledger differs from ROM')
    return actual


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path)
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument('--write',action='store_true')
    modes.add_argument('--check',action='store_true')
    a=p.parse_args()
    rom=a.rom.read_bytes()
    if hashlib.sha256(rom).hexdigest() != ROM_SHA:
        raise ValueError('Wrong original ROM')
    dest=ROOT/'phase11'/'bank6_records.json'
    if a.write:
        dest.write_text(json.dumps(metadata(rom),indent=2)+'\n')
    else:
        check_snapshot(rom,json.loads(dest.read_text()))
    print('PASS: 64 reversible count records; 6,322 newly structured bytes; contiguous $18080-$19931')

if __name__=='__main__':
    main()
