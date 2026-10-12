#!/usr/bin/env python3
"""M9 whole-bank boundary, code, source isolation and mutation regression tests."""
import copy,hashlib,json,shutil,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
from build_sms_phase14 import EXPECTED_SHA
from whole_banks09_11_12 import (BANKS as NEWBANKS,source_path,hash_path,asm_path,CODE9,
  full_bank,old_code,extra_code,load_new,mixed_source,assemble_mixed)
from build_system_m9 import complete_banks,build,BANKS,NEW,SOURCED
ROM=None

class SourceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rom=ROM.read_bytes()
  assert hashlib.sha256(cls.rom).hexdigest()==EXPECTED_SHA
  cls.images={n:cls.rom[n*16384:(n+1)*16384] for n in NEWBANKS}
 def test_01_rom_free_banks(self):
  for n in NEWBANKS:self.assertEqual(full_bank(n),self.images[n])
 def test_02_assembled_sources(self):
  for n in NEWBANKS:self.assertEqual(assemble_mixed((ROOT/asm_path(n)).read_text()),self.images[n])
 def test_03_mixed_source_unchanged(self):
  for n in NEWBANKS:self.assertEqual(mixed_source(n),(ROOT/asm_path(n)).read_text())
 def test_04_mnemonic_ownership(self):
  self.assertEqual(len(extra_code()[0]),CODE9[1]-CODE9[0]);self.assertEqual(len(old_code(12)),108)
  self.assertEqual(len(old_code(9)),0);self.assertEqual(len(old_code(11)),0)
 def test_05_new_ownership_ledger(self):
  for n in NEWBANKS:
   data,rows=load_new(n)
   self.assertEqual(sum(r['bytes'] for r in rows),len(data))
   self.assertEqual(len(data),{9:16319,11:16384,12:16276}[n])
 def test_06_glyph_table_and_index(self):
  d=json.loads((ROOT/source_path(9)).read_text())['six_byte_glyph_table'];seq=d['records'];p=d['pointers']
  self.assertEqual(len(seq),8);self.assertEqual([len(r) for r in seq],[6]*8)
  self.assertEqual(p,[0xBF52,0xBF5E,0xBF58,0xBF64,0xBF6A,0xBF70,0xBF76,0xBF4C])
  raw=self.images[9]
  for i,addr in enumerate(p):
   self.assertEqual(bytes(seq[(addr-0xBF4C)//6]),raw[addr-0x8000:addr-0x8000+6])
 def test_07_vdp_opcode_and_6_output_bytes(self):
  b=self.images[9];a=CODE9[0]-0x8000;z=CODE9[1]-0x8000
  code=b[a:z]
  self.assertIn(bytes.fromhex('06 06 0e be ed a3'),code)
  self.assertIn(bytes.fromhex('ed 79'),code)
  self.assertEqual(code[-1],0xc9)
 def test_08_curve_candidate_shape(self):
  d=json.loads((ROOT/source_path(12)).read_text())
  self.assertEqual(len(d['candidate_wave_samples_128']),128)
  self.assertEqual(bytes(d['candidate_wave_samples_128']),self.images[12][:128])
 def test_09_full_twelve_bank_standalone(self):
  banks=complete_banks();self.assertEqual(sorted(banks),BANKS)
  for n in BANKS:self.assertEqual(banks[n],self.rom[n*16384:(n+1)*16384])
 def test_10_whole_cartridge(self):
  result,report=build(self.rom)
  self.assertEqual(result,self.rom);self.assertEqual(report['source_backed_bytes'],SOURCED)
  self.assertEqual(report['new_source_backed_bytes'],NEW)
  self.assertEqual(report['original_rom_fallback_bytes'],65536)
 def test_11_report_snapshot(self):
  self.assertEqual(build(self.rom)[1],json.loads((ROOT/'whole_system/build_report_m9.json').read_text()))
 def test_12_rom_fingerprint_negative(self):
  b=bytearray(self.rom);b[0x2f000]^=1
  with self.assertRaises(ValueError):build(bytes(b))
 def test_13_unknown_bank_refuses(self):
  with self.assertRaises(ValueError):full_bank(13)
 def test_14_wla_no_tools_fails_closed(self):
  from wla_system_m9 import verify
  with patch('shutil.which',return_value=None):
   with self.assertRaises(FileNotFoundError):verify('/tmp/no-tools-for-m9')

class BoundedGlyphTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rom=ROM.read_bytes()
 def test_28_trace_snapshot(self):
  from bank09_glyph_trace import trace
  got=trace(self.rom)
  self.assertEqual(got,json.loads((ROOT/'wholebank09/glyph_trace.json').read_text()))
  self.assertEqual(got['cases'],24);self.assertEqual(got['bytes_written'],288)
 def test_29_output_matches_independent_records(self):
  from bank09_glyph_trace import execute
  for i in range(8):
   for value in (0,0x2E,0xA7):
    self.assertEqual(execute(self.rom,i,value)['output_bytes'],12)
 def test_30_bad_opcode_rejected(self):
  from bank09_glyph_trace import execute
  raw=bytearray(self.rom);raw[9*0x4000+0xBF30-0x8000]=0x76
  with self.assertRaises((ValueError,RuntimeError)):
   execute(bytes(raw),0,0)
 def test_31_bad_index_rejected(self):
  from bank09_glyph_trace import execute
  with self.assertRaises(ValueError):execute(self.rom,8,0)
 def test_32_bad_separator_rejected(self):
  from bank09_glyph_trace import execute
  with self.assertRaises(ValueError):execute(self.rom,0,256)

class SourceMutations(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  for n in NEWBANKS:
   for p in (source_path(n),hash_path(n),asm_path(n)):
    (self.root/p).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,self.root/p)
  for p in ('src/wholebank09/extra_code.asm','src/phase11_roundtrip/bank12.asm'):
   q=self.root/p;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,q)
 def tearDown(self):self.tmp.cleanup()
 def change(self,n,modify):
  p=self.root/source_path(n);d=json.loads(p.read_text());modify(d);p.write_text(json.dumps(d))
  with self.assertRaises((ValueError,KeyError,TypeError)):full_bank(n,self.root)
 def test_15_bank09_opaque_mutation(self):
  self.change(9,lambda d:d['unresolved_language_stream'][0].__setitem__('hex','ff'+d['unresolved_language_stream'][0]['hex'][2:]))
 def test_16_bank09_chunk_gap(self):
  self.change(9,lambda d:d['unresolved_language_stream'][1].__setitem__('start',d['unresolved_language_stream'][1]['start']+1))
 def test_17_glyph_record_changed(self):
  self.change(9,lambda d:d['six_byte_glyph_table']['records'][2].__setitem__(0,0))
 def test_18_glyph_record_size(self):
  self.change(9,lambda d:d['six_byte_glyph_table']['records'][5].pop())
 def test_19_glyph_index_changed(self):
  self.change(9,lambda d:d['six_byte_glyph_table']['pointers'].__setitem__(0,0xBF58))
 def test_20_glyph_code_changed(self):
  p=self.root/'src/wholebank09/extra_code.asm';s=p.read_text()
  assert 'ld b,$06' in s
  p.write_text(s.replace('ld b,$06','ld b,$07',1))
  with self.assertRaises(ValueError):full_bank(9,self.root)
 def test_21_bank11_stream_mutation(self):
  self.change(11,lambda d:d['unresolved_resource_stream'][5].__setitem__('hex','ee'+d['unresolved_resource_stream'][5]['hex'][2:]))
 def test_22_bank11_filler(self):
  self.change(11,lambda d:d['ff_padding'].__setitem__('value',0))
 def test_23_bank12_curve(self):
  self.change(12,lambda d:d['candidate_wave_samples_128'].__setitem__(1,255))
 def test_24_bank12_payload_gap(self):
  self.change(12,lambda d:d['undecoded_before_code'][1].__setitem__('start',0x8100+1))
 def test_25_bank12_code_mutation(self):
  p=self.root/'src/phase11_roundtrip/bank12.asm';s=p.read_text();a=s.find('ld ')
  self.assertGreaterEqual(a,0)
  # Any instruction source drift is forbidden, regardless of semantic interpretation.
  p.write_text(s.replace('    ld c,$00','    ld c,$01',1))
  with self.assertRaises(ValueError):full_bank(12,self.root)
 def test_26_wrong_digest(self):
  p=self.root/hash_path(11);d=json.loads(p.read_text());d['new_data_sha256']='0'*64;p.write_text(json.dumps(d))
  with self.assertRaises(ValueError):full_bank(11,self.root)
 def test_27_bank09_wrong_filler(self):
  self.change(9,lambda d:d['ff_padding'].__setitem__('start',0xBFE5))

if __name__=='__main__':
 if len(sys.argv)!=2:raise SystemExit('Usage: tests_whole_banks09_11_12.py original.sms')
 ROM=Path(sys.argv.pop(1));unittest.main(verbosity=1)
