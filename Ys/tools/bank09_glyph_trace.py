#!/usr/bin/env python3
"""Bounded ROM-instruction execution of bank9's six-byte VDP writer at $BF2C.

The mapper, RAM separator, VRAM starting address and selected HL are seeded.
This verifies output instructions but not prior RST $18/$28 or gameplay state.
"""
import argparse,hashlib,json
from pathlib import Path
from build_sms_phase14 import ROOT,EXPECTED_SHA
from phase18_z80_trace import Machine,UnsupportedOpcode
from whole_banks09_11_12 import full_bank,source_path

class GlyphMachine(Machine):
 def step(self):
  pc=self.pc;op=self.read(pc)
  if op==0x3A: # LD A,(nn)
   self.ins_pc=self.pc;self.fetch();self.a=self.read(self.fetch_word());self.steps+=1
  elif op==0xED and self.read((pc+1)&0xffff)==0x79: # OUT (C),A
   self.ins_pc=self.pc;self.fetch();self.fetch();self.port(self.c,self.a);self.steps+=1
  else:super().step()

def execute(rom,idx,separator):
 if len(rom)!=0x40000 or not 0<=idx<8 or not 0<=separator<256:
  raise ValueError('Invalid bounded bank9 execution input')
 src=json.loads((ROOT/source_path(9)).read_text())['six_byte_glyph_table']
 word=src['pointers'][idx]
 if word!=0xBF4C+6*((word-0xBF4C)//6) or not 0xBF4C<=word<0xBF7C:
  raise ValueError('Invalid source pointer')
 expected=bytes(src['records'][(word-0xBF4C)//6])
 m=GlyphMachine(rom,0xBF2C,ram={0xC026:bytes([separator])},max_instructions=90)
 m.slot[2]=9;m.set_hl(word);m.vram_addr=0x200;m.push(0xE000);m.run(0xE000)
 out=bytes(v for _,v in m.data_writes)
 target=b''.join(bytes((v,separator)) for v in expected)
 if out!=target or len(out)!=12 or m.hl()!=word+6 or m.b!=0 or m.c!=0xBE:
  raise ValueError('Bank9 byte output, register or transfer count mismatch')
 if any(addr!=0x200+i for i,(addr,_) in enumerate(m.data_writes)):
  raise ValueError('Bank9 VDP data destination mismatch')
 return {'index':idx,'pointer':f'{word:04X}','separator':separator,'steps':m.steps,
         'output_bytes':len(out),'sha256':hashlib.sha256(out).hexdigest()}

def trace(rom):
 if len(rom)!=0x40000 or hashlib.sha256(rom).hexdigest()!=EXPECTED_SHA:raise ValueError('Bad ROM fingerprint')
 results=[execute(rom,i,separator) for separator in (0,0x2E,0xA7) for i in range(8)]
 return {'schema':'ys-bank09-vdp-six-byte-bounded-v1','cases':len(results),'bytes_written':sum(x['output_bytes'] for x in results),
         'entry_cpu':'BF2C','mapper_bank':9,'port':'BE','six_byte_records':8,
         'execution_results':results,'limitations':[
          'Runs ROM opcode loop with manually selected HL, bank 9 mapper, RAM separator and VRAM address.',
          'RST $18/$28 caller setup, gameplay state, frames and cycle timing are not modeled.',
          'Candidate glyph identities/encoding are not decoded.']}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path)
 p.add_argument('--check',action='store_true');p.add_argument('--report',type=Path,default=ROOT/'wholebank09/glyph_trace.json')
 a=p.parse_args();report=trace(a.rom.read_bytes())
 if a.check:
  if json.loads(a.report.read_text())!=report:raise ValueError('Bank9 runtime report drift')
 else:a.report.write_text(json.dumps(report,indent=2)+'\n')
 print('Bank9 6-byte VDP execution PASS',report['cases'],'cases',report['bytes_written'],'written bytes')
if __name__=='__main__':main()
