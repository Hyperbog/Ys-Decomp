#!/usr/bin/env python3
"""Full ROM overlay with Z80 mnemonic code and source-only DB/DW tables.

The 256-KiB result still requires the user's original ROM for all uncovered
bytes. In particular, there is no claim of a full source-only reconstruction.
"""
import argparse
import hashlib
import json
from pathlib import Path

from build_sms_phase14 import ROOT, SOURCES, ROM_SIZE, validated_rom, offset, build as old_build
from source_tables_phase15 import SOURCES as TABLES, assemble_data, load_verified_sources
from z80_roundtrip_phase10 import assemble


def build(rom, root=ROOT, table_overrides=None):
    validated_rom(rom)
    result, old, refs = old_build(rom, root=root)
    rebuilt=bytearray(result)
    old_owners=set()
    for rel, bank in SOURCES:
        code, _ = assemble((root / rel).read_text(encoding='utf8'))
        old_owners.update(offset(bank, pc) for pc in code)
    assert len(old_owners)==old['matched_source_bytes']==14025
    table_owners=set()
    by_bank=[]
    committed = load_verified_sources(root) if table_overrides is None else None
    for bank, rel in TABLES.items():
        source=(root/rel).read_text(encoding='utf-8') if table_overrides is None else table_overrides[bank]
        code, labels = assemble_data(source) if table_overrides is not None else (
            committed[bank]['bytes'], committed[bank]['labels'])
        n=0
        for pc, byte in code.items():
            at=offset(bank,pc)
            if at in old_owners:
                raise ValueError(f'table/assembler overlap at ROM ${at:05X}')
            if at in table_owners:
                raise ValueError(f'overlapping table data at ROM ${at:05X}')
            if rom[at]!=byte:
                raise ValueError(f'data source/ROM mismatch bank {bank} CPU ${pc:04X}: '
                                 f'source {byte:02X}, ROM {rom[at]:02X}')
            rebuilt[at]=byte
            table_owners.add(at)
            n+=1
        by_bank.append({'bank':bank,'source':rel,'bytes':n,'labels':labels})
    output=bytes(rebuilt)
    if output!=rom:
        raise AssertionError('complete generated ROM differs from input')
    assert len(table_owners)==678 and not table_owners & old_owners
    total=len(old_owners|table_owners)
    per_bank=[]
    for bank in range(16):
        start,end=bank*0x4000,(bank+1)*0x4000
        code=sum(start<=v<end for v in old_owners)
        tables=sum(start<=v<end for v in table_owners)
        per_bank.append({'bank':bank,'z80_source_bytes':code,
                         'structured_source_bytes':tables,
                         'fallback_bytes':0x4000-code-tables})
    return output,{
        'schema':'ys-phase15-source-overlay-v1',
        'rom_sha256':hashlib.sha256(rom).hexdigest(),
        'rom_bytes':ROM_SIZE,
        'assembly_source_bytes':len(old_owners),
        'standalone_data_source_bytes':len(table_owners),
        'all_source_backed_bytes':total,
        'original_rom_fallback_bytes':ROM_SIZE-total,
        'source_backed_percentage':round(total/ROM_SIZE*100,4),
        'source_table_modules':by_bank,
        'banks':per_bank,
        'source_only_complete_rom':False,
        'external_z80_assembler_verified':False,
        'prior_candidate_classification_bytes':58133,
        'coverage_note':'Structured source bytes were already ROM-classified in prior phases; '
                        'do not add them again to candidate classification coverage.',
        'sha256_output':hashlib.sha256(output).hexdigest(),
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path)
    p.add_argument('--report',type=Path,default=ROOT/'phase15/build_report.json')
    p.add_argument('--out',type=Path,help='optional rebuilt ROM outside version control')
    p.add_argument('--verify',action='store_true')
    a=p.parse_args()
    if a.out and a.out.resolve()==a.rom.resolve():
        p.error('will not overwrite original ROM')
    orig=a.rom.read_bytes()
    output,report=build(orig)
    if a.verify:
        if json.loads(a.report.read_text())!=report:
            raise SystemExit('Phase 15 report mismatch')
    else:
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(json.dumps(report,indent=2)+'\n')
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_bytes(output)
    print(f"Matched {report['assembly_source_bytes']} code + "
          f"{report['standalone_data_source_bytes']} standalone data bytes; "
          f"fallback {report['original_rom_fallback_bytes']} bytes")
    print('SHA-256:',report['sha256_output'])


if __name__=='__main__':
    main()
