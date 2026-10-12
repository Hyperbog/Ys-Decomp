#!/usr/bin/env python3
"""Phase 18: independent bounded Z80 execution checks, including negative cases."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
from phase18_z80_trace import Machine, UnsupportedOpcode, trace
from vdp_upload_phase9 import CALLS

ROM_PATH=Path(sys.argv.pop(1)) if len(sys.argv)>1 and not sys.argv[1].startswith('-') else None

class Phase18Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not ROM_PATH:raise RuntimeError('Supply path to exact original Ys SMS ROM')
        cls.rom=ROM_PATH.read_bytes()
        cls.expected=json.loads((ROOT/'phase18/execution_report.json').read_text())
        cls.result=trace(cls.rom)

    def test_a_rom_identity(self):
        self.assertEqual(hashlib.sha256(self.rom).hexdigest(),self.expected['rom_sha256'])

    def test_b_report_exact(self):
        self.assertEqual(self.result,self.expected)

    def test_c_all_four_uploaders_execute(self):
        self.assertEqual(len(self.result['uploader_traces']),4)
        self.assertEqual([t['caller'] for t in self.result['uploader_traces']],
                         [f'{x[3]:04X}' for x in CALLS])
        self.assertEqual(sum(x['out_data_bytes'] for x in self.result['uploader_traces']),6496)

    def test_d_mapper_state_and_vram_command(self):
        for e in self.result['uploader_traces']:
            self.assertEqual(e['mapper_write_bank'],3)
            self.assertEqual(int(e['vdp_control_commands'][0],16)&0xC000,0x4000)
            self.assertGreater(e['executed_instructions'],e['out_data_bytes'])

    def test_e_sprite_attribute_table_upload(self):
        e=self.result['sprite_sat_trace']
        self.assertEqual(e['control_commands'],['7F00','7F80'])
        self.assertEqual(e['output_bytes'],192)
        self.assertEqual(e['executed_instructions'],206)
        self.assertEqual(e['record_elements'],30)

    def test_f_all_bank7_entries_execute(self):
        rows=self.result['bank7_unrolled_traces']
        self.assertEqual(len(rows),64)
        self.assertEqual([x['index'] for x in rows],list(range(64)))
        self.assertEqual(sum(x['vdp_bytes'] for x in rows),40224)
        self.assertEqual(sum(x['source_bytes'] for x in rows),10056)
        for x in rows:
            self.assertEqual(x['instructions'],x['source_bytes']*4+1)
            self.assertEqual(x['vdp_bytes'],x['source_bytes']*4)

    def test_g_bank7_sha_recomputed_independently(self):
        rows=json.loads((ROOT/'phase13/graphics_directory.json').read_text())['graphics_records']
        parts=[]
        for rec in rows:
            start=7*0x4000+int(rec['graphics_source_cpu'],16)-0x8000
            raw=self.rom[start:start+rec['graphics_bytes']]
            parts.append(b''.join(bytes((b,0,0,0)) for b in raw))
        self.assertEqual(hashlib.sha256(b''.join(parts)).hexdigest(),
                         self.result['bank7_combined_output_sha256'])

    def test_h_bad_rom_fingerprint_rejected(self):
        wrong=bytearray(self.rom);wrong[0x1C000]^=1
        with self.assertRaisesRegex(ValueError,'fingerprint'):
            trace(bytes(wrong))

    def test_i_invalid_z80_opcode_fails_closed(self):
        wrong=bytearray(self.rom);wrong[0x0BA1]=0xD9 # EXX not supported
        machine=Machine(bytes(wrong),0x0BA1)
        with self.assertRaisesRegex(UnsupportedOpcode,'D9'):
            machine.run(0x0BA7)

    def test_j_non_vram_vdp_command_rejected(self):
        machine=Machine(self.rom,0x0427)
        machine.port(0xBF,0x00)
        with self.assertRaisesRegex(UnsupportedOpcode,'Non-VRAM'):
            machine.port(0xBF,0x00)

    def test_k_incomplete_control_command_rejected(self):
        machine=Machine(self.rom,0x0427)
        machine.port(0xBF,0x02)
        with self.assertRaisesRegex(RuntimeError,'Incomplete VDP'):
            machine.run(0x0427)

    def test_l_budget_exhaustion_detected(self):
        m=Machine(self.rom,0x0BA1,max_instructions=2)
        with self.assertRaisesRegex(RuntimeError,'budget'):
            m.run(0x0BB7)

    def test_m_wrong_mapper_produces_other_rom_bytes(self):
        m=Machine(self.rom,0x82C0)
        m.slot[2]=8 # incorrect bank for this entrypoint
        self.assertNotEqual(m.read(0x82C0),0xED)

    def test_n_ram_seed_range_safety(self):
        with self.assertRaisesRegex(ValueError,'RAM range'):
            Machine(self.rom,0x0427,ram={0xFFFC:b'\x11'})

    def test_o_mapper_mutation_changes_output_or_fails_closed(self):
        patched=bytearray(self.rom);patched[0x0BA2]=4
        first=CALLS[0]
        m=Machine(bytes(patched),first[0])
        try:
            m.run(first[3]+3)
        except (UnsupportedOpcode,RuntimeError):
            return
        expected=self.result['uploader_traces'][0]['output_sha256']
        got=hashlib.sha256(bytes(v for _,v in m.data_writes)).hexdigest()
        self.assertNotEqual(got,expected)

if __name__=='__main__':unittest.main(verbosity=2)
