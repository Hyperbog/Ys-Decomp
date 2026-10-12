#!/usr/bin/env python3
"""M13 regression: source completeness and semantic uncertainty must stay visible."""
import copy
import tempfile
import unittest
from pathlib import Path
from tools.semantic_debt_m13 import make_report,analyze_bank
from tools.build_sms_phase14 import ROOT

class SemanticAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=make_report()
    def test_whole_cartridge_partition(self):
        r=self.report
        self.assertEqual(r['bank_count'],16)
        self.assertEqual(r['mnemonic_bytes']+r['data_directive_bytes'],262144)
        self.assertEqual(r['mnemonic_bytes'],22552)
        self.assertEqual(r['explicitly_uncertain_bytes_lower_bound'],141581)
    def test_every_bank_has_exact_size(self):
        for bank in self.report['banks']:
            self.assertEqual(bank['mnemonic_bytes']+bank['db_bytes']+bank['dw_bytes'],16384)
            self.assertLessEqual(bank['explicitly_uncertain_bytes_lower_bound'],16384)
    def test_generated_report_stable(self):
        import json
        existing=json.loads((ROOT/'whole_system/semantic_debt_m13.json').read_text())
        self.assertEqual(existing,self.report)
    def test_missing_bank_source_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):analyze_bank(5,Path(tmp))
    def test_unknown_opcode_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);dest=root/'src/wholebank05';dest.mkdir(parents=True)
            content=(ROOT/'src/wholebank05/bank05_complete.asm').read_text()
            (dest/'bank05_complete.asm').write_text(content+'\n    not_an_opcode\n')
            with self.assertRaises(Exception):analyze_bank(5,root)
    def test_modified_directive_fails_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);dest=root/'src/wholebank05';dest.mkdir(parents=True)
            content=(ROOT/'src/wholebank05/bank05_complete.asm').read_text()
            (dest/'bank05_complete.asm').write_text(content.replace('db $0D, $00, $83,', 'db $0D, $00,',1))
            with self.assertRaises(ValueError):analyze_bank(5,root)
    def test_duplicate_org_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);dest=root/'src/wholebank05';dest.mkdir(parents=True)
            content=(ROOT/'src/wholebank05/bank05_complete.asm').read_text()
            (dest/'bank05_complete.asm').write_text(content+'\norg $8000\n db $00\n')
            with self.assertRaises(ValueError):analyze_bank(5,root)
if __name__=='__main__':unittest.main()
