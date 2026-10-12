#!/usr/bin/env python3
"""Phase 5: fixed ROM/listing/data/CFG regression and negative controls."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent


def ok(test, name):
    if not test:
        raise AssertionError(name)
    print('PASS:', name)


def scan(root, rom):
    return subprocess.run([sys.executable, str(root/'tools/z80_cfg_phase5.py'),
                           str(rom), '--check'], capture_output=True, text=True)


def main(path):
    rom = path.read_bytes()
    manifest = json.loads((ROOT/'manifest.json').read_text())
    config = json.loads((ROOT/'phase5/regions.json').read_text())
    coverage = json.loads((ROOT/'phase5/coverage.json').read_text())
    ok(hashlib.sha256(rom).hexdigest() == manifest['sha256'], 'original ROM SHA-256')
    result = scan(ROOT, path)
    ok(result.returncode == 0, f'reproducible listing and metrics ({result.stderr.strip()})')

    listing = (ROOT/'phase5/code.lst').read_text()
    instructions = {}
    codebytes = set()
    for line in listing.splitlines():
        m = re.match(r'^([0-9A-F]{5}) ([0-9A-F]{4})  ((?:[0-9A-F]{2} )+)', line)
        if not m:
            continue
        pos = int(m.group(1), 16)
        words = bytes.fromhex(m.group(3))
        assert rom[pos:pos+len(words)] == words, f'listing differs at {pos:05X}'
        assert not codebytes.intersection(range(pos, pos+len(words)))
        codebytes.update(range(pos, pos+len(words)))
        instructions[pos] = len(words)
    ok(len(instructions) == 2055 and len(codebytes) == 4154,
       'independent instruction-byte listing check (2055 / 4154)')
    data_offsets = set()
    for d in config['data']:
        a, z = int(d['start'], 16), int(d['end_exclusive'], 16)
        assert hashlib.sha256(rom[a:z]).hexdigest() == d['sha256']
        assert not data_offsets.intersection(range(a, z))
        data_offsets.update(range(a, z))
    ok(len(data_offsets) == 780 and not codebytes.intersection(data_offsets),
       '780 non-overlapping, independently digest-anchored data bytes')
    ok(coverage['new_total_bytes'] == 4934 and coverage['cumulative_distinct_bytes'] == 7002,
       '4,934 new distinct ROM bytes, 7,002 cumulative')
    ok(coverage['new_code_bank0_bytes'] == 2499 and coverage['new_code_bank2_bytes'] == 1655,
       'bank-aware code-byte accounting')
    destinations = [int.from_bytes(rom[p:p+2], 'little') for p in range(0x8600, 0x8628, 2)]
    ok(len(destinations) == 20 and all(p in instructions for p in destinations),
       '20 event dispatch destinations correspond to decoded instruction starts')
    ok(rom[0x8C8F] == 0x80 and all(
       0xA000 <= int.from_bytes(rom[p:p+2], 'little') < 0xC000
       for p in range(0x8C90, 0x8CFE, 2)),
       'one music pointer directory marker and 55 bank-dependent addresses')
    ok(any('00DDA -> CPU 86C1' in edge for edge in coverage['unresolved_edges'])
       and 0x86C1 not in instructions,
       'unknown bank-0 to slot-2 call is not misclassified as bank-2 code')
    ok(rom[0x843E:0x8445] == bytes.fromhex('DD 7E 01 D3 F0 C6 10') and
       rom[0x8472:0x8479] == bytes.fromhex('DD 7E 01 C6 20 D3 F0'),
       'FM register-select hardware writes are ROM backed')

    with tempfile.TemporaryDirectory(prefix='ys_phase5_') as tmp:
        work = Path(tmp)/'Ys'
        shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        snapshot = work/'phase5/code.lst'
        initial = snapshot.read_text()
        snapshot.write_text(initial.replace('00260 0260', 'XXXXX 0260', 1))
        ok(scan(work, path).returncode != 0, 'mutated disassembly listing rejected')
        snapshot.write_text(initial)
        stats = work/'phase5/coverage.json'
        oldstats = stats.read_text()
        stats.write_text(oldstats.replace('"new_code_bytes": 4154', '"new_code_bytes": 4155', 1))
        ok(scan(work, path).returncode != 0, 'mutated coverage report rejected')
        stats.write_text(oldstats)
        anchor = work/'phase5/regions.json'
        raw_cfg = anchor.read_text()
        cfg = json.loads(raw_cfg)
        cfg['data'][0]['sha256'] = '0'*64
        anchor.write_text(json.dumps(cfg))
        ok(scan(work, path).returncode != 0, 'corrupt audio dispatch-table hash rejected')
        cfg = json.loads(raw_cfg)
        cfg['entrypoints'].append('8600')
        anchor.write_text(json.dumps(cfg))
        ok(scan(work, path).returncode != 0, 'code entrypoint inside anchored table rejected')
        anchor.write_text(raw_cfg)
        damaged = Path(tmp)/'bad.sms'
        changed = bytearray(rom)
        changed[0x8472] ^= 0x01
        damaged.write_bytes(changed)
        ok(scan(work, damaged).returncode != 0, 'modified ROM rejected')
    print('PASS: Phase 5 complete (15 substantive checks)')


if __name__ == '__main__':
    try:
        if len(sys.argv) != 2:
            raise ValueError('Usage: tests_phase5.py /path/to/original.sms')
        main(Path(sys.argv[1]).resolve())
    except (AssertionError, OSError, ValueError) as exc:
        sys.exit(f'FAIL Phase 5: {exc}')
