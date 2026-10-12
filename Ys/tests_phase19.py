#!/usr/bin/env python3
"""Phase 19: ROM-opcode SAT producer/consumer integration regression tests."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'tools'))
from phase19_sprite_execution import SpriteMachine, ORIGINS, trace
from phase18_z80_trace import UnsupportedOpcode

ROM_PATH = Path(sys.argv.pop(1)) if len(sys.argv)>1 and not sys.argv[1].startswith('-') else None


class Phase19Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if ROM_PATH is None:
            raise RuntimeError('Supply path to the original Ys SMS ROM')
        cls.rom = ROM_PATH.read_bytes()
        cls.expected = json.loads((ROOT/'phase19/execution_report.json').read_text())
        cls.actual = trace(cls.rom)

    def test_01_reference_rom(self):
        self.assertEqual(hashlib.sha256(self.rom).hexdigest(), self.expected['rom_sha256'])

    def test_02_snapshot_matches(self):
        self.assertEqual(self.actual, self.expected)

    def test_03_exact_case_coverage(self):
        self.assertEqual(len(self.actual['cases']), 192)
        self.assertEqual(self.actual['input_records'], 64)
        for i, pair in enumerate(ORIGINS):
            block=self.actual['cases'][i*64:(i+1)*64]
            self.assertEqual([e['record_index'] for e in block], list(range(64)))
            self.assertEqual({(e['first_origin'],e['second_origin']) for e in block}, {pair})

    def test_04_transfer_total_and_size(self):
        self.assertEqual(self.actual['sat_bytes_per_run'], 192)
        self.assertEqual(self.actual['total_sat_bytes_across_runs'], 36864)
        self.assertEqual({e['sat_upload_instruction_steps'] for e in self.actual['cases']}, {206})

    def test_05_bank_selected_by_executed_caller(self):
        self.assertEqual({e['mapper_value'] for e in self.actual['cases']}, {6})
        self.assertEqual(self.rom[0x26F3:0x26F8], bytes.fromhex('3e 06 32 ff ff'))
        self.assertEqual(self.rom[0x2704:0x2707], bytes.fromhex('cd 32 99'))

    def test_06_producer_loop_at_record_start(self):
        self.assertEqual(self.rom[0x19932:0x1993F],
                         bytes.fromhex('3a 99 c1 87 6f 26 80 7e 2c 66 6f 46 48'))

    def test_07_pointer_advance_from_count(self):
        for e in self.actual['cases']:
            self.assertEqual(int(e['y_pointer_end'],16),0xDD00+e['count'])
            self.assertEqual(int(e['xt_pointer_end'],16),0xDD40+2*e['count'])
            self.assertTrue(0 < e['count'] < 64)

    def test_08_buffer_hashes_recomputed_from_raw_rom(self):
        # Deliberately independent of existing consumer implementation:
        # parse the directory, sum raw offsets and interleaved byte pairs.
        for e in self.actual['cases']:
            i=e['record_index']
            off=0x18000+2*i
            ptr=self.rom[off] | (self.rom[off+1]<<8)
            start=0x18000+(ptr-0x8000)
            n=self.rom[start]
            self.assertEqual(n,e['count'])
            deltas=self.rom[start+1:start+1+n]
            pairs=self.rom[start+1+n:start+1+3*n]
            y=bytearray([0xD0]*64)
            xt=bytearray(128)
            a=e['first_origin']
            for j,value in enumerate(deltas):
                a=(a+value)&255
                y[j]=a
            y[n]=0xD0
            a=e['second_origin']
            for j in range(n):
                a=(a+pairs[2*j])&255
                xt[2*j]=a
                xt[2*j+1]=pairs[2*j+1]
            self.assertEqual(hashlib.sha256(y).hexdigest(),e['y_table_sha256'])
            self.assertEqual(hashlib.sha256(xt).hexdigest(),e['xt_table_sha256'])
            self.assertEqual(hashlib.sha256(y+xt).hexdigest(),e['sat_output_sha256'])

    def test_09_combined_hash_from_case_order(self):
        stream=bytearray()
        for e in self.actual['cases']:
            i=e['record_index']
            off=0x18000+2*i
            ptr=int.from_bytes(self.rom[off:off+2],'little')
            start=0x18000+ptr-0x8000
            count=self.rom[start]
            y=bytearray([0xD0]*64)
            xt=bytearray(128)
            running=e['first_origin']
            for j in range(count):
                running=(running+self.rom[start+1+j])&255
                y[j]=running
            running=e['second_origin']
            for j in range(count):
                running=(running+self.rom[start+1+count+2*j])&255
                xt[2*j]=running
                xt[2*j+1]=self.rom[start+2+count+2*j]
            stream.extend(y+xt)
        self.assertEqual(hashlib.sha256(stream).hexdigest(),self.actual['concat_sat_sha256'])

    def test_10_origin_changes_are_visible(self):
        for i in range(64):
            a,b,c=(self.actual['cases'][i+j*64] for j in range(3))
            self.assertEqual(a['count'],b['count'])
            self.assertEqual(b['count'],c['count'])
            self.assertEqual(len({a['sat_output_sha256'],b['sat_output_sha256'],c['sat_output_sha256']}),3)

    def test_11_wrong_rom_rejected(self):
        bad=bytearray(self.rom)
        bad[0x19947]^=1
        with self.assertRaisesRegex(ValueError,'fingerprint'):
            trace(bytes(bad))

    def test_12_unknown_opcode_fails_closed(self):
        wrong=bytearray(self.rom)
        wrong[0x26F3]=0xD9
        machine=SpriteMachine(bytes(wrong),0x26F3)
        with self.assertRaisesRegex(UnsupportedOpcode,'D9'):
            machine.run(0x2710)

    def test_13_bad_producer_opcode_fails_closed(self):
        wrong=bytearray(self.rom)
        wrong[0x19932]=0xD9
        machine=SpriteMachine(bytes(wrong),0x9932,ram={0xC199:b'\x07'})
        machine.slot[2]=6
        with self.assertRaisesRegex(UnsupportedOpcode,'D9'):
            machine.run(0x9966)

    def test_14_budget_detects_nontermination(self):
        machine=SpriteMachine(self.rom,0x26F3,max_instructions=4)
        with self.assertRaisesRegex(RuntimeError,'budget'):
            machine.run(0x2710)

    def test_15_wrong_mapper_changes_opcode_stream(self):
        machine=SpriteMachine(self.rom,0x9932)
        self.assertNotEqual(machine.read(0x9932),self.rom[0x19932])
        machine.slot[2]=6
        self.assertEqual(machine.read(0x9932),self.rom[0x19932])

    def test_16_no_new_coverage_claims(self):
        self.assertEqual(self.actual['source_backed_bytes_added'],0)
        self.assertEqual(self.actual['new_rom_bytes_classified'],0)

    def test_17_missing_report_case_is_detectable(self):
        truncated=dict(self.expected)
        truncated['cases']=self.expected['cases'][:-1]
        self.assertNotEqual(truncated,self.actual)

    def test_18_sat_buffer_is_traced_with_rom_opcodes(self):
        from phase18_z80_trace import Machine
        machine=SpriteMachine(self.rom,0x0427,ram={0xDD00:bytes([0xD0]*64),0xDD40:bytes(128)})
        machine.push(0xE000)
        machine.run(0xE000)
        self.assertEqual(machine.control,['7F00','7F80'])
        self.assertEqual(machine.steps,206)
        self.assertEqual(len(machine.data_writes),192)


if __name__ == '__main__':
    unittest.main(verbosity=2)
