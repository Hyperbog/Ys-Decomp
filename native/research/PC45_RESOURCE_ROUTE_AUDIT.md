# PC-45 — fixed-bank resource records and 41-way state dispatch

**Scope:** Source-structure audit, not authenticated gameplay.
**Base:** Draft PC-44 branch. The stable Ys/M45 release is untouched.

## Connected source subsystem

The original fixed-bank Z80 sequence at CPU $1FE3–$2059 ties
together two previously separate 41-word tables:

- **$2533–$2584 resource directory:** 41 references to 23 distinct,
  consecutive, nine-byte records at $2585 + (9 × record index).
  Directory indices 0–22 reference unique records. Indices 23–40
  intentionally alias record 22, beginning at $264B.
- **$205A–$20AB handler dispatch:** 41 words selected from the original
  $C181 state byte through the original RST $08 dispatch call. Several
  different selectors legitimately share an instruction entry point.
  The correspondence is a static source table relation, not proof
  of reachable scenes or semantically unique game states.

## Nine-byte record format

| Offset | Original fixed-bank use | Confidence |
| --- | --- | --- |
| +0 | Cartridge bank mapped into slot 2 for first source | Source instruction |
| +1,+2 | Little-endian first source pointer, then call $0C20 | Source instruction |
| +3 | Cartridge bank mapped into slot 2 for second source | Source instruction |
| +4,+5 | Little-endian second source pointer, then call $0BEF with C=1 | Source instruction |
| +6 | Byte copied into WRAM $C193 | Source instruction |
| +7 | Byte copied into WRAM $C194 | Source instruction |
| +8, bits 0–3 | Masked with $0F and stored in WRAM $C11D | Source instruction |
| +8, bit 7 | Zero or one stored in WRAM $C198 | Source instruction |
| +8, bit 6 | Zero or one stored in WRAM $C19A | Source instruction |
| +8, bits 4–5 | No proven role established here | Unresolved |

Every first/second source address is in the cartridge CPU slot-2
range $8000–$BFFF. These pointer ranges alone do not establish
the decoded contents or the later game's behavior.

Among 23 unique records, three set bit 7 and one sets bit 6.
PC-44 previously recorded a genuine source-ROM write at $2041
with HL=$258D, the final byte of record 0. That original byte
is zero, consistent with the observed physical $C198 write
and all 13 subsequent bank-6 sprite-gate skips in that one
bounded 600,000-instruction continuation. No additional
original-game sprite producer was observed by this audit.

## Independent source and ROM gates

The PC-45 tool reads the existing independent source ledgers:
Ys/wholebank00/source.json, Ys/phase21/source.json,
Ys/phase6/coverage.json and Ys/phase6/regions.json. It:

1. Validates all 41 directory references, the 23-record partition,
   pointer ranges, state-dispatch references and source schemas.
2. Recreates and checks the historical SHA-256 digests of the
   82-byte resource directory, 207-byte record payload and
   82-byte handler table without reading a commercial ROM.
3. Optionally verifies those three spans and 25 significant
   original Z80 opcode sites against the SHA-verified,
   independently reconstructed 262,144-byte source-only ROM.
4. Optionally cross-checks the authentic PC-44 physical WRAM
   write's source byte at HL=$258D with record 0's high flag.
5. Runs six unittest cases, including malformed index aliases,
   pointers, flags, handler and digest tampering and fake ROM
   identity or PC-44 register/flag provenance.

Run from repository root:

    python3 -m unittest discover -s native/tools -p 'test_pc45_resource_routes.py' -v
    python3 native/tools/pc45_resource_routes.py
    python3 native/tools/pc45_resource_routes.py --rom /tmp/source-built-Ys.sms --pc44-writes /tmp/ys-pc44-writes.json --out /tmp/ys-pc45-routes.json

The optional ROM, PC-44 JSON and generated route report are kept
outside the repository. GitHub's existing PC-44 CI job creates the
source-only ROM and passive original-game write report before the
PC-45 gates execute.

## Evidence boundary

This work assigns original *field consumers* to all 23 distinct
source-backed records and binds them to 41 indexed dispatch entries.
It does not prove all states execute, label scenes, identify a player
sprite, decode the two compressed payload types, or demonstrate
independent SMS emulator/hardware equivalence. The native SDL2
prototype remains separate, and no original-game Alpha gate is met.
