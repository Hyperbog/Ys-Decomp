#!/usr/bin/env python3
"""Phase 20: bounded ROM-opcode exercise of bank-6 $9966 -> $9932 -> $9AA9.

Synthetic object descriptor intentionally selects a direct, non-skipped $9AA9
path; no claim of in-game state or timing. Unsupported opcodes fail closed.
"""
import argparse
import hashlib
import json
from pathlib import Path
from phase19_sprite_execution import SpriteMachine, EXPECTED_SHA, ORIGINS
from phase18_z80_trace import UnsupportedOpcode
from recover_bank6_records_phase11b import extract, emulate_record_buffers

ROOT = Path(__file__).resolve().parents[1]

class ObjectMachine(SpriteMachine):
    """Adds only opcodes reached by the Phase 20 constrained object path."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.carry = False
        self.ix = 0
        self.object_calls = 0

    def step(self):
        self.ins_pc = self.pc
        op = self.read(self.pc)
        supported = {0xB7, 0x28, 0xFA, 0xC6, 0xD6, 0x85, 0x77, 0x24, 0x30, 0xC0}
        if op not in supported and op != 0xDD:
            return super().step()
        op = self.fetch()
        if op == 0xDD:
            sub = self.fetch()
            if sub == 0x21: self.ix = self.fetch_word()
            elif sub in (0x6E, 0x66, 0x7E):
                d = self.fetch()
                d = d if d < 128 else d-256
                value = self.read((self.ix+d)&0xffff)
                if sub == 0x6E: self.ix=(self.ix&0xff00)|value
                elif sub == 0x66: self.ix=(value<<8)|(self.ix&255)
                else: self.a=value
            elif sub == 0xCB:
                d = self.fetch()
                d = d if d < 128 else d-256
                cb = self.fetch()
                if cb != 0x4E: raise UnsupportedOpcode(f'Unsupported DD CB {cb:02X}')
                self.z = (self.read((self.ix+d)&0xffff)&2)==0 # BIT 1,(IX+d)
                self.object_calls += 1
            else: raise UnsupportedOpcode(f'Unsupported DD {sub:02X} at {self.ins_pc:04X}')
        elif op == 0xB7: # OR A
            self.z = self.a == 0
            self.carry = False
        elif op == 0x28: # JR Z
            d=self.fetch()
            if self.z:self.pc=(self.pc + (d if d<128 else d-256))&0xffff
        elif op == 0xFA: # JP M, nn (sign flag derived from preceding OR A)
            target=self.fetch_word()
            if self.a&0x80:self.pc=target
        elif op == 0xC6: # ADD A,n
            x=self.fetch();v=self.a+x
            self.carry=v>255
            self.a=v&255;self.z=self.a==0
        elif op == 0xD6: # SUB n
            x=self.fetch();v=self.a-x
            self.carry=v<0
            self.a=v&255;self.z=self.a==0
        elif op == 0x85: # ADD A,L
            v=self.a+self.l
            self.carry=v>255
            self.a=v&255;self.z=self.a==0
        elif op == 0x77: self.write(self.hl(),self.a)
        elif op == 0x24: self.h=(self.h+1)&255;self.z=self.h==0
        elif op == 0x30: # JR NC
            d=self.fetch()
            if not self.carry:self.pc=(self.pc+(d if d<128 else d-256))&0xffff
        elif op == 0xC0: # RET NZ
            if not self.z:self.pc=self.pop()
        else: raise UnsupportedOpcode(f'Unexpected opcode {op:02X}')
        self.steps += 1


def trace(rom, origins=ORIGINS):
    if len(rom)!=0x40000 or hashlib.sha256(rom).hexdigest()!=EXPECTED_SHA:
        raise ValueError('Original ROM fingerprint mismatch')
    records=extract(rom)
    cases=[]
    digest=hashlib.sha256()
    for first,second in origins:
        for rec in records:
            index=rec['directory_index'];count=rec['count']
            raw_y,raw_xt=emulate_record_buffers(rec['decoded'],first,second)
            initial={
                0xC198: b'\x01', # enter $9932 and $9AA9 path
                0xC199: bytes([index]),
                0xC1B9: b'\x80', # JP M directly to $9A71 after $9AA9
                0xC200: bytes([1,0]+[0]*18+[0]+[0]*2+[0x00,0xC2]),
                0xC210: bytes([first,second]),
                0xDD00: bytes([0xD0]*64),
                0xDD40: bytes(128),
                0xC028: bytes.fromhex('00 DD 40 DD'),
            }
            # C200+23=00 and +24=C2, so IX remains C200 in $9AA9.
            m=ObjectMachine(rom,0x9966,ram=initial,max_instructions=5000)
            m.slot[2]=6  # caller's bank-6 mapping; no boot/gameplay inference
            m.push(0xE000)
            m.run(0xE000)
            if m.object_calls!=1:raise AssertionError('Expected exactly one object BIT test')
            if m.ix!=0xC200:raise AssertionError('Descriptor pointer wrong')
            # HL points just past source record when $9932 returns.
            data_start=rec['cpu_address']
            hl_end=data_start+1+3*count
            tile_source=hl_end
            # Object tile-selection byte C214 is zero, so no 4-byte offset.
            if not 0x8000 <= tile_source <= 0xBFFC:
                raise AssertionError('Unexpected tile source outside bank 6')
            tile_offset=6*0x4000+tile_source-0x8000
            tiles=rom[tile_offset:tile_offset+4]
            y1=(first-17)&255; y2=(first-9)&255
            xs=[(second-8)&255, second&255, (second-8)&255, second&255]
            expected_y=raw_y+bytes([y1,y1,y2,y2,0xD0])
            expected_xt=raw_xt+b''.join(bytes((x,t)) for x,t in zip(xs,tiles))
            if m.ram[0x1D00:0x1D00+len(expected_y)]!=expected_y:
                raise AssertionError(f'Y object buffer mismatch at {index}')
            if m.ram[0x1D40:0x1D40+len(expected_xt)]!=expected_xt:
                raise AssertionError(f'XT object buffer mismatch at {index}')
            if (m.read(0xC028)|(m.read(0xC029)<<8)) != 0xDD00+count+4:
                raise AssertionError('Y buffer pointer mismatch')
            if (m.read(0xC02A)|(m.read(0xC02B)<<8)) != 0xDD40+count*2+8:
                raise AssertionError('XT buffer pointer mismatch')
            m.pc=0x0427;m.push(0xE001);m.run(0xE001)
            expected_sat=bytes(m.ram[0x1D00:0x1D40]+m.ram[0x1D40:0x1DC0])
            actual=bytes(v for _,v in m.data_writes)
            if expected_sat != actual or len(actual)!=192:
                raise AssertionError('Wrong integrated SAT output')
            if m.control!=['7F00','7F80']:raise AssertionError('Wrong VDP control writes')
            digest.update(actual)
            cases.append({'record':index,'origins':[first,second],'elements':count,
                          'steps':m.steps,'object_calls':m.object_calls,
                          'output_sha256':hashlib.sha256(actual).hexdigest()})
    return {'schema':'ys-phase20-object-execution-v1','rom_sha256':EXPECTED_SHA,
            'cases':cases,'case_count':len(cases),'sat_bytes_per_case':192,
            'sat_bytes_in_all_cases':len(cases)*192,
            'concat_sha256':digest.hexdigest(),
            'new_source_backed_bytes':0,'new_classified_rom_bytes':0,
            'limitations':['Bank-6 slot manually selected and RAM object state synthesized',
                           'The object pointer is held at C200 and the animation index is zero',
                           'This checks only the C198!=0, C1B9<0 branch, not all branches of $9966',
                           'Bounded instruction execution, not full emulator timing or gameplay']}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('rom',type=Path)
    x=ap.add_mutually_exclusive_group(required=True)
    x.add_argument('--write',action='store_true');x.add_argument('--check',action='store_true')
    a=ap.parse_args();result=trace(a.rom.read_bytes())
    dest=ROOT/'phase20/object_execution.json'
    if a.write:
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(result,indent=2)+'\n')
    elif json.loads(dest.read_text())!=result:raise AssertionError('Phase 20 report drift')
    print('PASS Phase20:',result['case_count'],'object producer/SAT executions')
if __name__=='__main__':main()
