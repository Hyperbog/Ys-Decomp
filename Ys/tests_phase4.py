#!/usr/bin/env python3
"""Phase 4 ROM-backed audio-engine tests; no emulator or assembler assertions.

Usage: python tests_phase4.py /path/to/original.sms
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent


def check(ok, description):
    if not ok:
        raise AssertionError(description)
    print('PASS:', description)


def scan(root, rom):
    return subprocess.run([sys.executable, str(root/'tools/z80_regions.py'),
                           str(rom), '--phase', '4', '--check'],
                          capture_output=True, text=True)


def occupied(phase):
    cfg = json.loads((ROOT/f'phase{phase}/regions.json').read_text())
    offsets = set()
    for r in cfg['code']:
        offsets.update(range(int(r['start'], 16), int(r['end_exclusive'], 16)))
    for r in cfg['data']:
        s = int(r['start'], 16)
        offsets.update(range(s, s + len(bytes.fromhex(r['hex']))))
    return offsets


def main(rom):
    data = rom.read_bytes()
    check(hashlib.sha256(data).hexdigest() == json.loads(
        (ROOT/'manifest.json').read_text())['sha256'], 'ROM fingerprint')
    check(scan(ROOT, rom).returncode == 0, 'fixed Phase 4 listing and data anchors')
    result = subprocess.run([sys.executable, str(ROOT/'tools/check_phase4_asm.py'),
                             str(rom)], capture_output=True, text=True)
    check(result.returncode == 0, 'partial command-dispatch assembly text and labels')
    earlier = set(range(0x102)) | occupied(2) | occupied(3)
    current = occupied(4)
    check(len(current) == 603 and not earlier.intersection(current),
          '603 distinct new bytes without Phase 1–3 overlap')
    check(data[0x80F1:0x80F7] == bytes.fromhex('08 20 02 08 C9 08') and
          data[0x80FE:0x8103] == bytes.fromhex('30 05 79 D3 F0'),
          'continued channel path switches to FM register output')
    check(data[0x818D:0x819B] == bytes.fromhex(
          'C5 0A E6 F0 1F 1F 1F 1F 21 B1 81 CD 20 83') and
          data[0x819D:0x81B1] == bytes.fromhex(
          '06 12 0E F1 0D ED A3 0C CD 83 88 ED A3 CD 83 88 20 F2 C1 C9'),
          'FM preset uses upper nibble and outputs 18 port bytes')
    check([int.from_bytes(data[p:p+2], 'little') for p in (0x81B1, 0x81B3)]
          == [0x81B5, 0x81C7] and
          len(data[0x81B5:0x81C7]) == len(data[0x81C7:0x81D9]) == 18,
          'two 18-byte FM preset streams with explicit pointers')
    check([int.from_bytes(data[p:p+2], 'little') for p in (0x8CFE, 0x8D00)]
          == [0x8112, 0x814C] and
          data[0x81F5:0x8204] == bytes.fromhex(
          'D6 BC 87 4F 06 00 21 FE 8C 09 7E 23 66 6F E9'),
          'BC/BD dispatches through two-word target table')
    check(data[0x8204:0x821B] == bytes.fromhex(
          'D6 81 F8 F5 CD 03 88 F1 06 00 4F 21 40 8D 09 F5 7E 32 61 DE 32 62 DE'),
          'commands 81..9F load timing fields from 8D40 table')
    check(data[0x82D9:0x82F4] == bytes.fromhex(
          '7E E6 0F 47 23 C5 E5 DD E1 ED A0 ED A0 ED A0 ED A0 ED A0 ED A0 ED A0 ED A0 ED A0'),
          'command record setup performs nine LDI transfers')
    check(data[0x808F:0x80AD] == bytes.fromhex(
          '1A CB 7F C8 E6 7F 21 02 8D 3D 06 00 4F 09 CB 7E 28 0C 1A 32 63 DE AF 12 E1 E1 C3 13 80 C9'),
          'queued command high-bit and priority lookup / stack skip')
    # Negative tests verify snapshots are actually enforced, not just generated.
    with tempfile.TemporaryDirectory(prefix='ys_phase4_') as td:
        temp = Path(td)/'Ys'
        shutil.copytree(ROOT, temp, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        listing = temp/'phase4/code.lst'
        listing.write_text(listing.read_text().replace('080F1', 'XXXXX', 1))
        outcome = scan(temp, rom)
        check(outcome.returncode != 0, 'mutated Phase 4 listing rejected')
        shutil.copy2(ROOT/'phase4/code.lst', listing)
        path = temp/'phase4/regions.json'
        cfg = json.loads(path.read_text())
        cfg['data'][0]['hex'] = '00' + cfg['data'][0]['hex'][2:]
        path.write_text(json.dumps(cfg))
        outcome = scan(temp, rom)
        check(outcome.returncode != 0, 'mutated FM preset data anchor rejected')
        asm = temp/'src/bank02_sound_dispatch.asm'
        asm.write_text(asm.read_text().replace('cp $a0', 'cp $a1', 1))
        outcome = subprocess.run([sys.executable, str(ROOT/'tools/check_phase4_asm.py'),
                                  str(rom), str(asm)], capture_output=True, text=True)
        check(outcome.returncode != 0, 'mutated command-dispatch source rejected')
    print('PASS: Phase 4 suite complete (14 checks)')


if __name__ == '__main__':
    try:
        if len(sys.argv) != 2:
            raise ValueError('Usage: tests_phase4.py original.sms')
        main(Path(sys.argv[1]).resolve())
    except (OSError, ValueError, AssertionError) as exc:
        sys.exit(f'FAIL: {exc}')
