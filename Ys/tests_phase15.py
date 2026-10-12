#!/usr/bin/env python3
"""Regression checks for source-backed ROM tables and named banked crossrefs."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'tools'))
from build_sms_phase14 import offset, EXPECTED_SHA
from build_phase15 import build
from source_tables_phase15 import (SOURCES, assemble_data, generated_sources,
                                   load_verified_sources, metadata)
from symbols_phase15 import make

ROM = Path('/mnt/data/Ys - The Vanished Omens (USA, Europe).sms')


class Phase15Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=ROM.read_bytes()
        cls.output,cls.report=build(cls.rom)
        cls.tables=load_verified_sources()
        cls.symbols=make()

    def test_original_and_image_match(self):
        self.assertEqual(hashlib.sha256(self.rom).hexdigest(),EXPECTED_SHA)
        self.assertEqual(self.output,self.rom)
        self.assertEqual(len(self.output),262144)

    def test_source_accounting_exact_no_double_count(self):
        d=self.report
        self.assertEqual(d['assembly_source_bytes'],14025)
        self.assertEqual(d['standalone_data_source_bytes'],678)
        self.assertEqual(d['all_source_backed_bytes'],14703)
        self.assertEqual(d['original_rom_fallback_bytes'],247441)
        self.assertEqual(d['prior_candidate_classification_bytes'],58133)
        self.assertFalse(d['source_only_complete_rom'])
        self.assertFalse(d['external_z80_assembler_verified'])
        self.assertEqual(sum(r['structured_source_bytes'] for r in d['banks']),678)
        self.assertEqual(sum(r['z80_source_bytes'] for r in d['banks']),14025)
        self.assertEqual(sum(r['fallback_bytes'] for r in d['banks']),247441)

    def test_source_modular_counts(self):
        self.assertEqual({bank:len(row['bytes']) for bank,row in self.tables.items()},
                         {0:100,1:16,6:178,7:384})
        for bank,desc in self.tables.items():
            source=(ROOT/SOURCES[bank]).read_text()
            emitted,labels=assemble_data(source)
            self.assertEqual(emitted,desc['bytes'])
            self.assertEqual(labels,desc['labels'])
            for pc,b in emitted.items():
                self.assertEqual(b,self.rom[offset(bank,pc)])

    def test_tables_are_standalone_metadata_derived(self):
        # The source and direct byte encoder can be used without reading ROM.
        expected=generated_sources()
        self.assertEqual(set(expected),set(SOURCES))
        for bank,asm in expected.items():
            self.assertEqual(asm,(ROOT/SOURCES[bank]).read_text())
        self.assertEqual(len(metadata()[7][0][2]),128)

    def test_data_little_endian_and_header(self):
        self.assertEqual(bytes(self.tables[1]['bytes'][pc] for pc in range(0x7FF0,0x8000))[:8],b'TMR SEGA')
        first=metadata()[6][0][2][0]
        self.assertEqual(self.tables[6]['bytes'][0x8000],first&255)
        self.assertEqual(self.tables[6]['bytes'][0x8001],first>>8)

    def test_report_and_symbols_reproducible(self):
        self.assertEqual(self.report,json.loads((ROOT/'phase15/build_report.json').read_text()))
        self.assertEqual(self.symbols,json.loads((ROOT/'phase15/symbols.json').read_text()))

    def test_symbols_have_physical_bank_locations(self):
        data=self.symbols
        self.assertEqual(data['summary']['symbols'],23)
        self.assertEqual(data['summary']['crossrefs'],1196)
        self.assertEqual(data['summary']['static_mapper_candidates'],12)
        self.assertFalse(data['summary']['runtime_verified'])
        for row in data['symbols']:
            if row['address_space']=='ROM':
                self.assertEqual(int(row['physical_offset'],16),
                                 offset(row['physical_bank'],int(row['cpu_address'],16)))

    def test_mapper_candidates_are_adjacent_constant_writes(self):
        rows=[r for r in self.symbols['references'] if 'static_target_bank_candidate' in r]
        self.assertEqual(len(rows),12)
        for r in rows:
            write=int(r['static_bank_evidence'].rsplit('$',1)[1],16)
            newbank=r['static_target_bank_candidate']
            self.assertEqual(self.rom[write-2:write+3],bytes([0x3E,newbank,0x32,0xFF,0xFF]))
            self.assertEqual(int(r['from_cpu'],16),write+3)
            self.assertIsNone(r['proven_target_bank'])
            self.assertGreaterEqual(int(r['target_cpu'],16),0x8000)

    def test_wrong_rom_or_size_rejected(self):
        changed=bytearray(self.rom)
        changed[0x3FF00]^=1
        with self.assertRaises(ValueError):build(bytes(changed))
        with self.assertRaises(ValueError):build(self.rom[:-1])

    def test_altered_structured_pointer_rejected(self):
        sources={bank:(ROOT/rel).read_text() for bank,rel in SOURCES.items()}
        src=sources[6]
        self.assertIn('dw $',src)
        pos=src.index('dw $')
        old=src[pos+4:pos+8]
        sources[6]=src[:pos+4]+('FFFF' if old!='FFFF' else '0000')+src[pos+8:]
        with self.assertRaisesRegex(ValueError,'data source/ROM mismatch'):
            build(self.rom,table_overrides=sources)

    def test_wrong_bank_and_overlap_rejected(self):
        sources={bank:(ROOT/rel).read_text() for bank,rel in SOURCES.items()}
        sources[6]=sources[6].replace('org $8000','org $9932',1)
        with self.assertRaisesRegex(ValueError,'overlap|mismatch'):
            build(self.rom,table_overrides=sources)

    def test_db_dw_parser_fail_closed(self):
        invalid=['org $8000\ndb $100\n','org $8000\ndw $10000\n',
                 'org $8000\ndb $01\norg $8000\ndb $02\n',
                 'dw $1234\n', 'org $8000\ninc a\n']
        for sample in invalid:
            with self.subTest(sample=sample),self.assertRaises(ValueError):
                assemble_data(sample)


if __name__=='__main__':unittest.main(verbosity=2)
