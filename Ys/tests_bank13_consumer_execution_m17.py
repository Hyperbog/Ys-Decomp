"""M17: validated Z80 consumer path, VDP output, and separate tail resource."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
from bank13_consumer_execution_m17 import (
    ConsumerMachine, DECOMPRESSOR, DIRECTORY, LOADER, REPORT,
    RECORD_BYTES, decode_rle_plane, execute, execute_tail, report,
)
from build_system_m10 import build
from phase18_z80_trace import UnsupportedOpcode


class Bank13ConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom, _ = build()
        cls.audit = report(cls.rom)

    def test_report_is_source_reproducible(self):
        self.assertEqual(self.audit, json.loads(REPORT.read_text()))

    def test_all_50_indexed_vdp_records(self):
        self.assertEqual(self.audit['resource_count'], 50)
        self.assertEqual(self.audit['decoded_output_bytes_all_resources'], 14400)
        self.assertEqual([r['index'] for r in self.audit['single_resource_runs']], list(range(50)))
        self.assertTrue(all(r['output_bytes'] == RECORD_BYTES for r in self.audit['single_resource_runs']))
        self.assertTrue(all(r['vdp_commands'] == RECORD_BYTES for r in self.audit['single_resource_runs']))

    def test_two_original_caller_batches(self):
        a, b = self.audit['full_batches']
        self.assertEqual([(v['index'], v['count']) for v in (a, b)], [(0, 26), (26, 24)])
        self.assertEqual((a['output_bytes'], b['output_bytes']), (7488, 6912))
        self.assertEqual(a['vram_start'], 0x0120)
        self.assertEqual(b['vram_start'], 0x0120)
        self.assertEqual(a['vdp_commands'], 7488)
        self.assertEqual(b['vdp_commands'], 6912)
        self.assertIn(0x0018, a['code_paths'])  # actual RST 18 pointer helper
        self.assertIn(0x0028, a['code_paths'])  # actual RST 28 VDP helper
        self.assertIn(0x0695, a['code_paths'])  # RLE consumer
        self.assertIn(0x3ACC, a['code_paths'])  # directory consumer
        self.assertGreater(a['cpu_instructions'], 140000)

    def test_directory_is_nonmonotonic_and_dispatched_correctly(self):
        bank = self.rom[13 * 0x4000:14 * 0x4000]
        pointers = [int.from_bytes(bank[DIRECTORY - 0x8000 + i * 2:
                                        DIRECTORY - 0x8000 + i * 2 + 2], 'little')
                    for i in range(50)]
        self.assertEqual(len(set(pointers)), 50)
        self.assertNotEqual(pointers, sorted(pointers))
        self.assertEqual([r['first_directory_pointer'] for r in self.audit['single_resource_runs']], pointers)

    def test_tail_has_two_independent_vdp_consumers(self):
        tail = self.audit['tail_graphics_consumers']
        self.assertEqual([x['vdp_write_command'] for x in tail], [0x5600, 0x7000, 0x7600])
        self.assertEqual([x['source_start'] for x in tail], [0xA9A3, 0xA9A3, 0xBBF7])
        self.assertEqual([x['source_end_exclusive'] for x in tail], [0xABBA, 0xABBA, 0xBC23])
        self.assertEqual([x['compressed_bytes'] for x in tail], [535, 535, 44])
        self.assertEqual([x['decoded_bytes'] for x in tail], [640, 640, 128])
        self.assertEqual(tail[0]['output_sha256'], tail[1]['output_sha256'])
        self.assertEqual(self.audit['tail_remaining_unclassified_bytes'], 5028)

    def test_rejects_invalid_resource_requests(self):
        for idx, count in [(-1, 1), (0, 0), (49, 2), (50, 1), (0, 51)]:
            with self.subTest(idx=idx, count=count), self.assertRaises(ValueError):
                execute(self.rom, idx, count)
        with self.assertRaises(ValueError):
            execute(self.rom, 0, 1, 0xFFFF)
        with self.assertRaises(ValueError):
            execute_tail(self.rom, 0x4120)

    def test_z80_model_fails_closed_for_unrecognized_instruction(self):
        bad = bytearray(self.rom)
        bad[LOADER] = 0xFF
        emulator = ConsumerMachine(bytes(bad), LOADER)
        emulator.slot[2] = 13
        with self.assertRaises(UnsupportedOpcode):
            emulator.step()
        with self.assertRaises(ValueError):
            report(bytes(bad))

    def test_decoder_rejects_malformed_or_wrong_size_plane(self):
        with self.assertRaises(ValueError):
            decode_rle_plane(b'\x01\x12\x00', 0)
        with self.assertRaises(ValueError):
            decode_rle_plane(b'\x80\x00', 0)
        with self.assertRaises(ValueError):
            decode_rle_plane(b'\x48\x12', 0)
        plane, ending = decode_rle_plane(b'\x48\x12\x00', 0)
        self.assertEqual(len(plane), 72)
        self.assertEqual(ending, 3)
        self.assertEqual(hashlib.sha256(plane).digest(), hashlib.sha256(bytes([0x12]) * 72).digest())


if __name__ == '__main__':
    unittest.main()
