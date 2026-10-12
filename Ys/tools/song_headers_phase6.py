#!/usr/bin/env python3
"""Extract the *regular* 21 x 37-byte audio headers; later entries unresolved.

Each header has a four-record, nine-byte structure. Only the +3/+4 word
is confidently identified as a stream pointer. Unknown fields are opaque.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE, COUNT, STRIDE = 0xAA77, 21, 37
DIRECTORY = 0x8C90


def snapshot(rom):
    sio = io.StringIO(newline='')
    writer = csv.writer(sio,lineterminator='\n')
    writer.writerow(['directory_index', 'descriptor_address', 'voice_index',
                     'record_sha256', 'stream_pointer_cpu', 'pointer_class'])
    seen = set()
    for idx in range(COUNT):
        start = BASE + STRIDE * idx
        assert rom[start] == 4, f'Descriptor {idx} has unexpected channel count'
        directory_ptr = int.from_bytes(rom[DIRECTORY+idx*2:DIRECTORY+idx*2+2], 'little')
        assert directory_ptr == start, f'Directory entry {idx} differs'
        for voice in range(4):
            offset = start + 1 + voice * 9
            item = rom[offset:offset+9]
            assert len(item)==9
            stream = int.from_bytes(item[3:5], 'little')
            # $8D57..$8D5E is shared with an earlier timing lookup;
            # record exact pointers but DO NOT reclassify that earlier span.
            assert 0x8D40 <= stream < 0xB319, f'Unexpected stream pointer {stream:04X}'
            seen.add(stream)
            kind = 'shared earlier lookup' if stream < 0x8D5F else ('event data' if stream < BASE else 'header-adjacent stream')
            writer.writerow([idx, f'{start:04X}', voice, hashlib.sha256(item).hexdigest(),f'{stream:04X}',kind])
    return sio.getvalue(), len(seen)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path)
    flags=p.add_mutually_exclusive_group(required=True)
    flags.add_argument('--write', action='store_true')
    flags.add_argument('--check', action='store_true')
    args=p.parse_args()
    rom=args.rom.read_bytes()
    assert hashlib.sha256(rom).hexdigest()==json.loads((ROOT/'manifest.json').read_text())['sha256']
    content, uniques = snapshot(rom)
    target=ROOT/'phase6/audio_descriptors.csv'
    if args.write:
        target.write_text(content)
    else:
        assert target.read_text()==content, 'Descriptor CSV differs from ROM'
    print(f'PASS: 21 regular audio headers, 84 stream refs, {uniques} unique streams')

if __name__=='__main__':
    try:main()
    except (AssertionError, ValueError, IndexError, OSError) as exc:
        sys.exit(f'FAIL Phase6 headers: {exc}')
