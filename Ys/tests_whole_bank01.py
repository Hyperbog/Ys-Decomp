#!/usr/bin/env python3
"""Source-only bank1 closure tests and strict negative regressions."""
import copy
import hashlib
import json
from pathlib import Path
from unittest import TestCase,main,mock
import sys
import tempfile
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
import whole_bank01 as wb
from build_system_m6 import complete_banks,build,BANKS,SOURCED
from build_sms_phase14 import EXPECTED_SHA
from wla_system_m6 import prepare,verify
ROM=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else None
if ROM:sys.argv=sys.argv[:1]

class Bank01Tests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=json.loads((ROOT/wb.SOURCE).read_text())
        cls.raw=wb.full_bank(ROOT)
        cls.original=ROM.read_bytes() if ROM else None

    def bad_source(self,change):
        bad=copy.deepcopy(self.src);change(bad)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'source.json';path.write_text(json.dumps(bad))
            with mock.patch.object(wb,'SOURCE',path):
                with self.assertRaises((ValueError,KeyError,TypeError)):
                    wb.new_data(ROOT)

    def test_01_complete_16kb_bank_hash(self):
        self.assertEqual(len(self.raw),0x4000)
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(),'e91fa8fb9109dc13555967e208cb4650972d1965c2c9088be8d748ea177b4505')

    def test_02_exact_ownership(self):
        old=wb.existing(ROOT);code=wb.new_code(ROOT);data,inventory=wb.new_data(ROOT)
        self.assertEqual([len(old),len(code),len(data)],[779,1717,13888])
        self.assertEqual(set(old)|set(code)|set(data),set(range(0x4000,0x8000)))
        self.assertFalse(set(old)&set(code));self.assertFalse(set(old)&set(data));self.assertFalse(set(code)&set(data))
        self.assertEqual(sum(x['bytes'] for x in inventory),len(data))

    def test_03_mixed_assembly_matches(self):
        source=wb.mixed_source(ROOT)
        self.assertEqual(source,(ROOT/wb.ASSEMBLY).read_text())
        self.assertEqual(wb.assemble_bank01_mixed(source),self.raw)

    def test_04_pointer_directory_values(self):
        dirs=self.src['pointer_directories']
        self.assertEqual(len(dirs),2)
        self.assertEqual(dirs[0]['targets'],[0x4C13,0x4C13,0x4C52,0x4C55,0x4C59,0x4C5D,0x4C61,0x4C65])
        self.assertEqual(dirs[1]['targets'],[0x602C,0x6043])

    def test_05_sentinel_and_header(self):
        self.assertEqual(self.src['ff_filler'],{'start':0x7E9C,'count':340,'value':255})
        self.assertEqual(self.raw[0x3E9C:0x3FF0],b'\xff'*340)
        self.assertEqual(self.raw[-16:-6],b'TMR SEGA  ')

    def test_06_unresolved_data_flagged(self):
        src=self.src
        self.assertEqual(sum(len(bytes.fromhex(s['bytes_hex'])) for s in src['unresolved_spans']),13528)
        self.assertIn('Unresolved',src['note'])

    def test_07_source_code_is_mnemonics(self):
        self.assertEqual(len(wb.instruction_index((ROOT/wb.CODE).read_text())),875)
        self.assertNotIn('    db ',(ROOT/wb.CODE).read_text().lower())

    def test_08_six_complete_banks(self):
        allbanks=complete_banks(ROOT)
        self.assertEqual(sorted(allbanks),BANKS)
        self.assertEqual(sum(len(b) for b in allbanks.values()),6*0x4000)

    def test_09_source_only_bank_matches_rom(self):
        if self.original is None:self.skipTest('Original user ROM not provided')
        self.assertEqual(hashlib.sha256(self.original).hexdigest(),EXPECTED_SHA)
        self.assertEqual(self.raw,self.original[0x4000:0x8000])

    def test_10_whole_rom(self):
        if self.original is None:self.skipTest('Original user ROM not provided')
        image,report=build(self.original)
        self.assertEqual(image,self.original)
        self.assertEqual(report['source_backed_bytes'],98787)
        self.assertEqual(report['original_rom_fallback_bytes'],163357)
        self.assertEqual(report['source_only_complete_banks'],[0,1,2,3,6,7])

    def test_11_bad_pointer(self):
        self.bad_source(lambda d:d['pointer_directories'][0]['targets'].__setitem__(0,0x4000))

    def test_12_out_of_range_pointer(self):
        self.bad_source(lambda d:d['pointer_directories'][1]['targets'].__setitem__(1,0x8000))

    def test_13_swapped_pointer_order(self):
        self.bad_source(lambda d:d['pointer_directories'].reverse())

    def test_14_bad_padding_count(self):
        self.bad_source(lambda d:d['ff_filler'].__setitem__('count',339))

    def test_15_corrupted_unresolved(self):
        def flip(d):
            s=d['unresolved_spans'][0];s['bytes_hex']=('aa' if s['bytes_hex'][:2]!='aa' else 'bb')+s['bytes_hex'][2:]
        self.bad_source(flip)

    def test_16_truncated_data(self):
        self.bad_source(lambda d:d['unresolved_spans'][-1].__setitem__('bytes_hex',d['unresolved_spans'][-1]['bytes_hex'][:-2]))

    def test_17_duplicate_span_address(self):
        self.bad_source(lambda d:d['unresolved_spans'][1].__setitem__('start',d['unresolved_spans'][0]['start']))

    def test_18_illegal_extra_field(self):
        self.bad_source(lambda d:d['unresolved_spans'][0].__setitem__('not_proven',1))

    def test_19_mutated_instruction_rejected(self):
        original=(ROOT/wb.CODE).read_text()
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'bad.asm';path.write_text(original.replace('ld (de),a','nop',1))
            self.assertNotEqual(path.read_text(),original)
            with mock.patch.object(wb,'CODE',path):
                with self.assertRaises(ValueError):wb.new_code(ROOT)

    def test_20_mutated_rom_rejected(self):
        if self.original is None:self.skipTest('Original user ROM not provided')
        altered=bytearray(self.original);altered[0x4C13]^=1
        with self.assertRaises(ValueError):build(bytes(altered))

    def test_21_bad_fingerprint_rejected_during_capture(self):
        with self.assertRaises(ValueError):wb.capture(b'\0'*0x40000)

    def test_22_wla_fixture_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            info=prepare(d)
            self.assertEqual(info['banks'],BANKS)
            self.assertFalse(info['external_assembler_verified'])
            fixture=(Path(d)/'bank01.asm').read_text()
            self.assertIn('.BANK 1 SLOT 1',fixture)
            self.assertIn('.ORGA $4000',fixture)
            with self.assertRaises(FileNotFoundError):verify(d,'missing-wla','missing-wlalink')

    def test_23_source_builder_rejects_changed_digest(self):
        with tempfile.TemporaryDirectory() as d:
            meta=json.loads((ROOT/wb.DIGEST).read_text());meta['bank_sha256']='0'*64
            path=Path(d)/'digest.json';path.write_text(json.dumps(meta))
            with mock.patch.object(wb,'DIGEST',path):
                with self.assertRaises(ValueError):wb.full_bank(ROOT)

if __name__=='__main__':main(verbosity=2)
