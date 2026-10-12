#!/usr/bin/env python3
"""Whole-bank closure gates: source-only bytes, boundaries, and negative cases."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
from whole_bank07 import (full_bank,known_bytes,load_tail,mixed_source,assemble_mixed,
                          CODE_RANGES,MAP_DIRECTORY,MAP_RECORDS,TEXT,TEXT_DIRECTORY,
                          SIZE,BASE,FILE,ASM,DIGEST)
from build_whole_bank07 import build
from build_sms_phase14 import EXPECTED_SHA
ROM=Path(sys.argv.pop(1)).resolve() if len(sys.argv)>1 and not sys.argv[1].startswith('-') else None

class FullBankTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if ROM is None:raise ValueError('Supply original Ys ROM to verify full-bank reconstruction')
        cls.rom=ROM.read_bytes()
        cls.source=json.loads((ROOT/FILE).read_text())
        cls.bank=full_bank(ROOT)

    def scratch(self,mutate=None,change_asm=None):
        td=tempfile.TemporaryDirectory()
        path=Path(td.name)
        for rel in (FILE,ASM,DIGEST):
            target=path/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/rel,target)
        if mutate:
            data=copy.deepcopy(self.source)
            mutate(data)
            (path/FILE).write_text(json.dumps(data))
        if change_asm:
            p=path/ASM
            p.write_text(change_asm(p.read_text()))
        return td,path

    def test_01_source_only_bank_matches_rom(self):
        self.assertEqual(len(self.bank),SIZE)
        self.assertEqual(self.bank,self.rom[BASE:BASE+SIZE])

    def test_02_source_only_known_graphics_and_tail_no_gaps(self):
        existing=known_bytes(ROOT)
        late=load_tail(ROOT)
        self.assertEqual(len(existing),13631)
        self.assertEqual(len(late),2753)
        self.assertEqual(set(existing)&set(late),set())
        self.assertEqual(set(existing)|set(late),set(range(0x8000,0xC000)))

    def test_03_mixed_assembly_roundtrip(self):
        text=mixed_source(ROOT)
        self.assertEqual(assemble_mixed(text),self.bank)
        self.assertEqual(text,(ROOT/'src/wholebank07/bank07_complete.asm').read_text())

    def test_04_code_boundaries_and_encoded_size(self):
        self.assertEqual(sum(stop-start for start,stop in CODE_RANGES),173)
        self.assertEqual(CODE_RANGES,((0xB53F,0xB596),(0xB9D6,0xBA0F),(0xBA1E,0xBA3B)))

    def test_05_map_groups_and_directory(self):
        src=self.source
        self.assertEqual(len(src['map_pointers']),22)
        self.assertEqual(len(src['map_groups']),22)
        self.assertEqual(len(self.bank[MAP_DIRECTORY[0]-0x8000:MAP_DIRECTORY[1]-0x8000]),44)
        self.assertEqual(sum(4*len(g['records'])+int(g['terminator_zero']) for g in src['map_groups']),856)
        self.assertEqual(src['map_pointers'][0],MAP_RECORDS[0])
        self.assertEqual(src['map_pointers'][-1],0xBDBA)

    def test_06_text_directory_and_spans(self):
        src=self.source
        self.assertEqual(len(src['text_pointers']),21)
        self.assertEqual(len(src['text_selector_symbols']),21)
        self.assertEqual(len(src['text_prefix'])+sum(map(len,src['text_blocks'])),TEXT[1]-TEXT[0])
        self.assertEqual(TEXT_DIRECTORY[1]-TEXT_DIRECTORY[0],42)

    def test_07_structurally_unresolved_not_hidden(self):
        self.assertEqual(len(bytes.fromhex(self.source['unresolved_visual_bytes_hex'])),1088)
        self.assertEqual(self.source['padding_length'],45)

    def test_08_system_overlay_exact_sha(self):
        out,report=build(self.rom)
        self.assertEqual(out,self.rom)
        self.assertEqual(hashlib.sha256(out).hexdigest(),EXPECTED_SHA)
        self.assertEqual(report['source_backed_bytes'],49102)
        self.assertEqual(report['fallback_bytes'],213042)
        self.assertEqual(report['whole_source_only_banks'],[7])
        self.assertEqual(report['per_bank'][7]['fallback_bytes'],0)
        self.assertFalse(report['source_only_complete_rom'])

    def test_09_system_report_matches_committed(self):
        _,report=build(self.rom)
        self.assertEqual(report,json.loads((ROOT/'wholebank07/build_report.json').read_text()))

    def test_10_mutated_unresolved_art_rejected(self):
        def mutate(src):
            a=src['unresolved_visual_bytes_hex']
            src['unresolved_visual_bytes_hex']=('00' if a[:2]!='00' else '01')+a[2:]
        td,p=self.scratch(mutate)
        try:self.assertRaises(ValueError,load_tail,p)
        finally:td.cleanup()

    def test_11_mutated_map_record_rejected(self):
        def mutate(src):src['map_groups'][0]['records'][0][2]^=1
        td,p=self.scratch(mutate)
        try:self.assertRaises(ValueError,load_tail,p)
        finally:td.cleanup()

    def test_12_corrupt_pointer_directory_rejected(self):
        def mutate(src):src['map_pointers'][1]+=1
        td,p=self.scratch(mutate)
        try:self.assertRaises(ValueError,load_tail,p)
        finally:td.cleanup()

    def test_13_corrupt_text_directory_rejected(self):
        def mutate(src):src['text_pointers'][2]=0xA000
        td,p=self.scratch(mutate)
        try:self.assertRaises(ValueError,load_tail,p)
        finally:td.cleanup()

    def test_14_corrupt_text_payload_rejected(self):
        def mutate(src):src['text_blocks'][1][1]^=0x2
        td,p=self.scratch(mutate)
        try:self.assertRaises(ValueError,load_tail,p)
        finally:td.cleanup()

    def test_15_corrupt_pad_rejected(self):
        def mutate(src):src['padding_length']=44
        td,p=self.scratch(mutate)
        try:self.assertRaises(ValueError,load_tail,p)
        finally:td.cleanup()

    def test_16_corrupt_z80_mnemonic_rejected(self):
        def mutate(s):
            self.assertIn('    xor a',s)
            return s.replace('    xor a','    or a',1)
        td,p=self.scratch(change_asm=mutate)
        try:self.assertRaises(ValueError,load_tail,p)
        finally:td.cleanup()

    def test_17_bad_mixed_z80_opcode_rejected(self):
        text=mixed_source(ROOT)
        self.assertIn('    outi',text)
        text=text.replace('    outi','    ret',1)
        self.assertRaises(ValueError,assemble_mixed,text)

    def test_18_bad_rom_fingerprint_rejected(self):
        altered=bytearray(self.rom)
        altered[0x20000]^=1
        self.assertRaises(ValueError,build,bytes(altered))

if __name__=='__main__':unittest.main(verbosity=2)
