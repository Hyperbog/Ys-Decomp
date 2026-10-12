#!/usr/bin/env python3
"""Interpret the anchored bank-3 prefix as SMS Mode-4 8x8, 4bpp tiles.

Only writes metadata to the repository; optional PNG is user-generated from
his/her private ROM, never committed. No claim that game displays every tile.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib

ROOT=Path(__file__).resolve().parents[1]
ROM_SHA=json.loads((ROOT/'manifest.json').read_text())['sha256']
BLOCKS=((0xC000,0xD000),(0xD000,0xD600))


def decode_tile(raw):
    if len(raw)!=32:raise ValueError('Each Mode-4 tile is 32 bytes')
    out=[]
    for y in range(8):
        p=raw[4*y:4*y+4]
        for x in range(8):
            out.append(sum(((plane>>(7-x))&1)<<bit for bit,plane in enumerate(p)))
    return out


def encode_tile(pixels):
    if len(pixels)!=64 or any(not isinstance(v,int) or v<0 or v>15 for v in pixels):
        raise ValueError('8x8 tile requires 64 pixel indexes in range 0..15')
    raw=bytearray(32)
    for y in range(8):
        for x in range(8):
            color=pixels[y*8+x]
            for bit in range(4):
                if color & (1<<bit):raw[y*4+bit] |= 1 << (7-x)
    return bytes(raw)


def png_chunk(name,payload):
    return struct.pack('>I',len(payload))+name+payload+struct.pack('>I',zlib.crc32(name+payload)&0xFFFFFFFF)


def render_atlas(tiles,destination):
    """Write a deterministic 16 columns x 11 rows gray-index preview, not actual palette colors."""
    width,height=128,88
    rows=[]
    for y in range(height):
        row=bytearray([0])
        for x in range(width):
            tile_index=(y//8)*16+(x//8)
            pixel=tiles[tile_index][(y%8)*8+(x%8)] if tile_index<len(tiles) else 0
            row.append(pixel*17)
        rows.append(bytes(row))
    raw=b''.join(rows)
    png=(b'\x89PNG\r\n\x1a\n'+png_chunk(b'IHDR',struct.pack('>2I5B',width,height,8,0,0,0,0))+
         png_chunk(b'IDAT',zlib.compress(raw,9))+png_chunk(b'IEND',b''))
    destination.write_bytes(png)


def analyze(rom):
    assert hashlib.sha256(rom).hexdigest()==ROM_SHA, 'Source fingerprint mismatch'
    blocks=[]
    all_tiles=[]
    for lo,hi in BLOCKS:
        assert (hi-lo)%32==0
        blob=rom[lo:hi]
        tiles=[decode_tile(blob[i:i+32]) for i in range(0,len(blob),32)]
        rebuilt=b''.join(encode_tile(pixels) for pixels in tiles)
        assert rebuilt==blob, 'Bitplane round-trip failed'
        all_tiles+=tiles
        rawtiles=[blob[i:i+32] for i in range(0,len(blob),32)]
        freq=Counter(v for tile in tiles for v in tile)
        blocks.append({
          'file_start':f'{lo:05X}','file_end_exclusive':f'{hi:05X}',
          'mode4_tile_count':len(tiles), 'raw_bytes':len(blob),
          'unique_raw_tile_patterns':len(set(rawtiles)),
          'sha256':hashlib.sha256(blob).hexdigest(),
          'pixel_value_histogram':{str(v):freq[v] for v in range(16)},
          'all_rows_round_trip_verified':True,
        })
    stats={
      'source_sha256':ROM_SHA,
      'status':'Strong Mode-4-compatible tile structure; actual game tile usage is not emulator-verified',
      'mode4_format':'32-byte 8x8 tile, row-major; each row has bitplanes 0,1,2,3 (MSB-left)',
      'blocks':blocks,'tiles_total':len(all_tiles),
      'interpreted_bytes':sum(x['raw_bytes'] for x in blocks),
      'coverage_note':'These bytes were already counted as provisional opaque data in Phase 7; reclassification adds ZERO new distinct bytes',
      'preview_note':'Atlas grayscale intensity represents index 0..15, not actual game colors; preview is not committed',
    }
    return json.dumps(stats,indent=2)+'\n',stats,all_tiles


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write',action='store_true')
    mode.add_argument('--check',action='store_true')
    p.add_argument('--atlas',type=Path,help='Optional visual preview outside the repository')
    a=p.parse_args()
    result,report,tiles=analyze(a.rom.read_bytes())
    dest=ROOT/'phase8/tile_metadata.json'
    if a.write:dest.write_text(result)
    else:assert dest.read_text()==result,'Changed tile metadata'
    if a.atlas:render_atlas(tiles,a.atlas)
    print(f"PASS Phase8 tiles: {report['tiles_total']} Mode-4-shaped tiles, "
          f"{report['interpreted_bytes']} bytes reversibly decoded")

if __name__=='__main__':
    try:main()
    except (AssertionError,ValueError,IndexError,OSError) as exc:sys.exit('FAIL Phase8 tile decoder: '+str(exc))
