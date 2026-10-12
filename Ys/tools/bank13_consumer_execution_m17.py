#!/usr/bin/env python3
"""M17: bounded execution of actual Z80 Bank13 graphics consumer instructions.

The Bank0 dispatcher at $3ACC uses RST $18 to read the 50 pointers at
Bank13:$BF8A and calls Bank0:$0695 to decompress four source streams to VDP.
Only the precise verified opcode subset is implemented; everything else fails
closed. Mapper selection and entry registers are seeded, not gameplay-executed.
"""
import argparse
import hashlib
import json
from pathlib import Path

from build_sms_phase14 import ROOT, EXPECTED_SHA
from build_system_m10 import build
from phase18_z80_trace import Machine, UnsupportedOpcode

REPORT = ROOT / 'whole_system/bank13_consumer_execution_m17.json'
BANK = 13
DIRECTORY = 0xBF8A
LOADER = 0x3ACC
DECOMPRESSOR = 0x0695
VDP_START = 0x4120
PLANES = 4
PLANE_BYTES = 72
RECORD_BYTES = PLANES * PLANE_BYTES


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


class ConsumerMachine(Machine):
    """Full flag handling only for the actual $3ACC/$0695 code path.

    Carry flag is essential to distinguish RLE literals from repeated runs
    and detect VRAM destination wrap. Alternated AF is modeled independently.
    """

    def __init__(self, rom, pc, max_instructions=500000):
        super().__init__(rom, pc, max_instructions=max_instructions)
        self.carry = False
        self.alt_a = 0
        self.alt_z = False
        self.alt_carry = False
        self.bank13_read_count = 0
        self.executed_pc = set()

    def read(self, addr):
        val = super().read(addr)
        if 0x8000 <= (addr & 0xFFFF) <= 0xBFFF:
            self.bank13_read_count += 1
        return val

    def pair(self):
        return (self.b << 8) | self.c

    def set_pair(self, val):
        self.b, self.c = (val >> 8) & 255, val & 255

    def branch(self, cond):
        disp = self.fetch()
        if cond:
            self.pc = (self.pc + (disp if disp < 128 else disp - 256)) & 0xFFFF

    def step(self):
        self.ins_pc = self.pc
        if not (0x0018 <= self.pc < 0x0024 or
                0x0028 <= self.pc < 0x0031 or
                0x0695 <= self.pc < 0x06C1 or
                0x3ACC <= self.pc < 0x3AE3):
            raise UnsupportedOpcode(f'Unexpected execution target ${self.pc:04X}')
        self.executed_pc.add(self.pc)
        op = self.fetch()
        if op == 0x21:  # LD HL,nn
            self.set_hl(self.fetch_word())
        elif op == 0x01:  # LD BC,nn
            self.set_pair(self.fetch_word())
        elif op == 0x0E:  # LD C,n
            self.c = self.fetch()
        elif op == 0x41:  # LD B,C
            self.b = self.c
        elif op == 0x47:  # LD B,A
            self.b = self.a
        elif op == 0x79:  # LD A,C
            self.a = self.c
        elif op == 0x7E:  # LD A,(HL)
            self.a = self.read(self.hl())
        elif op == 0x66:  # LD H,(HL)
            self.h = self.read(self.hl())
        elif op == 0x6F:  # LD L,A
            self.l = self.a
        elif op == 0x7B:
            self.a = self.e
        elif op == 0x7A:
            self.a = self.d
        elif op == 0x5F:  # LD E,A
            self.e = self.a
        elif op == 0x23:
            self.set_hl(self.hl() + 1)
        elif op == 0x13:  # INC DE, preserves flags
            val = (self.de() + 1) & 0xFFFF
            self.d, self.e = val >> 8, val & 255
        elif op == 0x14:  # INC D, preserve C
            self.d = (self.d + 1) & 255
            self.z = self.d == 0
        elif op == 0x24:  # INC H, preserve C
            self.h = (self.h + 1) & 255
            self.z = self.h == 0
        elif op == 0x09:  # ADD HL,BC; preserve Z
            val = self.hl() + self.pair()
            self.carry = val > 0xFFFF
            self.set_hl(val & 0xFFFF)
        elif op == 0x83:  # ADD A,E
            val = self.a + self.e
            self.carry = val > 255
            self.a = val & 255
            self.z = self.a == 0
        elif op == 0x85:  # ADD A,L
            val = self.a + self.l
            self.carry = val > 255
            self.a = val & 255
            self.z = self.a == 0
        elif op == 0x87:  # ADD A,A
            val = self.a * 2
            self.carry = val > 255
            self.a = val & 255
            self.z = self.a == 0
        elif op == 0x07:  # RLCA, preserve Z
            self.carry = bool(self.a & 128)
            self.a = ((self.a << 1) | int(self.carry)) & 255
        elif op == 0xB7:  # OR A
            self.z = self.a == 0
            self.carry = False
        elif op == 0x3C:  # INC A, preserve C
            self.a = (self.a + 1) & 255
            self.z = self.a == 0
        elif op == 0x08:  # EX AF,AF'
            self.a, self.alt_a = self.alt_a, self.a
            self.z, self.alt_z = self.alt_z, self.z
            self.carry, self.alt_carry = self.alt_carry, self.carry
        elif op == 0xEB:  # EX DE,HL
            old_hl = self.hl()
            self.set_hl(self.de())
            self.d, self.e = old_hl >> 8, old_hl & 255
        elif op == 0xF5:
            self.push((self.a << 8) | (int(self.z) << 6) | int(self.carry))
        elif op == 0xF1:
            val = self.pop()
            self.a = val >> 8
            self.z = bool(val & 0x40)
            self.carry = bool(val & 1)
        elif op == 0xC5:
            self.push(self.pair())
        elif op == 0xC1:
            self.set_pair(self.pop())
        elif op == 0xD5:
            self.push(self.de())
        elif op == 0xD1:
            val = self.pop()
            self.d, self.e = val >> 8, val & 255
        elif op == 0xDF:  # RST 18h indexed little-endian pointer lookup
            self.push(self.pc)
            self.pc = 0x0018
        elif op == 0xEF:  # RST 28h SMS VDP control port
            self.push(self.pc)
            self.pc = 0x0028
        elif op == 0xCD:
            target = self.fetch_word()
            self.push(self.pc)
            self.pc = target
        elif op == 0xC9:
            self.pc = self.pop()
        elif op == 0x28:  # JR Z,e
            self.branch(self.z)
        elif op == 0x30:  # JR NC,e
            self.branch(not self.carry)
        elif op == 0x38:  # JR C,e
            self.branch(self.carry)
        elif op == 0x18:
            self.branch(True)
        elif op == 0x10:  # DJNZ,e does not alter flags
            self.b = (self.b - 1) & 255
            self.branch(self.b != 0)
        elif op == 0xD3:  # OUT (n),A
            self.port(self.fetch(), self.a)
        elif op == 0xF3 or op == 0xFB:  # DI/EI, interrupts not injected
            pass
        elif op == 0xCB:  # RES 7,B
            sub = self.fetch()
            if sub != 0xB8:
                raise UnsupportedOpcode(f'Unexpected CB opcode ${sub:02X}')
            self.b &= 0x7F
        else:
            raise UnsupportedOpcode(f'Unexpected opcode ${op:02X} at ${self.ins_pc:04X}')
        self.steps += 1


def decode_rle_plane(data, offset, expected_bytes=PLANE_BYTES):
    """Independent packet decoder for the direct Z80 output comparison."""
    out = bytearray()
    while True:
        if offset >= len(data):
            raise ValueError('Unterminated Bank13 RLE plane')
        op = data[offset]
        offset += 1
        if op == 0:
            if len(out) != expected_bytes:
                raise ValueError('Unexpected RLE plane length')
            return bytes(out), offset
        count = op & 127 if op & 128 else 1
        if count == 0 or offset + count > len(data):
            raise ValueError('Truncated RLE packet')
        chunk = data[offset:offset + count]
        offset += count
        out.extend(chunk if op & 128 else chunk * op)
        if len(out) > expected_bytes:
            raise ValueError('RLE plane overflow')


def expected_resource(rom, start):
    data = rom[BANK * 0x4000:(BANK + 1) * 0x4000]
    off = start - 0x8000
    planes = []
    for _ in range(PLANES):
        plane, off = decode_rle_plane(data, off)
        planes.append(plane)
    return b''.join(bytes(planes[p][row] for p in range(PLANES))
                    for row in range(PLANE_BYTES)), off + 0x8000


def execute(rom, index, count, vdp_dest=VDP_START):
    """Execute $3ACC from seeded Bank13 mapper and ROM-index arguments."""
    if not 0 <= index < 50 or not 1 <= count <= 50 - index:
        raise ValueError('Invalid Bank13 resource request')
    if not 0x4000 <= vdp_dest <= 0x7FFF or vdp_dest + count * RECORD_BYTES > 0x8000:
        raise ValueError('VDP destination outside available VRAM')
    m = ConsumerMachine(rom, LOADER)
    m.slot[2] = BANK
    m.a, m.b = index, count
    m.d, m.e = vdp_dest >> 8, vdp_dest & 255
    m.push(0xE000)
    initial_sp = m.sp
    m.run(0xE000)
    assert m.sp == initial_sp + 2
    if m.slot[2] != BANK:
        raise ValueError('Unexpected mapper state change')
    if len(m.data_writes) != count * RECORD_BYTES:
        raise ValueError('Unexpected VDP write count')
    base = vdp_dest & 0x3FFF
    actual = bytes(m.vram[base:base + count * RECORD_BYTES])
    ptrs = [int.from_bytes(rom[BANK * 0x4000 + DIRECTORY - 0x8000 + i * 2:
                               BANK * 0x4000 + DIRECTORY - 0x8000 + i * 2 + 2], 'little')
            for i in range(50)]
    expected = bytearray()
    for idx in range(index, index + count):
        item, end = expected_resource(rom, ptrs[idx])
        expected.extend(item)
    if actual != bytes(expected):
        raise ValueError('ROM opcode VRAM writes mismatch independent RLE decoding')
    written_addrs = [addr for addr, _ in m.data_writes]
    if sorted(written_addrs) != list(range(base, base + count * RECORD_BYTES)):
        raise ValueError('VDP transfer omitted, duplicated, or misaddressed a byte')
    if len(m.control) != count * RECORD_BYTES:
        raise ValueError('Incorrect VDP control command count')
    return {'index': index, 'count': count, 'vram_start': base,
            'output_bytes': len(actual), 'output_sha256': digest(actual),
            'first_directory_pointer': ptrs[index],
            'last_directory_pointer': ptrs[index + count - 1],
            'cpu_instructions': m.steps, 'vdp_commands': len(m.control),
            'bank13_read_count': m.bank13_read_count,
            'code_paths': sorted(m.executed_pc)}



def execute_tail(rom, vdp_dest):
    """Execute the separate four-plane RLE at Bank13:$A9A3 used by two callers.

    Fixed-bank caller anchors at $3CDE/$3E57 select the same source and
    transfer to VDP write commands $5600 and $7000 respectively.
    """
    tail_records = {0x5600: (0xA9A3, 0xABBA, 160),
                    0x7000: (0xA9A3, 0xABBA, 160),
                    0x7600: (0xBBF7, 0xBC23, 32)}
    if vdp_dest not in tail_records:
        raise ValueError('Unrecognized fixed-bank tail graphics destination')
    source_start, source_end, plane_size = tail_records[vdp_dest]
    expected_vdp_bytes = 4 * plane_size
    m = ConsumerMachine(rom, DECOMPRESSOR)
    m.slot[2] = BANK
    m.set_hl(source_start)
    m.d, m.e = vdp_dest >> 8, vdp_dest & 255
    m.push(0xE000)
    m.run(0xE000)
    if m.hl() != source_end:
        raise ValueError('Tail graphics stream reached unexpected endpoint')
    if len(m.data_writes) != expected_vdp_bytes or len(m.control) != expected_vdp_bytes:
        raise ValueError('Tail VDP transfer has incorrect plane size')
    source = rom[BANK * 0x4000:(BANK + 1) * 0x4000]
    off = source_start - 0x8000
    planes = []
    for _ in range(PLANES):
        decoded, off = decode_rle_plane(source, off, expected_bytes=plane_size)
        planes.append(decoded)
    if off + 0x8000 != source_end:
        raise ValueError('Independently decoded tail source boundary differs')
    expected = b''.join(bytes(p[i] for p in planes) for i in range(plane_size))
    dest = vdp_dest & 0x3FFF
    if bytes(m.vram[dest:dest + expected_vdp_bytes]) != expected:
        raise ValueError('Tail VDP output differs from independently decoded source')
    if sorted(addr for addr, _ in m.data_writes) != list(range(dest, dest + expected_vdp_bytes)):
        raise ValueError('Tail VDP addresses are not an exact 640-byte set')
    return {'source_start': source_start, 'source_end_exclusive': source_end,
            'compressed_bytes': source_end - source_start,
            'decoded_plane_bytes': plane_size, 'decoded_bytes': expected_vdp_bytes,
            'vdp_write_command': vdp_dest,
            'output_sha256': digest(expected), 'cpu_instructions': m.steps,
            'vdp_commands': len(m.control)}

def report(rom):
    if len(rom) != 0x40000 or digest(rom) != EXPECTED_SHA:
        raise ValueError('ROM fingerprint mismatch')
    fixed = rom[:0x4000]
    # Instructions must match independently audited Z80 source anchors.
    if fixed[0x38F0:0x38FC] != bytes.fromhex('21 00 80 11 20 41 06 1a af cd cc 3a'):
        raise ValueError('Initial 26-record graphics caller changed')
    if fixed[0x3991:0x399B] != bytes.fromhex('11 20 41 3e 1a 06 18 cd cc 3a'):
        raise ValueError('Followup 24-record graphics caller changed')
    if fixed[LOADER:LOADER + 6] != bytes.fromhex('21 8a bf f5 df c5'):
        raise ValueError('Bank13 loader pointer address or dispatch changed')
    if fixed[DECOMPRESSOR:DECOMPRESSOR + 5] != bytes.fromhex('0e 04 41 c5 d5'):
        raise ValueError('Bank13 RLE transfer routine changed')
    if fixed[0x38E7:0x38F0] != bytes.fromhex('21 f7 bb 11 00 76 cd 95 06'):
        raise ValueError('Third Bank13 tail graphics caller changed')
    if fixed[0x3CDE:0x3CE7] != bytes.fromhex('21 a3 a9 11 00 56 cd 95 06'):
        raise ValueError('First Bank13 tail graphics caller changed')
    if fixed[0x3E57:0x3E60] != bytes.fromhex('21 a3 a9 11 00 70 cd 95 06'):
        raise ValueError('Second Bank13 tail graphics caller changed')
    tail = [execute_tail(rom, addr) for addr in (0x5600, 0x7000, 0x7600)]
    each = [execute(rom, i, 1) for i in range(50)]
    batch0 = execute(rom, 0, 26)
    batch1 = execute(rom, 26, 24)
    return {'schema': 'ys-bank13-consumer-execution-m17-v1',
            'rom_sha256': EXPECTED_SHA,
            'bank0_dispatcher': f'{LOADER:04X}', 'bank0_rle_transfer': f'{DECOMPRESSOR:04X}',
            'bank13_pointer_directory': f'{DIRECTORY:04X}',
            'bank13_mapped_into_slot2': BANK,
            'vdp_data_port': 'BE', 'vdp_control_port': 'BF',
            'resource_count': len(each),
            'single_resource_bytes': RECORD_BYTES,
            'decoded_output_bytes_all_resources': 50 * RECORD_BYTES,
            'full_batches': [batch0, batch1],
            'tail_graphics_consumers': tail,
            'tail_graphics_compressed_bytes_recovered': 579,
            'tail_remaining_unclassified_bytes': 5028,
            'single_resource_runs': [{k: v for k, v in x.items() if k != 'code_paths'} for x in each],
            'limitations': [
                'Seeds bank13 mapper and entry registers, not actual gameplay control flow.',
                'Executes a fail-closed opcode subset, without cycle timing or interrupts.',
                'All 50 outputs are compared with an independently implemented RLE decoder.',
                'VRAM command order and bytes are modeled; on-screen rendering is not verified.',
                'The graphics transfer does not establish palette identity or item icon names.',
                'Only two noncontiguous tail RLE spans (535+44 bytes) have been consumer-validated.',
                'The remaining 5028 tail bytes are not yet semantically classified.',
            ]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check', action='store_true')
    p.add_argument('--write', action='store_true')
    a = p.parse_args()
    if a.check == a.write:
        p.error('Select exactly one of --check or --write')
    rom, _ = build()
    result = report(rom)
    if a.check:
        if json.loads(REPORT.read_text()) != result:
            raise ValueError('M17 report drift')
    else:
        REPORT.write_text(json.dumps(result, indent=2) + '\n')
    print('M17 Bank13: 50 indexed records, 14400 VDP bytes; 3 direct tail transfer cases')


if __name__ == '__main__':
    main()
