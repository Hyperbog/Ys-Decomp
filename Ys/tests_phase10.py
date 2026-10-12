#!/usr/bin/env python3
"""Phase 10B: independent Z80 encoder, physical mapper layout and anti-tamper gates."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
from tools import rebuild_phase10 as work
from tools.z80_roundtrip_phase10 import encode, assemble
from tools.z80_regions import decode


def gate(condition, explanation):
    if not condition:
        raise AssertionError(explanation)
    print('PASS:', explanation)


def must_fail(fn, explanation):
    try:
        fn()
    except (AssertionError, ValueError, IndexError, KeyError):
        gate(True, explanation)
    else:
        raise AssertionError('Unexpected acceptance: '+explanation)


def run(rom_path):
    rom = rom_path.read_bytes()
    manifest = json.loads((ROOT/'manifest.json').read_text())
    gate(len(rom) == 0x40000 and hashlib.sha256(rom).hexdigest() == manifest['sha256'],
         'unaltered source ROM SHA-256 and size')

    cases = [
        ('jr nz,$06DA', 0x06E3, '20F5'),
        ('djnz $06DA', 0x06E5, '10F3'),
        ('bit 2,(iy-2)', 0x8100, 'FDCBFE56'),
        ('rst $0028', 0x8100, 'EF'),
        ('ld a,(ix+17)', 0x8100, 'DD7E11'),
        ('add ix,bc', 0x8100, 'DD09'),
        ('add iy,de', 0x8100, 'FD19'),
        ('rld', 0x8100, 'ED6F'),
        ('rl d', 0x8100, 'CB12'),
        ('ld (ix-3),$5A', 0x8100, 'DD36FD5A'),
    ]
    for text, pc, expected in cases:
        assert encode(text, pc) == bytes.fromhex(expected), (text, encode(text, pc).hex(), expected)
    gate(True, '10 independent opcode encoding vectors, including RLD/RL D distinction')

    for instruction, pc in [('jrz $0400', 0x100), ('jr z,$0700', 0x100),
                            ('ld a,(ix+180)', 0x100), ('made_up $01', 0x100)]:
        must_fail(lambda op=instruction, addr=pc: encode(op, addr), f'reject invalid opcode: {instruction}')

    rows = work.read_listings()
    gate(len(rows) == 4960 and sum(len(r[3]) for r in rows) == 10188,
         '4,960 unique physical instruction addresses / 10,188 bytes')
    bank_stats = work.grouped(rows)
    gate(sorted(bank_stats) == [0,1,2,4,7,8,10,12],
         'explicit bank inventory and 16-KiB address mapping')

    # Independent source-ROM instruction-length check, not based on the encoder.
    for offset, pc, text, opcodes, source in rows:
        end, disasm = decode(rom, offset)
        assert end == offset + len(opcodes), (hex(offset), text, disasm, end)
    gate(True, 'independent original Z80 decoder agrees with all 4,960 boundaries')

    report = work.compare(rom)
    gate(report['matching_instructions'] == 4960 and
         report['newly_assembled_distinct_bytes'] == 10188 and
         report['phase9_overlap'] == 61 and
         report['total_distinct_assembler_matched_bytes'] == 10238,
         'all generated ASM assembles to source ROM bytes; unique union includes Phase 9')
    gate((ROOT/'phase10/roundtrip_report.json').read_text() ==
         json.dumps(report, indent=2) + '\n', 'committed report reproducibility')

    # Must reject ROM mutations, even if the unmodified listing is present.
    altered = bytearray(rom)
    altered[0x0260] ^= 1
    must_fail(lambda: work.compare(bytes(altered)), 'reject one-byte ROM mutation')
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        asm = tmpdir/'src'
        shutil.copytree(work.SOURCE, asm)
        path = asm/'bank00.asm'
        original = path.read_text()
        gate('call $03A9' in original, 'source to mutate has correct branch')
        path.write_text(original.replace('call $03A9', 'call $03A8', 1))
        must_fail(lambda: work.compare(rom, source=asm),
                  'reject incorrect ASM operand before any matching claim')

        fake = tmpdir/'listing'
        for name in work.LISTINGS:
            dest = fake/name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT/name, dest)
        path = fake/work.LISTINGS[0]
        original = path.read_text()
        path.write_text(original.replace('CD A9 03', 'CD A8 03', 1))
        must_fail(lambda: work.compare(rom, root=fake, source=work.SOURCE),
                  'reject incorrect listing byte independently of encoder')
        path.write_text(original.replace('00260 0260', '00260 0261', 1))
        must_fail(lambda: work.read_listings(fake),
                  'reject wrong fixed-bank CPU/ROM address mapping')
        path.write_text(original + '\n' + next(line for line in original.splitlines()
                                                  if line.startswith('00260 0260')) + '\n')
        must_fail(lambda: work.read_listings(fake), 'reject duplicate/overlapping instruction spans')

    sample, symbols = assemble('org $06E3\njr nz,$06DA\ndjnz $06DA\n')
    gate([sample[a] for a in range(0x06E3,0x06E7)] == list(bytes.fromhex('20F510F3')),
         'complete source-to-bytes assembly on original relative branch span')
    print('PHASE 10B: PASS')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python tests_phase10.py /path/to/source.sms')
    run(Path(sys.argv[1]))
