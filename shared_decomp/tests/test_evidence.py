import copy
import unittest
from shared_decomp.evidence import validate_graph

class EvidenceContractTests(unittest.TestCase):
    def setUp(self):
        self.nodes=[{'id':'00000','offset':0,'size':2}, {'id':'00002','offset':2,'size':1}]
        self.blocks=[{'id':'00000','offset':0,'byte_count':3,'instruction_count':2}]
        self.edges=[{'from':'00000','from_block':'00000','to_instruction':'00002','to_block':'00000'}]
    def validate(self, nodes=None,blocks=None,edges=None):
        return validate_graph(self.nodes if nodes is None else nodes, self.blocks if blocks is None else blocks,
                              self.edges if edges is None else edges,16)
    def test_valid_graph(self):self.assertTrue(self.validate()['valid'])
    def test_overlapping_instructions(self):
        n=copy.deepcopy(self.nodes);n[1]['offset']=1
        self.assertFalse(self.validate(nodes=n)['valid'])
    def test_bad_link(self):
        e=copy.deepcopy(self.edges);e[0]['to_instruction']='no such node'
        self.assertFalse(self.validate(edges=e)['valid'])
    def test_bad_block_span(self):
        b=copy.deepcopy(self.blocks);b[0]['byte_count']=2
        self.assertFalse(self.validate(blocks=b)['valid'])
    def test_unmapped_target_allowed(self):
        e=copy.deepcopy(self.edges);e[0]['to_instruction']=None;e[0]['to_block']=None
        self.assertTrue(self.validate(edges=e)['valid'])
    def test_reject_oob_span(self):
        n=copy.deepcopy(self.nodes);n[1]['size']=100
        self.assertFalse(self.validate(nodes=n)['valid'])

if __name__ == '__main__':unittest.main()
