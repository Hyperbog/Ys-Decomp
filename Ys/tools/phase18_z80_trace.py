#!/usr/bin/env python3
"""Fail-closed, instruction-level Z80 harness for two Ys SMS VDP routines.

Executes *actual ROM opcodes* with a restricted instruction set, minimal Sega
mapper and VRAM-write-port model. This is NOT a complete SMS emulator: no
cycle accuracy, interrupts, VDP renderer, PSG, frame timing or game bootstrap.
"""
import argparse
import hashlib
import json
from pathlib import Path
from vdp_upload_phase9 import CALLS
from recover_bank6_records_phase11b import extract, emulate_record_buffers

ROOT=Path(__file__).resolve().parents[1]
SHA=json.loads((ROOT/'manifest.json').read_text())['sha256']

class UnsupportedOpcode(RuntimeError):
    pass

class Machine:
    def __init__(self, rom, pc, ram=None, max_instructions=25000):
        if len(rom)!=0x40000:
            raise ValueError('Expected 256-KiB ROM')
        self.rom=rom
        self.pc=pc
        self.sp=0xDFF0
        self.a=self.b=self.c=self.d=self.e=self.h=self.l=0
        self.z=False
        self.slot=[0,1,2]
        self.ram=bytearray(0x4000)
        if ram:
            for addr,blob in ram.items():
                if addr<0xC000 or addr+len(blob)>0xFFFC:
                    raise ValueError('Invalid seeded RAM range')
                self.ram[addr-0xC000:addr-0xC000+len(blob)]=blob
        self.max_instructions=max_instructions
        self.steps=0
        self.mapper_writes=[]
        self.control=[]
        self.data_writes=[]
        self.vram=bytearray(0x4000)
        self.vram_addr=None
        self.control_first=None
        self.port_events=[]
    def read(self,addr):
        addr &= 0xffff
        if addr>=0xC000:return self.ram[addr-0xC000]
        if addr<0x4000:pos=addr
        elif addr<0x8000:pos=self.slot[1]*0x4000+(addr-0x4000)
        else:pos=self.slot[2]*0x4000+(addr-0x8000)
        return self.rom[pos]
    def write(self,addr,val):
        addr&=0xffff;val&=255
        if addr==0xFFFF:
            self.slot[2]=val%16
            self.mapper_writes.append({'pc':f'{self.ins_pc:04X}','address':'FFFF','value':val})
        elif addr>=0xC000:self.ram[addr-0xC000]=val
        else:raise UnsupportedOpcode(f'Unexpected ROM write {addr:04X}')
    def fetch(self):
        v=self.read(self.pc);self.pc=(self.pc+1)&0xffff;return v
    def fetch_word(self):
        lo=self.fetch();return lo|(self.fetch()<<8)
    def push(self,val):
        self.sp=(self.sp-1)&0xffff;self.write(self.sp,val>>8)
        self.sp=(self.sp-1)&0xffff;self.write(self.sp,val)
    def pop(self):
        lo=self.read(self.sp);self.sp=(self.sp+1)&0xffff
        hi=self.read(self.sp);self.sp=(self.sp+1)&0xffff
        return lo|(hi<<8)
    def hl(self):return (self.h<<8)|self.l
    def set_hl(self,val):self.h=(val>>8)&255;self.l=val&255
    def de(self):return (self.d<<8)|self.e
    def port(self,port,value):
        port &=255;value &=255
        if port==0xBF:
            if self.control_first is None:self.control_first=value
            else:
                cmd=self.control_first|(value<<8)
                if cmd>>14!=1:raise UnsupportedOpcode(f'Non-VRAM VDP command {cmd:04X}')
                self.vram_addr=cmd&0x3fff
                self.control.append(f'{cmd:04X}')
                self.control_first=None
            self.port_events.append(('BF',value))
        elif port==0xBE:
            if self.vram_addr is None:raise UnsupportedOpcode('VDP data written without VRAM address')
            self.data_writes.append((self.vram_addr,value))
            self.vram[self.vram_addr]=value
            self.vram_addr=(self.vram_addr+1)&0x3fff
            self.port_events.append(('BE',value))
        else:raise UnsupportedOpcode(f'Unsupported port ${port:02X}')
    def step(self):
        self.ins_pc=self.pc
        op=self.fetch()
        if op==0x00:pass # NOP
        elif op==0xF3 or op==0xFB:pass # DI, EI; no interrupts injected
        elif op==0x3E:self.a=self.fetch()
        elif op==0x06:self.b=self.fetch()
        elif op==0x0E:self.c=self.fetch()
        elif op==0x21:self.set_hl(self.fetch_word())
        elif op==0x11:
            v=self.fetch_word();self.d=v>>8;self.e=v&255
        elif op==0x32:self.write(self.fetch_word(),self.a)
        elif op==0x7B:self.a=self.e
        elif op==0x7A:self.a=self.d
        elif op==0x7E:self.a=self.read(self.hl())
        elif op==0x23:self.set_hl(self.hl()+1)
        elif op==0xAF:self.a=0;self.z=True
        elif op==0x3C:self.a=(self.a+1)&255;self.z=self.a==0
        elif op==0x3D:self.a=(self.a-1)&255;self.z=self.a==0
        elif op==0x0D:self.c=(self.c-1)&255;self.z=self.c==0
        elif op==0x10:
            disp=self.fetch();self.b=(self.b-1)&255
            if self.b:self.pc=(self.pc+(disp if disp<128 else disp-256))&0xffff
        elif op==0x20:
            disp=self.fetch()
            if not self.z:self.pc=(self.pc+(disp if disp<128 else disp-256))&0xffff
        elif op==0xD3:self.port(self.fetch(),self.a)
        elif op==0xCD:
            target=self.fetch_word();self.push(self.pc);self.pc=target
        elif op==0xEF:self.push(self.pc);self.pc=0x28
        elif op==0xC9:self.pc=self.pop()
        elif op==0xED:
            sub=self.fetch()
            if sub!=0xA3:raise UnsupportedOpcode(f'Unsupported ED opcode {sub:02X} at {self.ins_pc:04X}')
            self.port(self.c,self.read(self.hl()))
            self.set_hl(self.hl()+1);self.b=(self.b-1)&255
            self.z=self.b==0 # Z80 OUTI sets Z according to decremented B
        else:raise UnsupportedOpcode(f'Unsupported opcode {op:02X} at {self.ins_pc:04X}')
        self.steps+=1
    def run(self,stop_pc):
        while self.pc!=stop_pc:
            if self.steps>=self.max_instructions:raise RuntimeError('Instruction budget exceeded')
            self.step()
        if self.control_first is not None:raise RuntimeError('Incomplete VDP control word')
        return self


def trace(rom):
    if hashlib.sha256(rom).hexdigest()!=SHA:raise ValueError('Original ROM fingerprint mismatch')
    old=json.loads((ROOT/'phase9/vdp_uploads.json').read_text())
    uploads=[]
    for ((start,_,_,caller),anchor) in zip(CALLS,old['vdp_uploads']):
        cpu=Machine(rom,start)
        cpu.run(caller+3)
        actual=bytes(v for _,v in cpu.data_writes)
        dest=int(anchor['vram_start'],16)
        expected_len=anchor['vdp_output_bytes']
        assert cpu.mapper_writes==[{'pc':'0BA3','address':'FFFF','value':3}]
        assert cpu.control==[anchor['vdp_command']]
        assert len(actual)==expected_len
        assert all(addr==dest+i for i,(addr,_) in enumerate(cpu.data_writes))
        assert hashlib.sha256(actual).hexdigest()==anchor['vdp_output_sha256']
        assert cpu.vram[dest:dest+expected_len]==actual
        uploads.append({'caller':f'{caller:04X}','executed_instructions':cpu.steps,
                        'mapper_write_bank':cpu.mapper_writes[0]['value'],
                        'vdp_control_commands':cpu.control,'vram_start':f'{dest:04X}',
                        'out_data_bytes':len(actual),'output_sha256':hashlib.sha256(actual).hexdigest()})
    # Seed RAM from an actual ROM record, using the independently reconstructed
    # consumer's cumulative-delta model. This does NOT execute that producer.
    records=extract(rom)
    record=records[7]
    y,xt=emulate_record_buffers(record['decoded'])
    ybuf=(y+bytes([0xD0])*(64-len(y)))
    xtbuf=xt+bytes(128-len(xt))
    sprite=Machine(rom,0x0427,ram={0xDD00:ybuf,0xDD40:xtbuf})
    sprite.push(0xE000)
    sprite.run(0xE000)
    assert sprite.control==['7F00','7F80'],sprite.control
    assert sprite.vram[0x3f00:0x3f40]==ybuf
    assert sprite.vram[0x3f80:0x4000]==xtbuf
    assert bytes(v for _,v in sprite.data_writes)==ybuf+xtbuf
    assert len(sprite.data_writes)==192
    directory=json.loads((ROOT/'phase13/graphics_directory.json').read_text())
    graphics=[]
    total_graphics=bytearray()
    for item in directory['graphics_records']:
        idx=item['index']
        entry=int(item['unrolled_entry_cpu'],16)
        source=int(item['graphics_source_cpu'],16)
        n=item['graphics_bytes']
        assert 0x8180<=entry<0x86C0 and 0x8800<=source<0xB000
        assert (0x86C0-entry)//8==n and (0x86C0-entry)%8==0
        m=Machine(rom,entry)
        m.slot[2]=7 # mapper state is initialized, not reached through gameplay
        m.set_hl(source)
        m.c=0xBE
        m.a=0
        m.port(0xBF,0x20);m.port(0xBF,0x74) # from static graphics caller
        m.push(0xE000)
        m.run(0xE000)
        raw=rom[7*0x4000+source-0x8000:7*0x4000+source-0x8000+n]
        expected=b''.join((bytes((x,0,0,0)) for x in raw))
        actual=bytes(v for _,v in m.data_writes)
        assert hashlib.sha256(raw).hexdigest()==item['graphics_sha256']
        assert len(actual)==n*4 and actual==expected
        assert m.steps==4*n+1 and m.control==['7420']
        assert all(pos==0x3420+i for i,(pos,_) in enumerate(m.data_writes))
        graphics.append({'index':idx,'entry_cpu':f'{entry:04X}',
                         'source_cpu':f'{source:04X}','instructions':m.steps,
                         'source_bytes':n,'vdp_bytes':len(actual),
                         'vdp_sha256':hashlib.sha256(actual).hexdigest()})
        total_graphics.extend(actual)
    assert len(graphics)==64 and len(total_graphics)==40224
    return {'schema':'ys-phase18-bounded-z80-execution-v1',
            'rom_sha256':SHA,
            'scope':'ROM opcode execution of fixed-bank $0BA1 and $0427 with synthetic caller state; not a full-system gameplay trace',
            'uploader_traces':uploads,
            'uploader_output_bytes_with_repeats':sum(x['out_data_bytes'] for x in uploads),
            'sprite_sat_trace':{'entry_cpu':'0427','executed_instructions':sprite.steps,
              'record_directory_index':7,'record_elements':record['count'],
              'ram_y_start':'DD00','ram_xt_start':'DD40',
              'control_commands':sprite.control,
              'sat_y_range':'3F00-3F3F','sat_x_tile_range':'3F80-3FFF',
              'output_bytes':len(sprite.data_writes),
              'output_sha256':hashlib.sha256(ybuf+xtbuf).hexdigest()},
            'bank7_unrolled_traces':graphics,
            'bank7_total_output_bytes_across_record_runs':len(total_graphics),
            'bank7_combined_output_sha256':hashlib.sha256(total_graphics).hexdigest(),
            'new_rom_bytes_classified':0,'new_source_backed_bytes':0,
            'limitations':['Unsupported Z80 instructions fail closed',
                           'No frame timing, rendering, interrupts or real gameplay state',
                           'RAM buffers seeded using independent static producer model',
                           'No external SMS emulator or Z80 assembler installed']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--write',action='store_true')
    group.add_argument('--check',action='store_true')
    a=p.parse_args()
    result=trace(a.rom.read_bytes())
    dest=ROOT/'phase18/execution_report.json'
    if a.write:
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(result,indent=2)+'\n')
    elif json.loads(dest.read_text())!=result:raise ValueError('Phase18 trace report drift')
    print(f"PASS Phase18: {result['uploader_output_bytes_with_repeats']} upload bytes, 192 SAT bytes, and {result['bank7_total_output_bytes_across_record_runs']} bank7 graphics bytes across 64 bounded ROM executions")
if __name__=='__main__':main()
