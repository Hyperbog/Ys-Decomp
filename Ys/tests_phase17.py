#!/usr/bin/env python3
"""Independent checks for Phase17 editable graphics sources and ROM overlay."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
from graphics_source_phase17 import capture, segments, load_verified, read_json, generated_sources
from build_phase17 import build
from mode4_tiles_phase8 import encode_tile

ROM_FILE=Path(sys.argv[1]).resolve() if len(sys.argv)>1 and not sys.argv[1].startswith('-') else None
if ROM_FILE:
    sys.argv.pop(1)

class Phase17Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not ROM_FILE:
            raise ValueError('Supply path to original Ys SMS ROM')
        cls.rom=ROM_FILE.read_bytes()
        cls.data=read_json(ROOT,'phase17/graphics.json')

    def test_original_fingerprint(self):
        self.assertEqual(len(self.rom),262144)
        self.assertEqual(hashlib.sha256(self.rom).hexdigest(),self.data['rom_sha256'])

    def test_graphics_sources_reproduce_capture(self):
        self.assertEqual(capture(self.rom),self.data)

    def test_exact_size_and_disjoint_segments(self):
        chunks=segments(self.data)
        self.assertEqual(sum(len(s[3]) for s in chunks),15688)
        self.assertEqual(sum(len(s[3]) for s in chunks if s[0]==3),5632)
        self.assertEqual(sum(len(s[3]) for s in chunks if s[0]==7),10056)

    def test_176_tile_decode_encode(self):
        self.assertEqual(len(self.data['bank3_mode4_tiles']),176)
        for i,tile in enumerate(self.data['bank3_mode4_tiles']):
            pixel=[int(p,16) for row in tile['rows'] for p in row]
            self.assertEqual(encode_tile(pixel),self.rom[0xC000+32*i:0xC000+32*(i+1)])

    def test_64_graphics_records_and_expansion(self):
        refs=read_json(ROOT,'phase13/graphics_directory.json')['graphics_records']
        self.assertEqual(len(refs),64)
        total=0
        for record,ref in zip(self.data['bank7_mono_graphics'],refs):
            src=bytes(int(row,2) for row in record['rows'])
            expanded=b''.join(bytes((byte,0,0,0)) for byte in src)
            self.assertEqual(len(expanded),ref['expanded_4bpp_bytes'])
            self.assertEqual(expanded[::4],src)
            self.assertEqual(expanded[1::4],bytes(len(src)))
            self.assertEqual(expanded[2::4],bytes(len(src)))
            self.assertEqual(expanded[3::4],bytes(len(src)))
            total+=len(expanded)
        self.assertEqual(total,40224)

    def test_generated_sources_equal_committed(self):
        verified=load_verified()
        self.assertEqual(sum(len(m['bytes']) for m in verified.values()),15688)
        self.assertEqual(len(verified[3]['bytes']),5632)
        self.assertEqual(len(verified[7]['bytes']),10056)

    def test_reject_pixel_corruption(self):
        wrong=copy.deepcopy(self.data)
        old=wrong['bank3_mode4_tiles'][0]['rows'][0]
        wrong['bank3_mode4_tiles'][0]['rows'][0]=('1' if old[0]!='1' else '0')+old[1:]
        with self.assertRaisesRegex(ValueError,'digest'):
            segments(wrong)

    def test_reject_graphics_corruption(self):
        wrong=copy.deepcopy(self.data)
        old=wrong['bank7_mono_graphics'][0]['rows'][0]
        wrong['bank7_mono_graphics'][0]['rows'][0]=('1' if old[0]=='0' else '0')+old[1:]
        with self.assertRaisesRegex(ValueError,'digest'):
            segments(wrong)

    def test_reject_duplicate_index(self):
        wrong=copy.deepcopy(self.data)
        wrong['bank7_mono_graphics'][1]['index']=0
        with self.assertRaisesRegex(ValueError,'indices'):
            segments(wrong)

    def test_reject_record_length(self):
        wrong=copy.deepcopy(self.data)
        wrong['bank7_mono_graphics'][0]['rows'].pop()
        with self.assertRaisesRegex(ValueError,'length'):
            segments(wrong)

    def test_reject_source_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)
            for rel in ('phase17/graphics.json','phase13/graphics_directory.json',
                        'phase8/tile_metadata.json','src/phase17/bank03_tiles.asm',
                        'src/phase17/bank07_graphics.asm'):
                p=target/rel;p.parent.mkdir(parents=True,exist_ok=True)
                p.write_bytes((ROOT/rel).read_bytes())
            file=target/'src/phase17/bank07_graphics.asm'
            file.write_text(file.read_text().replace('db $','db $FF, $',1))
            with self.assertRaisesRegex(ValueError,'source drift'):
                load_verified(target)

    def test_full_rom_build_and_accounting(self):
        made,report=build(self.rom)
        self.assertEqual(made,self.rom)
        self.assertEqual(report,read_json(ROOT,'phase17/build_report.json'))
        self.assertEqual(report['source_backed_bytes'],38293)
        self.assertEqual(report['fallback_bytes'],223851)
        self.assertEqual(sum(b['source_bytes'] for b in report['per_bank']),38293)

    def test_wrong_rom_rejected(self):
        bad=bytearray(self.rom);bad[0x1C877]^=1
        with self.assertRaisesRegex(ValueError,'ROM'):
            build(bytes(bad))

if __name__=='__main__':
    unittest.main(verbosity=1)
