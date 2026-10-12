#!/usr/bin/env python3
"""Mutation, system integration, and provenance checks for fixed-bank reconstruction."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent/'tools'))
from build_sms_phase14 import ROOT, EXPECTED_SHA
import whole_bank00 as bank0
import build_system_m3
import build_system_graph_m3
import wla_system_m3

ROM=None

class FixedBankSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=ROM.read_bytes()
        assert hashlib.sha256(cls.rom).hexdigest()==EXPECTED_SHA
    def test_exact_bank_hash(self):self.assertEqual(bank0.full_bank(),self.rom[:0x4000])
    def test_full_mixed_assembly(self):self.assertEqual(bank0.assemble_mixed_fixed(bank0.mixed_source()),self.rom[:0x4000])
    def test_old_and_new_byte_partition(self):
        old=bank0.existing();new,_=bank0.parsed_new_instructions();data,details=bank0.data_chunks()
        self.assertFalse(set(old)&set(new) or set(old)&set(data) or set(new)&set(data))
        self.assertEqual((len(old),len(new),len(data)),(8242,6518,1624))
        self.assertEqual(set(old)|set(new)|set(data),set(range(0x4000)))
        self.assertEqual(sum(e-s for s,(e,k,_) in details.items() if k=='unresolved'),1161)
    def test_no_db_in_new_instruction_source(self):
        text=(ROOT/bank0.ASM).read_text().lower()
        self.assertNotIn('\n    db ',text)
        self.assertNotIn('\n    dw ',text)
        self.assertEqual(len(bank0.CODE_SPANS),35)
    def test_full_256k_overlay(self):
        rebuilt,report=build_system_m3.build(self.rom)
        self.assertEqual(rebuilt,self.rom)
        self.assertEqual(report['source_only_complete_banks'],[0,3,7])
        self.assertEqual((report['source_backed_bytes'],report['original_rom_fallback_bytes']),(61391,200753))
    def test_standalone_banks(self):
        images=build_system_m3.complete_banks()
        self.assertEqual(sorted(images),[0,3,7])
        for n,img in images.items():self.assertEqual(img,self.rom[n*0x4000:(n+1)*0x4000])
    def test_corrupt_rom_rejected(self):
        corrupt=bytearray(self.rom);corrupt[0x0718]^=1
        with self.assertRaises(ValueError):build_system_m3.build(bytes(corrupt))
    def test_graph_new_bank_bytes(self):
        result=build_system_graph_m3.build(self.rom)
        self.assertEqual(result['summary']['verified_instruction_bytes'],20716)
        self.assertEqual(result['banks'][0]['verified_code_bytes'],14453)
        self.assertTrue(result['summary']['portable_topology_validated'])
    def test_malformed_pointer_rejected(self):
        obj=json.loads((ROOT/bank0.SOURCE).read_text())
        for seg in obj['segments']:
            if seg['name']=='actor_handler_dispatch_34':
                seg['words'][0]=0xFFFF;break
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'wholebank00').mkdir()
            (p/bank0.SOURCE).write_text(json.dumps(obj))
            with self.assertRaises(ValueError):bank0.data_chunks(p)
    def test_mutated_unresolved_data_changes_fingerprint(self):
        obj=json.loads((ROOT/bank0.SOURCE).read_text())
        for seg in obj['segments']:
            if seg['kind']=='unresolved' and len(seg['hex'])>=2:
                seg['hex']=('00' if seg['hex'][:2]!='00' else '01')+seg['hex'][2:];break
        # Metadata accepts unresolved bytes but bank digest rejects any source drift.
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'wholebank00').mkdir()
            (p/bank0.SOURCE).write_text(json.dumps(obj))
            changed,_=bank0.data_chunks(p)
            pristine,_=bank0.data_chunks()
            self.assertNotEqual(changed,pristine)
    def test_duplicate_data_segment_rejected(self):
        obj=json.loads((ROOT/bank0.SOURCE).read_text());obj['segments'].append(obj['segments'][0])
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'wholebank00').mkdir()
            (p/bank0.SOURCE).write_text(json.dumps(obj))
            with self.assertRaises(ValueError):bank0.data_chunks(p)
    def test_invalid_z80_instruction_rejected(self):
        text=(ROOT/bank0.ASM).read_text()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'src/wholebank00').mkdir(parents=True)
            (p/bank0.ASM).write_text(text.replace('    ld ', '    broken ',1))
            with self.assertRaises(ValueError):bank0.parsed_new_instructions(p)
    def test_invalid_z80_org_rejected(self):
        text=(ROOT/bank0.ASM).read_text()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'src/wholebank00').mkdir(parents=True)
            (p/bank0.ASM).write_text(text.replace('org $0288','org $0289',1))
            with self.assertRaises(ValueError):bank0.parsed_new_instructions(p)
    def test_wla_fixture_banks_and_failclosed(self):
        with tempfile.TemporaryDirectory() as d:
            result=wla_system_m3.prepare(d)
            self.assertEqual(result['banks'],[0,3,7])
            self.assertFalse(result['independent_assembly_verified'])
            self.assertIn('.BANK 0 SLOT 0',(Path(d)/'bank00.asm').read_text())
            with self.assertRaises(FileNotFoundError):
                wla_system_m3.verify(d,assembler='missing-wla-z80-m3',linker='missing-wlalink-m3')

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: tests_whole_bank00.py path/to/Ys.sms')
    ROM=Path(sys.argv.pop())
    unittest.main(verbosity=2)
