import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import workflow as wf


def fixture():
    data = b"01234567"
    return data, {
        'schema': 'decomp-project-v1',
        'project': 'synthetic',
        'binary': {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()},
        'partitions': [
            {'name': 'b0', 'offset': 0, 'length': 4, 'source_backed_bytes': 4, 'fallback_bytes': 0,
             'source_only_complete': True, 'semantic_status': 'partial', 'external_assembler_verified': False,
             'runtime_verified': False, 'sha256': hashlib.sha256(data[:4]).hexdigest()},
            {'name': 'b1', 'offset': 4, 'length': 4, 'source_backed_bytes': 1, 'fallback_bytes': 3,
             'source_only_complete': False, 'semantic_status': 'unresolved', 'external_assembler_verified': False,
             'runtime_verified': False, 'sha256': hashlib.sha256(data[4:]).hexdigest()},
        ],
    }


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.raw, self.config = fixture()

    def test_valid_manifest(self):
        report = wf.check_manifest(self.config)
        self.assertTrue(report['valid'])
        self.assertEqual(report['source_backed_bytes_reported'], 5)
        self.assertEqual(report['source_only_partitions_reported'], ['b0'])

    def test_binary_sha_and_partition_verification(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td, 'original.bin'); p.write_bytes(self.raw)
            report = wf.check_manifest(self.config, p)
            self.assertTrue(report['valid'])
            self.assertTrue(report['binary_digest_verified'])
            self.assertEqual(len(report['partition_digests_checked']), 2)

    def test_reject_wrong_binary(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td, 'original.bin'); p.write_bytes(b'01234569')
            self.assertFalse(wf.check_manifest(self.config, p)['valid'])

    def test_reject_truncated_binary(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td, 'original.bin'); p.write_bytes(self.raw[:-1])
            self.assertFalse(wf.check_manifest(self.config, p)['valid'])

    def test_reject_overlap(self):
        c=copy.deepcopy(self.config); c['partitions'][1]['offset'] = 3
        self.assertFalse(wf.check_manifest(c)['valid'])

    def test_reject_gap(self):
        c=copy.deepcopy(self.config); c['partitions'][1]['offset'] = 5
        self.assertFalse(wf.check_manifest(c)['valid'])

    def test_reject_unaccounted_byte(self):
        c=copy.deepcopy(self.config); c['partitions'][1]['source_backed_bytes'] = 0
        self.assertFalse(wf.check_manifest(c)['valid'])

    def test_reject_false_source_only_claim(self):
        c=copy.deepcopy(self.config); c['partitions'][1]['source_only_complete'] = True
        self.assertFalse(wf.check_manifest(c)['valid'])

    def test_reject_invalid_semantics(self):
        c=copy.deepcopy(self.config); c['partitions'][0]['semantic_status'] = 'VERIFIED'
        self.assertFalse(wf.check_manifest(c)['valid'])

    def test_reject_duplicate_name(self):
        c=copy.deepcopy(self.config); c['partitions'][1]['name'] = 'b0'
        self.assertFalse(wf.check_manifest(c)['valid'])

    def test_reject_unsupported_schema(self):
        c=copy.deepcopy(self.config); c['schema'] = 'something-else'
        self.assertFalse(wf.check_manifest(c)['valid'])

    def test_reject_per_partition_digest_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td, 'original.bin'); p.write_bytes(self.raw)
            c=copy.deepcopy(self.config); c['partitions'][0]['sha256'] = '0'*64
            self.assertFalse(wf.check_manifest(c, p)['valid'])


class GuardTests(unittest.TestCase):
    def test_stops_after_two_non_improvements(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td,'target.s'); p.write_text('NOP\n')
            state = wf.guard_init([p], 2)
            wf.guard_record(state, 70, 'a')
            self.assertEqual(state['status'], 'CONTINUE')
            wf.guard_record(state, 70, 'b')
            self.assertEqual(state['status'], 'CONTINUE')
            wf.guard_record(state, 69, 'c')
            self.assertEqual(state['status'], 'STOP')
            with self.assertRaises(ValueError): wf.guard_record(state, 95, 'd')

    def test_improvement_resets_stalls(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td,'target.s'); p.write_text('NOP\n')
            state = wf.guard_init([p], 2)
            for score in (80,79,81,80): wf.guard_record(state, score, str(score))
            self.assertEqual(state['status'],'CONTINUE')
            self.assertEqual(state['stalls'], 1)

    def test_reject_changed_target(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td,'target.s'); p.write_text('NOP\n')
            state=wf.guard_init([p],2)
            p.write_text('RET\n')
            with self.assertRaisesRegex(ValueError, 'locked reference changed'):
                wf.guard_record(state, 100, 'cheat')
            self.assertEqual(state['attempts'], [])

    def test_reject_missing_target(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td,'target.s'); p.write_text('NOP\n')
            state=wf.guard_init([p],2)
            p.unlink()
            with self.assertRaisesRegex(ValueError,'missing'):
                wf.guard_record(state, 99, 'bad')

    def test_reject_non_finite_or_outside_score(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td,'target.s'); p.write_text('NOP\n')
            state=wf.guard_init([p],2)
            for score in (float('nan'),float('inf'),101,-1):
                with self.assertRaises(ValueError):
                    wf.guard_record(state,score,'invalid')

    def test_reject_reset_existing_guard(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td,'target.s'); p.write_text('NOP\n')
            state=Path(td,'state.json')
            cli=[sys.executable,str(ROOT/'workflow.py'),'guard-init','--state',str(state),'--lock',str(p)]
            self.assertEqual(subprocess.run(cli,capture_output=True).returncode,0)
            self.assertNotEqual(subprocess.run(cli,capture_output=True).returncode,0)

    def test_stop_exit_code_and_state_persistence(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td,'target.s'); p.write_text('NOP\n')
            state=Path(td,'state.json')
            command=[sys.executable,str(ROOT/'workflow.py')]
            self.assertEqual(subprocess.run(command+['guard-init','--state',str(state),'--lock',str(p)],capture_output=True).returncode,0)
            for score, label, expected in [(85,'first',0),(85,'second',0),(80,'third',3)]:
                got=subprocess.run(command+['guard-record','--state',str(state),'--score',str(score),'--label',label],capture_output=True)
                self.assertEqual(got.returncode,expected,got.stderr)
            self.assertEqual(wf.load(state)['status'],'STOP')


class ContextTests(unittest.TestCase):
    def test_bank_identity_prevents_false_callers(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            (p/'syms.json').write_text(json.dumps({'symbols':[{'name':'routine','address_space':'ROM','physical_bank':6,'cpu_address':'9932'}]}))
            (p/'refs.json').write_text(json.dumps({'references':[
                {'from_bank':0,'from_cpu':'2000','target_cpu':'9932','proven_target_bank':6},
                {'from_bank':0,'from_cpu':'2003','target_cpu':'9932','proven_target_bank':7},
                {'from_bank':0,'from_cpu':'2006','target_cpu':'9932','proven_target_bank':None},
            ]}))
            m={'context_sources':{'symbols':'syms.json','references':'refs.json'}}
            mpath=p/'manifest.json'; mpath.write_text(json.dumps(m))
            result=wf.context(m,mpath,6,0x9932,12)
            self.assertEqual(result['incoming_refs_total'],1)
            self.assertEqual(result['symbols_at_address'][0]['name'],'routine')

    def test_context_clips_long_refs(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            refs=[{'from_bank':0,'from_cpu':f'{100+i:04X}','target_cpu':'9932','proven_target_bank':6} for i in range(20)]
            (p/'refs.json').write_text(json.dumps({'references':refs}))
            m={'context_sources':{'references':'refs.json'}}
            result=wf.context(m,p/'manifest.json',6,0x9932,3)
            self.assertEqual(result['incoming_refs_total'],20)
            self.assertEqual(len(result['incoming_proven_static_refs']),3)


if __name__=='__main__':
    unittest.main()
