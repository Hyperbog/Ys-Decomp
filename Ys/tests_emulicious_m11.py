#!/usr/bin/env python3
"""Fast fail-closed Emulicious smoke/report tests; actual GUI run is separate."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
import emulicious_smoke_m11 as m


class EmulatorSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT / 'whole_system/emulicious_report_m11.json').read_text())

    def test_provenance(self):
        self.assertEqual(self.report['schema'], 'ys-emulicious-independent-boot-m11-v1')
        self.assertEqual(self.report['emulator'], 'Emulicious')
        self.assertEqual(len(self.report['jar_sha256']), 64)

    def test_source_rom_identity(self):
        self.assertEqual(self.report['rebuilt_rom_bytes'], 262144)
        self.assertEqual(self.report['rebuilt_rom_sha256'], m.ROM_SHA256)
        self.assertTrue(self.report['source_only_build'])

    def test_image_reference(self):
        self.assertTrue(self.report['boot_and_title_render_passed'])
        for key in ('title_observation', 'reference_title_observation'):
            o = self.report[key]
            self.assertEqual(o['logo_rgb_sha256'], m.TITLE_SHA256)
            self.assertEqual(o['roi'], list(m.TITLE_ROI))
            self.assertGreaterEqual(o['unique_colors'], 8)

    def test_no_unsupported_runtime_claim(self):
        for key in ('emulated_gameplay_verified', 'emulated_audio_verified',
                    'external_assembler_verified'):
            self.assertIs(self.report[key], False)

    def test_missing_jar_rejected(self):
        with self.assertRaises(FileNotFoundError):
            m.check_tools(Path('/nonexistent/emulicious-no-such-file.jar'))

    def test_invalid_capture_dimensions_rejected(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest('Pillow not installed')
        with tempfile.TemporaryDirectory() as td:
            png = Path(td) / 'tiny.png'
            Image.new('RGB', (40, 40)).save(png)
            with self.assertRaisesRegex(ValueError, 'dimensions too small'):
                m.title_observation(png)

    def test_uniform_capture_is_not_title(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest('Pillow not installed')
        with tempfile.TemporaryDirectory() as td:
            png = Path(td) / 'blank.png'
            Image.new('RGB', (800, 600)).save(png)
            o = m.title_observation(png)
            self.assertNotEqual(o['logo_rgb_sha256'], m.TITLE_SHA256)
            self.assertEqual(o['unique_colors'], 1)

    @mock.patch.object(m, 'check_tools')
    def test_bad_reference_rom_rejected_before_launch(self, _):
        image = bytes(262144)
        with tempfile.TemporaryDirectory() as td:
            reference = Path(td) / 'wrong.sms'
            reference.write_bytes(image)
            with self.assertRaisesRegex(ValueError, 'fingerprint mismatch'):
                m.run(Path('fake.jar'), reference)

    @mock.patch.object(m, 'check_tools')
    @mock.patch.object(m, 'build', return_value=(b'wrong', {}))
    def test_bad_rebuilt_rom_rejected_before_launch(self, _, __):
        with self.assertRaisesRegex(ValueError, 'fingerprint mismatch'):
            m.run(Path('fake.jar'))

    def test_digest_cryptographic(self):
        self.assertEqual(m.digest(b'abc'), hashlib.sha256(b'abc').hexdigest())


if __name__ == '__main__':
    unittest.main(verbosity=2)
