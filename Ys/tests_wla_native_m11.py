#!/usr/bin/env python3
"""Native assembler adapter tests; do not require third-party source archive."""
import io
from pathlib import Path
import sys
import subprocess
from unittest.mock import patch
import tempfile
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'tools'))
from wla_native_m11 import archive_type, safe_archive_extract, clone_public_source, PINNED_REF, PUBLIC_REPO


class NativeWlaTests(unittest.TestCase):
    def test_missing_archive(self):
        with self.assertRaises(FileNotFoundError):
            archive_type(Path('/missing-wla-source.zip'))

    def test_windows_binary_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'wla_windows.zip'
            with ZipFile(p, 'w') as z:
                z.writestr('win/wla-z80.exe', b'MZxxxx')
                z.writestr('win/wlalink.exe', b'MZxxxx')
            with self.assertRaisesRegex(ValueError, 'Windows PE binary'):
                archive_type(p)

    def test_missing_cmake_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'random.zip'
            with ZipFile(p,'w') as z:z.writestr('README.md','hello')
            with self.assertRaisesRegex(ValueError, 'CMakeLists'):
                archive_type(p)

    def test_zip_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'traversal.zip'
            with ZipFile(p,'w') as z:
                z.writestr('wla-dx/CMakeLists.txt','project(wla)')
                z.writestr('wla-dx/README.md','WLA')
                z.writestr('../escape-file.txt','bad')
            with self.assertRaisesRegex(ValueError, 'Unsafe'):
                safe_archive_extract(p,Path(td)/'out')

    def test_public_clone_is_pinned_and_noninteractive(self):
        with tempfile.TemporaryDirectory() as td:
            calls = []
            def fake_git(cmd, **kwargs):
                calls.append((cmd, kwargs))
                dest = Path(cmd[-1]); dest.mkdir()
                (dest/'CMakeLists.txt').write_text('project(wla)')
                (dest/'README.md').write_text('WLA')
            with patch('wla_native_m11.subprocess.run', side_effect=fake_git):
                root = clone_public_source(td)
            self.assertEqual(len(calls), 1)
            self.assertIn('--depth', calls[0][0])
            self.assertEqual(calls[0][0][calls[0][0].index('--branch') + 1], PINNED_REF)
            self.assertIn(PUBLIC_REPO, calls[0][0])
            self.assertEqual(calls[0][1]['env']['GIT_TERMINAL_PROMPT'], '0')
            self.assertTrue((root/'CMakeLists.txt').is_file())
            with patch('wla_native_m11.subprocess.run') as run:
                self.assertEqual(clone_public_source(td), root)
                run.assert_not_called()

    def test_public_clone_failure_gives_offline_instruction(self):
        with tempfile.TemporaryDirectory() as td:
            error = subprocess.CalledProcessError(128, 'git clone',
                                                  stderr='Could not resolve host: github.com')
            with patch('wla_native_m11.subprocess.run', side_effect=error):
                with self.assertRaisesRegex(RuntimeError, 'source archive'):
                    clone_public_source(td)
            self.assertFalse((Path(td)/'wla-dx-v10.7-public').exists())

    def test_valid_source_layout_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'source.zip'
            with ZipFile(p,'w') as z:
                z.writestr('wla-dx-v10.7/CMakeLists.txt','project(wla)')
                z.writestr('wla-dx-v10.7/README.md','WLA')
            root=safe_archive_extract(p,Path(td)/'out')
            self.assertEqual(root.name,'wla-dx-v10.7')


if __name__ == '__main__':unittest.main(verbosity=2)
