#!/usr/bin/env python3
"""Create/check one readable 16-bank source-backed Ys SMS ROM master listing.

This is a deterministic *index/consolidation* of already checked-in complete
bank assembly sources. It does not redisassemble bytes, guess data as Z80
instructions, require the owner ROM, or emit a commercial binary cartridge.
The result is a reference text, NOT one 16-bank assembler translation unit:
banks 2..15 share mapper-visible CPU addresses $8000..$BFFF.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

try:
    from .build_sms_phase14 import ROOT, EXPECTED_SHA
    from .semantic_debt_m13 import make_report
except ImportError:
    # Also support the standalone invocation from within the Ys/ directory.
    from build_sms_phase14 import ROOT, EXPECTED_SHA
    from semantic_debt_m13 import make_report

SIZE = 0x4000
COUNT = 16
DEFAULT = ROOT / "whole_system" / "MASTER_ROM_LISTING.txt"
REPORT = ROOT / "whole_system" / "semantic_debt_m13.json"
BUILD = ROOT / "whole_system" / "build_report_m10.json"


def assembled_reference(root=ROOT):
    # The source semantic audit checks every ORG, Z80 instruction length,
    # DB/DW literal, overlap and bank boundary. This is not a raw hex dump.
    audited = make_report(root)
    if audited["bank_count"] != COUNT or (
        audited["mnemonic_bytes"] + audited["data_directive_bytes"]
    ) != SIZE * COUNT:
        raise ValueError("Original 16-bank source byte closure is incomplete")
    expected_audit = json.loads((root / "whole_system" /
                                 "semantic_debt_m13.json").read_text())
    if audited != expected_audit:
        raise ValueError("Source audit drift: rerun independently reviewed M13 audit")
    m10 = json.loads((root / "whole_system" /
                      "build_report_m10.json").read_text())
    if m10["rom_sha256"] != EXPECTED_SHA or m10["rom_bytes"] != SIZE * COUNT or (
        m10["source_only_complete_banks"] != list(range(COUNT))
    ):
        raise ValueError("M10 original cartridge source fingerprint mismatch")

    sections = [
        "; Ys: The Vanished Omens (USA/Europe) — Master ROM listing\n",
        "; Complete 16-physical-bank source-backed listing, 262144 bytes.\n",
        "; THIS TEXT IS A REFERENCE, NOT A SINGLE ASSEMBLABLE Z80 FILE.\n",
        "; All mapper slots 2..15 reuse CPU $8000..$BFFF.\n",
        "; Only original source-confirmed code has mnemonics; DB/DW remains data.\n",
        "; No ROM image is needed; sources already exist in src/wholebankXX/.\n",
        "; Cartridge SHA-256: " + EXPECTED_SHA + "\n",
        "; Instruction bytes: " + str(audited["mnemonic_bytes"]) + "\n",
        "; Data directive bytes: " + str(audited["data_directive_bytes"]) + "\n",
        "; Uncertain labels lower bound: " +
            str(audited["explicitly_uncertain_bytes_lower_bound"]) + "\n\n",
    ]
    for bank in range(COUNT):
        rel = "src/wholebank%02d/bank%02d_complete.asm" % (bank, bank)
        path = root / rel
        source = path.read_text(encoding="utf-8")
        sha = hashlib.sha256(source.encode("utf-8")).hexdigest()
        if audited["banks"][bank]["source_sha256"] != sha:
            raise ValueError("Bank %02d verified source SHA drift" % bank)
        begin = bank * SIZE
        end = begin + SIZE - 1
        cpu = 0 if bank == 0 else 0x4000 if bank == 1 else 0x8000
        sections += [
            "; " + "=" * 72 + "\n",
            "; PHYSICAL BANK %02d | ROM $%05X-$%05X | CPU $%04X-$%04X\n" %
            (bank, begin, end, cpu, cpu + SIZE - 1),
            "; Source: Ys/" + rel + "\n",
            "; Source SHA256: " + sha + "\n",
            "; Mnemonic bytes: %d; DB/DW bytes: %d\n" % (
                audited["banks"][bank]["mnemonic_bytes"],
                audited["banks"][bank]["db_bytes"] + audited["banks"][bank]["dw_bytes"]),
            "; " + "=" * 72 + "\n",
            source if source.endswith("\n") else source + "\n",
            "\n",
        ]
    return "".join(sections)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--out", type=Path,
                      help="Write master text to this path, without a ROM")
    mode.add_argument("--check", action="store_true",
                      help="Verify committed master text is exactly current source")
    args = parser.parse_args()
    wanted = assembled_reference()
    destination = args.out or DEFAULT
    if args.check:
        if not destination.is_file() or destination.read_text(
            encoding="utf-8"
        ) != wanted:
            raise ValueError("Stale/master listing differs from source; regenerate")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(wanted, encoding="utf-8")
    print("PASS Ys master ROM listing: 16 banks, 262144 verified source bytes,",
          len(wanted.encode("utf-8")), "text bytes;",
          "CHECKED" if args.check else "GENERATED", destination)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        sys.exit("FAIL Ys master ROM listing: " + str(exc))
