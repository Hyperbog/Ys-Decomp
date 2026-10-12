#!/usr/bin/env python3
"""Phase 9B: independent Z80 assembly, graphics upload and mutation gates."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
SCRIPTS = ('z80_subset_asm_phase9.py', 'vdp_upload_phase9.py')
SECTIONS = [(0x05F2, 0x0624), (0x06C1, 0x06D4),
            (0x06D4, 0x06E8), (0x0BA1, 0x0BB7)]


def require(cond, message):
    assert cond, message
    print('PASS:', message)


def run(root, script, rom):
    return subprocess.run([sys.executable, str(root/'tools'/script), str(rom), '--check'],
                          capture_output=True, text=True)


def fails(root, script, rom, context):
    completed = run(root, script, rom)
    require(completed.returncode != 0, context)
    return completed.stderr + completed.stdout


def check(path):
    from tools import z80_subset_asm_phase9 as assembler
    from tools.z80_regions import decode
    from tools.vdp_upload_phase9 import analyze as analyze_uploads

    rom = path.read_bytes()
    manifest = json.loads((ROOT/'manifest.json').read_text())
    require(len(rom) == 0x40000 and hashlib.sha256(rom).hexdigest() == manifest['sha256'],
            '256 KiB source ROM identity verified')
    report_text, report, emitted = assembler.analyze(rom)
    require(report_text == (ROOT/'phase9/assembly_report.json').read_text(),
            'assembly report reproduced independently from source')
    require(report['total_assembled_bytes'] == 111 and report['span_count'] == 4,
            'exactly 111 assembled bytes in four nonoverlapping ranges')
    require(run(ROOT, SCRIPTS[0], path).returncode == 0,
            'restricted two-pass Z80 assembly --check succeeds')
    require(run(ROOT, SCRIPTS[1], path).returncode == 0,
            'graphics uploader --check succeeds')

    memory, spans, labels = assembler.assemble(assembler.SOURCE.read_text())
    require(spans == SECTIONS and memory == emitted and len(labels) == 11,
            'section addresses, assembler output and symbols agree')
    require(labels['VDPFillWordPattern.WordLoop'] == 0x06DA and
            labels['VDPExpandBank3PairPlanes.BlockLoop'] == 0x0BA7,
            'critical word and tile loop targets located at correct addresses')
    require(rom[0x06E3:0x06E7] == bytes.fromhex('20 f5 10 f3') and
            all((pc + 2 + int.from_bytes(rom[pc+1:pc+2], 'little', signed=True)) == 0x06DA
                for pc in (0x06E3, 0x06E5)),
            'both original relative branches target $06DA')
    for (first, last), row in zip(SECTIONS, report['sections']):
        payload = bytes(emitted[a] for a in range(first, last))
        assert row['start'] == f'{first:04X}'
        assert row['end_exclusive'] == f'{last:04X}'
        assert row['bytes'] == len(payload)
        assert row['sha256'] == hashlib.sha256(payload).hexdigest()
        assert payload == rom[first:last]
        # The ROM-backed decoder is separate from the assembly emitter.
        cursor = first
        while cursor < last:
            nxt, _ = decode(rom, cursor)
            assert cursor in emitted and nxt <= last and nxt > cursor
            cursor = nxt
        assert cursor == last
    require(True, 'independent decoder aligns at every assembled instruction boundary')
    require(not (set(memory) & set(range(0x06E8, 0x0BA1))),
            'gaps between assembled spans are not falsely claimed as rebuilt code')

    graphics_text, graphics = analyze_uploads(rom)
    require(graphics_text == (ROOT/'phase9/vdp_uploads.json').read_text(),
            'VDP upload report reproduced from actual call-site operand bytes')
    require(len(graphics['vdp_uploads']) == 4 and
            graphics['total_source_bytes_with_repeats'] == 3248 and
            graphics['distinct_source_bytes'] == 1184 and
            graphics['total_vdp_output_bytes_with_repeats'] == 6496 and
            graphics['distinct_new_rom_bytes'] == 0,
            'four bank-3 uploads, source union and no double-counted bytes')

    for desc, source in [('unsupported mnemonic', 'org $0100\nfoo\n'),
                         ('duplicate label', 'org $0100\nX:\nX:\nret\n'),
                         ('overlapping regions', 'org $0100\nret\norg $0100\nnop\n'),
                         ('out-of-range JR', 'org $0100\njr nz,$0400\n')]:
        try:
            assembler.assemble(source)
        except ValueError:
            pass
        else:
            raise AssertionError(f'Assembler did not reject {desc}')
    require(True, 'unsupported, duplicate, overlapping and out-of-range inputs rejected')

    with tempfile.TemporaryDirectory(prefix='ys_phase9b_') as directory:
        temp = Path(directory)
        copy = temp/'Ys'
        shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        source = copy/'src/phase9_vdp.asm'
        old = source.read_text()
        faulty = old.replace('.WordLoop:\n    ld a,l', '    ld a,l\n.WordLoop:', 1)
        assert faulty != old
        source.write_text(faulty)
        failure = fails(copy, SCRIPTS[0], path, 'Phase 9A off-by-one branch-label regression rejected')
        require('06E4' in failure, 'regression reports the precise original mismatch $06E4')
        source.write_text(old.replace('ld a,$03', 'ld a,$02', 1))
        fails(copy, SCRIPTS[0], path, 'changed immediate opcode rejected')
        source.write_text(old)
        tool = copy/'tools/z80_subset_asm_phase9.py'
        baseline = tool.read_text()
        assert "'outi':0xa3" in baseline
        tool.write_text(baseline.replace("'outi':0xa3", "'outi':0xa2", 1))
        fails(copy, SCRIPTS[0], path, 'modified encoder opcode rejected')
        tool.write_text(baseline)
        output = copy/'phase9/assembly_report.json'
        original = output.read_text()
        output.write_text(original.replace('"total_assembled_bytes": 111',
                                           '"total_assembled_bytes": 112', 1))
        fails(copy, SCRIPTS[0], path, 'tampered assembly report rejected')
        output.write_text(original)
        output = copy/'phase9/vdp_uploads.json'
        original = output.read_text()
        output.write_text(original.replace('"distinct_source_bytes": 1184',
                                           '"distinct_source_bytes": 1185', 1))
        fails(copy, SCRIPTS[1], path, 'tampered upload analysis rejected')
        output.write_text(original)
        badrom = temp/'bad.sms'
        changed = bytearray(rom)
        changed[0x06E4] ^= 1
        badrom.write_bytes(changed)
        for tool in SCRIPTS:
            fails(copy, tool, badrom, f'{tool}: changed ROM rejected')
    print('PASS Phase 9B suite completed')


if __name__ == '__main__':
    try:
        if len(sys.argv) != 2:
            raise ValueError('Usage: tests_phase9.py original.sms')
        check(Path(sys.argv[1]).resolve())
    except (AssertionError, ValueError, OSError, IndexError) as error:
        sys.exit('FAIL Phase 9B: ' + str(error))
