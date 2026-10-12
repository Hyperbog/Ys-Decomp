#!/usr/bin/env python3
"""Phase 3: banked-code classification, state vectors, and SRAM bounds.

Usage: python tests_phase3.py /path/to/Ys.sms
These tests check byte claims, NOT emulator behavior or assembled equivalence.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent


def check(ok, label):
    if not ok:
        raise AssertionError(label)
    print('PASS:', label)


def scanner(root, rom, phase=3):
    return subprocess.run(
        [sys.executable, str(root / 'tools/z80_regions.py'), str(rom),
         '--phase', str(phase), '--check'], capture_output=True, text=True)


def ranges(root, phase):
    cfg = json.loads((root / f'phase{phase}/regions.json').read_text())
    covered = set()
    for region in cfg['code']:
        covered.update(range(int(region['start'], 16),
                             int(region['end_exclusive'], 16)))
    for region in cfg['data']:
        p = int(region['start'], 16)
        covered.update(range(p, p + len(bytes.fromhex(region['hex']))))
    return covered


def main(rom):
    source = rom.read_bytes()
    expected = json.loads((HERE / 'manifest.json').read_text())['sha256']
    check(hashlib.sha256(source).hexdigest() == expected, 'exact input ROM SHA-256')
    for n in (2, 3):
        outcome = scanner(HERE, rom, n)
        check(outcome.returncode == 0, f'Phase {n} listing: {outcome.stderr.strip()}')

    asm_check = subprocess.run(
        [sys.executable, str(HERE / 'tools/check_partial_asm.py'), str(rom)],
        capture_output=True, text=True)
    check(asm_check.returncode == 0,
          f'partial bank-2 assembly matches decoded mnemonics: {asm_check.stderr.strip()}')

    previous = set(range(0x0000, 0x0102)) | ranges(HERE, 2)
    current = ranges(HERE, 3)
    check(not previous.intersection(current) and len(current) == 541,
          'Phase 3 adds 541 non-overlapping classified ROM bytes')

    entries = [int.from_bytes(source[a:a + 2], 'little')
               for a in range(0x01EB, 0x01FD, 2)]
    check(entries == [0x01FD, 0x01FE, 0x0288, 0x02B1, 0x02C2,
                      0x032A, 0x0339, 0x035D, 0x0389],
          'nine original secondary dispatch targets')
    check(source[0x01DF:0x01E6] == bytes.fromhex('3A 05 C1 21 EB 01 CF')
          and source[0x01FD] == 0xC9,
          'C105 indexes table at 01EB via RST 08; entry zero is RET')
    check(source[0x01DA:0x01DF] == bytes.fromhex('3E 03 32 FF FF')
          and source[0x01C6:0x01CE] == bytes.fromhex('3E 07 32 FF FF C3 19 88'),
          'explicit mapper slot 2 selection: banks 3 and 7')
    check(source[0x800A:0x8016] == bytes.fromhex(
          'CD 67 80 CD 80 80 CD C0 80 CD D9 81'),
          'bank 2 8000 updater calls four original routines')
    check(source[0x806F:0x8080] == bytes.fromhex(
          '3A 62 DE 77 21 79 DE 11 20 00 06 06 34 19 10 FC C9'),
          'DE61 timer reload and six +20h record increments')
    check(source[0x079A:0x07A2] == bytes.fromhex(
          '3A FC FF F6 08 32 FC FF') and
          source[0x07B4:0x07C1] == bytes.fromhex(
          '21 10 80 11 11 80 01 EE 1F 36 00 ED B0'),
          'SRAM mapping enabled and zero-fill parameters verified')
    check((0x8010 + 0x1FEE) == 0x9FFE and
          source[0x07C1:0x07CC] == bytes.fromhex(
          '21 82 07 11 10 80 01 18 00 ED B0') and
          source[0x0782:0x079A] == b'Ancient Ys Vanished Omen',
          'SRAM initialized 8010–9FFE, 24-byte signature at 8010–8027')

    with tempfile.TemporaryDirectory(prefix='ys_phase3_') as tmp:
        root = Path(tmp)
        (root / 'phase3').mkdir()
        (root / 'tools').mkdir()
        for file in ('manifest.json', 'phase3/regions.json',
                     'phase3/code.lst', 'tools/z80_regions.py'):
            shutil.copy2(HERE / file, root / file)
        config = root / 'phase3/regions.json'
        original = config.read_text()
        config.write_text(original.replace('FD 01 FE 01 88 02',
                                           'FD 01 FF 01 88 02', 1))
        check(scanner(root, rom).returncode != 0,
              'modified secondary jump table rejected')
        config.write_text(original)
        listing = root / 'phase3/code.lst'
        listing.write_text(listing.read_text().replace('exx', 'nop', 1))
        check(scanner(root, rom).returncode != 0,
              'modified banked-code listing rejected')
        asm = root / 'bank02_mutated.asm'
        asm.write_text((HERE / 'src/bank02_update.asm').read_text().replace(
            'call $80c0', 'call $80c1', 1))
        bad_source = subprocess.run(
            [sys.executable, str(HERE / 'tools/check_partial_asm.py'), str(rom),
             str(asm)], capture_output=True, text=True)
        check(bad_source.returncode != 0 and 'source ' in bad_source.stderr,
              'modified annotated assembly rejected')
    print('PASS: Phase 3 complete (15 checks)')


if __name__ == '__main__':
    try:
        if len(sys.argv) != 2:
            raise ValueError('Usage: python tests_phase3.py /path/to/Ys.sms')
        main(Path(sys.argv[1]).resolve())
    except (AssertionError, ValueError, OSError) as exc:
        sys.exit(f'FAIL: {exc}')
