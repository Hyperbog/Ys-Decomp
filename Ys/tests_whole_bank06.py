#!/usr/bin/env python3
"""Standalone sprite-bank closure tests, including fail-closed corruption cases."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
from whole_bank06 import (full_bank,new_chunks,known_bytes,mixed_source,parse_layouts,
                         parse_pointer_directory,expand_lanes,LAYOUT_A,LAYOUT_B,DATA,DIGEST,
                         SIZE,CPU,PIXEL)
from whole_bank07 import assemble_mixed
from build_system_m4 import complete_banks,build, SOURCE_BYTES, EXPECTED_COMPLETE
from build_sms_phase14 import EXPECTED_SHA

ROM=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else None
if ROM:sys.argv=sys.argv[:1]

class Bank06Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=full_bank(ROOT)
        cls.data=json.loads((ROOT/DATA).read_text())
        cls.orig_rom=ROM.read_bytes() if ROM else None

    def file_meta(self,modified):
        tmp=tempfile.TemporaryDirectory()
        root=Path(tmp.name)
        (root/'wholebank06').mkdir()
        (root/DATA).write_text(json.dumps(modified))
        (root/DIGEST).write_bytes((ROOT/DIGEST).read_bytes())
        return tmp,root

    def assert_rejected(self,mutate):
        obj=copy.deepcopy(self.data);mutate(obj)
        tmp,root=self.file_meta(obj)
        try:
            with self.assertRaises(ValueError):new_chunks(root)
        finally:tmp.cleanup()

    def test_01_exact_bank_sha(self):
        self.assertEqual(len(self.raw),16384)
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(),
          'cd64e2820b24ee57c2d909b9edf871246d37fc5e9e6dc889c0d58116a92524eb')

    def test_02_source_ownership_complete(self):
        old=known_bytes(ROOT);tail,owners=new_chunks(ROOT)
        self.assertEqual(len(old),7192)
        self.assertEqual(len(tail),9192)
        self.assertFalse(set(old)&set(tail))
        self.assertEqual({*old,*tail},set(range(0x8000,0xC000)))
        self.assertEqual(sum(v['bytes'] for v in owners),9192)

    def test_03_mixed_listing_full_byte_match(self):
        compiled=assemble_mixed(mixed_source(ROOT))
        self.assertEqual(compiled,self.raw)
        self.assertEqual(mixed_source(ROOT),(ROOT/'src/wholebank06/bank06_complete.asm').read_text())

    def test_04_layout_counts_and_boundaries(self):
        chunks,_=new_chunks(ROOT)
        for bounds in LAYOUT_A+LAYOUT_B:
            a,z=bounds
            self.assertEqual(z-a,1+3*chunks[a])
        count=sum(chunks[a] for a,z in LAYOUT_A+LAYOUT_B)
        self.assertEqual(count,78)

    def test_05_both_pointer_dirs_and_alias(self):
        self.assertEqual(self.data['layout_directory_a'],[0xB9D0,0xB9F8,0xBA23,0xB9F8])
        self.assertEqual(self.data['layout_directory_b'],[0xBA63,0xBA7C,0xBA9B,0xBABA])
        self.assertEqual(self.data['layout_directory_a'][1],self.data['layout_directory_a'][3])

    def test_06_visual_graphics_uninterpreted(self):
        self.assertEqual(len(self.data['graphics_byte_lanes_8']),926)
        self.assertEqual(PIXEL[1]-PIXEL[0],7408)

    def test_07_rom_input_compare(self):
        if self.orig_rom is None:self.skipTest('No original ROM supplied')
        self.assertEqual(hashlib.sha256(self.orig_rom).hexdigest(),EXPECTED_SHA)
        self.assertEqual(self.orig_rom[6*SIZE:7*SIZE],self.raw)

    def test_08_four_source_only_banks(self):
        assembled=complete_banks(ROOT)
        self.assertEqual(sorted(assembled),EXPECTED_COMPLETE)
        self.assertEqual(sum(map(len,assembled.values())),65536)

    def test_09_full_rom_overlay(self):
        if self.orig_rom is None:self.skipTest('No original ROM supplied')
        result,report=build(self.orig_rom,ROOT)
        self.assertEqual(result,self.orig_rom)
        self.assertEqual(report['source_backed_bytes'],SOURCE_BYTES)
        self.assertEqual(report['source_only_complete_banks'],[0,3,6,7])
        self.assertEqual(report['original_rom_fallback_bytes'],191561)

    def test_10_bad_graphics_byte_rejected(self):
        self.assert_rejected(lambda a:a['graphics_byte_lanes_8'][0].__setitem__(0,(a['graphics_byte_lanes_8'][0][0]+1)%256))

    def test_11_graphics_lane_missing_rejected(self):
        self.assert_rejected(lambda a:a['graphics_byte_lanes_8'].pop())

    def test_12_modified_pointer_rejected(self):
        self.assert_rejected(lambda a:a['layout_directory_a'].__setitem__(0,0xB9D1))

    def test_13_directory_alias_rejected(self):
        self.assert_rejected(lambda a:a['layout_directory_a'].__setitem__(3,0xBA23))

    def test_14_invalid_layout_count_rejected(self):
        self.assert_rejected(lambda a:a['sprite_layouts_b'][1]['triplets'].pop())

    def test_15_changed_layout_field_rejected(self):
        self.assert_rejected(lambda a:a['sprite_layouts_a'][0]['triplets'][0].__setitem__(0,77))

    def test_16_layout_start_rejected(self):
        self.assert_rejected(lambda a:a['sprite_layouts_b'][0].__setitem__('start',0xBA64))

    def test_17_tile_id_mutation_rejected(self):
        self.assert_rejected(lambda a:a['tile_indices_after_layouts_8'][0].__setitem__(0,(a['tile_indices_after_layouts_8'][0][0]+1)%256))

    def test_18_padding_drift_rejected(self):
        self.assert_rejected(lambda a:a.__setitem__('ff_padding_count',6))

    def test_19_triple_field_out_of_range_rejected(self):
        self.assert_rejected(lambda a:a['sprite_layouts_a'][0]['triplets'][0].__setitem__(1,256))

    def test_20_crossed_boundary_rejected(self):
        self.assert_rejected(lambda a:a['sprite_layouts_b'][0]['triplets'].append([0,0,0]))

    def test_21_wrong_rom_rejected(self):
        if self.orig_rom is None:self.skipTest('No original ROM supplied')
        mutant=bytearray(self.orig_rom);mutant[0x18000]^=1
        with self.assertRaises(ValueError):build(bytes(mutant),ROOT)

    def test_22_source_driven_without_rom(self):
        self.assertEqual(full_bank(ROOT),self.raw)

if __name__=='__main__':unittest.main(verbosity=1)
