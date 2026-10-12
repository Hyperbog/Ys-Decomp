#!/usr/bin/env python3
"""Phase21 ROM-independent source emission and full-template regression tests."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
from phase21_semantic_sources import assemble, extracted, load_verified, ROM_DIGEST
from build_phase21 import build, old_positions
from build_sms_phase14 import offset

ROM = Path(sys.argv.pop(1)).resolve() if len(sys.argv)>1 and not sys.argv[1].startswith('-') else None

class SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if ROM is None:raise ValueError('Supply original Ys ROM as positional argument')
        cls.rom=ROM.read_bytes()
        cls.source=json.loads((ROOT/'phase21/source.json').read_text())

    def test_01_manifest_identity(self):
        self.assertEqual(hashlib.sha256(self.rom).hexdigest(),ROM_DIGEST)

    def test_02_source_reproduces_byte_hash_without_rom(self):
        src,counts,digest=load_verified(ROOT)
        self.assertEqual(len(src),8056)
        self.assertEqual(counts,{'resource_records':207,'song_directory':110,
                                 'regular_descriptors':777,'variable_headers':357,'candidate_glyph_stream':6605})
        self.assertEqual(digest,'60ae3a49243e5b1830bd01166e548e52ac1072c1b12c67c7d4a3e80aaf8d553c')

    def test_03_source_matches_rom_at_all_offsets(self):
        source,_,_=load_verified(ROOT)
        for (bank,pc),byte in source.items():
            self.assertEqual(self.rom[offset(bank,pc)],byte)

    def test_04_source_ownership_disjoint(self):
        old=old_positions(ROOT)
        new={offset(bank,pc) for bank,pc in load_verified(ROOT)[0]}
        self.assertEqual(len(old),38293)
        self.assertFalse(old & new)
        self.assertEqual(len(new),8056)

    def test_05_exact_template_output(self):
        out,report=build(self.rom,ROOT)
        self.assertEqual(out,self.rom)
        self.assertEqual(report['source_backed_bytes'],46349)
        self.assertEqual(report['fallback_bytes'],215795)
        self.assertEqual(report['new_distinct_classification_bytes'],357)
        self.assertFalse(report['source_only_rom'])

    def test_06_report_drift(self):
        _,report=build(self.rom,ROOT)
        self.assertEqual(report,json.loads((ROOT/'phase21/build_report.json').read_text()))

    def test_07_music_variable_channels_and_ptrs(self):
        directory=self.source['bank2_song_directory'];variable=self.source['bank2_variable_descriptors']
        self.assertEqual(len(variable),24)
        self.assertEqual([p['address'] for p in variable],directory[31:])
        for r in variable:
            head_end=r['address']+1+9*len(r['channels'])
            for c in r['channels']:
                self.assertGreaterEqual(c['stream_pointer'],head_end)
                self.assertLess(c['stream_pointer'],r['next_address'])
        self.assertEqual(variable[-1]['next_address'],0xB6E8)
        self.assertEqual(self.rom[0xB6E7],0xFF)

    def test_08_variable_pointer_out_of_bounds_rejected(self):
        d=copy.deepcopy(self.source)
        d['bank2_variable_descriptors'][0]['channels'][0]['stream_pointer']=0x8000
        with self.assertRaisesRegex(ValueError,'stream points outside'):assemble(d)

    def test_09_regular_channel_count_rejected(self):
        d=copy.deepcopy(self.source)
        d['bank2_regular_descriptors'][0]['channels'].pop()
        with self.assertRaisesRegex(ValueError,'Misaligned regular'):assemble(d)

    def test_10_directory_tamper_rejected(self):
        d=copy.deepcopy(self.source)
        d['bank2_song_directory'][31]+=1
        with self.assertRaisesRegex(ValueError,'boundary|directory'):assemble(d)

    def test_11_glyph_slot_range_rejected(self):
        d=copy.deepcopy(self.source)
        tok=next(t for t in d['bank3_candidate_glyph_stream'] if t['op']=='glyph_slots_0_to_25')
        tok['slots'][0]=26
        with self.assertRaisesRegex(ValueError,'glyph slot'):assemble(d)

    def test_12_unknown_token_rejected(self):
        d=copy.deepcopy(self.source)
        d['bank3_candidate_glyph_stream'][0]['op']='decoded_english'
        with self.assertRaisesRegex(ValueError,'Unknown glyph-stream token'):assemble(d)

    def test_13_raw_token_rejects_reserved_byte(self):
        d=copy.deepcopy(self.source)
        tok=next(t for t in d['bank3_candidate_glyph_stream'] if t['op']=='unresolved')
        tok['bytes'][0]=0xE7
        with self.assertRaisesRegex(ValueError,'Opaque run'):assemble(d)

    def test_14_changed_source_rejected_by_digest(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'phase21').mkdir()
            d=copy.deepcopy(self.source)
            d['bank0_indexed_records'][0]['bytes'][0]^=1
            (root/'phase21/source.json').write_text(json.dumps(d))
            (root/'phase21/digests.json').write_bytes((ROOT/'phase21/digests.json').read_bytes())
            with self.assertRaisesRegex(ValueError,'source hash/metadata drift'):load_verified(root)

    def test_15_wrong_rom_rejected(self):
        mutated=bytearray(self.rom);mutated[0xDF40]^=1
        with self.assertRaisesRegex(ValueError,'Original ROM missing/wrong'):build(bytes(mutated),ROOT)

    def test_16_extraction_identity_gate(self):
        with self.assertRaisesRegex(ValueError,'Original ROM identity mismatch'):
            extracted(self.rom[:-1])

    def test_17_header_trailer_not_source_owned(self):
        source=load_verified(ROOT)[0]
        for entry in self.source['bank2_variable_descriptors']:
            cpu=entry['address']+1+9*len(entry['channels'])
            self.assertNotIn((2,cpu),source)

    def test_18_variable_headers_new_only(self):
        original=old_positions(ROOT)
        source=load_verified(ROOT)[0]
        headers={(bank,pc) for bank,pc in source if bank==2 and
            any(e['address']<=pc<e['address']+1+len(e['channels'])*9 for e in self.source['bank2_variable_descriptors'])}
        self.assertEqual(len(headers),357)
        self.assertTrue(all(offset(b,pc) not in original for b,pc in headers))

if __name__=='__main__':unittest.main(verbosity=1)
