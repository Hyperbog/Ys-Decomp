#!/usr/bin/env python3
"""Phase 14: strict offline full-image overlay and bank-aware reference tests."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
from build_sms_phase14 import EXPECTED_SHA, ROM_SIZE, SOURCES, build, offset  # noqa: E402

ROM = Path('/mnt/data/Ys - The Vanished Omens (USA, Europe).sms')


class OverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM.read_bytes()
        cls.built, cls.report, cls.refs = build(cls.rom)

    def test_complete_image_has_exact_original_sha(self):
        self.assertEqual(len(self.built), ROM_SIZE)
        self.assertEqual(hashlib.sha256(self.built).hexdigest(), EXPECTED_SHA)
        self.assertEqual(self.built, self.rom)

    def test_strict_coverage_partition_and_11_sources(self):
        self.assertEqual(self.report['matched_source_bytes'], 14025)
        self.assertEqual(self.report['unknown_template_bytes'], 248119)
        self.assertEqual(len(self.report['sources']), 11)
        self.assertEqual(sum(r['sourced_code_bytes'] for r in self.report['banks']), 14025)
        self.assertEqual(sum(r['template_bytes'] for r in self.report['banks']), 248119)
        self.assertFalse(self.report['source_only_build'])
        self.assertFalse(self.report['external_assembler_verified'])

    def test_physical_bank_mappings_and_boundaries(self):
        self.assertEqual(offset(0, 0x0000), 0)
        self.assertEqual(offset(1, 0x4000), 0x4000)
        self.assertEqual(offset(2, 0x8000), 0x8000)
        self.assertEqual(offset(6, 0x9932), 0x19932)
        self.assertEqual(offset(7, 0x8180), 0x1C180)
        self.assertEqual(offset(15, 0xBFFF), 0x3FFFF)
        for bank, cpu in [(0, 0x8000), (1, 0x8000), (6, 0x7FFF), (15, 0xC000), (16, 0x8000)]:
            with self.subTest(bank=bank, cpu=cpu), self.assertRaises(ValueError):
                offset(bank, cpu)

    def test_reference_index_is_explicitly_conservative(self):
        refs = self.refs['references']
        self.assertEqual(len(refs), self.report['cross_references']['total'])
        self.assertTrue(refs)
        for entry in refs:
            t = int(entry['target_cpu'], 16)
            if t < 0x4000:
                self.assertEqual(entry['proven_target_bank'], 0)
                self.assertEqual(entry['mapping_evidence'], 'fixed_bank0')
            else:
                self.assertIsNone(entry['proven_target_bank'])
                self.assertIn(entry['mapping_evidence'], (
                    'slot1_mapper_not_proven', 'slot2_mapper_not_proven'))
        self.assertGreater(self.report['cross_references']['mapper_unresolved'], 0)

    def test_committed_metadata_matches_recomputed(self):
        expected = json.loads((ROOT / 'phase14/build_report.json').read_text())
        references = json.loads((ROOT / 'phase14/crossrefs.json').read_text())
        self.assertEqual(expected, self.report)
        self.assertEqual(references, self.refs)

    def test_wrong_rom_rejected_including_single_changed_byte(self):
        altered = bytearray(self.rom)
        altered[0x3FFF0] ^= 1
        with self.assertRaisesRegex(ValueError, 'Original ROM missing/wrong'):
            build(bytes(altered))
        with self.assertRaises(ValueError):
            build(self.rom[:-1])

    def test_duplicate_module_rejected_without_double_count(self):
        specs = SOURCES + (SOURCES[0],)
        with self.assertRaisesRegex(ValueError, 'duplicate source module'):
            build(self.rom, specs=specs)

    def test_mutated_assembly_is_rejected_not_template_masked(self):
        with tempfile.TemporaryDirectory() as td:
            temp = Path(td)
            rel = SOURCES[0][0]
            path = temp / rel
            path.parent.mkdir(parents=True)
            original = (ROOT / rel).read_text()
            self.assertIn('    di ', original)
            path.write_text(original.replace('    di ', '    ei ', 1))
            with self.assertRaisesRegex(ValueError, 'ASM/ROM mismatch'):
                build(self.rom, root=temp, specs=(SOURCES[0],))

    def test_source_bank_mapping_error_rejected(self):
        with self.assertRaisesRegex(ValueError, 'outside its expected slot'):
            build(self.rom, specs=((SOURCES[0][0], 1),))


if __name__ == '__main__':
    unittest.main(verbosity=2)
