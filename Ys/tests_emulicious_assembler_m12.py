#!/usr/bin/env python3
"""Fail-closed checks for independent third-party Z80 opcode matching."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
import verify_emulicious_assembler_m12 as m
from z80_roundtrip_phase10 import encode


class IndependentAssemblyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((ROOT/'whole_system/emulicious_assembler_report_m12.json').read_text())
        cls.instructions=m.enumerate_instructions()

    def test_report_signature(self):
        self.assertEqual(self.report['schema'],'ys-external-emulicious-z80-assembler-m12-v1')
        self.assertEqual(self.report['assembler'],'Emulicious built-in Z80Assembler')
        self.assertEqual(self.report['source_cartridge_sha256'],m.EXPECTED)

    def test_report_matched_every_submitted_instruction(self):
        self.assertEqual(self.report['instructions_submitted'],11009)
        self.assertEqual(self.report['instruction_bytes_examined'],22552)
        self.assertEqual(self.report['externally_matched_instruction_bytes'],22552)
        self.assertEqual(self.report['unsupported_instruction_count'],0)
        self.assertEqual(self.report['mismatching_instruction_count'],0)

    def test_external_link_not_claimed(self):
        self.assertFalse(self.report['independent_full_cartridge_link_passed'])
        self.assertFalse(self.report['independent_wla_dx_passed'])

    def test_all_sixteen_banks_owned(self):
        self.assertEqual(set(b for _,_,_,b,_ in self.instructions),{0,1,2,4,6,7,8,9,10,12})
        self.assertTrue(self.report['all_16_banks_source_only'])
        self.assertEqual(len(self.instructions),11009)
        self.assertEqual(sum(len(encode(s,pc)) for _,pc,s,_,_ in self.instructions),22552)

    def test_physical_address_boundaries(self):
        seen=set()
        for offset,pc,s,bank,_ in self.instructions:
            size=len(encode(s,pc))
            self.assertGreaterEqual(offset,bank*0x4000)
            self.assertLessEqual(offset+size,(bank+1)*0x4000)
            self.assertTrue(all(i not in seen for i in range(offset,offset+size)))
            seen.update(range(offset,offset+size))

    def test_bank1_uses_correct_cpu_window(self):
        bank1=[r for r in self.instructions if r[3]==1]
        self.assertEqual(bank1[0][0],0x4000)
        self.assertEqual(bank1[0][1],0x4000)
        self.assertTrue(all(0x4000<=pc<0x8000 for _,pc,_,_,_ in bank1))

    def test_bank7_uses_correct_cpu_window(self):
        bank7=[r for r in self.instructions if r[3]==7]
        self.assertTrue(all(0x8000<=pc<0xC000 for _,pc,_,_,_ in bank7))
        self.assertTrue(any(s.lower()=='outi' for _,_,s,_,_ in bank7))

    def test_modified_external_bytes_detected(self):
        source=[(0x1C180,0x8180,'outi',7,1)]
        reference=bytearray(0x40000)
        reference[0x1C180:0x1C182]=b'\xED\xA3'
        matched,mismatch,unsupported,examined=m.audit_responses(source,['8180\tED44'],reference)
        self.assertEqual(matched,0)
        self.assertEqual(len(mismatch),1)
        self.assertEqual(examined,2)
        self.assertFalse(unsupported)

    def test_correct_external_bytes_accepted(self):
        source=[(0x1C180,0x8180,'outi',7,1)]
        reference=bytearray(0x40000)
        reference[0x1C180:0x1C182]=b'\xED\xA3'
        self.assertEqual(m.audit_responses(source,['8180\tEDA3'],reference), (2,[],[],2))

    def test_unsupported_not_reported_as_matched(self):
        source=[(0,0,'di',0,1)]
        matched,mismatch,unsupported,examined=m.audit_responses(source,['0000\tERROR:ParseException:bad'],bytes(4))
        self.assertEqual(matched,0)
        self.assertFalse(mismatch)
        self.assertEqual(len(unsupported),1)
        self.assertEqual(examined,1)

    def test_missing_or_duplicate_reply_rejected(self):
        source=[(0,0,'di',0,1)]
        with self.assertRaises(AssertionError):m.audit_responses(source,[],bytes(4))
        with self.assertRaises(AssertionError):m.audit_responses(source,['0001\tF3'],bytes(4))

    def test_invalid_external_hex_rejected(self):
        with self.assertRaises(AssertionError):
            m.audit_responses([(0,0,'di',0,1)],['0000\tZZ'],bytes(4))

    def test_missing_emulator_jar_rejected(self):
        with self.assertRaises(FileNotFoundError):m.run(Path('/tmp/unavailable-emulicious-m12.jar'))

    def test_corrupted_source_origin_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            dst=Path(tmp)
            for n in range(16):
                directory=dst/'src'/f'wholebank{n:02}'
                directory.mkdir(parents=True)
                name=f'bank{n:02}_complete.asm'
                src=ROOT/'src'/f'wholebank{n:02}'/name
                if n==1:
                    directory.joinpath(name).write_text(src.read_text().replace('org $4000','org $8000',1))
                else:
                    directory.joinpath(name).symlink_to(src)
            with self.assertRaisesRegex(ValueError,'crosses bank boundary'):
                m.enumerate_instructions(dst)

    def test_jvm_bridge_source_is_committed(self):
        self.assertIn('assembler.Z80Assembler',m.JAVA_SOURCE.read_text())
        self.assertIn('relative branch out of range',m.JAVA_SOURCE.read_text())


if __name__=='__main__':unittest.main(verbosity=2)
