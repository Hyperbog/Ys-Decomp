#!/usr/bin/env python3
"""Byte-identity, graph-construction, and epistemic safety regressions."""
import json
import tempfile
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
from build_system_graph import build, flow, io_effects, parse_source, ROOT as CODE_ROOT
from query_system_graph import query
from build_graph_frontier import build_frontier
from build_sms_phase14 import validated_rom

EXPECTED_INST=7047
EXPECTED_BYTES=14198
EXPECTED_BLOCKS=1765

class TestSystemGraph(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if len(sys.argv)>1 and not sys.argv[1].startswith('-'):
            cls.rom=Path(sys.argv[1]).read_bytes()
        else:
            raise ValueError('provide user-owned original ROM path')
        validated_rom(cls.rom)
        cls.graph=build(cls.rom)

    def test_instructions_matched(self):
        self.assertEqual(self.graph['summary']['verified_instruction_count'], EXPECTED_INST)
        self.assertEqual(self.graph['summary']['verified_instruction_bytes'], EXPECTED_BYTES)

    def test_banks_cover_full_image(self):
        self.assertEqual([x['bank'] for x in self.graph['banks']],list(range(16)))
        self.assertEqual(sum(x['verified_code_bytes'] for x in self.graph['banks']),EXPECTED_BYTES)

    def test_blocks_partition(self):
        self.assertEqual(self.graph['summary']['basic_blocks'],EXPECTED_BLOCKS)
        self.assertEqual(sum(b['instruction_count'] for b in self.graph['blocks']),EXPECTED_INST)
        self.assertEqual(sum(b['byte_count'] for b in self.graph['blocks']),EXPECTED_BYTES)

    def test_unique_instruction_byte_ownership(self):
        spans=[]
        for n in self.graph['instructions']:
            self.assertEqual(n['id'],f'{n["offset"]:05X}')
            self.assertLessEqual(n['offset']+n['size'],(n['bank']+1)*0x4000)
            spans.extend(range(n['offset'],n['offset']+n['size']))
        self.assertEqual(len(spans),len(set(spans)))

    def test_all_direct_edges_have_valid_instruction_starts(self):
        known={n['id'] for n in self.graph['instructions']}
        for edge in self.graph['edges']:
            self.assertIn(edge['from'],known)
            if edge['to_instruction'] is not None:
                self.assertIn(edge['to_instruction'],known)

    def test_unresolved_edges_not_labeled_proven(self):
        unresolved=[e for e in self.graph['edges'] if e['resolution']=='unresolved_mapper_slot']
        self.assertTrue(unresolved)
        self.assertTrue(all(e.get('to_instruction') is None and e.get('to_bank_candidate') is None for e in unresolved))

    def test_local_edge_is_not_runtime_proof(self):
        local=[e for e in self.graph['edges'] if e['resolution']=='same_image_candidate']
        self.assertGreater(len(local),100)
        self.assertTrue(all(e['to_bank_candidate'] is not None for e in local))

    def test_immediate_mapper_candidate_has_provenance(self):
        selected=[e for e in self.graph['edges'] if e['resolution']=='static_mapper_candidate']
        self.assertEqual(len(selected),12)
        self.assertTrue(all(e['mapping_evidence'] and 'mapper-write' in e['mapping_evidence'] for e in selected))

    def test_known_graphical_hardware_sites(self):
        ports={e['port'] for item in self.graph['effects'] for e in item['effects'] if e['kind']=='io_write'}
        self.assertIn('BF',ports)
        self.assertIn('BE',ports)

    def test_mapper_register_evidence(self):
        rows=[e for item in self.graph['effects'] for e in item['effects'] if e.get('mapper_register')]
        self.assertTrue(any(e['cpu_address']=='FFFF' for e in rows))

    def test_bad_rom_fails_closed(self):
        wrong=bytearray(self.rom);wrong[0]^=1
        with self.assertRaises(ValueError):build(bytes(wrong))

    def test_source_instruction_mutation(self):
        with tempfile.TemporaryDirectory(dir=CODE_ROOT/'src') as temp:
            testpath=Path(temp)/'mutant.asm'
            testpath.write_text('org $0000\n ei\n')
            with self.assertRaises(ValueError):list(parse_source(testpath,0,self.rom))

    def test_no_instruction_before_org(self):
        with tempfile.TemporaryDirectory(dir=CODE_ROOT/'src') as temp:
            testpath=Path(temp)/'bad.asm'
            testpath.write_text('di\n')
            with self.assertRaises(ValueError):list(parse_source(testpath,0,self.rom))

    def test_indirect_jump_is_not_target_guess(self):
        kind,target,conditional,falls=flow({'id':'00012','asm':'jp (hl)'})
        self.assertEqual((kind,target,falls),('indirect_jump',None,False))

    def test_push_ret_is_not_assumed_normal_return(self):
        self.assertEqual(flow({'id':'00000','asm':'push de'})[0],None)
        self.assertEqual(flow({'id':'00001','asm':'ret'})[0],'return')

    def test_conditional_return_fallthrough(self):
        kind,target,conditional,falls=flow({'id':'00000','asm':'ret z'})
        self.assertEqual((kind,conditional,falls),('return',True,True))

    def test_query_gives_context(self):
        data=query(self.graph,0,0, symbols=json.loads((ROOT/'phase15/symbols.json').read_text()))
        self.assertTrue(data['matched_instruction'])
        self.assertEqual(data['instruction']['asm'],'di')
        self.assertEqual(data['symbols_at_entry'][0]['name'],'ResetEntry')

    def test_query_refuses_unmatched_rom_bytes(self):
        data=query(self.graph,5,0x8000)
        self.assertFalse(data['matched_instruction'])

    def test_query_rejects_invalid_mapping(self):
        with self.assertRaises(ValueError):query(self.graph,6,0x2000)

    def test_reconstruction_frontier_is_not_code_coverage(self):
        frontier=build_frontier(self.graph)
        self.assertEqual(frontier["summary"]["missing_fixed_bank0_target_count"],5)
        self.assertEqual(frontier["summary"]["missing_fixed_bank0_ref_count"],7)
        self.assertEqual(frontier["summary"]["unresolved_mapper_ref_count"],17)
        self.assertEqual(frontier["summary"]["new_source_backed_bytes"],0)

    def test_frontier_snapshot_reproducible(self):
        expected=json.loads((ROOT/"whole_system/frontier.json").read_text())
        self.assertEqual(build_frontier(self.graph),expected)

    def test_snapshot_reproducible(self):
        target=json.loads((ROOT/'whole_system/evidence_graph.json').read_text())
        self.assertEqual(self.graph,target)

if __name__=='__main__':
    if len(sys.argv)!=2:
        raise SystemExit('usage: tests_system_graph.py user_owned_original.sms')
    unittest.main(argv=[sys.argv[0]],verbosity=1)
