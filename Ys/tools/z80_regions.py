#!/usr/bin/env python3
"""Deterministic, bounded Z80 ROM scanner. No unbounded code/data inference.

python tools/z80_regions.py /path/to/Ys.sms --write
python tools/z80_regions.py /path/to/Ys.sms --check

Ranges and bank identities are maintained in phaseN/regions.json. The program
intentionally refuses unhandled opcodes rather than disguising them as code.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parents[1]
REG = ('b', 'c', 'd', 'e', 'h', 'l', '(hl)', 'a')
RP = ('bc', 'de', 'hl', 'sp')
RP2 = ('bc', 'de', 'hl', 'af')
CC = ('nz', 'z', 'nc', 'c', 'po', 'pe', 'p', 'm')
ALU = ('add a,', 'adc a,', 'sub ', 'sbc a,', 'and ', 'xor ', 'or ', 'cp ')
ROT = ('rlca', 'rrca', 'rla', 'rra', 'daa', 'cpl', 'scf', 'ccf')
CB_OP = ('rlc', 'rrc', 'rl', 'rr', 'sla', 'sra', 'sll', 'srl')


def u16(data, pos):
    return data[pos] | data[pos + 1] << 8


def byte(n):
    return f'${n:02X}'


def word(n):
    return f'${n:04X}'


def rel(data, p):
    disp = data[p] - 256 if data[p] >= 128 else data[p]
    return word((p + 1 + disp) & 0xFFFF)


def decode(data, pos, offset_to_cpu=0):
    """Return (end_offset, mnemonic); translate relative targets to CPU addresses."""
    o = pos
    pref = None
    if data[pos] in (0xDD, 0xFD):
        pref = 'ix' if data[pos] == 0xDD else 'iy'
        pos += 1
    op = data[pos]
    pos += 1
    if op == 0xCB:
        disp = None
        if pref:
            disp = data[pos]
            pos += 1
        cb = data[pos]
        pos += 1
        x, y, z = cb >> 6, (cb >> 3) & 7, cb & 7
        r = REG[z]
        if pref:
            off = disp - 256 if disp >= 128 else disp
            r = f'({pref}{off:+d})'
        if x == 0:
            txt = f'{CB_OP[y]} {r}'
        elif x == 1:
            txt = f'bit {y},{r}'
        else:
            txt = f'{"res" if x == 2 else "set"} {y},{r}'
        if pref and z != 6 and x != 1:
            txt += f',{REG[z]}'
        return pos, txt
    if op == 0xED:
        ed = data[pos]
        pos += 1
        x, y, z = ed >> 6, (ed >> 3) & 7, ed & 7
        p, q = y >> 1, y & 1
        if x == 1:
            if z == 0:
                txt = f'in {REG[y]},(c)' if y != 6 else 'in (c)'
            elif z == 1:
                txt = f'out (c),{REG[y]}' if y != 6 else 'out (c),0'
            elif z == 2:
                txt = f'{"adc" if q else "sbc"} hl,{RP[p]}'
            elif z == 3:
                value = u16(data, pos)
                pos += 2
                txt = f'ld {RP[p]},({word(value)})' if q else f'ld ({word(value)}),{RP[p]}'
            elif z == 4:
                txt = 'neg'
            elif z == 5:
                txt = 'reti' if y == 1 else 'retn'
            elif z == 6:
                txt = f'im {(0,0,1,2,0,0,1,2)[y]}'
            else:
                m = ('ld i,a', 'ld r,a', 'ld a,i', 'ld a,r', 'rrd', 'rld')
                if y >= len(m):
                    raise ValueError(f'Unhandled ED {ed:02X} at {o:04X}')
                txt = m[y]
        elif x == 2 and z <= 3 and y >= 4:
            table = ('ldi','cpi','ini','outi','ldd','cpd','ind','outd',
                     'ldir','cpir','inir','otir','lddr','cpdr','indr','otdr')
            txt = table[(y - 4)*4 + z]
        else:
            raise ValueError(f'Unhandled ED {ed:02X} at {o:04X}')
        return pos, txt
    x, y, z = op >> 6, (op >> 3) & 7, op & 7
    p, q = y >> 1, y & 1
    r = list(REG)
    pairs = list(RP)
    stack_pairs = list(RP2)
    if pref:
        r[4], r[5], r[6] = pref + 'h', pref + 'l', f'({pref})'
        pairs[2], stack_pairs[2] = pref, pref
        # Indexed (IX/IY+d) opcodes consume a displacement *before* immediates.
        needs_disp = ((x in (1, 2) and (y == 6 or z == 6)) or
                      (x == 0 and y == 6 and z in (4, 5, 6)))
        if needs_disp and op != 0x76:
            d = data[pos]
            pos += 1
            d = d - 256 if d >= 128 else d
            r[6] = f'({pref}{d:+d})'
    def n8():
        nonlocal pos
        v = data[pos]
        pos += 1
        return byte(v)
    def n16():
        nonlocal pos
        v = u16(data, pos)
        pos += 2
        return word(v)
    def branch():
        nonlocal pos
        v = (int(rel(data, pos)[1:], 16) + offset_to_cpu) & 0xFFFF
        pos += 1
        return word(v)
    if x == 0:
        if z == 0:
            txt = ('nop', "ex af,af'")[y] if y < 2 else (
                ('djnz ', 'jr ', 'jr nz,', 'jr z,', 'jr nc,', 'jr c,')[y - 2]
                + branch())
        elif z == 1:
            txt = f'add {pairs[2]},{pairs[p]}' if q else f'ld {pairs[p]},{n16()}'
        elif z == 2:
            if p == 0: target = '(bc)'
            elif p == 1: target = '(de)'
            else: target = f'({n16()})'
            if p < 2: txt = f'ld {"a,"+target if q else target+",a"}'
            elif p == 2: txt = f'ld {pairs[2]},{target}' if q else f'ld {target},{pairs[2]}'
            else: txt = f'ld a,{target}' if q else f'ld {target},a'
        elif z == 3:
            txt = f'{"dec" if q else "inc"} {pairs[p]}'
        elif z in (4, 5):
            txt = f'{"inc" if z == 4 else "dec"} {r[y]}'
        elif z == 6:
            txt = f'ld {r[y]},{n8()}'
        else:
            txt = ROT[y]
    elif x == 1:
        txt = 'halt' if op == 0x76 else f'ld {r[y]},{r[z]}'
    elif x == 2:
        txt = f'{ALU[y]}{r[z]}'
    else:
        if z == 0: txt = f'ret {CC[y]}'
        elif z == 1:
            if q == 0: txt = f'pop {stack_pairs[p]}'
            else: txt = ('ret', 'exx', f'jp ({pairs[2]})', f'ld sp,{pairs[2]}')[p]
        elif z == 2: txt = f'jp {CC[y]},{n16()}'
        elif z == 3:
            if y == 0: txt = f'jp {n16()}'
            elif y == 2: txt = f'out ({n8()}),a'
            elif y == 3: txt = f'in a,({n8()})'
            elif y == 4: txt = f'ex (sp),{pairs[2]}'
            elif y == 5: txt = 'ex de,hl'
            elif y == 6: txt = 'di'
            elif y == 7: txt = 'ei'
            else: raise ValueError(f'Unexpected prefix at {o:04X}')
        elif z == 4: txt = f'call {CC[y]},{n16()}'
        elif z == 5:
            if q == 0: txt = f'push {stack_pairs[p]}'
            elif p == 0: txt = f'call {n16()}'
            else: raise ValueError(f'Unexpected prefix at {o:04X}')
        elif z == 6: txt = f'{ALU[y]}{n8()}'
        else: txt = f'rst {word(y * 8)}'
    # Correct base opcode x=0,z=0: only y=2..7 use a relative operand.
    return pos, txt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    parser.add_argument('--phase', type=int, choices=(2, 3, 4), default=2,
                        help='bounded region set (default: 2)')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write', action='store_true')
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    manifest = json.loads((BASE / 'manifest.json').read_text())
    assert hashlib.sha256(rom).hexdigest() == manifest['sha256'], 'ROM SHA-256 mismatch'
    cfg = json.loads((BASE / f'phase{args.phase}' / 'regions.json').read_text())
    out = [f'; Phase {args.phase}: ROM-backed, explicit bounded ranges. Not an assembled ROM.',
           '; Offset  CPU     Bytes              Decoded Z80 instruction', '']
    total = 0
    occupied = set()
    for region in cfg['code']:
        first, last = int(region['start'], 16), int(region['end_exclusive'], 16)
        bank = region['bank']
        out.append(f'; {region["name"]} | bank {bank} | file {first:05X}-{last-1:05X}')
        for addr in range(first, last):
            assert addr not in occupied, f'Overlapping regions at {addr:05X}'
            occupied.add(addr)
        ptr = first
        while ptr < last:
            offset_to_cpu = (region['slot'] - bank) * 0x4000
            nxt, decoded = decode(rom, ptr, offset_to_cpu)
            assert nxt <= last, f'Instruction crosses boundary at {ptr:05X}'
            cpu = (ptr - bank * 0x4000) + (region['slot'] * 0x4000)
            chunk = rom[ptr:nxt].hex(' ').upper()
            out.append(f'{ptr:05X}  {cpu:04X}  {chunk:<18} {decoded}')
            total += nxt - ptr
            ptr = nxt
        out.append('')
    data_total = 0
    for region in cfg['data']:
        start = int(region['start'], 16)
        expected = bytes.fromhex(region['hex'])
        assert rom[start:start+len(expected)] == expected, (f'Data mismatch at {start:05X}')
        for addr in range(start, start+len(expected)):
            assert addr not in occupied, f'Code/data overlap at {addr:05X}'
            occupied.add(addr)
        out.append(f'; data: {region["name"]} ({region["note"]})')
        out.append(f'{start:05X}  ----  {expected.hex(" ").upper()}')
        out.append('')
        data_total += len(expected)
    result = '\n'.join(out) + '\n'
    path = BASE / f'phase{args.phase}' / 'code.lst'
    if args.write:
        path.write_text(result)
    else:
        assert result == path.read_text(), f'Phase {args.phase} disassembly differs from committed listing'
    print(f'PASS: {len(cfg["code"])} bounded regions / {total} instruction bytes /'
          f' {data_total} anchored data bytes',
          '(generated)' if args.write else '(exact listing match)')


if __name__ == '__main__':
    try: main()
    except (OSError, ValueError, AssertionError, IndexError) as ex:
        sys.exit(f'FAIL: {ex}')
