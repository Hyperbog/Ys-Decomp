#!/usr/bin/env python3
"""Lossless Bank 13 graphics source: decoded 72-byte planes + RLE control recipes.

The stored decoded bytes plus packet controls regenerate original RLE bytes
without including duplicate encoded payloads. The final 5,607 bytes remain
opaque. Recovered graphics format does not imply confirmed palette/consumer use.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

START, POINTER_START = 0x8000, 0xBF8A
LAST_RESOURCE_END = 0xA9A3
PLANES, PLANE_SIZE, RESOURCE_COUNT = 4, 72, 50


def encode_plane(plane):
    if not isinstance(plane, dict) or set(plane) != {'decoded_hex', 'packet_controls'}:
        raise ValueError('Invalid decoded plane schema')
    hexdump = plane['decoded_hex']
    controls = plane['packet_controls']
    if not isinstance(hexdump, str) or len(hexdump) != PLANE_SIZE * 2:
        raise ValueError('Decoded plane must contain 72 bytes')
    try:
        decoded = bytes.fromhex(hexdump)
    except ValueError as exc:
        raise ValueError('Malformed decoded hex') from exc
    if len(decoded) != PLANE_SIZE or not isinstance(controls, list) or not controls:
        raise ValueError('Malformed decoded plane or missing packet recipe')
    out = bytearray()
    pos = 0
    for op in controls:
        if type(op) is not int or not 1 <= op <= 255:
            raise ValueError('Invalid RLE control')
        n = op if op < 0x80 else (op & 0x7f)
        if n == 0 or pos + n > PLANE_SIZE:
            raise ValueError('RLE recipe under/overflows decoded plane')
        segment = decoded[pos:pos + n]
        if op < 0x80:
            if any(b != segment[0] for b in segment):
                raise ValueError('Run packet disagrees with decoded bytes')
            packet = segment[:1]
        else:
            packet = segment
        out.append(op)
        out.extend(packet)
        pos += n
    if pos != PLANE_SIZE:
        raise ValueError('RLE recipe does not consume whole plane')
    out.append(0)
    return bytes(out)


def encode_resources(records, pointers):
    if (not isinstance(records, list) or len(records) != RESOURCE_COUNT
            or not isinstance(pointers, list) or len(pointers) != RESOURCE_COUNT
            or len(set(pointers)) != RESOURCE_COUNT
            or any(type(p) is not int or p < START or p >= POINTER_START for p in pointers)):
        raise ValueError('Wrong Bank 13 directory or resource count')
    order = sorted(pointers)
    out = bytearray()
    for i, entry in enumerate(records):
        if not isinstance(entry, dict) or set(entry) != {'start', 'planes'}:
            raise ValueError('Malformed indexed resource record')
        if type(entry['start']) is not int or entry['start'] != order[i]:
            raise ValueError('Resource order differs from pointer directory')
        if START + len(out) != entry['start']:
            raise ValueError('Non-contiguous encoded Bank 13 resources')
        blocks = entry['planes']
        if not isinstance(blocks, list) or len(blocks) != PLANES:
            raise ValueError('Resource must have four bitplanes')
        for plane in blocks:
            out.extend(encode_plane(plane))
        if i < RESOURCE_COUNT - 1 and START + len(out) != order[i + 1]:
            raise ValueError('RLE packet lengths disagree with next pointer')
    if START + len(out) != LAST_RESOURCE_END or len(out) != 10659:
        raise ValueError('Bank 13 RLE asset endpoint/size drift')
    return bytes(out)


def decode_legacy_resources(data, pointers):
    """Read original encoded source only during migration from v1 to v2."""
    if len(data) != POINTER_START - START:
        raise ValueError('Expected original Bank 13 asset payload')
    records = []
    for i, addr in enumerate(sorted(pointers)):
        cursor = addr - START
        planes = []
        for plane_number in range(PLANES):
            decoded = bytearray()
            controls = []
            while True:
                if cursor >= len(data):
                    raise ValueError('Missing Bank 13 terminator')
                op = data[cursor]
                cursor += 1
                if op == 0:
                    break
                n = op if op < 0x80 else op & 0x7f
                payload_size = 1 if op < 0x80 else n
                if n == 0 or cursor + payload_size > len(data):
                    raise ValueError('Truncated or malformed packet')
                payload = data[cursor:cursor + payload_size]
                cursor += payload_size
                decoded.extend(payload * n if op < 0x80 else payload)
                if len(decoded) > PLANE_SIZE:
                    raise ValueError('Oversized decoded plane')
                controls.append(op)
            if len(decoded) != PLANE_SIZE:
                raise ValueError(f'Wrong decoded bytes for resource {i} plane {plane_number}')
            planes.append({'decoded_hex': decoded.hex(), 'packet_controls': controls})
        if i < RESOURCE_COUNT - 1 and cursor + START != sorted(pointers)[i + 1]:
            raise ValueError('Resource endpoint disagrees with pointer directory')
        records.append({'start': addr, 'planes': planes})
    if cursor + START != LAST_RESOURCE_END:
        raise ValueError('Last resource endpoint differs from audited source')
    if encode_resources(records, pointers) != data[:cursor]:
        raise ValueError('Decoded asset recipes fail original byte identity')
    return records


def migrate(root):
    import sys
    sys.path.insert(0, str(root / 'tools'))
    from whole_banks05_13_14_15 import full_bank, split_chunks
    source_path = root / 'wholebank13/source.json'
    obj = json.loads(source_path.read_text())
    if obj.get('schema') != 'ys-bank13-source-v1':
        raise ValueError('Migration requires legacy v1 source; no overwrite')
    original = full_bank(13, root)
    pointers = obj['indexed_resource_directory']['pointers']
    records = decode_legacy_resources(original[:POINTER_START - START], pointers)
    encoded = encode_resources(records, pointers)
    new = {'schema': 'ys-bank13-source-v2',
           'rle_resource_records': records,
           'unresolved_asset_chunks': split_chunks(original[len(encoded):POINTER_START - START],
                                                    START + len(encoded)),
           'indexed_resource_directory': obj['indexed_resource_directory'],
           'end_fill': obj['end_fill']}
    source_path.write_text(json.dumps(new, separators=(',', ':')) + '\n')
    rebuilt = full_bank(13, root)
    if rebuilt != original:
        raise AssertionError('Lossless Bank 13 source migration failed')
    print(f'Converted 50 resources/200 planes into typed source; '
          f'{len(encoded)} compressed bytes; 5,607 unresolved tail bytes; '
          f'SHA-256={hashlib.sha256(rebuilt).hexdigest()}')


def verify(root):
    import sys
    sys.path.insert(0, str(root / 'tools'))
    from whole_banks05_13_14_15 import full_bank
    obj = json.loads((root / 'wholebank13/source.json').read_text())
    if obj.get('schema') != 'ys-bank13-source-v2':
        raise ValueError('Expected typed Bank 13 source v2')
    encoded = encode_resources(obj['rle_resource_records'], obj['indexed_resource_directory']['pointers'])
    data = full_bank(13, root)
    if encoded != data[:len(encoded)]:
        raise ValueError('Encoded semantic source differs from bank bytes')
    print(f'OK: 50 resource records / 200 bitplanes / {len(encoded)} encoded bytes')


def main():
    from build_sms_phase14 import ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    opts = parser.add_mutually_exclusive_group(required=True)
    opts.add_argument('--migrate', action='store_true')
    opts.add_argument('--check', action='store_true')
    args = parser.parse_args()
    migrate(ROOT) if args.migrate else verify(ROOT)


if __name__ == '__main__':
    main()
