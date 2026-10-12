#!/usr/bin/env python3
"""Run the Phase 1 positive and negative verification checks.

Requires the exact ROM identified in manifest.json. No ROM is copied to Git.
Usage: python Ys/tests_check.py "/path/to/own/Ys (USA, Europe).sms"
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
VERIFIER = HERE / 'tools' / 'verify.py'


def verify(root, rom):
    return subprocess.run(
        [sys.executable, str(root / 'tools' / 'verify.py'), str(rom)],
        capture_output=True, text=True, check=False,
    )


def require(test, label):
    if not test:
        raise RuntimeError('FAILED: ' + label)
    print('PASS:', label)


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    rom = Path(sys.argv[1]).resolve()
    expected = json.loads((HERE / 'manifest.json').read_text())['sha256']
    require(hashlib.sha256(rom.read_bytes()).hexdigest() == expected,
            'reference ROM matches manifest SHA-256')

    baseline = verify(HERE, rom)
    require(baseline.returncode == 0, 'clean ROM and listing accepted: '\
            + baseline.stderr.strip())

    with tempfile.TemporaryDirectory(prefix='ys_verify_') as temp:
        root = Path(temp)
        (root / 'src').mkdir()
        (root / 'tools').mkdir()
        for name in ('manifest.json', 'src/bank00_boot.lst', 'tools/verify.py'):
            shutil.copy2(HERE / name, root / name)

        altered = bytearray(rom.read_bytes())
        altered[0] ^= 0x01
        bad_rom = root / 'mutated.sms'
        bad_rom.write_bytes(altered)
        failed_rom = verify(root, bad_rom)
        require(failed_rom.returncode != 0 and 'Wrong ROM SHA-256' in failed_rom.stderr,
                'altered ROM rejected by fingerprint')

        listing = root / 'src' / 'bank00_boot.lst'
        original = listing.read_text()
        require('0000  F3' in original, 'baseline listing first byte found')
        listing.write_text(original.replace('0000  F3', '0000  00', 1))
        failed_listing = verify(root, rom)
        require(failed_listing.returncode != 0 and 'Listing mismatch' in failed_listing.stderr,
                'altered disassembly listing rejected by byte comparison')

    print('PASS: Phase 1 regression suite (3 acceptance/rejection scenarios)')


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError) as error:
        raise SystemExit(str(error)) from error
