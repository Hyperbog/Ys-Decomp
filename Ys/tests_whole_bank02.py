#!/usr/bin/env python3
"""Complete bank2 sound-source closure checks and mutation rejection."""
import copy
import hashlib
import json
from pathlib import Path
from unittest import TestCase,main,mock
import sys
import tempfile
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
import whole_bank02 as wb
from build_system_m5 import complete_banks,build,BANKS,SOURCED
from whole_bank07 import assemble_mixed
from build_sms_phase14 import EXPECTED_SHA
from wla_system_m5 import prepare,verify
ROM=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else None
if ROM:sys.argv=sys.argv[:1]

class Bank02Tests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=json.loads((ROOT/wb.DATA).read_text())
        cls.raw=wb.full_bank(ROOT)
        cls.original=ROM.read_bytes() if ROM else None

    def bad_source(self,change):
        data=copy.deepcopy(self.src);change(data)
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'source.json';source.write_text(json.dumps(data))
            with mock.patch.object(wb,'DATA',source):
                with self.assertRaises(ValueError):wb.new_data(ROOT)

    def test_01_complete_bank_hash(self):
        self.assertEqual(len(self.raw),0x4000)
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(),'78b8ac016f2574ffece7f944f9b7680e873eb33f8481c31bbc0a480c4c74a4d8')

    def test_02_every_byte_owned_without_overlap(self):
        known=wb.known(ROOT);code=wb.decoded_code(ROOT);data,_=wb.new_data(ROOT)
        self.assertEqual([len(known),len(code),len(data)],[3785,16,12583])
        self.assertFalse(set(known)&set(code))
        self.assertFalse(set(known)&set(data))
        self.assertFalse(set(code)&set(data))
        self.assertEqual(set(known)|set(code)|set(data),set(range(0x8000,0xc000)))

    def test_03_mixed_source_independently_reassembles(self):
        s=wb.mixed_source(ROOT)
        self.assertEqual(s,(ROOT/wb.ASM).read_text())
        self.assertEqual(assemble_mixed(s),self.raw)

    def test_04_note_tables_are_bounded(self):
        psg=self.src['psg_note_periods'];fm=self.src['fm_note_registers']
        self.assertEqual(len(psg),73);self.assertEqual(len(fm),73)
        self.assertEqual(psg[:5],[0,1023,967,912,861])
        self.assertEqual(fm[:5],[0,4439,4459,4481,4504])
        self.assertTrue(all(a>b for a,b in zip(psg[1:],psg[2:])))
        self.assertTrue(all(a<b for a,b in zip(fm[1:],fm[2:])))

    def test_05_note_tables_referenced_from_engine(self):
        asm=(ROOT/'src/phase11_roundtrip/bank02.asm').read_text()
        self.assertIn('ld hl,$8A58',asm)
        self.assertIn('ld hl,$8AEA',asm)
        self.assertIn('ld hl,$8B7D',asm)
        self.assertIn('ld hl,$8C90',asm)

    def test_06_register_ports_present_in_verified_code(self):
        asm=(ROOT/'src/phase11_roundtrip/bank02.asm').read_text()
        for text in ('out ($F0),a','out ($F1),a','out ($7F),a'):
            self.assertIn(text,asm)

    def test_07_sound_lookups_are_pointer_bounded(self):
        a=self.src
        self.assertEqual(len(a['sequence_pointers']),17)
        self.assertEqual(a['sequence_pointers'][0],0x8B9F)
        self.assertEqual(a['sequence_pointers'][-1],0x8C2A)
        self.assertEqual(len(a['shape_pointers']),5)
        self.assertEqual(a['shape_pointers'],[0x8C39,0x8C52,0x8C68,0x8C80,0x8C89])
        self.assertEqual(sum(len(x['bytes']) for x in a['sequences']),0x8C2F-0x8B9F)
        self.assertEqual(sum(len(x['bytes']) for x in a['shapes']),0x8C90-0x8C39)

    def test_08_variable_song_events_are_strictly_partitioned(self):
        data=self.src['variable_event_bodies']
        ref=json.loads((ROOT/'phase21/source.json').read_text())['bank2_variable_descriptors']
        self.assertEqual(len(data),24)
        self.assertEqual(sum(len(x['unresolved_event_bytes']) for x in data),618)
        for r,s in zip(data,ref):
            self.assertEqual(r['index'],s['index'])
            self.assertEqual(r['start'],s['address']+1+9*len(s['channels']))
            self.assertEqual(r['end_exclusive'],s['next_address'])

    def test_09_five_complete_banks(self):
        banks=complete_banks(ROOT)
        self.assertEqual(sorted(banks),BANKS)
        self.assertEqual(len(banks),5)
        self.assertEqual(sum(map(len,banks.values())),5*0x4000)

    def test_10_rom_matches_original(self):
        if self.original is None:self.skipTest('User ROM not supplied')
        self.assertEqual(hashlib.sha256(self.original).hexdigest(),EXPECTED_SHA)
        self.assertEqual(self.raw,self.original[2*0x4000:3*0x4000])

    def test_11_whole_rom_overlay(self):
        if self.original is None:self.skipTest('User ROM not supplied')
        output,report=build(self.original)
        self.assertEqual(output,self.original)
        self.assertEqual(report['source_backed_bytes'],83182)
        self.assertEqual(report['original_rom_fallback_bytes'],178962)
        self.assertEqual(report['source_only_complete_banks'],[0,2,3,6,7])

    def test_12_broken_note_period_is_rejected(self):
        self.bad_source(lambda d:d['psg_note_periods'].__setitem__(4,d['psg_note_periods'][4]^1))

    def test_13_short_register_table_rejected(self):
        self.bad_source(lambda d:d['fm_note_registers'].pop())

    def test_14_bad_sound_handler_pointer_rejected(self):
        self.bad_source(lambda d:d['dispatch_targets'].__setitem__(0,0x7000))

    def test_15_swapped_sequence_offsets_rejected(self):
        self.bad_source(lambda d:d['sequence_pointers'].__setitem__(1,0x8B9F))

    def test_16_short_sequence_payload_rejected(self):
        self.bad_source(lambda d:d['sequences'][0]['bytes'].pop())

    def test_17_invalid_shape_pointer_rejected(self):
        self.bad_source(lambda d:d['shape_pointers'].__setitem__(4,0x8000))

    def test_18_short_shape_payload_rejected(self):
        self.bad_source(lambda d:d['shapes'][-1]['bytes'].pop())

    def test_19_wrong_song_body_start_rejected(self):
        self.bad_source(lambda d:d['variable_event_bodies'][0].__setitem__('start',0xB319))

    def test_20_changed_song_event_rejected(self):
        self.bad_source(lambda d:d['variable_event_bodies'][0]['unresolved_event_bytes'].__setitem__(0,255))

    def test_21_truncated_event_stream_rejected(self):
        self.bad_source(lambda d:d.__setitem__('event_stream_bytes_hex',d['event_stream_bytes_hex'][:-2]))

    def test_22_changed_post_song_unresolved_rejected(self):
        self.bad_source(lambda d:d.__setitem__('post_song_data_hex','00'+d['post_song_data_hex'][2:]))

    def test_23_mutated_rom_rejected(self):
        if self.original is None:self.skipTest('User ROM not supplied')
        damaged=bytearray(self.original);damaged[0x20000]^=1
        with self.assertRaises(ValueError):build(bytes(damaged))

    def test_24_wla_fixture_does_not_fake_external_verification(self):
        with tempfile.TemporaryDirectory() as d:
            result=prepare(d)
            self.assertEqual(result['banks'],BANKS)
            self.assertFalse(result['external_assembler_verified'])
            self.assertTrue((Path(d)/'bank02.asm').is_file())
            with self.assertRaises(FileNotFoundError):verify(d,assembler='absent-wla-z80-binary',linker='absent-wla-linker')

    def test_25_mutated_mnemonic_rejected(self):
        original=(ROOT/wb.CODE).read_text()
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'other.asm';path.write_text(original.replace('jp $8357','jp $8358'))
            with mock.patch.object(wb,'CODE',path):
                with self.assertRaises(ValueError):wb.full_bank(ROOT)

    def test_26_source_without_original_rom(self):
        self.assertEqual(wb.full_bank(ROOT),self.raw)

if __name__=='__main__':main(verbosity=1)
