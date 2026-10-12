#!/usr/bin/env python3
"""Validate SMS ROM metadata and byte-accurate first-stage listing.

Usage: python tools/verify.py "/path/to/Ys - The Vanished Omens (USA, Europe).sms"
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import zlib

HERE = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path, help='Original 256 KiB SMS ROM')
    args = parser.parse_args()
    data = args.rom.read_bytes()
    manifest = json.loads((HERE / 'manifest.json').read_text())

    sha = hashlib.sha256(data).hexdigest()
    crc = f'{zlib.crc32(data) & 0xFFFFFFFF:08X}'
    assert len(data) == 0x40000, f'Wrong ROM length: {len(data)}'
    assert sha == manifest['sha256'], f'Wrong ROM SHA-256: {sha}'
    assert crc == manifest['crc32'], f'Unexpected CRC32: {crc}'

    header = data[0x7FF0:0x8000]
    assert header[:8] == b'TMR SEGA', 'Invalid SMS header magic'
    assert header[15] == 0x40, f'Unexpected region/size: {header[15]:02X}'
    expected = int.from_bytes(header[10:12], 'little')
    calculated = (sum(data[:0x7FF0]) + sum(data[0x8000:])) & 0xFFFF
    assert expected == calculated, (
        f'Checksum mismatch: header {expected:04X}, computed {calculated:04X}'
    )

    # Only the listing's machine-code bytes are authoritative at this stage.
    listing = HERE / 'src' / 'bank00_boot.lst'
    row_pattern = re.compile(r'^([0-9A-F]{4})  ((?:[0-9A-F]{2} ?)+?)  +(?:\S|$)')
    next_offset = 0
    instructions = 0
    for line in listing.read_text().splitlines():
        match = row_pattern.match(line)
        if not match:
            continue
        start = int(match.group(1), 16)
        enc = bytes.fromhex(match.group(2))
        assert start == next_offset, (
            f'Listing gap/overlap: expected {next_offset:04X}, saw {start:04X}'
        )
        assert data[start:start + len(enc)] == enc, (
            f'Listing mismatch at ROM offset {start:04X}'
        )
        next_offset += len(enc)
        instructions += 1
    assert next_offset == 0x0102, f'Incomplete listing: stopped at {next_offset:04X}'
    print('ROM SHA-256       :', sha)
    print('ROM CRC32         :', crc)
    print('ROM bytes         :', len(data))
    print('ROM banks (16 KiB):', len(data)//0x4000)
    print('SMS header        :', header[:8].decode('ascii'))
    print('Checksum          :', f'{calculated:04X}', '(matches)')
    print('Listing coverage  :', f'0000-{next_offset-1:04X}',
          f'({next_offset} verified bytes; {instructions} listing rows)')
    print('PASS: ROM metadata and boot listing verified')

if __name__ == '__main__':
    try:
        main()
    except (OSError, AssertionError, ValueError) as err:
        sys.exit(f'FAIL: {err}')
