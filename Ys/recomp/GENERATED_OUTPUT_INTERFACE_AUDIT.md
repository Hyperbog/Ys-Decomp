# External SMSRecomp four-file output — non-promoting interface audit

A user supplied these four **generated** files for review. The source
bytes themselves, commercial cartridge and binary runner are **not**
committed to Git. These SHA-256 fingerprints characterize only the
received files, not the original Ys ROM or provenance of the upstream
`SmsRecomp` binary:

| Uploaded file | SHA-256 |
| --- | --- |
| `ys_sms_full.c` | `be2d96cae95bdef7cda26454fffe4010222482b2577cdc4dbb377e4e0a0eaabb` |
| `ys_sms_dispatch.c` | `068b7dbab8ae98c07c3b71f2923178f43036f292dc381384ed5afab0f42d55c7` |
| `ys_sms_funcs.h` | `853a2e5602f29271f3e7139080f2d08d032a1c4bc7a4dc69b37f366c736e3ab4` |
| `ys_sms_layout.c` | `c7e79612405b8a98ca16f02999f72ff0596a7136f2093106471c053f3f4bd9c5` |

## Source bundle interface and coverage

Static inspection of the uploaded files (no compile, runner, or emulator
execution) found:

- 16 generated `void func(void)` definitions, matching 16 prototypes
  and 16 static dispatcher cases; these cover the reset/IRQ/NMI/RST
  vectors and 7 named `func_...` entries.
- 407 `SMS_PC(...)` markers containing 382 *distinct CPU addresses*;
  duplicate markers can represent overlapping entry functions.
- Nine literal `call_by_address(...)` targets that are **not**
  present in the generated dispatch table: `$8067`, `$8080`,
  `$80C0`, `$81D9`, `$8329`, `$837F`, `$8883`, `$8889`,
  `$8947`. The generated C explicitly relies on `sms_dispatch_miss()`
  on unresolved targets. No complete-game call coverage is implied.
- Despite its bank-aware comment, this particular dispatch source has
  no `sms_slot_bank` branch. The `game.toml` config has no speculative
  `[functions].extra` or jump-table seeds.
- Its generated `g_game_layout` initializer is empty, with the
  structure guarded by `SMSGG_HAVE_GAME_LAYOUT`.
- Both `ys_sms_full.c` and `ys_sms_dispatch.c` **include**
  `ys_sms_funcs.h`. The former adapter copied only three `.c` files,
  mistakenly omitting a header essential for compilation.

## Adapter correction (generation-contract infrastructure only)

`shared_decomp/smsgg_recomp.py` now requires, copies, hashes and
reverifies all four artifacts, including the generated header;
the synthetic generator and regression tests reject missing,
modified or symlinked headers. As before, it fails closed when
ROM identity/config/tool hashes do not match. The existing
`Ys/recomp/generated/` gitignore remains in force.

No generated C/header, binary game assets, source ROM or
unlicensed upstream tool is checked in. `runtime_verified` remains
false, and no original-player, native soundtrack, gameplay
equivalence, hardware timing, M45 or Alpha release claim changes.

This uploaded snapshot did **not** include the adapter
`report.json`, upstream tool executable/hash, and a verified runner
ABI. Therefore its actual provenance against the checked-in
original-ROM SHA-256 and its ability to link/run cannot be established
from these four files alone. Next evidence: capture a complete
four-output `make recomp-generate / recomp-verify` run using the
user-owned original ROM and external `SmsRecomp` tool, then
separately test dispatch completeness/runner ABI against source
checkpoint traces.
