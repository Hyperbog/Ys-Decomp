#!/usr/bin/env python3
"""Ys SMS strict source-overlay rebuild, coverage audit, and cross-reference index.

The original ROM supplies *all* unimplemented bytes. This is NOT a ROM rebuild
from source alone and is NOT independent third-party assembler validation.
Fails closed on bad ROM, source drift, address conflicts, and output mismatch.
No commercial ROM bytes are added to the repository by this program by default.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from z80_roundtrip_phase10 import assemble, encode  # noqa: E402

EXPECTED_SHA = '02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9'
ROM_SIZE = 0x40000
BANK_SIZE = 0x4000
SOURCES = tuple([(f'src/phase11_roundtrip/bank{i:02d}.asm', i) for i in
                 (0, 1, 2, 4, 6, 7, 8, 10, 12)] + [
                     ('src/phase12/bank06_sprite_handlers.asm', 6),
                     ('src/phase13/bank07_unrolled_vdp.asm', 7),
                 ])
CONTROL_FLOW = {'call', 'jp', 'jr', 'djnz', 'rst'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def offset(bank, pc):
    if not 0 <= bank < 16:
        raise ValueError(f'invalid physical bank {bank}')
    origin = 0 if bank == 0 else 0x4000 if bank == 1 else 0x8000
    if not origin <= pc < origin + BANK_SIZE:
        raise ValueError(f'bank {bank}: CPU ${pc:04X} outside its expected slot')
    return bank * BANK_SIZE + pc - origin


def validated_rom(rom):
    if len(rom) != ROM_SIZE or sha(rom) != EXPECTED_SHA:
        raise ValueError('Original ROM missing/wrong: expected 256 KiB and Ys SHA-256')
    return rom


def scan_references(source, bank, owners):
    """Static syntax-only references. Do not infer dynamic mapper state."""
    pc = None
    references = []
    for line in source.splitlines():
        t = line.split(';', 1)[0].strip()
        if not t or t.endswith(':'):
            continue
        if t.lower().startswith('org '):
            pc = int(t[4:].strip().replace('$', '0x'), 16)
            continue
        if pc is None:
            raise ValueError('Instruction before ORG')
        parts = t.lower().split(None, 1)
        mnemonic = parts[0]
        raw = encode(t, pc)
        if mnemonic in CONTROL_FLOW and len(parts) == 2:
            operand = parts[1].split(',')[-1].strip()
            if re.fullmatch(r'\$[0-9a-f]{1,4}', operand):
                target = int(operand[1:], 16)
                if target < 0x4000:
                    tb, status = 0, 'fixed_bank0'
                elif target < 0x8000:
                    tb, status = None, 'slot1_mapper_not_proven'
                elif bank >= 2:
                    tb, status = None, 'slot2_mapper_not_proven'
                else:
                    tb, status = None, 'slot2_mapper_not_proven'
                # Even when the candidate's slot equals the current source,
                # an interrupt or call may change mapper state before use.
                references.append(dict(from_bank=bank, from_cpu=f'{pc:04X}',
                    mnemonic=mnemonic, target_cpu=f'{target:04X}',
                    proven_target_bank=tb, mapping_evidence=status))
        pc += len(raw)
    return references


def build(rom, root=ROOT, specs=SOURCES):
    validated_rom(rom)
    rebuilt = bytearray(rom)  # Template: unknown code/data preserved from input
    written = {}
    per_file = []
    references = []
    for rel, bank in specs:
        source = (root / rel).read_text(encoding='utf8')
        built, labels = assemble(source)
        if not built:
            raise ValueError(f'empty assembly module: {rel}')
        if any(bank == prior['bank'] and rel == prior['source'] for prior in per_file):
            raise ValueError(f'duplicate source module: {rel}')
        for pc, emitted in sorted(built.items()):
            at = offset(bank, pc)
            if at in written:
                raise ValueError(f'overlapping modules: {written[at]} / {rel} at {at:05X}')
            if emitted != rom[at]:
                raise ValueError(f'ASM/ROM mismatch {rel} physical ${at:05X}, '
                                 f'CPU ${pc:04X}: source {emitted:02X}, ROM {rom[at]:02X}')
            written[at] = rel
            rebuilt[at] = emitted
        per_file.append(dict(source=rel, bank=bank, emitted_bytes=len(built),
                             label_count=len(labels)))
        references.extend(scan_references(source, bank, written))
    if bytes(rebuilt) != rom:
        raise AssertionError('overlay output differs from original ROM')
    bank_totals = []
    for bank in range(16):
        lo = bank * BANK_SIZE
        bank_totals.append(dict(bank=bank,
            sourced_code_bytes=sum(lo <= n < lo + BANK_SIZE for n in written),
            template_bytes=BANK_SIZE - sum(lo <= n < lo + BANK_SIZE for n in written),
            reconstructed_bank_sha256=sha(rebuilt[lo:lo + BANK_SIZE])))
    result = {
        'schema': 'ys-phase14-source-overlay-v1',
        'rom_sha256': EXPECTED_SHA,
        'complete_image_length': len(rebuilt),
        'complete_output_sha256': sha(rebuilt),
        'matched_source_bytes': len(written),
        'unknown_template_bytes': ROM_SIZE - len(written),
        'matching_source_fraction': round(len(written) / ROM_SIZE, 8),
        'template_fraction': round((ROM_SIZE - len(written)) / ROM_SIZE, 8),
        'sources': per_file, 'banks': bank_totals,
        'cross_references': {
            'total': len(references),
            'fixed_bank0': sum(r['mapping_evidence'] == 'fixed_bank0' for r in references),
            'mapper_unresolved': sum(r['mapping_evidence'] != 'fixed_bank0' for r in references),
        },
        'external_assembler_verified': False,
        'source_only_build': False,
        'notes': 'All unimplemented ROM bytes come from supplied source ROM, not assembly. '
                 'Exact full-image equality is a template integrity check, NOT complete decompilation.',
    }
    refs = {'schema': 'ys-phase14-crossref-v1',
            'interpretation': 'Syntactic Z80 targets; mapper-dependent banks not inferred',
            'references': references}
    return bytes(rebuilt), result, refs


def independent_sjasmplus(rom, executable):
    """Optional *actual external process* check of the contiguous bank-7 block.

    No bundled/cached substitute is accepted: an absent executable is an error.
    SJAsmPlus --raw emits source machine code; no original bytes are given to it.
    """
    path = shutil.which(executable)
    if not path:
        raise FileNotFoundError(f'external SJAsmPlus executable unavailable: {executable}')
    with tempfile.TemporaryDirectory(prefix='ys_sjasmplus_') as directory:
        output = Path(directory) / 'assembled.bin'
        source = ROOT / 'src/phase13/bank07_unrolled_vdp.asm'
        run = subprocess.run([path, '--nologo', '--raw=' + str(output), str(source)],
                             capture_output=True, text=True, timeout=60)
        if run.returncode or not output.is_file():
            raise RuntimeError(f'SJAsmPlus failed ({run.returncode}): {run.stderr[-1500:]}')
        generated = output.read_bytes()
        # Single contiguous ORG $8180 .. $86C0, physical bank 7.
        expected = rom[0x1C180:0x1C6C1]
        if generated != expected:
            raise ValueError(f'External assembly mismatch: {len(generated)} vs {len(expected)} bytes')
        return {'external_assembler': path, 'verified_module': source.relative_to(ROOT).as_posix(),
                'external_matched_bytes': len(generated)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path, help='locally supplied original 256-KiB Ys ROM')
    parser.add_argument('--out', type=Path, help='optional reconstructed .sms (keep outside Git)')
    parser.add_argument('--report', type=Path, help='write metadata without ROM bytes')
    parser.add_argument('--references', type=Path, help='write syntactic cross-references')
    parser.add_argument('--sjasmplus', metavar='EXE', help='optional external check of Phase 13 module')
    args = parser.parse_args()
    original = args.rom.read_bytes()
    rebuilt, report, refs = build(original)
    if args.sjasmplus:
        external = independent_sjasmplus(original, args.sjasmplus)
        report['external_assembler_verified'] = True
        report['external_verification'] = external
    if args.out:
        if args.out.resolve() == args.rom.resolve():
            parser.error('refusing to overwrite original ROM')
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(rebuilt)
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    if args.references:
        args.references.write_text(json.dumps(refs, indent=2) + '\n')
    print(f"Overlay matched {report['matched_source_bytes']:,} Z80 bytes; "
          f"{report['unknown_template_bytes']:,} bytes sourced from original ROM")
    print('Full-image SHA-256:', report['complete_output_sha256'])
    print('NOT a standalone ROM rebuild; no external assembler used')


if __name__ == '__main__':
    main()
