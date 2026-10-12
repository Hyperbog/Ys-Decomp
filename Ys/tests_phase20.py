#!/usr/bin/env python3
"""Regression tests for bounded bank-6 object-handler opcode execution."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
from phase20_object_execution import ObjectMachine, trace
from phase18_z80_trace import UnsupportedOpcode
from wla_z80_check import make_source, prepare, SOURCE, HEADER

if len(sys.argv)<2:
    raise SystemExit('Usage: python Ys/tests_phase20.py /path/to/Ys.sms')
ROM=Path(sys.argv[1]).read_bytes()
sys.argv=sys.argv[:1]

class Phase20Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=trace(ROM)
        cls.saved=json.loads((ROOT/'phase20/object_execution.json').read_text())

    def test_trace_matches_committed_report(self):
        self.assertEqual(self.report,self.saved)

    def test_all_records_and_three_origins(self):
        self.assertEqual(self.report['case_count'],192)
        self.assertEqual(len(self.report['cases']),192)
        self.assertEqual({tuple(x['origins']) for x in self.report['cases']},
                         {(0,0),(17,29),(240,250)})
        for origin in ((0,0),(17,29),(240,250)):
            subset=[x['record'] for x in self.report['cases'] if x['origins']==list(origin)]
            self.assertEqual(sorted(subset),list(range(64)))

    def test_unique_output_hashes_and_steps(self):
        self.assertTrue(all(x['steps']>200 for x in self.report['cases']))
        self.assertTrue(all(x['object_calls']==1 for x in self.report['cases']))
        self.assertEqual(len(self.report['concat_sha256']),64)
        self.assertEqual(self.report['sat_bytes_in_all_cases'],192*192)
        self.assertGreater(len({x['output_sha256'] for x in self.report['cases']}),64)

    def test_skip_branch_object_bit_flag(self):
        # BIT 1,(IX+1) set means $9AA9 must return immediately without sprites.
        m=ObjectMachine(ROM,0x9AA9,ram={0xC201:b'\x02',0xC028:bytes.fromhex('00 DD 40 DD')})
        m.slot[2]=6;m.ix=0xC200
        m.push(0xE000)
        m.run(0xE000)
        self.assertEqual(m.object_calls,1)
        self.assertEqual(m.steps,2)
        self.assertEqual(m.data_writes,[])
        self.assertEqual(m.read(0xC028),0)
        self.assertEqual(m.read(0xC02A),0x40)

    def test_rom_sha_rejects_mutation(self):
        bad=bytearray(ROM)
        bad[0x19AA9]^=1
        with self.assertRaisesRegex(ValueError,'fingerprint'):
            trace(bytes(bad))

    def test_rom_sha_rejects_truncation(self):
        with self.assertRaisesRegex(ValueError,'fingerprint'):
            trace(ROM[:-1])

    def test_fail_closed_unimplemented_opcode(self):
        bad=bytearray(ROM)
        bad[0x19AA9]=0x76 # HALT is explicitly unsupported
        m=ObjectMachine(bytes(bad),0x9AA9,ram={0xC201:b'\x00'})
        m.slot[2]=6;m.ix=0xC200
        with self.assertRaises(UnsupportedOpcode):m.step()

    def test_instruction_budget(self):
        m=ObjectMachine(ROM,0x9966,ram={0xC198:b'\x01'},max_instructions=1)
        m.slot[2]=6
        with self.assertRaisesRegex(RuntimeError,'budget'):
            m.run(0xE000)

    def test_wrong_mapped_bank_rejected(self):
        m=ObjectMachine(ROM,0x9AA9,ram={0xC201:b'\x00'})
        m.slot[2]=4;m.ix=0xC200;m.push(0xE000)
        with self.assertRaises((UnsupportedOpcode,RuntimeError)):
            m.run(0xE000)

    def test_report_contains_no_raw_output_arrays(self):
        self.assertFalse(any('payload' in x or 'hex_bytes' in x for x in self.report))
        self.assertTrue(all(set(x)=={'record','origins','elements','steps','object_calls','output_sha256'}
                            for x in self.report['cases']))

    def test_reproducibility_on_subset(self):
        a=trace(ROM,((0,0),))
        self.assertEqual(len(a['cases']),64)
        self.assertEqual(a['cases'],self.report['cases'][:64])

    def test_external_assembler_fixture_metadata(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as td:
            report=prepare(td)
            self.assertEqual(report['module_bytes'],1345)
            self.assertEqual(report['physical_offset'],'1C180')
            data=(Path(td)/'bank07.asm').read_text()
            self.assertTrue(data.startswith(HEADER))
            self.assertEqual(data.count('.ORGA $8180'),1)
            self.assertIn('.BANK 7 SLOT 2',data)
            self.assertNotIn('original ROM data',data)

    def test_external_assembler_fixture_rejects_drift(self):
        source=SOURCE.read_text().replace('org $8180','org $8182',1)
        with self.assertRaisesRegex(ValueError,'origin'):
            make_source(source)
        source=SOURCE.read_text().replace('    outi','    nop',1)
        with self.assertRaisesRegex(ValueError,'count'):
            make_source(source)

    def test_no_rom_classification_inflation(self):
        self.assertEqual(self.report['new_source_backed_bytes'],0)
        self.assertEqual(self.report['new_classified_rom_bytes'],0)

if __name__=='__main__':unittest.main(verbosity=1)
