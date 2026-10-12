#!/usr/bin/env python3
"""Conservative symbol and mapper-context database for Ys SMS.

A nearby constant mapper write proves a *static candidate* bank for the
immediately following instruction, but not its reachability or runtime state.
Never replace unknown dynamic mappings with an inferred bank.
"""
import argparse
import json
from pathlib import Path

from build_sms_phase14 import offset
from source_tables_phase15 import load_verified_sources

ROOT = Path(__file__).resolve().parents[1]

# Names describe evidence from ROM-access/dispatch analysis; names are not
# claims about original developer identifiers or emulator-executed paths.
CODE_LABELS = (
    ('ResetEntry', 0, 0x0000, 'startup'),
    ('InterruptMode1', 0, 0x0038, 'interrupt'),
    ('NonMaskableInterrupt', 0, 0x0066, 'interrupt'),
    ('InitializeSystem', 0, 0x0089, 'startup'),
    ('VDPSpriteTableUpload', 0, 0x0427, 'graphics'),
    ('VDPExpandedGraphicsUpload', 0, 0x0BA1, 'graphics'),
    ('SoundTick', 2, 0x8000, 'audio'),
    ('SpriteRecordConsumer', 6, 0x9932, 'sprite'),
    ('SpriteObjectHandler', 6, 0x9AF6, 'sprite'),
    ('UnrolledGraphicsUpload', 7, 0x8180, 'graphics'),
    ('GraphicsSlotUpdate', 7, 0x86C1, 'graphics'),
    ('GraphicsDispatch', 7, 0x8856, 'graphics'),
)
RAM_LABELS = (
    ('SpriteYBuffer', 0xDD00, 64, 'SAT Y-coordinate staging'),
    ('SpriteXTileBuffer', 0xDD40, 128, 'SAT X/tile staging'),
    ('WorkRecordBase', 0xC200, 0x330, '17 work slots, stride 0x30'),
)


def make():
    refs = json.loads((ROOT / 'phase14/crossrefs.json').read_text())['references']
    audit = json.loads((ROOT / 'phase8/mapper_audit.json').read_text())['mapper_audit']
    tables = load_verified_sources()
    symbols = []
    for name, bank, pc, subsystem in CODE_LABELS:
        symbols.append(dict(name=name, address_space='ROM', physical_bank=bank,
                            cpu_address=f'{pc:04X}', physical_offset=f'{offset(bank, pc):05X}',
                            kind='code_entry', subsystem=subsystem, confidence='static_code'))
    for bank, data in tables.items():
        for name, pc in data['labels'].items():
            symbols.append(dict(name=name, address_space='ROM', physical_bank=bank,
                                cpu_address=f'{pc:04X}', physical_offset=f'{offset(bank,pc):05X}',
                                kind='source_table', subsystem='metadata', confidence='source_reencoded'))
    for name, start, size, meaning in RAM_LABELS:
        symbols.append(dict(name=name, address_space='RAM', ram_address=f'{start:04X}',
                            byte_length=size, kind='ram_region', description=meaning,
                            confidence='static_access'))
    symbols.sort(key=lambda x:(x['address_space'], x.get('physical_bank',0),x.get('physical_offset',x.get('ram_address','')),x['name']))
    ids = [(r.get('physical_bank'),r.get('cpu_address'),r['name']) for r in symbols if r['address_space']=='ROM']
    assert len(ids)==len(set(ids))
    by_target={(s['physical_bank'],s['cpu_address']):s['name'] for s in symbols if s['address_space']=='ROM'}
    # Only annotate a *direct* call/jp whose instruction address is precisely
    # the 3-byte LD ($FFFF),A mapper selection's successor.
    direct = {}
    for row in audit:
        target = row.get('immediate_slot2_call_or_jump')
        newbank = row.get('bank_immediately_loaded')
        if newbank is None or target is None:
            continue
        written = int(row['write_offset'],16)
        if written >= 0x8000:
            continue
        caller_bank = 0 if written < 0x4000 else 1
        caller_pc = (written+3)  # fixed slots 0 and 1 match physical offsets
        direct[(caller_bank, f'{caller_pc:04X}',target)] = (newbank, row['write_offset'])
    enhanced = []
    candidate_count = 0
    known_symbol_count = 0
    for r in refs:
        item = dict(r)
        bank = r['proven_target_bank']
        hint = direct.get((r['from_bank'],r['from_cpu'],r['target_cpu']))
        if bank is None and hint and int(r['target_cpu'],16)>=0x8000:
            item['static_target_bank_candidate']=hint[0]
            item['static_bank_evidence']='immediate constant mapper-write at physical $'+hint[1]
            candidate_count += 1
            bank=hint[0]
        symbol = by_target.get((bank,r['target_cpu']))
        if symbol:
            item['target_symbol']=symbol
            known_symbol_count += 1
        enhanced.append(item)
    return {
        'schema':'ys-phase15-symbol-index-v1',
        'symbols':symbols,
        'summary':{'symbols':len(symbols),'rom_symbols':sum(s['address_space']=='ROM' for s in symbols),
                   'ram_symbols':len(RAM_LABELS), 'crossrefs':len(enhanced),
                   'static_mapper_candidates':candidate_count,
                   'references_to_named_symbols':known_symbol_count,
                   'unresolved_mapper_refs_prior':sum(r['proven_target_bank'] is None for r in refs),
                   'runtime_verified':False},
        'references':enhanced,
        'limitations':['Static candidates do not establish path reachability',
                       'ROM names describe reverse-engineering functions, not recovered original labels',
                       'Mapper state may be modified by called code or interrupts',
                       'Ambiguous slot 1 and 2 references are left unresolved']
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,default=ROOT/'phase15/symbols.json')
    p.add_argument('--verify',action='store_true')
    opts=p.parse_args()
    generated=make()
    if opts.verify:
        if json.loads(opts.out.read_text())!=generated:
            raise SystemExit('symbol ledger out-of-date')
    else:
        opts.out.parent.mkdir(parents=True,exist_ok=True)
        opts.out.write_text(json.dumps(generated,indent=2)+'\n')
    print(generated['summary'])


if __name__=='__main__':
    main()
