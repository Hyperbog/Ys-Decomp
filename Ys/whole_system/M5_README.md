# Whole-system milestone 5: independent sound bank reconstruction

| Metric | M4 | M5 |
|---|---:|---:|
| Complete physical banks | 0,3,6,7 | **0,2,3,6,7** |
| Whole-bank source bytes | 65,536 | **81,920** |
| All source-backed bytes | 70,583 | **83,182 (31.73%)** |
| Remaining original-ROM fallback | 191,561 | **178,962** |
| Newly source-backed | — | **12,599** |
| Newly recovered short Z80 code regions | — | **16 instruction bytes** |
| Variable song data body records individually bounded | — | **24** |
| Exact complete 256-KiB ROM SHA match | yes | **yes** |

A complete bank means **byte-reconstructable**, not that every game subsystem
has been understood. Sound-related tables were identified and reproduced, but
most of the 12,583 newly sourced data bytes are mechanically preserved, not
symbolically interpreted. See `wholebank02/README.md` for boundaries and open
questions. The bank2 original sound code and typed song headers were source-backed
in earlier phases and are not counted again.

## Sound-system evidence

The original sound bank's ROM-matched instructions reference the two 73-word
note tables, the sequence directory, and the 55-entry song directory. The same
code emits commands via PSG `$7F`, YM2413 address `$F0`, and YM2413 data `$F1`.
The directory-to-record spans and all 24 late-song event payloads are checked
without decoding unknown command meanings. Neither independent emulator audio
execution nor external WLA-DX validation occurred in this milestone.

## Independent build commands

```
cd Ys
make five-bank-source
make bank02-source
make five-bank-rom-verify ROM='/path/to/Ys.sms'
make system-m5-verify ROM='/path/to/Ys.sms'
make five-bank-wla-prepare
```

The complete ROM still requires fallback for the **11 remaining physical banks**.
Next priorities: **bank 1 control and input**, then source-only closure of
bank 4 and other low-coverage banks. Parallel research: interpret bank2's
music-event opcodes through Z80 runtime traces and integrate real WLA-DX
assembly / full SMS emulation as soon as those executables are available.
