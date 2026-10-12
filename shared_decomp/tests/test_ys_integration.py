"""Check that the reusable manifest is synchronized with the committed Ys ledger."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]

class YsIntegrationTests(unittest.TestCase):
    def test_snapshot_matches_source_ledger(self):
        ledger=json.loads((ROOT/'Ys/whole_system/build_report_m10.json').read_text())
        manifest=json.loads((ROOT/'shared_decomp/examples/ys_sms_manifest.json').read_text())
        self.assertEqual(manifest['binary']['size'],ledger['rom_bytes'])
        self.assertEqual(manifest['binary']['sha256'],ledger['rom_sha256'])
        self.assertEqual(len(manifest['partitions']),len(ledger['per_bank']))
        for a,b in zip(manifest['partitions'],ledger['per_bank']):
            self.assertEqual(a['offset'],b['bank']*16384)
            self.assertEqual(a['length'],16384)
            self.assertEqual(a['source_backed_bytes'],b['source_backed_bytes'])
            self.assertEqual(a['fallback_bytes'],b['original_rom_fallback_bytes'])
            self.assertEqual(a['source_only_complete'],b['source_only_complete'])
            self.assertEqual(a['sha256'],b['sha256'])

if __name__ == '__main__': unittest.main()
