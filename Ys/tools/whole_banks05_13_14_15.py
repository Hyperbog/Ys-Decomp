#!/usr/bin/env python3
"""ROM-independent source rebuild of the four final Ys SMS banks.

Bank 13 ends with a 50-word indexed directory. Remaining asset bodies
are explicitly UNRESOLVED, preserved losslessly as bounded source chunks.
Capture from the owner ROM is an explicit one-time authoring action only.
Normal build never reads an original ROM or a previously generated bank binary.
"""
import argparse
import hashlib
import json
from pathlib import Path
from build_sms_phase14 import ROOT, EXPECTED_SHA
from whole_bank07 import assemble_mixed

BANKS=(5,13,14,15)
SIZE=0x4000
START=0x8000
END=0xC000
POINTER_START=0xBF8A
POINTER_END=0xBFEE
FILL_START={5:0xBC5B,13:0xBFEE,14:0xBFD6,15:0xBFFC}

def sha(blob):return hashlib.sha256(blob).hexdigest()
def source_file(bank):return Path(f'wholebank{bank:02}/source.json')
def digest_file(bank):return Path(f'wholebank{bank:02}/digests.json')
def asm_file(bank):return Path(f'src/wholebank{bank:02}/bank{bank:02}_complete.asm')

def split_chunks(blob,start):
 return [{'start':start+i,'hex':blob[i:i+256].hex()} for i in range(0,len(blob),256)]

def unpack_chunks(chunks,start,end):
 if not isinstance(chunks,list) or (start!=end and not chunks):raise ValueError('Missing source chunks')
 result=bytearray();cursor=start
 for item in chunks:
  if type(item)!=dict or set(item)!={'start','hex'} or type(item['start'])!=int or item['start']!=cursor:
   raise ValueError('Noncontiguous source chunk or schema change')
  if type(item['hex'])!=str:raise ValueError('Invalid chunk encoding')
  b=bytes.fromhex(item['hex'])
  if not 1<=len(b)<=256:raise ValueError('Invalid source chunk size')
  result+=b;cursor+=len(b)
 if cursor!=end:raise ValueError(f'Source chunk gap: ${cursor:04X} != ${end:04X}')
 return bytes(result)

def source_parts(bank,root=ROOT):
 if bank not in BANKS:raise ValueError('Bank is not in final-four reconstruction')
 obj=json.loads((root/source_file(bank)).read_text())
 if obj.get('schema')!=f'ys-bank{bank:02}-source-v1':raise ValueError('Source schema drift')
 pad=FILL_START[bank];payload_end=POINTER_START if bank==13 else pad
 payload=unpack_chunks(obj['unresolved_asset_chunks'],START,payload_end)
 sections=[(START,payload,'asset/resource bytes: semantics unresolved')]
 if bank==13:
  directory=obj.get('indexed_resource_directory')
  if type(directory)!=dict or set(directory)!={'start','pointers'} or directory['start']!=POINTER_START:
   raise ValueError('Bank13 directory schema drift')
  ptrs=directory['pointers']
  if type(ptrs)!=list or len(ptrs)!=50 or any(type(p)!=int or not START<=p<POINTER_START for p in ptrs):
   raise ValueError('Bank13 must have 50 in-bank resource pointers')
  if len(set(ptrs))!=50 or ptrs[0]!=0x8000 or ptrs[-1]!=0xA7FB:
   raise ValueError('Bank13 pointer count/alias/endpoints changed')
  sections.append((POINTER_START,b''.join(p.to_bytes(2,'little') for p in ptrs),
                    '50 resource pointers (target contents not semantically decoded)'))
 pad_obj=obj.get('end_fill')
 if pad_obj!={'start':pad,'count':END-pad,'byte':255}:
  raise ValueError('Bank-end FF fill drift')
 sections.append((pad,bytes([255])*(END-pad),'bank-end FF filler'))
 out={};inventory=[]
 for origin,data,kind in sections:
  if not START<=origin<END or not data or origin+len(data)>END:raise ValueError('Bank section bounds invalid')
  for i,v in enumerate(data):
   at=origin+i
   if at in out:raise ValueError(f'Overlapping source data at ${at:04X}')
   out[at]=v
  inventory.append({'start':origin,'end_exclusive':origin+len(data),'bytes':len(data),'classification':kind})
 if set(out)!=set(range(START,END)):raise ValueError('Bank source not complete or has gaps')
 raw=bytes(out[i] for i in range(START,END))
 stored=json.loads((root/digest_file(bank)).read_text())
 if stored!={'bank':bank,'bank_sha256':sha(raw),'size':SIZE}:
  raise ValueError('Independent bank source fingerprint drift')
 return raw,inventory

def full_bank(bank,root=ROOT):return source_parts(bank,root)[0]

def mixed_source(bank,root=ROOT):
 blob=full_bank(bank,root)
 lines=[f'; Ys SMS physical bank {bank:02}: ROM-independent 16-KiB image.',
        '; Asset payload is source-owned but semantic format is UNRESOLVED.',
        'org $8000',f'Bank{bank:02}_UnresolvedAssets:']
 stop=POINTER_START if bank==13 else FILL_START[bank]
 pc=START
 while pc<stop:
  end=min(pc+16,stop)
  lines.append('    db '+', '.join(f'${b:02X}' for b in blob[pc-START:end-START]))
  pc=end
 if bank==13:
  lines.append('Bank13_ResourcePointerDirectory50:')
  for pc in range(POINTER_START,POINTER_END,8):
   end=min(pc+8,POINTER_END)
   words=[int.from_bytes(blob[p-START:p-START+2],'little') for p in range(pc,end,2)]
   lines.append('    dw '+', '.join(f'${p:04X}' for p in words))
  pc=POINTER_END
 lines.append(f'Bank{bank:02}_VerifiedFFFill:')
 while pc<END:
  end=min(pc+16,END)
  lines.append('    db '+', '.join(f'${b:02X}' for b in blob[pc-START:end-START]))
  pc=end
 return '\n'.join(lines)+'\n'

def capture(owner_rom,root=ROOT):
 if len(owner_rom)!=0x40000 or sha(owner_rom)!=EXPECTED_SHA:raise ValueError('Wrong owner ROM fingerprint')
 for bank in BANKS:
  blob=owner_rom[bank*SIZE:(bank+1)*SIZE];pad=FILL_START[bank]
  if blob[pad-START:]!=b'\xff'*(END-pad):raise ValueError('Unverified padding boundary')
  raw=blob[:(POINTER_START-START if bank==13 else pad-START)]
  obj={'schema':f'ys-bank{bank:02}-source-v1','unresolved_asset_chunks':split_chunks(raw,START)}
  if bank==13:
   ptrs=[int.from_bytes(blob[pc-START:pc-START+2],'little') for pc in range(POINTER_START,POINTER_END,2)]
   obj['indexed_resource_directory']={'start':POINTER_START,'pointers':ptrs}
  obj['end_fill']={'start':pad,'count':END-pad,'byte':255}
  sf=root/source_file(bank);sf.parent.mkdir(parents=True,exist_ok=True);sf.write_text(json.dumps(obj,separators=(',',':'))+'\n')
  (root/digest_file(bank)).write_text(json.dumps({'bank':bank,'bank_sha256':sha(blob),'size':SIZE},indent=2)+'\n')
  if full_bank(bank,root)!=blob:raise ValueError(f'Bank{bank} captured bytes did not reconstruct')
  af=root/asm_file(bank);af.parent.mkdir(parents=True,exist_ok=True);af.write_text(mixed_source(bank,root))

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--capture',type=Path);p.add_argument('--verify-rom',type=Path)
 p.add_argument('--verify-mixed',action='store_true');p.add_argument('--bank',type=int,choices=BANKS)
 p.add_argument('--out-directory',type=Path)
 args=p.parse_args()
 if args.capture:capture(args.capture.read_bytes())
 banks=(args.bank,) if args.bank is not None else BANKS
 original=args.verify_rom.read_bytes() if args.verify_rom else None
 if original is not None and (len(original)!=0x40000 or sha(original)!=EXPECTED_SHA):raise ValueError('Incorrect original ROM fingerprint')
 for bank in banks:
  blob=full_bank(bank)
  if original is not None and original[bank*SIZE:(bank+1)*SIZE]!=blob:raise ValueError('Owner ROM differs from source')
  if args.verify_mixed:
   if assemble_mixed(mixed_source(bank))!=blob:raise ValueError('Mixed-assembly verification failed')
   checked=(ROOT/asm_file(bank)).read_text()
   if checked!=mixed_source(bank) or assemble_mixed(checked)!=blob:raise ValueError('Committed assembly drift')
  if args.out_directory:
   args.out_directory.mkdir(exist_ok=True,parents=True)
   (args.out_directory/f'bank{bank:02}.bin').write_bytes(blob)
  print(f'Bank {bank:02} independent source {SIZE} bytes SHA256 {sha(blob)}')
if __name__=='__main__':main()
