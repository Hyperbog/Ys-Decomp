#!/usr/bin/env python3
"""ROM-free tests: master listing is exact, bank-addressed source reference."""
import tempfile
import unittest
from pathlib import Path

from tools.build_master_rom_listing import assembled_reference
from tools.build_sms_phase14 import ROOT


class MasterListingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = assembled_reference()

    def test_document_stays_in_sync(self):
        committed = (ROOT/"whole_system/MASTER_ROM_LISTING.txt").read_text()
        self.assertEqual(committed, self.document)

    def test_all_16_bank_sections_in_order(self):
        last = -1
        for bank in range(16):
            marker = "; PHYSICAL BANK %02d | ROM $%05X-$%05X" % (
                bank, bank*0x4000, bank*0x4000+0x3FFF)
            pos = self.document.find(marker)
            self.assertGreater(pos,last)
            self.assertEqual(self.document.count(marker),1)
            last = pos
        self.assertEqual(self.document.count("; PHYSICAL BANK "),16)

    def test_source_mnemonics_and_data_not_reclassified(self):
        self.assertIn("; Instruction bytes: 22552",self.document)
        self.assertIn("; Data directive bytes: 239592",self.document)
        self.assertIn("; Uncertain labels lower bound: 141581",self.document)
        for bank in range(16):
            name="src/wholebank%02d/bank%02d_complete.asm" % (bank,bank)
            source=(ROOT/name).read_text()
            if not source.endswith("\n"):
                source += "\n"
            self.assertIn(source,self.document)

    def test_modified_master_rejected_by_comparison(self):
        changed = self.document.replace("; Instruction bytes: 22552",
                                        "; Instruction bytes: 262144",1)
        self.assertNotEqual(changed,self.document)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"MASTER_ROM_LISTING.txt"
            path.write_text(changed)
            self.assertNotEqual(path.read_text(),assembled_reference())


if __name__=="__main__":
    unittest.main()
