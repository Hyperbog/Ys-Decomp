"""M14 Bank 13 RLE format, bounds, and SMS 4bpp pixel regressions."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
from bank13_rle_m14 import (Packet, PLANE_BYTES, RESOURCE_BYTES, REPORT,
                            decode_block, decode_resource, encode_packets,
                            inventory, pixels_to_planes, planes_to_pixels)
from whole_banks05_13_14_15 import full_bank


class Bank13RleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank = full_bank(13)
        cls.report = inventory(cls.bank)

    def test_manifest_is_reproducible(self):
        self.assertEqual(self.report, json.loads(REPORT.read_text()))

    def test_50_resources_have_exactly_200_planes(self):
        self.assertEqual(self.report['resource_count'], 50)
        self.assertEqual(self.report['decoded_blocks'], 200)
        self.assertEqual(self.report['decoded_resource_bytes'], 14400)
        self.assertTrue(all(r['decoded_bytes'] == RESOURCE_BYTES
                            and len(r['blocks']) == 4
                            for r in self.report['resources']))

    def test_resource_boundary_and_unresolved_tail(self):
        rows = self.report['resources']
        self.assertTrue(all(a['end_exclusive'] == b['start']
                            for a, b in zip(rows, rows[1:])))
        self.assertEqual(self.report['encoded_resource_bytes'], 10659)
        self.assertEqual(rows[-1]['end_exclusive'], 0xa9a3)
        self.assertEqual(self.report['unresolved_tail_bytes'], 5607)
        self.assertEqual(self.report['unresolved_tail_end_exclusive'], 0xbf8a)

    def test_lossless_packet_roundtrip_for_every_block(self):
        for resource in self.report['resources']:
            for block in resource['blocks']:
                start, end = block['start'] - 0x8000, block['end_exclusive'] - 0x8000
                decoded, packets, stopped = decode_block(self.bank, start, end)
                self.assertEqual(len(decoded), PLANE_BYTES)
                self.assertEqual(stopped, end)
                self.assertEqual(encode_packets(packets), self.bank[start:end])
                self.assertEqual(hashlib.sha256(decoded).hexdigest(), block['decoded_sha256'])

    def test_pixel_bitplane_roundtrip_every_icon(self):
        for resource in self.report['resources']:
            planes, _, stopped = decode_resource(
                self.bank, resource['start'], resource['end_exclusive'])
            self.assertEqual(stopped, resource['end_exclusive'])
            pixels = planes_to_pixels(planes)
            self.assertEqual(len(pixels), 576)
            self.assertTrue(all(px < 16 for px in pixels))
            self.assertEqual(pixels_to_planes(pixels), planes)
            self.assertEqual(hashlib.sha256(pixels).hexdigest(), resource['pixels_sha256'])

    def test_rejects_truncation_or_absent_terminator(self):
        with self.assertRaises(ValueError):
            decode_block(bytes([0x82, 0x10]), 0, 2)
        with self.assertRaises(ValueError):
            decode_block(bytes([72, 0x42]), 0, 2)
        with self.assertRaises(ValueError):
            decode_block(bytes([72, 0x42, 0]), 0, 2)

    def test_rejects_overrun_and_invalid_packet(self):
        with self.assertRaises(ValueError):
            decode_block(bytes([73, 0x42, 0]), 0, 3)
        with self.assertRaises(ValueError):
            decode_block(bytes([0x80, 0]), 0, 2)
        with self.assertRaises(ValueError):
            encode_packets([Packet(0x81, b'')])

    def test_rejects_invalid_pixels_and_plane_dimensions(self):
        with self.assertRaises(ValueError):
            planes_to_pixels([bytes(PLANE_BYTES)] * 3)
        with self.assertRaises(ValueError):
            pixels_to_planes(bytes([16]) + bytes(575))
        with self.assertRaises(ValueError):
            pixels_to_planes(bytes(575))


if __name__ == '__main__':
    unittest.main()