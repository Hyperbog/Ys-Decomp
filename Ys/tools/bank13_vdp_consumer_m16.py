#!/usr/bin/env python3
"""M16: statically anchor and independently reproduce Bank 13 -> VDP tile uploads.

Uses source-backed bank images only, not a commercial ROM. The RLE packet
expansion and four-plane VRAM byte-interleaving are checked against the precise
fixed-bank code signatures; no whole-game CPU/VDP execution is claimed.
"""
import argparse
import hashlib
import json
from pathlib import Path

from build_sms_phase14 import ROOT
from whole_bank00 import full_bank as fixed_bank
from whole_banks05_13_14_15 import full_bank as asset_bank

REPORT = ROOT / 'whole_system/bank13_vdp_consumer_m16.json'
BANK = 13
DIRECTORY = 0xBF8A
BASE = 0x8000
RESOURCE_BYTES = 288
PLANE_BYTES = 72
VDP_START = 0x0120
GROUPS = ((0, 26), (26, 24))
# Exact, source-controlled opcode spans, confirmed independently as Z80 code.
SIGNATURES = {
    'rst18_pointer_word_lookup': (0x0018, '87856f3001247e23666fc9'),
    'rst28_vdp_address_command': (0x0028, 'f37bd3bf7ad3bffbc9'),
    'rle_four_plane_vdp_writer': (0x0695, '0e0441c5d57e23b7281c47cbb80708ef7ed3be083001230879835f30011410ef0838e22318dfd113c110d8c9'),
    'directory_index_and_tile_stride': (0x3ACC, '218abff5dfc5d5cd9506d1eb01200109ebc1f13c10eac9'),
    'first_page_bank13_26_icons': (0x38E2, '3e0d32ffff21f7bb110076cd9506210080112041061aafcdcc3a'),
    'second_page_bank13_24_icons': (0x398C, '3e0d32ffff1120413e1a0618cdcc3a'),
    'tail_128byte_upload': (0x38E7, '21f7bb110076cd9506'),
    'tail_640byte_upload_a': (0x3CDE, '21a3a9110056cd9506'),
    'tail_640byte_upload_b': (0x3E57, '21a3a9110070cd9506'),
}

def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify_code(fixed):
    if len(fixed) != 0x4000:
        raise ValueError('Invalid fixed bank length')
    for name, (address, hex_bytes) in SIGNATURES.items():
        required = bytes.fromhex(hex_bytes)
        if fixed[address:address + len(required)] != required:
            raise ValueError(f'Bank 0 code anchor changed: {name} at ${address:04X}')


def expand_one_plane(source, begin, limit, expected_length=PLANE_BYTES):
    """Independent translation of the Z80 $0695 run/literal control loop."""
    decoded = bytearray()
    offset = begin
    while offset < limit:
        opcode = source[offset]
        offset += 1
        if opcode == 0:
            if len(decoded) != expected_length:
                raise ValueError('Incorrect decoded plane length')
            return bytes(decoded), offset
        if opcode < 0x80:
            if offset >= limit:
                raise ValueError('Truncated repeated byte')
            decoded.extend(bytes([source[offset]]) * opcode)
            offset += 1
        else:
            length = opcode & 0x7F
            if not length or offset + length > limit:
                raise ValueError('Truncated or empty literal packet')
            decoded.extend(source[offset:offset + length])
            offset += length
        if len(decoded) > expected_length:
            raise ValueError('Overflow in graphics plane')
    raise ValueError('Missing graphics plane terminator')


def decode_icon(source, begin, limit, plane_bytes=PLANE_BYTES):
    cursor = begin
    planes = []
    for _ in range(4):
        plane, cursor = expand_one_plane(source, cursor, limit, plane_bytes)
        planes.append(plane)
    # Bank 0 $0695 uses LD C,$04; OUT ($BE),A, DE+=4; plane pass DE+=1.
    # SMS Mode-4 tiles are four consecutive bitplane bytes per pixel row.
    vram = bytearray(plane_bytes * 4)
    for plane_index, plane in enumerate(planes):
        for i, value in enumerate(plane):
            vram[4 * i + plane_index] = value
    return bytes(vram), cursor


def analyze(root=ROOT, fixed=None, graphics=None):
    fixed = fixed if fixed is not None else fixed_bank(root)
    graphics = graphics if graphics is not None else asset_bank(BANK, root)
    verify_code(fixed)
    if len(graphics) != 0x4000:
        raise ValueError('Invalid Bank 13 length')
    ptrpos = DIRECTORY - BASE
    pointers = [int.from_bytes(graphics[ptrpos + 2*i:ptrpos + 2*i + 2], 'little')
                for i in range(50)]
    if len(set(pointers)) != 50 or min(pointers) != BASE or max(pointers) >= DIRECTORY:
        raise ValueError('Invalid resource directory')
    ordered = sorted(pointers)
    bounds = {ptr: ordered[i+1] if i+1 < 50 else DIRECTORY
              for i, ptr in enumerate(ordered)}
    assets = []
    payloads = []
    last_finish = None
    for index, ptr in enumerate(pointers):
        vram, finish = decode_icon(graphics, ptr - BASE, bounds[ptr] - BASE)
        end = finish + BASE
        if end > bounds[ptr]:
            raise ValueError('RLE resource crosses pointer boundary')
        if bounds[ptr] != DIRECTORY and end != bounds[ptr]:
            raise ValueError('Gap between adjacent resources')
        page, start_index = ((0, 0) if index < 26 else (1, 26))
        tile_slot = 9 + (index - start_index) * 9
        vram_start = VDP_START + RESOURCE_BYTES * (index - start_index)
        if vram_start != tile_slot * 32 or vram_start + RESOURCE_BYTES > 0x4000:
            raise ValueError('VRAM tile alignment or capacity failure')
        assets.append({'directory_index': index, 'bank13_cpu_source': ptr,
                       'source_end_exclusive': end, 'page': page,
                       'vram_write_command': 0x4000 | vram_start,
                       'first_tile_index': tile_slot, 'tile_count': 9,
                       'vdp_bytes_sha256': sha(vram)})
        payloads.append(vram)
        if ptr == ordered[-1]:
            last_finish = end
    compressed_bytes = sum(x['source_end_exclusive'] - x['bank13_cpu_source']
                           for x in assets)
    if compressed_bytes != 10659:
        raise ValueError('Unexpected encoded RLE payload length')
    if last_finish != 0xA9A3:
        raise ValueError('Unexpected end of last graphics stream')
    tail = graphics[last_finish - BASE:ptrpos]
    if len(tail) != 5607:
        raise ValueError('Unexpected unresolved trailing bytes')
    # Two direct-call tail graphics resources are independently identified by
    # the same Z80 writer ($0695); these are NOT 72-byte icon planes.
    tail_references = ((0xA9A3, 160, (0x5600, 0x7000)),
                       (0xBBF7, 32, (0x7600,)))
    direct_tail = []
    for address, plane_size, commands in tail_references:
        payload, end_offset = decode_icon(graphics, address - BASE, ptrpos, plane_bytes=plane_size)
        end = end_offset + BASE
        expected_end = {0xA9A3: 0xABBA, 0xBBF7: 0xBC23}[address]
        if end != expected_end:
            raise ValueError('Direct Bank 13 RLE source endpoint changed')
        for command in commands:
            address_vram = command & 0x3FFF
            if command & 0xC000 != 0x4000 or address_vram % 32:
                raise ValueError('Invalid VDP command for tail graphics')
            if address_vram + len(payload) > 0x4000:
                raise ValueError('Tail VDP write exceeds VRAM')
        direct_tail.append({'source_start': address, 'source_end_exclusive': end,
                            'compressed_bytes': end - address,
                            'decoded_plane_bytes': plane_size, 'decoded_vdp_bytes': len(payload),
                            'tile_count': len(payload) // 32,
                            'vdp_write_commands': list(commands),
                            'vdp_bytes_sha256': sha(payload)})
    if not (direct_tail[0]['source_end_exclusive'] <= direct_tail[1]['source_start']):
        raise ValueError('Overlapping tail graphics spans')
    recovered_tail_bytes = sum(r['compressed_bytes'] for r in direct_tail)
    if recovered_tail_bytes != 579:
        raise ValueError('Tail RLE byte accounting changed')
    pages = []
    for page, (start, count) in enumerate(GROUPS):
        data = b''.join(payloads[start:start+count])
        pages.append({'page': page, 'directory_start_index': start,
                      'resource_count': count, 'vram_start': VDP_START,
                      'vram_end_exclusive': VDP_START + len(data),
                      'first_tile': 9, 'tile_count': count * 9,
                      'output_bytes': len(data), 'output_sha256': sha(data)})
    return {'schema': 'ys-bank13-vdp-consumer-m16-v1',
            'fixed_bank_sha256': sha(fixed), 'bank13_sha256': sha(graphics),
            'validated_opcode_spans': len(SIGNATURES),
            'indexed_directory_cpu': DIRECTORY,
            'consumer_entry_cpu': 0x3ACC, 'decompressor_entry_cpu': 0x0695,
            'vdp_control_port': 0xBF, 'vdp_data_port': 0xBE,
            'consumer_vram_start': VDP_START, 'indexed_resource_count': 50,
            'decoded_plane_count': 200, 'compressed_resource_bytes': compressed_bytes,
            'decoded_vdp_bytes': sum(map(len, payloads)),
            'pages': pages, 'resources': assets,
            'unresolved_tail_cpu_start': last_finish,
            'tail_region_bytes': len(tail), 'tail_region_sha256': sha(tail),
            'direct_call_tail_rle_sources': direct_tail,
            'recovered_tail_rle_bytes': recovered_tail_bytes,
            'not_yet_attributed_tail_bytes': len(tail) - recovered_tail_bytes,
            'limitations': [
                'Anchored opcode inspection and independent bounded data replay, not live Z80 execution.',
                'VRAM destinations are tile-pattern bytes, not proof of final palette selection.',
                'Two UI loads reuse the same VRAM tile slots; they are not simultaneous resident assets.',
                'The remaining tail bytes have not been assigned semantic format or ownership.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--write', action='store_true')
    args = parser.parse_args()
    result = analyze()
    if args.check:
        if json.loads(REPORT.read_text()) != result:
            raise ValueError('M16 Bank 13 consumer report drift')
    else:
        REPORT.write_text(json.dumps(result, indent=2) + '\n')
    print('M16: 9 code anchors; 26+24 icons -> 234+216 VRAM tiles; '
          '579 additional RLE bytes in two tail graphics records; 5,028 tail bytes unattributed')


if __name__ == '__main__':
    main()
