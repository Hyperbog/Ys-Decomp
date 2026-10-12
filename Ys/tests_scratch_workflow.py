#!/usr/bin/env python3
"""Regression checks for the offline function-level matching workflow."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
from scratch_compare import compare, file_offset, ROM_LENGTH


def fails(fn, expected=(ValueError,)):
    try:
        fn()
    except expected:
        return
    raise AssertionError('Invalid input was accepted')


def run(rom):
    source = (ROOT / 'src/phase13/bank07_unrolled_vdp.asm').read_text()
    baseline = compare(rom, source, 7)
    assert baseline['exact_match']
    assert baseline['matching_bytes'] == 1345
    assert baseline['emitted_bytes'] == 1345
    assert baseline['mismatching_bytes'] == 0
    assert file_offset(7, 0x8180) == 0x1C180
    assert file_offset(1, 0x4000) == 0x04000
    assert file_offset(0, 0x0000) == 0x00000
    print('PASS unchanged ROM and bank-7 1,345-byte assembly region')

    changed = source.replace('outi', 'nop ', 1)
    assert changed != source
    negative = compare(rom, changed, 7)
    assert not negative['exact_match']
    assert negative['mismatching_bytes'] >= 1
    assert negative['differences'][0]['rom_offset'] == '1C180' or negative['mismatching_bytes'] > 1
    print('PASS detects changed mnemonic without trusting source annotations')

    mutated = bytearray(rom)
    mutated[0x1C180] ^= 1
    fails(lambda: compare(bytes(mutated), source, 7))
    fails(lambda: compare(rom[:-1], source, 7))
    fails(lambda: compare(rom, source, 1))
    fails(lambda: file_offset(7, 0x4000))
    fails(lambda: file_offset(16, 0x8000))
    fails(lambda: compare(rom, 'org $8180\n', 7))
    print('PASS rejects wrong ROM, bank mismatch, invalid slot and empty source')
    print('LOCAL MATCHING WORKFLOW: PASS')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: tests_scratch_workflow.py ROM.sms')
    data = Path(sys.argv[1]).read_bytes()
    assert len(data) == ROM_LENGTH
    run(data)
