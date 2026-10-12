#!/usr/bin/env python3
"""ROM-independent source rebuild of banks 9, 11 and 12.

Bank9 has ROM-verified code at $BEFB-$BF3B driving eight six-byte
text/glyph runs via VDP port $BE. Bank11 and much of bank12 remain
semantically unresolved; no complete text interpreter is claimed.
Capture mode requires the user's fingerprinted ROM; normal build does not.
"""
import argparse,hashlib,json,re
from pathlib import Path
from build_sms_phase14 import ROOT,SOURCES,EXPECTED_SHA
from z80_roundtrip_phase10 import assemble,encode
from z80_regions import decode
from whole_bank07 import assemble_mixed

SIZE=0x4000;START=0x8000;END=0xC000; BANKS=(9,11,12)
CODE9=(0xBEFB,0xBF3C); KNOWN12=(0x9EFC,0x9F68)
PAD={9:(0xBFE6,END),11:(0xBFCC,END),12:(0xBF98,END)}

def sha(b):return hashlib.sha256(b).hexdigest()
def source_path(n):return Path(f'wholebank{n:02d}/source.json')
def hash_path(n):return Path(f'wholebank{n:02d}/digests.json')
def asm_path(n):return Path(f'src/wholebank{n:02d}/bank{n:02d}_complete.asm')

def chunks(blob,start):
 return [{'start':start+i,'hex':blob[i:i+256].hex()} for i in range(0,len(blob),256)]

def unchunk(chunks,start,end):
 if type(chunks)!=list or (start!=end and not chunks):raise ValueError('Missing data chunks')
 data=bytearray();pc=start
 for c in chunks:
  if type(c)!=dict or set(c)!={'start','hex'} or type(c['start'])!=int or c['start']!=pc:raise ValueError('Noncontiguous chunk')
  if type(c['hex'])!=str:raise ValueError('Bad chunk format')
  b=bytes.fromhex(c['hex'])
  if not 1<=len(b)<=256:raise ValueError('Bad chunk length')
  data+=b;pc+=len(b)
 if pc!=end:raise ValueError(f'Chunk end drift ${pc:04X} != ${end:04X}')
 return bytes(data)

def old_code(n,root=ROOT):
 out={}
 for rel,b in SOURCES:
  if b==n:
   byte_map,_=assemble((root/rel).read_text())
   for pc,v in byte_map.items():
    if pc in out:raise ValueError('Old source overlap')
    out[pc]=v
 if n==12 and set(out)!=set(range(*KNOWN12)):raise ValueError('Bank12 existing code ownership changed')
 if n!=12 and out:raise ValueError('Unexpected previous code')
 return out

def source_instructions(text):
 ins={};pc=None
 for raw in text.splitlines():
  line=raw.split(';',1)[0].strip()
  if not line or line.endswith(':'):continue
  if line.lower().startswith('org '):pc=int(line.split('$')[1],16);continue
  if pc is None or re.match(r'^(db|dw|ds|incbin)\b',line,re.I):raise ValueError('Expected mnemonic instruction')
  b=encode(line,pc)
  if pc in ins:raise ValueError('Duplicate instruction')
  ins[pc]=(line,len(b));pc+=len(b)
 return ins

def extra_code(root=ROOT):
 path=root/'src/wholebank09/extra_code.asm'
 text=path.read_text();result,_=assemble(text)
 instr=source_instructions(text)
 if set(result)!=set(range(*CODE9)) or sum(n for _,n in instr.values())!=CODE9[1]-CODE9[0]:
  raise ValueError('Bank9 complete executable span drift')
 return result,instr

def load_new(n,root=ROOT):
 obj=json.loads((root/source_path(n)).read_text())
 if obj.get('schema')!=f'ys-whole-bank{n:02d}-source-v1':raise ValueError('Source schema mismatch')
 parts=[]
 def add(start,data,kind):
  if not START<=start<END or start+len(data)>END:raise ValueError('Bad bank source bounds')
  parts.append((start,bytes(data),kind))
 if n==9:
  add(START,unchunk(obj['unresolved_language_stream'],START,CODE9[0]),'language/resource stream: grammar unresolved')
  d=obj['six_byte_glyph_table'];records=d['records'];pointers=d['pointers']
  if type(records)!=list or len(records)!=8 or type(pointers)!=list or len(pointers)!=8:
   raise ValueError('Eight glyph sequences required')
  if any(type(row)!=list or len(row)!=6 or any(type(v)!=int or not 0<=v<256 for v in row) for row in records):
   raise ValueError('Invalid six-byte glyph record')
  addresses=[0xBF4C+6*i for i in range(8)]
  if pointers!=[addresses[j] for j in (1,3,2,4,5,6,7,0)]:
   raise ValueError('Glyph lookup permutation or targets changed')
  add(0xBF3C,bytes(x for a in pointers for x in (a&255,a>>8)),'eight source pointers to six-byte VDP strings')
  add(0xBF4C,bytes(v for row in records for v in row),'eight fixed six-byte glyph sequences')
  add(0xBF7C,unchunk(obj['unresolved_tail'],0xBF7C,PAD[n][0]),'undecoded metadata/text fragments')
 elif n==11:
  add(START,unchunk(obj['unresolved_resource_stream'],START,PAD[n][0]),'unresolved resource stream')
 else:
  arr=obj['candidate_wave_samples_128']
  if type(arr)!=list or len(arr)!=128 or any(type(v)!=int or not 0<=v<256 for v in arr):raise ValueError('Bank12 wave candidate layout')
  add(START,bytes(arr),'128-byte candidate waveform/curve (unproven consumer)')
  add(0x8080,unchunk(obj['undecoded_before_code'],0x8080,KNOWN12[0]),'undecoded resource body before Z80')
  add(KNOWN12[1],unchunk(obj['undecoded_after_code'],KNOWN12[1],PAD[n][0]),'undecoded resource body after Z80')
 p,z=PAD[n]
 if obj.get('ff_padding')!={'start':p,'count':z-p,'value':255}:raise ValueError('Bank end filler drift')
 add(p,bytes([255])*(z-p),'verified bank-end FF filler')
 result={};inventory=[]
 for start,chunk,kind in parts:
  for i,v in enumerate(chunk):
   if start+i in result:raise ValueError('Overlapping data regions')
   result[start+i]=v
  inventory.append({'start':start,'end_exclusive':start+len(chunk),'bytes':len(chunk),'classification':kind})
 old=old_code(n,root);new=extra_code(root)[0] if n==9 else {}
 if set(result)&set(old) or set(result)&set(new) or set(old)&set(new) or set(result)|set(old)|set(new)!=set(range(START,END)):
  raise ValueError('Whole-bank code/data ownership conflict or gap')
 encoded=bytes(result[k] for k in sorted(result))
 if sha(encoded)!=json.loads((root/hash_path(n)).read_text())['new_data_sha256']:
  raise ValueError('Source data fingerprint failed')
 return result,inventory

def full_bank(n,root=ROOT):
 if n not in BANKS:raise ValueError('Unsupported bank')
 data,_=load_new(n,root);old=old_code(n,root);new=extra_code(root)[0] if n==9 else {}
 raw=bytes((data|old|new)[i] for i in range(START,END))
 if sha(raw)!=json.loads((root/hash_path(n)).read_text())['bank_sha256']:
  raise ValueError(f'Bank {n} source fingerprint mismatch')
 return raw

def mixed_source(n,root=ROOT):
 data=full_bank(n,root)
 ins={}
 files=[root/rel for rel,b in SOURCES if b==n]
 if n==9:files.append(root/'src/wholebank09/extra_code.asm')
 for file in files:
  for pc,item in source_instructions(file.read_text()).items():
   if pc in ins:raise ValueError('Overlapping instruction declarations')
   ins[pc]=item
 stops={9:{0xBEFB:'Bank09_GlyphVDPUpload',0xBF3C:'Bank09_GlyphIndex8',0xBF4C:'Bank09_GlyphRecords8x6',0xBF7C:'Bank09_UnresolvedTail',PAD[n][0]:'Bank09_FFPad'},
        11:{PAD[n][0]:'Bank11_FFPad'},
        12:{0x8080:'Bank12_UnresolvedPayload',KNOWN12[0]:'Bank12_KnownZ80',KNOWN12[1]:'Bank12_OtherPayload',PAD[n][0]:'Bank12_FFPad'}}[n]
 lines=[f'; Physical ROM bank {n:02d}, ROM-independent byte-identity source.',
        '; Unresolved bytes retain exact values; semantic decompilation remains incomplete.', 'org $8000']
 pc=START
 while pc<END:
  if pc in stops:lines.append(stops[pc]+':')
  if pc in ins:
   text,size=ins[pc]
   if data[pc-START:pc-START+size]!=encode(text,pc):raise ValueError('Mnemonic byte mismatch')
   lines.append('    '+text);pc+=size;continue
  candidates=[c for c in list(ins)+list(stops) if c>pc]
  stop=min(candidates+[END]);z=min(pc+16,stop)
  if z<=pc:raise ValueError('Invalid split point')
  lines.append('    db '+', '.join(f'${v:02X}' for v in data[pc-START:z-START]));pc=z
 return '\n'.join(lines)+'\n'

def capture(rom,root=ROOT):
 if len(rom)!=0x40000 or sha(rom)!=EXPECTED_SHA:raise ValueError('Incorrect owner ROM fingerprint')
 for n in BANKS:
  bank=rom[n*SIZE:(n+1)*SIZE]
  (root/source_path(n)).parent.mkdir(parents=True,exist_ok=True)
  def span(a,z):return bank[a-START:z-START]
  if n==9:
   code=['org $BEFB'];pc=CODE9[0]
   while pc<CODE9[1]:
    off=n*SIZE+pc-START;end,mnemonic=decode(rom,off,START-n*SIZE)
    if end>n*SIZE+CODE9[1]-START or encode(mnemonic,pc)!=rom[off:end]:raise ValueError('Invalid code span')
    code.append('    '+mnemonic);pc=end-n*SIZE+START
   (root/'src/wholebank09').mkdir(parents=True,exist_ok=True)
   (root/'src/wholebank09/extra_code.asm').write_text('\n'.join(code)+'\n')
   pointers=[int.from_bytes(span(p,p+2),'little') for p in range(0xBF3C,0xBF4C,2)]
   obj={'schema':'ys-whole-bank09-source-v1','unresolved_language_stream':chunks(span(START,CODE9[0]),START),
        'six_byte_glyph_table':{'pointers':pointers,'records':[list(span(p,p+6)) for p in range(0xBF4C,0xBF7C,6)]},
        'unresolved_tail':chunks(span(0xBF7C,PAD[n][0]),0xBF7C)}
  elif n==11:obj={'schema':'ys-whole-bank11-source-v1','unresolved_resource_stream':chunks(span(START,PAD[n][0]),START)}
  else:obj={'schema':'ys-whole-bank12-source-v1','candidate_wave_samples_128':list(span(START,0x8080)),
          'undecoded_before_code':chunks(span(0x8080,KNOWN12[0]),0x8080),
          'undecoded_after_code':chunks(span(KNOWN12[1],PAD[n][0]),KNOWN12[1])}
  obj['ff_padding']={'start':PAD[n][0],'count':END-PAD[n][0],'value':255}
  (root/source_path(n)).write_text(json.dumps(obj,separators=(',',':'))+'\n')
  known=old_code(n,root);new=extra_code(root)[0] if n==9 else {}
  for p,v in (known|new).items():
   if bank[p-START]!=v:raise ValueError('Capture code mismatched original ROM')
  owned={p:bank[p-START] for p in range(START,END) if p not in (known|new)}
  (root/hash_path(n)).write_text(json.dumps({'bank_sha256':sha(bank),
         'new_data_sha256':sha(bytes(owned[p] for p in sorted(owned))),
         'new_source_backed_bytes':SIZE-len(known),'new_mnemonic_bytes':len(new),
         'unresolved_semantics':True},indent=2)+'\n')
  if full_bank(n,root)!=bank:raise ValueError('Bank capture not reproducible')
  (root/asm_path(n)).parent.mkdir(parents=True,exist_ok=True)
  (root/asm_path(n)).write_text(mixed_source(n,root))

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--capture',type=Path);p.add_argument('--verify-rom',type=Path)
 p.add_argument('--verify-mixed',action='store_true');p.add_argument('--output-directory',type=Path)
 a=p.parse_args()
 if a.capture:capture(a.capture.read_bytes())
 for n in BANKS:
  b=full_bank(n)
  if a.verify_rom:
   rom=a.verify_rom.read_bytes()
   if len(rom)!=0x40000 or sha(rom)!=EXPECTED_SHA or rom[n*SIZE:(n+1)*SIZE]!=b:raise ValueError('ROM identity check failed')
  if a.verify_mixed:
   src=mixed_source(n)
   if src!=(ROOT/asm_path(n)).read_text() or assemble_mixed(src)!=b:raise ValueError('Mixed source mismatch')
  if a.output_directory:
   a.output_directory.mkdir(parents=True,exist_ok=True)
   (a.output_directory/f'bank{n:02d}.bin').write_bytes(b)
  print('Bank',n,'ROM-independent',len(b),'SHA256',sha(b))
if __name__=='__main__':main()
