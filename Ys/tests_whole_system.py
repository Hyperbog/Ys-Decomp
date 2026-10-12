#!/usr/bin/env python3
"""16-bank architecture accounting and whole-bank milestone gates."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
from build_whole_system import assemble_complete_banks,build,SOURCED
from build_sms_phase14 import EXPECTED_SHA
from whole_bank03 import mixed_source as bank3_source
from whole_bank07 import mixed_source as bank7_source
ROM=Path(sys.argv.pop(1)).resolve() if len(sys.argv)>1 and not sys.argv[1].startswith('-') else None

class SystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if ROM is None:raise ValueError('Requires original user-owned Ys ROM')
        cls.rom=ROM.read_bytes()
        cls.complete=assemble_complete_banks(ROOT)

    def test_01_complete_bank_is_independent(self):
        self.assertEqual(set(self.complete),{3,7})
        self.assertEqual([len(v) for v in self.complete.values()],[16384,16384])

    def test_02_bank_assembly_is_not_rom_copying(self):
        self.assertIn('Mode4Tiles:',bank3_source(ROOT))
        self.assertIn('GridGraphicsEngine:',bank7_source(ROOT))
        self.assertIn('    outi',bank7_source(ROOT))

    def test_03_integrated_system_matches_user_rom(self):
        result,report=build(self.rom)
        self.assertEqual(result,self.rom)
        self.assertEqual(hashlib.sha256(result).hexdigest(),EXPECTED_SHA)
        self.assertEqual(report['total_source_backed_bytes'],53249)
        self.assertEqual(report['total_fallback_bytes'],208895)
        self.assertFalse(report['full_rom_source_only'])

    def test_04_every_physical_bank_counted_once(self):
        _,r=build(self.rom)
        self.assertEqual([b['bank'] for b in r['per_bank']],list(range(16)))
        self.assertEqual(sum(b['source_backed_bytes'] for b in r['per_bank']),SOURCED)
        self.assertEqual(sum(b['original_rom_fallback_bytes'] for b in r['per_bank']),208895)
        self.assertEqual([b['bank'] for b in r['per_bank'] if b['source_only_complete']],[3,7])

    def test_05_system_report_is_reproducible(self):
        _,r=build(self.rom)
        self.assertEqual(r,json.loads((ROOT/'whole_system/build_report.json').read_text()))

    def test_06_no_false_semantic_or_external_claims(self):
        _,r=build(self.rom)
        self.assertEqual(r['new_unresolved_visual_bytes'],3043)
        self.assertFalse(r['full_system_emulator_verified'])
        self.assertFalse(r['external_wla_dx_verified'])
        self.assertEqual(r['new_matched_instruction_bytes'],173)

    def test_07_both_original_bank_digests_match(self):
        for bank,blob in self.complete.items():
            self.assertEqual(blob,self.rom[bank*16384:(bank+1)*16384])

if __name__=='__main__':unittest.main(verbosity=2)
