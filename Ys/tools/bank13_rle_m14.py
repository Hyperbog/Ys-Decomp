#!/usr/bin/env python3
"""M14: ROM-independent, lossless Bank 13 RLE resource and SMS tile audit.

Source authority: checked-in 16-KiB bank 13 source and its 50-word directory.
This module does NOT assert that all Bank 13 data has been semantically decoded.
"""
import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from build_sms_phase14 import ROOT
from whole_banks05_13_14_15 import POINTER_START, START, full_bank

TILE_GRID = 3
TILE_WIDTH = 8
PLANES = 4
PLANE_BYTES = TILE_GRID * TILE_GRID * TILE_WIDTH  # 72
RESOURCE_BYTES = PLANES * PLANE_BYTES             # 288
IMAGE_WIDTH = TILE_GRID * TILE_WIDTH              # 24
REPORT = ROOT / 'whole_system/bank13_rle_m14.json'


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


@dataclass(frozen=True)
class Packet:
    control: int
    payload: bytes


def encode_packets(packets):
    """Preserve original packet boundaries, including non-canonical runs."""
    out = bytearray()
    for packet in packets:
        op = packet.control
        if not 1 <= op <= 255:
            raise ValueError('Invalid packet control')
        length = 1 if op < 0x80 else op & 0x7f
        if not length or len(packet.payload) != length:
            raise ValueError('Invalid packet payload length')
        out.append(op)
        out.extend(packet.payload)
    return bytes(out) + b'\x00'


def decode_block(source, pos, stop):
    """Decode one zero-terminated stream, bounded by its directory range."""
    start = pos
    raw = bytearray()
    packets = []
    while pos < stop:
        op = source[pos]
        pos += 1
        if op == 0:
            if len(raw) != PLANE_BYTES:
                raise ValueError(f'Block at ${start + START:04X} has {len(raw)} decoded bytes')
            if encode_packets(packets) != source[start:pos]:
                raise ValueError('RLE packet identity failed')
            return bytes(raw), tuple(packets), pos
        count = 1 if op < 0x80 else op & 0x7f
        if not count or pos + count > stop:
            raise ValueError('Truncated or invalid RLE packet')
        payload = source[pos:pos + count]
        pos += count
        raw.extend(payload * op if op < 0x80 else payload)
        if len(raw) > PLANE_BYTES:
            raise ValueError('RLE block exceeds 72 decoded bytes')
        packets.append(Packet(op, payload))
    raise ValueError('Missing RLE block terminator')


def decode_resource(source, start, stop):
    if not START <= start < stop <= POINTER_START:
        raise ValueError('Resource outside Bank 13 asset bounds')
    position = start - START
    upper = stop - START
    blocks = []
    details = []
    for plane in range(PLANES):
        begin = position
        decoded, packets, position = decode_block(source, position, upper)
        blocks.append(decoded)
        details.append({'plane': plane, 'start': begin + START,
                        'end_exclusive': position + START,
                        'compressed_bytes': position - begin,
                        'decoded_sha256': digest(decoded),
                        'packet_count': len(packets)})
    # Last directory entry leaves an independent, unresolved data tail.
    if position > upper:
        raise ValueError('Resource overran next directory pointer')
    return tuple(blocks), tuple(details), position + START


def planes_to_pixels(planes):
    """24x24 row-major 4bpp indices; each plane stores nine tiles of eight rows."""
    if len(planes) != PLANES or any(len(p) != PLANE_BYTES for p in planes):
        raise ValueError('Expected four 72-byte planes')
    image = bytearray(IMAGE_WIDTH * IMAGE_WIDTH)
    for tile in range(TILE_GRID * TILE_GRID):
        ty, tx = divmod(tile, TILE_GRID)
        for row in range(TILE_WIDTH):
            for col in range(TILE_WIDTH):
                byte_index = tile * TILE_WIDTH + row
                mask = 0x80 >> col
                color = sum(((planes[p][byte_index] & mask) != 0) << p
                            for p in range(PLANES))
                image[(ty * TILE_WIDTH + row) * IMAGE_WIDTH + tx * TILE_WIDTH + col] = color
    return bytes(image)


def pixels_to_planes(image):
    if len(image) != IMAGE_WIDTH * IMAGE_WIDTH or any(px > 0xf for px in image):
        raise ValueError('Expected 24x24 pixels with palette indices 0..15')
    planes = [bytearray(PLANE_BYTES) for _ in range(PLANES)]
    for tile in range(TILE_GRID * TILE_GRID):
        ty, tx = divmod(tile, TILE_GRID)
        for row in range(TILE_WIDTH):
            for col in range(TILE_WIDTH):
                pixel = image[(ty * TILE_WIDTH + row) * IMAGE_WIDTH + tx * TILE_WIDTH + col]
                for plane in range(PLANES):
                    if pixel & (1 << plane):
                        planes[plane][tile * TILE_WIDTH + row] |= 0x80 >> col
    return tuple(bytes(p) for p in planes)


def inventory(source=None, root=ROOT):
    source = source if source is not None else full_bank(13, root)
    obj = json.loads((root / 'wholebank13/source.json').read_text())
    pointers = obj['indexed_resource_directory']['pointers']
    if len(source) != 0x4000 or len(pointers) != 50 or len(set(pointers)) != 50:
        raise ValueError('Wrong Bank 13 image or directory count')
    if not all(START <= p < POINTER_START for p in pointers):
        raise ValueError('Directory pointer outside resource region')
    ordered = sorted(enumerate(pointers), key=lambda entry: entry[1])
    resources = []
    encoded_total = 0
    for index, (directory_index, start) in enumerate(ordered):
        stop = ordered[index + 1][1] if index + 1 < len(ordered) else POINTER_START
        planes, parts, decoded_end = decode_resource(source, start, stop)
        if index + 1 < len(ordered) and decoded_end != stop:
            raise ValueError('Nonterminal resource leaves a gap before the next pointer')
        image = planes_to_pixels(planes)
        if pixels_to_planes(image) != planes:
            raise ValueError('Pixel-to-plane round trip failed')
        encoded_total += decoded_end - start
        resources.append({'directory_index': directory_index, 'start': start,
                          'end_exclusive': decoded_end,
                          'compressed_bytes': decoded_end - start,
                          'decoded_bytes': RESOURCE_BYTES,
                          'pixels_sha256': digest(image), 'blocks': list(parts)})
    tail_start = resources[-1]['end_exclusive']
    tail = source[tail_start - START:POINTER_START - START]
    report = {'schema': 'ys-bank13-rle-m14-v1', 'source_bank_sha256': digest(source),
              'resource_count': len(resources), 'decoded_blocks': 4 * len(resources),
              'encoded_resource_bytes': encoded_total,
              'decoded_resource_bytes': RESOURCE_BYTES * len(resources),
              'resource_start': START, 'resource_end_exclusive': tail_start,
              'unresolved_tail_start': tail_start,
              'unresolved_tail_end_exclusive': POINTER_START,
              'unresolved_tail_bytes': len(tail), 'unresolved_tail_sha256': digest(tail),
              'directory_start': POINTER_START,
              'directory_order': pointers, 'resources': resources,
              'limitations': ['Bitplane ordering and on-console consumer use still need verification.',
                              'RLE streams after the indexed resources are not claimed decoded.',
                              'The original RLE packets are preserved losslessly, not recompressed.']}
    if encoded_total != 10659 or len(tail) != 5607 or decoded_end != 0xa9a3:
        raise ValueError('Bank 13 expected resource/tail accounting changed')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true')
    group.add_argument('--write', action='store_true')
    args = parser.parse_args()
    result = inventory()
    if args.check:
        if json.loads(REPORT.read_text()) != result:
            raise ValueError('Bank 13 resource inventory drift')
    else:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(result, indent=2) + '\n')
    print('M14 Bank13: 50 resources, 200 blocks, 14,400 decoded bytes, '
          '10,659 compressed bytes, 5,607 unresolved trailing bytes')


if __name__ == '__main__':
    main()