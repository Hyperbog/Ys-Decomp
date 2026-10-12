#!/usr/bin/env python3
"""Bounded ROM-opcode execution of Ys SMS sprite record producer and SAT upload.

Runs fixed-bank $26F3 -> bank-6 $9932 -> fixed-bank $0427 with initialized
RAM. This is an isolated ROM instruction test, NOT a whole-game emulator.
Only additional Z80 instructions required by those particular paths are
implemented; all others retain Phase 18's fail-closed behavior.
"""
import argparse
import hashlib
import json
from pathlib import Path
from phase18_z80_trace import Machine, UnsupportedOpcode
from recover_bank6_records_phase11b import extract, emulate_record_buffers

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA = json.loads((ROOT / 'manifest.json').read_text())['sha256']
ORIGINS = ((0, 0), (17, 29), (240, 250))


class SpriteMachine(Machine):
    """A minimal extension for the exact caller and record-decoding opcode path."""
    def step(self):
        opcode = self.read(self.pc)
        extra = {0x3A, 0x87, 0x6F, 0x26, 0x66, 0x2C, 0x46, 0x48,
                 0x86, 0x12, 0x13, 0x41, 0x22, 0x2A, 0x36}
        if opcode not in extra and opcode != 0xED:
            return super().step()
        if opcode == 0xED and self.read((self.pc + 1) & 0xFFFF) == 0xA3:
            return super().step()
        self.ins_pc = self.pc
        op = self.fetch()
        if op == 0x3A:  # LD A,(nn)
            self.a = self.read(self.fetch_word())
        elif op == 0x87:  # ADD A,A
            self.a = (2*self.a) & 255
            self.z = self.a == 0
        elif op == 0x6F: self.l = self.a
        elif op == 0x26: self.h = self.fetch()
        elif op == 0x66: self.h = self.read(self.hl())
        elif op == 0x2C:  # INC L
            self.l = (self.l + 1) & 255
            self.z = self.l == 0
        elif op == 0x46: self.b = self.read(self.hl())
        elif op == 0x48: self.c = self.b
        elif op == 0x86:  # ADD A,(HL)
            self.a = (self.a + self.read(self.hl())) & 255
            self.z = self.a == 0
        elif op == 0x12: self.write(self.de(), self.a)
        elif op == 0x13:
            value = (self.de() + 1) & 0xFFFF
            self.d, self.e = value >> 8, value & 255
        elif op == 0x41: self.b = self.c
        elif op == 0x22:  # LD (nn),HL
            address = self.fetch_word()
            self.write(address, self.l)
            self.write((address + 1) & 0xFFFF, self.h)
        elif op == 0x2A:  # LD HL,(nn)
            address = self.fetch_word()
            self.set_hl(self.read(address) | (self.read((address+1)&0xFFFF)<<8))
        elif op == 0x36: self.write(self.hl(), self.fetch())
        elif op == 0xED:
            second = self.fetch()
            if second in (0x5B, 0x53):
                address = self.fetch_word()
                if second == 0x5B:  # LD DE,(nn)
                    self.e = self.read(address)
                    self.d = self.read((address+1)&0xFFFF)
                else:  # LD (nn),DE
                    self.write(address, self.e)
                    self.write((address+1)&0xFFFF, self.d)
            elif second == 0xA0:  # LDI: BC--, HL++, DE++, does not change Z
                self.write(self.de(), self.read(self.hl()))
                self.set_hl(self.hl()+1)
                de = (self.de()+1)&0xFFFF
                self.d, self.e = de>>8, de&255
                bc = (((self.b<<8)|self.c)-1)&0xFFFF
                self.b, self.c = bc>>8, bc&255
            else:
                raise UnsupportedOpcode(f'Unsupported ED opcode {second:02X} at {self.ins_pc:04X}')
        else:
            raise UnsupportedOpcode(f'Unsupported opcode {op:02X} at {self.ins_pc:04X}')
        self.steps += 1


def trace(rom):
    if len(rom) != 0x40000 or hashlib.sha256(rom).hexdigest() != EXPECTED_SHA:
        raise ValueError('ROM SHA-256 fingerprint mismatch')
    records = extract(rom)
    if len(records) != 64:
        raise ValueError('Expected 64 bank-6 sprite records')
    entries = []
    all_sat_hashes = hashlib.sha256()
    for first_origin, second_origin in ORIGINS:
        for record in records:
            index = record['directory_index']
            count = record['count']
            y, xt = emulate_record_buffers(record['decoded'], first_origin, second_origin)
            y_expected = bytearray([0xD0]*64)
            y_expected[:count] = y
            y_expected[count] = 0xD0
            xt_expected = bytearray(128)
            xt_expected[:2*count] = xt
            seeded = {
                0xDD00: bytes([0xD0]*64),
                0xDD40: bytes(128),
                0xC199: bytes([index]),
                0xC210: bytes([first_origin, second_origin]),
                0xC028: bytes.fromhex('CC CC CC CC'),
                0xC100: b'\xFF',
            }
            machine = SpriteMachine(rom, 0x26F3, ram=seeded, max_instructions=5000)
            machine.run(0x2710)
            producer_steps = machine.steps
            if machine.mapper_writes != [{'pc':'26F5','address':'FFFF','value':6}]:
                raise AssertionError('Producer caller mapper state unexpected')
            if machine.slot[2] != 6:
                raise AssertionError('Producer ran with incorrect bank')
            if machine.ram[0x1D00:0x1D40] != y_expected:
                raise AssertionError(f'Y buffer mismatch at record {index}')
            if machine.ram[0x1D40:0x1DC0] != xt_expected:
                raise AssertionError(f'X/tile buffer mismatch at record {index}')
            if machine.read(0xC028) | (machine.read(0xC029)<<8) != 0xDD00+count:
                raise AssertionError('Y producer pointer advancement wrong')
            if machine.read(0xC02A) | (machine.read(0xC02B)<<8) != 0xDD40+2*count:
                raise AssertionError('X/tile producer pointer advancement wrong')
            if machine.read(0xC100) != 0:
                raise AssertionError('Caller state byte was not cleared')
            # Run the actual fixed-bank 192-byte sprite table VDP uploader on
            # precisely the same machine state: no synthetic transfer bytes.
            machine.pc = 0x0427
            machine.push(0xE000)
            machine.run(0xE000)
            if machine.control != ['7F00','7F80']:
                raise AssertionError('Wrong SAT VDP control words')
            actual = bytes(value for _,value in machine.data_writes)
            expected = bytes(y_expected + xt_expected)
            if actual != expected:
                raise AssertionError(f'VDP output disagrees with producer at {index}')
            if len(machine.data_writes) != 192:
                raise AssertionError('Incorrect SAT transfer length')
            if any(addr != (0x3F00+i if i<64 else 0x3F80+i-64)
                   for i,(addr,_) in enumerate(machine.data_writes)):
                raise AssertionError('SAT port destination wrong')
            all_sat_hashes.update(actual)
            entries.append({
                'record_index': index, 'count': count,
                'first_origin': first_origin, 'second_origin': second_origin,
                'producer_instruction_steps': producer_steps,
                'sat_upload_instruction_steps': machine.steps-producer_steps,
                'mapper_value': 6,
                'y_pointer_end': f'{0xDD00+count:04X}',
                'xt_pointer_end': f'{0xDD40+2*count:04X}',
                'y_table_sha256': hashlib.sha256(y_expected).hexdigest(),
                'xt_table_sha256': hashlib.sha256(xt_expected).hexdigest(),
                'sat_output_sha256': hashlib.sha256(actual).hexdigest(),
            })
    if len(entries) != len(ORIGINS)*64:
        raise AssertionError('Record trace count unexpected')
    return {
        'schema':'ys-phase19-producer-sat-execution-v1',
        'rom_sha256':EXPECTED_SHA,
        'input_records':64,
        'origin_pairs':[list(x) for x in ORIGINS],
        'bounded_producer_and_sat_runs':len(entries),
        'sat_bytes_per_run':192,
        'total_sat_bytes_across_runs':192*len(entries),
        'concat_sat_sha256':all_sat_hashes.hexdigest(),
        'source_backed_bytes_added':0,
        'new_rom_bytes_classified':0,
        'limitations':[
            'Original opcodes executed with synthetic RAM record selection and origins',
            'Only the fixed-bank caller, bank-6 record producer, and SAT upload run',
            'Not gameplay execution, not full CPU/VDP emulation, and not cycle-accurate',
            'Other game setup, interrupts, sprites rendering and video mode unverified',
        ],
        'cases':entries,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom',type=Path)
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--write',action='store_true')
    modes.add_argument('--check',action='store_true')
    args=parser.parse_args()
    result=trace(args.rom.read_bytes())
    output=ROOT/'phase19/execution_report.json'
    if args.write:
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(result,indent=2)+'\n')
    elif json.loads(output.read_text())!=result:
        raise ValueError('Phase 19 trace report drift')
    print(f"PASS Phase19: {result['bounded_producer_and_sat_runs']} bank-6 producer -> SAT execution chains; {result['total_sat_bytes_across_runs']} traced output bytes")


if __name__=='__main__':
    main()
