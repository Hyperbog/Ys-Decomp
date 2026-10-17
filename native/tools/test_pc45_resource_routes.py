"""PC-45 mutation tests against committed source records and ROM hashes."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pc45_resource_routes import analyze, strict_json, ROOT


class ResourceRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = [strict_json(ROOT / name) for name in (
            'Ys/wholebank00/source.json', 'Ys/phase21/source.json',
            'Ys/phase6/coverage.json', 'Ys/phase6/regions.json')]

    def copied(self):
        return copy.deepcopy(self.inputs)

    def test_complete_source_dataset(self):
        r = analyze(*self.copied())
        self.assertEqual((r['directory_entries'], r['unique_records'],
                          r['directory_bytes'], r['record_bytes'],
                          r['handler_bytes']), (41, 23, 82, 207, 82))
        self.assertEqual((r['record_flags_c198_one'], r['record_flags_c19a_one']),
                         (3, 1))
        self.assertEqual([x['record_index'] for x in r['routes']],
                         [*range(23), *([22] * 18)])
        self.assertEqual(r['records'][0]['address'], '2585')
        self.assertEqual(r['records'][0]['C198'], 0)
        self.assertEqual(r['records'][22]['C19A'], 1)
        self.assertEqual(r['routes'][40]['handler_pc'], '249D')

    def test_directory_alias_corruption_fails(self):
        v = self.copied()
        v[0]['segments'][next(i for i,s in enumerate(v[0]['segments'])
                         if s.get('name') == 'nine_byte_resource_directory_41')]['words'][40] = 0x2585
        with self.assertRaises(ValueError): analyze(*v)

    def test_record_flag_and_pointer_mutations_fail(self):
        for index, cell, replacement in ((0, 8, 128), (0, 0, 255), (0, 1, 0)):
            with self.subTest(index=index, cell=cell):
                v = self.copied()
                v[1]['bank0_indexed_records'][index]['bytes'][cell] = replacement
                with self.assertRaises(ValueError): analyze(*v)

    def test_handler_and_digest_mutations_fail(self):
        v = self.copied()
        v[2]['dispatch_tables']['205A'][0] = '249D'
        with self.assertRaises(ValueError): analyze(*v)
        v = self.copied()
        v[3]['data'][1]['sha256'] = '0' * 64
        with self.assertRaises(ValueError): analyze(*v)

    def test_rom_integrity_and_opcode_gates(self):
        v = self.copied()
        with self.assertRaisesRegex(ValueError, 'Wrong original'):
            analyze(*v, rom=bytes(262144))
        with self.assertRaisesRegex(ValueError, 'Wrong original'):
            analyze(*v, rom=bytes(262143))

    def test_pc44_real_source_relation_fails_closed(self):
        event = {'pc': '2041', 'hl': '258D',
                 'source_at_hl': 0, 'after': 0}
        audit = {'schema': 'ys-pc44-physical-c198-writes-v1', 'events': [event]}
        analyze(*self.copied(), pc44=audit)
        for key, invalid in (('hl', '258C'), ('source_at_hl', 128), ('after', 1)):
            with self.subTest(key=key):
                tampered = copy.deepcopy(audit)
                tampered['events'][0][key] = invalid
                with self.assertRaises(ValueError):
                    analyze(*self.copied(), pc44=tampered)


if __name__ == '__main__':
    unittest.main()
