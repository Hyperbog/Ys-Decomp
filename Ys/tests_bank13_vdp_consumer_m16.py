"""M16 ROM-independent consumer address, packet replay, and VDP layout tests."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
from bank13_vdp_consumer_m16 import (REPORT, SIGNATURES, analyze, decode_icon,
                                      expand_one_plane, verify_code)
from whole_bank00 import full_bank as fixed_bank
from whole_banks05_13_14_15 import full_bank as asset_bank


class Bank13ConsumerM16Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixed = fixed_bank()
        cls.graphics = asset_bank(13)
        cls.report = analyze(fixed=cls.fixed, graphics=cls.graphics)

    def test_reproducible_manifest(self):
        self.assertEqual(self.report, json.loads(REPORT.read_text()))

    def test_opcode_anchors_are_actual_bank0_code(self):
        self.assertEqual(self.report['validated_opcode_spans'], 9)
        self.assertEqual(self.report['consumer_entry_cpu'], 0x3ACC)
        self.assertEqual(self.report['decompressor_entry_cpu'], 0x0695)
        self.assertEqual(self.report['vdp_data_port'], 0xBE)
        self.assertEqual(self.report['fixed_bank_sha256'],
                         '3bc23bce4f0bdcf88669187f949c7a89dea9341a9653fb21025fe704e8ce872b')
        verify_code(self.fixed)
        for _, (address, signature) in SIGNATURES.items():
            bank = bytearray(self.fixed)
            bank[address + len(bytes.fromhex(signature))//2] ^= 1
            with self.assertRaises(ValueError):
                verify_code(bank)

    def test_two_vram_pages_are_disjoint_in_time_not_space(self):
        page0, page1 = self.report['pages']
        self.assertEqual([p['resource_count'] for p in (page0, page1)], [26, 24])
        self.assertEqual([p['tile_count'] for p in (page0, page1)], [234, 216])
        self.assertEqual([p['output_bytes'] for p in (page0, page1)], [7488, 6912])
        self.assertEqual([p['vram_start'] for p in (page0, page1)], [0x120, 0x120])
        self.assertEqual([p['vram_end_exclusive'] for p in (page0, page1)],
                         [0x1E60, 0x1C20])
        self.assertEqual(page0['output_sha256'],
                         '112a2a9ec2c99c05f528c3dd42682952130f8922d1337d72599d6e9dd93d0162')
        self.assertEqual(page1['output_sha256'],
                         '3e6a9616976c53a187b4b0b6b519b162f03fc22ac8dfaaca7218b146ec10619f')

    def test_each_icon_uses_nine_mode4_tiles(self):
        resources = self.report['resources']
        self.assertEqual(len(resources), 50)
        self.assertEqual(self.report['decoded_plane_count'], 200)
        self.assertEqual(self.report['decoded_vdp_bytes'], 14400)
        self.assertEqual(self.report['compressed_resource_bytes'], 10659)
        for i, r in enumerate(resources):
            tile = 9 + (i if i < 26 else i - 26) * 9
            self.assertEqual(r['first_tile_index'], tile)
            self.assertEqual(r['vram_write_command'], 0x4000 + tile * 32)
            self.assertEqual(r['tile_count'], 9)
            self.assertLessEqual(r['source_end_exclusive'], 0xA9A3)

    def test_last_resource_ends_before_unresolved_tail(self):
        self.assertEqual(self.report['unresolved_tail_cpu_start'], 0xA9A3)
        self.assertEqual(self.report['tail_region_bytes'], 5607)
        self.assertEqual(self.report['tail_region_sha256'],
                         'acac1ec8f2126c6ad96c54ea64fcaf020419ab511adc089b5d747df2fa5ab4e2')

    def test_direct_tail_graphics_are_two_bounded_four_plane_streams(self):
        rows = self.report['direct_call_tail_rle_sources']
        self.assertEqual(len(rows), 2)
        self.assertEqual([(r['source_start'], r['source_end_exclusive']) for r in rows],
                         [(0xA9A3, 0xABBA), (0xBBF7, 0xBC23)])
        self.assertEqual([r['compressed_bytes'] for r in rows], [535, 44])
        self.assertEqual([r['decoded_plane_bytes'] for r in rows], [160, 32])
        self.assertEqual([r['tile_count'] for r in rows], [20, 4])
        self.assertEqual([r['vdp_write_commands'] for r in rows],
                         [[0x5600, 0x7000], [0x7600]])
        self.assertEqual(self.report['recovered_tail_rle_bytes'], 579)
        self.assertEqual(self.report['not_yet_attributed_tail_bytes'], 5028)

    def test_vdp_four_plane_byte_interleave(self):
        # Literal 72-byte streams; each plane holds its own uniform byte.
        payload = b''.join(bytes([0xC8]) + bytes([v]) * 72 + b'\x00'
                           for v in (1, 2, 4, 8))
        interleaved, end = decode_icon(payload, 0, len(payload))
        self.assertEqual(end, len(payload))
        self.assertEqual(interleaved, bytes([1, 2, 4, 8]) * 72)

    def test_repeat_control_matches_z80_decoder(self):
        result, offset = expand_one_plane(bytes([72, 0x42, 0]), 0, 3)
        self.assertEqual(result, bytes([0x42]) * 72)
        self.assertEqual(offset, 3)
        with self.assertRaises(ValueError):
            expand_one_plane(bytes([0x80, 0]), 0, 2)
        with self.assertRaises(ValueError):
            expand_one_plane(bytes([73, 0x42, 0]), 0, 3)
        with self.assertRaises(ValueError):
            expand_one_plane(bytes([0xC8, 0x42, 0]), 0, 3)

    def test_corrupt_pointer_directory_rejected(self):
        corrupt = bytearray(self.graphics)
        corrupt[0x3F8A] = 0xFF
        with self.assertRaises(ValueError):
            analyze(fixed=self.fixed, graphics=corrupt)


if __name__ == '__main__':
    unittest.main()
