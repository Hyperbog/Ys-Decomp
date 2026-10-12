"""M15 regression suite: lossless resource-owned Bank 13 source, not opaque hex."""
import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
from bank13_semantic_source_m15 import (START, LAST_RESOURCE_END, PLANE_SIZE,
                                         decode_legacy_resources, encode_plane,
                                         encode_resources, verify)
from whole_banks05_13_14_15 import full_bank, unpack_chunks


class SemanticBank13SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads((ROOT / 'wholebank13/source.json').read_text())
        cls.pointers = cls.source['indexed_resource_directory']['pointers']
        cls.records = cls.source['rle_resource_records']
        cls.bank = full_bank(13)

    def test_schema_and_source_owned_graphics(self):
        self.assertEqual(self.source['schema'], 'ys-bank13-source-v2')
        self.assertEqual(len(self.records), 50)
        self.assertEqual(sum(len(r['planes']) for r in self.records), 200)
        self.assertTrue(all(len(p['decoded_hex']) == PLANE_SIZE * 2
                            for r in self.records for p in r['planes']))

    def test_lossless_source_to_verified_cartridge_bank(self):
        data = encode_resources(self.records, self.pointers)
        self.assertEqual(len(data), 10659)
        self.assertEqual(data, self.bank[:len(data)])
        self.assertEqual(hashlib.sha256(self.bank).hexdigest(),
                         '00227b5f7b913280a53e60ad90743371b82381a30c8514aa4d92a287e062b39e')
        verify(ROOT)

    def test_200_packet_recipes_roundtrip_exact_original(self):
        reconstructed = decode_legacy_resources(self.bank[:0x3f8a], self.pointers)
        self.assertEqual(reconstructed, self.records)
        self.assertEqual(sum(len(encode_plane(p)) for r in self.records for p in r['planes']),
                         10659)

    def test_unresolved_tail_is_only_raw_source(self):
        tail = unpack_chunks(self.source['unresolved_asset_chunks'], LAST_RESOURCE_END, 0xbf8a)
        self.assertEqual(len(tail), 5607)
        self.assertEqual(tail, self.bank[LAST_RESOURCE_END - START:0x3f8a])

    def test_reject_bad_plane_bytes_and_schema(self):
        p = self.records[0]['planes'][0]
        with self.assertRaises(ValueError):
            encode_plane({'decoded_hex': p['decoded_hex'][:-2],
                          'packet_controls': p['packet_controls']})
        with self.assertRaises(ValueError):
            encode_plane({'decoded_hex': p['decoded_hex'], 'packet_controls': [0]})
        with self.assertRaises(ValueError):
            encode_plane({'decoded_hex': p['decoded_hex'], 'packet_controls': [0x80]})

    def test_reject_wrong_packet_control_and_missing_last_packet(self):
        p = self.records[0]['planes'][0]
        with self.assertRaises(ValueError):
            encode_plane({'decoded_hex': p['decoded_hex'], 'packet_controls': [0xFF]})
        with self.assertRaises(ValueError):
            encode_plane({'decoded_hex': p['decoded_hex'], 'packet_controls': p['packet_controls'][:-1]})

    def test_reject_wrong_resource_directory(self):
        with self.assertRaises(ValueError):
            encode_resources(self.records[:-1], self.pointers)
        with self.assertRaises(ValueError):
            encode_resources(self.records, self.pointers[:-1])
        bad = list(self.pointers)
        bad[1] = bad[0]
        with self.assertRaises(ValueError):
            encode_resources(self.records, bad)

    def test_reject_reordered_and_noncontiguous_resources(self):
        reversed_records = list(reversed(self.records))
        with self.assertRaises(ValueError):
            encode_resources(reversed_records, self.pointers)
        wrong = copy.deepcopy(self.records)
        wrong[1]['start'] += 1
        with self.assertRaises(ValueError):
            encode_resources(wrong, self.pointers)


if __name__ == '__main__':
    unittest.main()
