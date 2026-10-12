#!/usr/bin/env python3
"""Whole-bank 8+10 source isolation, structure, negative mutation and execution gates."""
import copy
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
from build_sms_phase14 import EXPECTED_SHA
from whole_banks08_10 import (full_bank,existing,new_bytes,new_code,mixed_source,assemble_mixed,
    path,digestpath,asmpath,B8_LOOKUP,B10_DIR,B10_WORDS,B10_MAIN)
from build_system_m8 import complete_banks,build,SOURCED,NEW,BANKS
from bank10_decimal_trace import execute,trace

ROM=None

class TestBankClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=ROM.read_bytes()
        assert hashlib.sha256(cls.rom).hexdigest()==EXPECTED_SHA
        cls.bank8=cls.rom[8*16384:9*16384]
        cls.bank10=cls.rom[10*16384:11*16384]

    def test_01_bank8_source_only(self):self.assertEqual(full_bank(8),self.bank8)
    def test_02_bank10_source_only(self):self.assertEqual(full_bank(10),self.bank10)
    def test_03_bank8_complete_assembly(self):self.assertEqual(assemble_mixed((ROOT/asmpath(8)).read_text()),self.bank8)
    def test_04_bank10_complete_assembly(self):self.assertEqual(assemble_mixed((ROOT/asmpath(10)).read_text()),self.bank10)
    def test_05_canonical_source_views(self):
        for n in (8,10):self.assertEqual((ROOT/asmpath(n)).read_text(),mixed_source(n))
    def test_06_original_code_separate(self):
        self.assertEqual(len(existing(8)),138);self.assertEqual(len(existing(10)),75)
        self.assertEqual(len(new_code()),38)
    def test_07_new_source_ownership(self):
        a,la=new_bytes(8);b,lb=new_bytes(10)
        self.assertEqual(len(a),16208);self.assertEqual(len(b),16309)
        self.assertEqual(sum(x['bytes'] for x in la),len(a))
        self.assertEqual(sum(x['bytes'] for x in lb),len(b))
    def test_08_bank8_lookup(self):
        src=json.loads((ROOT/path(8)).read_text())['lookup_tables']
        self.assertEqual(len(src['records_11x5']),11)
        self.assertEqual(len(src['offset_x_6']),6)
        self.assertEqual(len(src['offset_y_6']),6)
        self.assertEqual(6+6+1+11*5,B8_LOOKUP[1]-B8_LOOKUP[0])
    def test_09_bank10_directory_and_terminated_records(self):
        src=json.loads((ROOT/path(10)).read_text())['text_directory']
        rec=src['terminated_records'];words=src['pointers']
        self.assertEqual(len(rec),9);self.assertEqual(len(words),11)
        self.assertEqual(words[-2:],[rec[0]['start'],rec[-1]['start']])
        self.assertEqual(sum(len(r['encoded'])+1 for r in rec),B10_WORDS[1]-B10_WORDS[0])
    def test_10_standalone_nine_banks(self):
        banks=complete_banks();self.assertEqual(sorted(banks),BANKS)
        for n in BANKS:self.assertEqual(banks[n],self.rom[n*16384:(n+1)*16384])
    def test_11_full_rom_exact(self):
        output,report=build(self.rom)
        self.assertEqual(output,self.rom)
        self.assertEqual(report['new_source_backed_bytes'],NEW)
        self.assertEqual(report['source_backed_bytes'],SOURCED)
        self.assertEqual(report['source_only_complete_banks'],BANKS)
    def test_12_snapshot(self):
        _,report=build(self.rom)
        self.assertEqual(report,json.loads((ROOT/'whole_system/build_report_m8.json').read_text()))
    def test_13_decimal_runtime(self):
        result=trace();self.assertEqual(result,json.loads((ROOT/'wholebank10/decimal_trace.json').read_text()))
        self.assertGreaterEqual(result['tested_values'],250)
    def test_14_decimal_boundary_and_separator(self):
        for v in (0,1,9,10,99,100,999,1000,9999,10000,65535):
            self.assertEqual(execute(full_bank(10),v,0x20)['port_bytes'],10)
    def test_15_invalid_decimal_code(self):
        b=bytearray(self.bank10);b[0xBF35-0x8000]=0x76
        with self.assertRaises(ValueError):execute(bytes(b),1000)
    def test_16_fingerprint_rejection(self):
        b=bytearray(self.rom);b[-30]^=1
        with self.assertRaises(ValueError):build(bytes(b))

class TestMutations(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        for n in (8,10):
            for p in (path(n),digestpath(n),asmpath(n)):
                (self.root/p).parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(ROOT/p,self.root/p)
            p=Path(f'src/phase11_roundtrip/bank{n:02}.asm')
            (self.root/p).parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/p,self.root/p)
        p=Path('src/wholebank08/extra_code.asm')
        shutil.copy2(ROOT/p,self.root/p)
    def tearDown(self):self.temp.cleanup()
    def change(self,n,mutation):
        p=self.root/path(n);data=json.loads(p.read_text());mutation(data)
        p.write_text(json.dumps(data))
        with self.assertRaises((ValueError,KeyError,TypeError)):full_bank(n,self.root)
    def test_17_bank8_bad_script_byte(self):
        self.change(8,lambda d:d['unresolved_script_region'][0].__setitem__('hex','ff'+d['unresolved_script_region'][0]['hex'][2:]))
    def test_18_bank8_script_chunk_gap(self):
        self.change(8,lambda d:d['unresolved_script_region'][1].__setitem__('start',d['unresolved_script_region'][1]['start']+1))
    def test_19_bank8_record_length(self):
        self.change(8,lambda d:d['lookup_tables']['records_11x5'][1].pop())
    def test_20_bank8_lookup_changed(self):
        self.change(8,lambda d:d['lookup_tables']['offset_y_6'].__setitem__(0,255))
    def test_21_bank8_extra_code_changed(self):
        p=self.root/'src/wholebank08/extra_code.asm'
        p.write_text(p.read_text().replace('ld a,($C120)','ld a,($C121)',1))
        with self.assertRaises(ValueError):full_bank(8,self.root)
    def test_22_bank8_padding(self):
        self.change(8,lambda d:d['padding'].__setitem__('count',14))
    def test_23_bank10_pointer_alias(self):
        self.change(10,lambda d:d['text_directory']['pointers'].__setitem__(-1,0xBE93))
    def test_24_bank10_string_mutation(self):
        self.change(10,lambda d:d['text_directory']['terminated_records'][2]['encoded'].__setitem__(0,0))
    def test_25_bank10_embedded_terminator(self):
        self.change(10,lambda d:d['text_directory']['terminated_records'][0]['encoded'].__setitem__(0,255))
    def test_26_bank10_resource_byte(self):
        self.change(10,lambda d:d['unresolved_resource_region'][2].__setitem__('hex','00'+d['unresolved_resource_region'][2]['hex'][2:]))
    def test_27_bank10_trailer_gap(self):
        self.change(10,lambda d:d['undecoded_trailing_region'][0].__setitem__('start',B10_MAIN[1]))
    def test_28_bank10_assembler_mismatch(self):
        p=self.root/'src/phase11_roundtrip/bank10.asm'
        p.write_text(p.read_text().replace('rst $0028','rst $0030',1))
        with self.assertRaises(ValueError):full_bank(10,self.root)
    def test_29_bank10_padding_changed(self):
        self.change(10,lambda d:d['padding'].__setitem__('value',0))
    def test_30_bank8_wrong_sha(self):
        p=self.root/digestpath(8);d=json.loads(p.read_text());d['bank_sha256']='f'*64;p.write_text(json.dumps(d))
        with self.assertRaises(ValueError):full_bank(8,self.root)

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: tests_whole_banks08_10.py owner.sms')
    ROM=Path(sys.argv.pop(1))
    unittest.main(verbosity=1)
