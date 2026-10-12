#!/usr/bin/env python3
"""Phase 2 bounded Z80 scan, code/data anchors, and negative regression checks."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROM_SHA = json.loads((HERE / 'manifest.json').read_text())['sha256']


def run(root, rom):
    return subprocess.run([sys.executable, str(root/'tools/z80_regions.py'),
                           str(rom), '--check'], capture_output=True, text=True)


def require(ok, detail):
    if not ok:
        raise AssertionError(detail)
    print('PASS:', detail)


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    rom = Path(sys.argv[1]).resolve()
    data = rom.read_bytes()
    require(hashlib.sha256(data).hexdigest() == ROM_SHA, 'input ROM fingerprint')
    baseline = run(HERE, rom)
    require(baseline.returncode == 0, f'Phase 2 snapshot: {baseline.stderr.strip()}')
    require(data[0x8841:0x8843] == bytes.fromhex('E1 E5'),
            'bank 2 $8803 falls through into $8842 (no intervening RET)')
    require(data[0x0782:0x079A] == b'Ancient Ys Vanished Omen',
            'exact 24-byte SRAM signature')
    targets = [int.from_bytes(data[a:a+2], 'little') for a in range(0x01AC, 0x01B4, 2)]
    require(targets == [0x01B4, 0x01BA, 0x01D7, 0x03B8],
            'interrupt dispatch targets at $01AC-$01B3')
    with tempfile.TemporaryDirectory(prefix='ys_phase2_') as d:
        root = Path(d)
        (root / 'tools').mkdir()
        (root / 'phase2').mkdir()
        for f in ('manifest.json','tools/z80_regions.py','phase2/regions.json',
                  'phase2/code.lst'):
            shutil.copy2(HERE / f, root / f)
        altered = bytearray(data)
        altered[0x0102] ^= 1
        bad = root / 'mutated.sms'
        bad.write_bytes(altered)
        result = run(root, bad)
        require(result.returncode != 0 and 'ROM SHA-256 mismatch' in result.stderr,
                'wrong ROM rejected')
        listing = root / 'phase2/code.lst'
        clean = listing.read_text()
        listing.write_text(clean.replace('ld a,($C021)', 'nop', 1))
        result = run(root, rom)
        require(result.returncode != 0 and 'listing' in result.stderr,
                'altered instruction snapshot rejected')
        listing.write_text(clean)
        cfg = root / 'phase2/regions.json'
        original = cfg.read_text()
        cfg.write_text(original.replace('B4 01 BA 01 D7 01 B8 03',
                                        'B5 01 BA 01 D7 01 B8 03', 1))
        result = run(root, rom)
        require(result.returncode != 0 and 'Data mismatch' in result.stderr,
                'altered data anchor rejected')
    print('PASS: Phase 2 regression suite (8 checks)')


if __name__ == '__main__':
    try: main()
    except (AssertionError, OSError) as exc:
        sys.exit(f'FAIL: {exc}')
