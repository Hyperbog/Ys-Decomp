#!/usr/bin/env python3
"""M7 bank4 source closure, runtime-bounded predicate, and corruption regressions."""
import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from unittest import TestCase,main,mock
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
import whole_bank04 as wb
from whole_bank07 import assemble_mixed
from build_system_m7 import build,complete_banks,BANKS,SOURCED
from build_sms_phase14 import EXPECTED_SHA
from bank04_collision_trace import trace,CollisionMachine,collision_reference
from bank04_crossbank_ledger import build as static_links
from wla_system_m7 import prepare,verify
ROM=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else None
if ROM:sys.argv=sys.argv[:1]

class Bank04Tests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank=wb.full_bank()
        cls.src=json.loads((ROOT/wb.SOURCE).read_text())
        cls.rom=ROM.read_bytes() if ROM else None
    def mutate(self,callback):
        altered=copy.deepcopy(self.src);callback(altered)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'source.json';p.write_text(json.dumps(altered))
            with mock.patch.object(wb,'SOURCE',p):
                with self.assertRaises((ValueError,KeyError,TypeError)):wb.new_chunks()
    def test_01_bank_length_hash(self):
        self.assertEqual(len(self.bank),16384)
        self.assertEqual(hashlib.sha256(self.bank).hexdigest(),'bd2e9c90792a9f462a3f8ff42763c676ffc9568d9913227e3460c592beb42354')
    def test_02_exact_source_ownership(self):
        known=wb.existing();other,inventory=wb.new_chunks()
        self.assertEqual([len(known),len(other)],[162,16222])
        self.assertEqual(set(known)|set(other),set(range(0x8000,0xC000)))
        self.assertFalse(set(known)&set(other))
        self.assertEqual(sum(row['bytes'] for row in inventory),16222)
    def test_03_committed_mixed_asm_rebuild(self):
        s=wb.mixed_source()
        self.assertEqual(s,(ROOT/wb.ASM).read_text())
        self.assertEqual(assemble_mixed(s),self.bank)
        self.assertIn('add a,(ix+17)',s)
    def test_04_31_collision_descriptors(self):
        self.assertEqual(len(self.bank[:124]),31*4)
        self.assertEqual(self.bank[:4],bytes([0,0,0,0]))
    def test_05_potential_32byte_groups_not_decoded(self):
        self.assertEqual(len(self.src['candidate_32byte_groups']),502)
        self.assertEqual(502*32,16064)
        self.assertIn('does not establish',self.src['provenance'])
    def test_06_trailer_padding(self):
        self.assertEqual(len(self.src['undecoded_trailer']),86)
        self.assertEqual(self.bank[-72:],b'\xff'*72)
    def test_07_seven_complete_banks(self):
        banks=complete_banks()
        self.assertEqual(sorted(banks),BANKS)
        self.assertEqual(sum(map(len,banks.values())),7*16384)
    def test_08_rom_exact_match(self):
        if self.rom is None:self.skipTest('owner ROM absent')
        self.assertEqual(hashlib.sha256(self.rom).hexdigest(),EXPECTED_SHA)
        self.assertEqual(self.bank,self.rom[0x10000:0x14000])
    def test_09_full_256k_build(self):
        if self.rom is None:self.skipTest('owner ROM absent')
        out,report=build(self.rom)
        self.assertEqual(out,self.rom)
        self.assertEqual(report['source_backed_bytes'],SOURCED)
        self.assertEqual(SOURCED,115009)
        self.assertEqual(report['original_rom_fallback_bytes'],147135)
        self.assertEqual(report['source_only_complete_banks'],BANKS)
    def test_10_collision_execution_all_cases(self):
        if self.rom is None:self.skipTest('owner ROM absent')
        r=trace(self.rom)
        self.assertEqual(r,json.loads((ROOT/'wholebank04/collision_report.json').read_text()))
        self.assertEqual(r['case_count'],3968)
        self.assertGreater(r['collision_positive_cases'],0)
        self.assertGreater(r['collision_negative_cases'],0)
    def test_11_collision_zero_record_returns_no_carry(self):
        rom=self.rom
        if rom is None:self.skipTest('owner ROM absent')
        for y in (0,64,255):
            machine=CollisionMachine(rom,0,y,255,0,10,0,10)
            self.assertFalse(machine.run())
            self.assertEqual(machine.exit_pc,0x8086)
    def test_12_model_direct_boundary(self):
        self.assertFalse(collision_reference(bytes([0,0,0,0]),0,0,0,0,0,0))
        self.assertTrue(collision_reference(bytes([0xF9,13,0xF1,13]),20,20,20,10,20,10))
    def test_13_crossbank_caller_ledger(self):
        r=static_links()
        self.assertEqual(r,json.loads((ROOT/'wholebank04/crossbank_links.json').read_text()))
        self.assertEqual([x['from_cpu'] for x in r['call_references']],['47C2','486C','48DF'])
        self.assertFalse(r['mapper_proven_at_calls'])
    def test_14_wrong_group_count(self):
        self.mutate(lambda s:s['candidate_32byte_groups'].pop())
    def test_15_wrong_row_count(self):
        self.mutate(lambda s:s['candidate_32byte_groups'][0].pop())
    def test_16_wrong_lane_count(self):
        self.mutate(lambda s:s['candidate_32byte_groups'][0][0].pop())
    def test_17_modified_graphics_group(self):
        self.mutate(lambda s:s['candidate_32byte_groups'][0][0].__setitem__(0,s['candidate_32byte_groups'][0][0][0]^1))
    def test_18_modified_unresolved_trailer(self):
        self.mutate(lambda s:s['undecoded_trailer'].__setitem__(0,s['undecoded_trailer'][0]^1))
    def test_19_modified_ff_fill(self):
        self.mutate(lambda s:s['ff_padding'].__setitem__('count',71))
    def test_20_invalid_source_schema(self):
        self.mutate(lambda s:s.__setitem__('schema','invalid'))
    def test_21_illegal_group_value(self):
        self.mutate(lambda s:s['candidate_32byte_groups'][0][0].__setitem__(0,256))
    def test_22_wrong_rom_refused(self):
        if self.rom is None:self.skipTest('owner ROM absent')
        bad=bytearray(self.rom);bad[0x100A2]^=1
        with self.assertRaises(ValueError):build(bytes(bad))
    def test_23_capture_wrong_rom_rejected(self):
        with self.assertRaises(ValueError):wb.capture(b'\0'*0x40000)
    def test_24_collision_unknown_opcode_rejected(self):
        if self.rom is None:self.skipTest('owner ROM absent')
        wrong=bytearray(self.rom);wrong[0x1007C]=0xFF
        with self.assertRaises(ValueError):CollisionMachine(bytes(wrong),3,20,20,20,20,20,20).run()
    def test_25_wla_fixture_prepared_and_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            r=prepare(d)
            self.assertEqual(r['banks'],BANKS)
            self.assertFalse(r['external_assembler_verified'])
            self.assertIn('.BANK 4 SLOT 2',(Path(d)/'bank04.asm').read_text())
            with self.assertRaises(FileNotFoundError):verify(d,'absent-wla-asm','absent-wla-link')
    def test_26_wrong_digest_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            m=json.loads((ROOT/wb.DIGEST).read_text());m['bank_sha256']='0'*64
            p=Path(d)/'dig.json';p.write_text(json.dumps(m))
            with mock.patch.object(wb,'DIGEST',p):
                with self.assertRaises(ValueError):wb.full_bank()
    def test_27_mnemonics_reproducible(self):
        self.assertEqual(self.bank[0x7C:0xA2],bytes.fromhex('87876f26807e2cdd8611d0b92807d0863812b8380f2c7edd8610d0bb2806d02c863801ba3fc9'))
    def test_28_mutated_crossbank_caller_rejected(self):
        from bank04_crossbank_ledger import build as links
        import bank04_crossbank_ledger as x
        caller=bytearray(x.bank01())
        caller[0x47C2-0x4000]=0x00
        with mock.patch.object(x,'bank01',return_value=bytes(caller)):
            with self.assertRaises(ValueError):links()

if __name__=='__main__':main(verbosity=2)
