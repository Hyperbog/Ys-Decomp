#!/usr/bin/env python3
"""Whole bank 3 ownership, pointer-bounded field emission, and negative tests."""
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
from whole_bank03 import (full_bank,known_bytes,tail_bytes,mixed_source,
                          BANK,BASE,SIZE,GFX,UNRESOLVED,DIRECTORY,TEXT_PREFIX,TEXT,PADDING,JSON,DIGEST)
from whole_bank07 import assemble_mixed
from build_sms_phase14 import EXPECTED_SHA
from build_whole_system import build
ROM=Path(sys.argv.pop(1)).resolve() if len(sys.argv)>1 and not sys.argv[1].startswith('-') else None

class Bank3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if ROM is None:raise ValueError('Original Ys ROM argument required for verification')
        cls.rom=ROM.read_bytes()
        cls.bank=full_bank(ROOT)
        cls.source=json.loads((ROOT/JSON).read_text())

    def modified(self,change):
        tmp=tempfile.TemporaryDirectory();p=Path(tmp.name)
        for f in (JSON,DIGEST):
            dest=p/f;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/f,dest)
        x=copy.deepcopy(self.source);change(x)
        (p/JSON).write_text(json.dumps(x))
        return tmp,p

    def test_01_original_rom_exact(self):
        self.assertEqual(hashlib.sha256(self.rom).hexdigest(),EXPECTED_SHA)
        self.assertEqual(self.bank,self.rom[BASE:BASE+SIZE])

    def test_02_source_only_bank_byte_ownership(self):
        early=known_bytes(ROOT);new=tail_bytes(ROOT)
        self.assertEqual(len(early),12237)
        self.assertEqual(len(new),4147)
        self.assertFalse(set(early)&set(new))
        self.assertEqual(set(early)|set(new),set(range(0x8000,0xC000)))

    def test_03_compressed_visual_unknown(self):
        self.assertEqual(len(bytes.fromhex(self.source['unresolved_visual_bytes_hex'])),1955)

    def test_04_60_text_directory_records(self):
        d=self.source['text_directory']
        self.assertEqual(len(d),60)
        self.assertEqual(DIRECTORY[1]-DIRECTORY[0],240)
        self.assertEqual(d[0]['pointer'],0x9E93)
        self.assertEqual(d[-1]['pointer'],0xB2D7)
        self.assertTrue(all(0x9E93<=r['pointer']<0xB8CD for r in d))
        self.assertEqual(len(self.source['candidate_text_prefix']),109)

    def test_05_verified_uniform_ff_padding(self):
        self.assertEqual(self.source['padding_length'],1843)
        self.assertEqual(self.bank[PADDING[0]-0x8000:],b'\xff'*1843)

    def test_06_whole_bank_mixed_source_roundtrip(self):
        source=mixed_source(ROOT)
        self.assertEqual(assemble_mixed(source),self.bank)
        self.assertEqual(source,(ROOT/'src/wholebank03/bank03_complete.asm').read_text())

    def test_07_mutated_visual_bytes_rejected(self):
        def mutate(d):d['unresolved_visual_bytes_hex']='00'+d['unresolved_visual_bytes_hex'][2:]
        t,p=self.modified(mutate)
        try:self.assertRaises(ValueError,tail_bytes,p)
        finally:t.cleanup()

    def test_08_bad_pointer_rejected(self):
        def mutate(d):d['text_directory'][12]['pointer']=0xC012
        t,p=self.modified(mutate)
        try:self.assertRaises(ValueError,tail_bytes,p)
        finally:t.cleanup()

    def test_09_changed_parameter_rejected(self):
        def mutate(d):d['text_directory'][12]['parameter0']^=1
        t,p=self.modified(mutate)
        try:self.assertRaises(ValueError,tail_bytes,p)
        finally:t.cleanup()

    def test_10_mutated_text_prefix_rejected(self):
        def mutate(d):d['candidate_text_prefix'][0]^=2
        t,p=self.modified(mutate)
        try:self.assertRaises(ValueError,tail_bytes,p)
        finally:t.cleanup()

    def test_11_truncated_padding_rejected(self):
        def mutate(d):d['padding_length']-=1
        t,p=self.modified(mutate)
        try:self.assertRaises(ValueError,tail_bytes,p)
        finally:t.cleanup()

    def test_12_entire_16bank_rom_output(self):
        out,report=build(self.rom)
        self.assertEqual(out,self.rom)
        self.assertEqual(report['complete_source_only_banks'],[3,7])
        self.assertEqual(report['per_bank'][3]['original_rom_fallback_bytes'],0)

    def test_13_wrong_rom_rejected(self):
        bad=bytearray(self.rom);bad[0xD600]^=0x01
        self.assertRaises(ValueError,build,bytes(bad))

if __name__=='__main__':unittest.main(verbosity=2)
