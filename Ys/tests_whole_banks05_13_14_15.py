#!/usr/bin/env python3
"""M10: source independence, data ownership, integrity, and ROM-match tests."""
import json,sys,tempfile,unittest,hashlib,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'tools'))
from build_sms_phase14 import ROOT,EXPECTED_SHA
from whole_banks05_13_14_15 import (BANKS,SIZE,END,START,POINTER_START,POINTER_END,
 FILL_START,source_file,digest_file,asm_file,source_parts,full_bank,mixed_source,split_chunks,unpack_chunks,capture)
from whole_bank07 import assemble_mixed
from build_system_m10 import build,complete_banks

def sha(x):return hashlib.sha256(x).hexdigest()
class ReconstructTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.image,cls.report=build()
  cls.banks={n:full_bank(n) for n in BANKS}
  cls.root=ROOT

 def test_01_full_rom_size_sha(self):self.assertEqual((len(self.image),sha(self.image)),(262144,EXPECTED_SHA))
 def test_02_all_sixteen_banks_complete(self):self.assertEqual(self.report["source_only_complete_banks"],list(range(16)))
 def test_03_zero_fallback(self):self.assertEqual((self.report['source_backed_bytes'],self.report['original_rom_fallback_bytes']),(262144,0))
 def test_04_report_binary_reconstruction_not_semantics(self):
  self.assertTrue(self.report['source_only_complete_rom']);self.assertFalse(self.report['all_game_assets_semantically_decoded'])
 def test_05_not_external_assembler_verified(self):self.assertFalse(self.report['external_wla_dx_verified'])
 def test_06_not_full_emulator_verified(self):self.assertFalse(self.report['full_emulator_verified'])
 def test_07_all_final_banks_sha(self):
  for n in BANKS:
   with self.subTest(bank=n):self.assertEqual(self.banks[n],self.image[n*SIZE:(n+1)*SIZE])
 def test_08_final_four_have_exact_ownership(self):
  for n in BANKS:
   with self.subTest(bank=n):
    _,parts=source_parts(n)
    self.assertEqual(sum(x['bytes'] for x in parts),SIZE)
    self.assertEqual(parts[0]['start'],START);self.assertEqual(parts[-1]['end_exclusive'],END)
    self.assertEqual([p['end_exclusive'] for p in parts[:-1]],[p['start'] for p in parts[1:]])
 def test_09_pointer_directory_has_50_valid_targets(self):
  ptrs=json.loads((ROOT/source_file(13)).read_text())['indexed_resource_directory']['pointers']
  self.assertEqual((len(ptrs),len(set(ptrs)),ptrs[0],ptrs[-1]),(50,50,0x8000,0xA7FB))
  self.assertEqual(self.banks[13][POINTER_START-START:POINTER_END-START],b''.join(x.to_bytes(2,'little') for x in ptrs))
 def test_10_pointer_targets_inside_source_owned_body(self):
  pts=json.loads((ROOT/source_file(13)).read_text())['indexed_resource_directory']['pointers']
  self.assertTrue(all(START<=p<POINTER_START for p in pts))
 def test_11_explicit_fill_boundaries(self):
  for n in BANKS:
   with self.subTest(bank=n):
    p=FILL_START[n];self.assertEqual(self.banks[n][p-START:],bytes([255])*(END-p))
 def test_12_precise_final_four_classification(self):
  self.assertEqual((self.report['final_four_unresolved_resource_bytes'],self.report['final_four_structured_pointer_bytes'],self.report['final_four_explicit_fill_bytes']),(64439,100,997))
 def test_13_mixed_source_round_trip(self):
  for n in BANKS:
   with self.subTest(bank=n):
    self.assertEqual(assemble_mixed(mixed_source(n)),self.banks[n])
 def test_14_checked_in_assembly_round_trip(self):
  for n in BANKS:
   with self.subTest(bank=n):
    src=(ROOT/asm_file(n)).read_text()
    self.assertEqual(src,mixed_source(n))
    self.assertEqual(assemble_mixed(src),self.banks[n])
 def test_15_no_rom_argument_needed(self):self.assertEqual(len(self.image),262144) # setUpClass build() has no ROM argument
 def test_16_invalid_bank_rejected(self):
  with self.assertRaises(ValueError):full_bank(1)
 def test_17_invalid_rom_capture_rejected(self):
  with self.assertRaises(ValueError):capture(b'\x00'*262144)
 def test_18_chunk_gap_rejected(self):
  with self.assertRaises(ValueError):unpack_chunks([{'start':START+1,'hex':'ff'}],START,START+1)
 def test_19_chunk_overlong_rejected(self):
  with self.assertRaises(ValueError):unpack_chunks([{'start':START,'hex':'aa'*257}],START,START+257)
 def test_20_chunk_round_trip(self):
  data=bytes(i%256 for i in range(801));self.assertEqual(unpack_chunks(split_chunks(data,START),START,START+len(data)),data)
 def _mutate(self,n,fn):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);s=root/source_file(n);s.parent.mkdir(parents=True,exist_ok=True)
   dg=root/digest_file(n);dg.write_text((ROOT/digest_file(n)).read_text())
   obj=json.loads((ROOT/source_file(n)).read_text());fn(obj)
   s.write_text(json.dumps(obj))
   with self.assertRaises(ValueError):source_parts(n,root)
 def test_21_changed_asset_byte_rejected(self):
  self._mutate(5,lambda o:o['unresolved_asset_chunks'][0].__setitem__('hex','01'+o['unresolved_asset_chunks'][0]['hex'][2:]))
 def test_22_changed_directory_pointer_rejected(self):
  self._mutate(13,lambda o:o['indexed_resource_directory']['pointers'].__setitem__(0,0xC000))
 def test_23_duplicate_pointer_rejected(self):
  self._mutate(13,lambda o:o['indexed_resource_directory']['pointers'].__setitem__(1,0x8000))
 def test_24_invalid_fill_length_rejected(self):
  self._mutate(14,lambda o:o['end_fill'].__setitem__('count',0))
 def test_25_corrupt_chunk_boundary_rejected(self):
  self._mutate(15,lambda o:o['unresolved_asset_chunks'][1].__setitem__('start',0xDEAD))
 def test_26_invalid_source_schema_rejected(self):
  self._mutate(5,lambda o:o.__setitem__('schema','invalid'))
 def test_27_corrupt_last_byte_rejected(self):
  self._mutate(15,lambda o:o['end_fill'].__setitem__('byte',0))
 def test_28_report_all_banks_have_sha(self):
  self.assertEqual(len(set(r['sha256'] for r in self.report['per_bank'])),16)
 def test_29_no_new_instructions_claimed(self):self.assertEqual(self.report['newly_recovered_mnemonic_bytes'],0)

if __name__=='__main__':
 args=sys.argv[1:];sys.argv=[sys.argv[0]]
 if args:
  if len(args)!=1:raise SystemExit('Usage: tests_whole_banks05_13_14_15.py [optional_rom]')
  owner=Path(args[0]).read_bytes()
  if (len(owner),sha(owner))!=(262144,EXPECTED_SHA):raise SystemExit('Wrong owner ROM')
  assert build()[0]==owner
 unittest.main(verbosity=2)
