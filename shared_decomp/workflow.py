#!/usr/bin/env python3
"""Portable, fail-closed controls for AI-assisted decompilation projects.

Does not disassemble/compile games or certify semantic correctness.
Requires only Python 3.9+ standard library. Run `python workflow.py --help`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def save_atomic(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".decomp-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(obj, out, indent=2, sort_keys=True)
            out.write("\n")
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def check_manifest(manifest, binary=None):
    """Validate full partition ownership and explicitly qualified byte accounting."""
    errors = []
    if manifest.get("schema") != "decomp-project-v1":
        errors.append("unsupported manifest schema")
    b = manifest.get("binary", {})
    size = b.get("size")
    sha = b.get("sha256")
    if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
        errors.append("binary.size must be a positive integer")
        size = 0
    if not isinstance(sha, str) or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
        errors.append("binary.sha256 must be a lowercase SHA-256 hex digest")
    parts = manifest.get("partitions", [])
    if not isinstance(parts, list) or not parts:
        errors.append("at least one partition required")
        parts = []
    cursor = backed = fallback = 0
    seen = set()
    verified_partitions = []
    try:
        parts = sorted(parts, key=lambda x: x["offset"])
    except (KeyError, TypeError):
        errors.append("partition missing sortable offset")
        parts = []
    bytes_input = None
    if binary is not None:
        try:
            with Path(binary).open("rb") as inp:
                bytes_input = inp.read()
        except OSError as exc:
            errors.append(f"cannot read binary: {exc}")
        if bytes_input is not None:
            if len(bytes_input) != size:
                errors.append(f"binary size mismatch: {len(bytes_input)} != {size}")
            actual = hashlib.sha256(bytes_input).hexdigest()
            if actual != sha:
                errors.append("binary SHA-256 mismatch")
    for part in parts:
        name = part.get("name", "<unnamed>")
        offset, length = part.get("offset"), part.get("length")
        source, raw = part.get("source_backed_bytes"), part.get("fallback_bytes")
        complete = part.get("source_only_complete")
        if name in seen:
            errors.append(f"duplicate partition name: {name}")
        seen.add(name)
        if any(not isinstance(v, int) or isinstance(v, bool) for v in (offset, length, source, raw)):
            errors.append(f"{name}: offset, length and counts must be integers")
            continue
        if length <= 0 or min(offset, source, raw) < 0 or source + raw != length:
            errors.append(f"{name}: invalid length/count accounting")
        if offset != cursor:
            errors.append(f"{name}: overlap or gap at offset {cursor:#x}, got {offset:#x}")
        if complete is not True and complete is not False:
            errors.append(f"{name}: source_only_complete must be boolean")
        if complete is not (raw == 0 and source == length):
            errors.append(f"{name}: source_only_complete disagrees with fallback count")
        semantic = part.get("semantic_status")
        if semantic not in {"unresolved", "partial", "understood"}:
            errors.append(f"{name}: semantic_status must be unresolved/partial/understood")
        for flag in ("external_assembler_verified", "runtime_verified"):
            if not isinstance(part.get(flag), bool):
                errors.append(f"{name}: {flag} must be boolean")
        if bytes_input is not None:
            expected = part.get("sha256")
            actual = hashlib.sha256(bytes_input[offset:offset + length]).hexdigest()
            if expected is not None and expected != actual:
                errors.append(f"{name}: partition SHA-256 mismatch")
            verified_partitions.append(name)
        cursor = offset + length
        backed += source
        fallback += raw
    if cursor != size:
        errors.append(f"partitions end at {cursor}, expected {size}")
    if backed + fallback != size:
        errors.append(f"total count {backed + fallback} != {size}")
    return {
        "project": manifest.get("project"),
        "valid": not errors,
        "errors": errors,
        "partition_count": len(parts),
        "source_backed_bytes_reported": backed,
        "fallback_bytes_reported": fallback,
        "source_only_partitions_reported": [p.get("name") for p in parts if p.get("source_only_complete")],
        "binary_digest_verified": bytes_input is not None and sha == hashlib.sha256(bytes_input).hexdigest(),
        "partition_digests_checked": verified_partitions,
        "qualifications": [
            "Source-backed accounting comes from manifest claims; this audit does not assemble source.",
            "An exact binary digest check does not establish emulator/gameplay correctness.",
            "Semantic status, external assembler evidence, and runtime evidence are separate gates.",
        ],
    }


def resolve(manifest_path, subpath):
    p = Path(subpath)
    if p.is_absolute():
        return p
    return Path(manifest_path).resolve().parent / p


def addr(value):
    if isinstance(value, int):
        return value
    # Legacy project ledgers store hexadecimal addresses as unprefixed strings.
    s = value.strip().lower()
    return int(s, 16)


def context(manifest, manifest_path, bank, address, limit):
    sources = manifest.get("context_sources", {})
    symbols = load(resolve(manifest_path, sources["symbols"])).get("symbols", []) if sources.get("symbols") else []
    references = load(resolve(manifest_path, sources["references"])).get("references", []) if sources.get("references") else []
    matching = [s for s in symbols if s.get("address_space") == "ROM" and s.get("physical_bank") == bank and addr(s["cpu_address"]) == address]
    incoming = []
    at_entry = []
    for ref in references:
        try:
            if addr(ref["target_cpu"]) == address and ref.get("proven_target_bank") == bank:
                incoming.append(ref)
            if ref.get("from_bank") == bank and addr(ref["from_cpu"]) == address:
                at_entry.append(ref)
        except (KeyError, ValueError, TypeError):
            continue
    incoming.sort(key=lambda r: (r.get("from_bank", -1), addr(r.get("from_cpu", "0"))))
    at_entry.sort(key=lambda r: addr(r.get("target_cpu", "0")))
    return {
        "target": {"physical_bank": bank, "cpu_address": f"{address:04X}"},
        "symbols_at_address": matching,
        "incoming_proven_static_refs": incoming[:limit],
        "outgoing_refs_at_entry_instruction": at_entry[:limit],
        "incoming_refs_total": len(incoming),
        "qualification": "Only existing static references are included. This is not a complete function CFG, ABI signature, or execution proof; mapper-dependent edges without proven banks are excluded.",
    }


def check_locked(state):
    for p, original in state["locked_sha256"].items():
        try:
            current = digest(p)
        except OSError:
            raise ValueError(f"locked file missing/unreadable: {p}")
        if current != original:
            raise ValueError(f"locked reference changed: {p}")


def guard_init(paths, max_stalls):
    if max_stalls < 1 or max_stalls > 20:
        raise ValueError("max_stalls must be within 1..20")
    if not paths:
        raise ValueError("at least one protected file required")
    return {"schema": "decomp-guard-v1", "locked_sha256": {str(Path(p).resolve()): digest(p) for p in paths}, "best_score": None,
            "max_stalls": max_stalls, "stalls": 0, "status": "CONTINUE", "attempts": []}


def guard_record(state, score, label):
    if state.get("schema") != "decomp-guard-v1":
        raise ValueError("invalid guard state")
    if state["status"] == "STOP":
        raise ValueError("guard already stopped; open a new task after review")
    check_locked(state)
    if not math.isfinite(score) or score < 0 or score > 100:
        raise ValueError("score must be finite and between 0 and 100")
    best = state["best_score"]
    improved = best is None or score > best
    state["best_score"] = score if improved else best
    state["stalls"] = 0 if improved else state["stalls"] + 1
    state["status"] = "STOP" if state["stalls"] >= state["max_stalls"] else "CONTINUE"
    state["attempts"].append({"label": label, "score": score, "improved": improved, "stalls": state["stalls"]})
    return state


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    audit_p = sub.add_parser("audit", help="validate whole-binary partition accounting; optionally hash an original binary")
    audit_p.add_argument("--manifest", required=True)
    audit_p.add_argument("--binary")
    audit_p.add_argument("--output")
    ctx_p = sub.add_parser("context", help="assemble bounded bank-aware symbol/cross-reference context")
    ctx_p.add_argument("--manifest", required=True)
    ctx_p.add_argument("--bank", type=lambda s: int(s, 0), required=True)
    ctx_p.add_argument("--address", type=lambda s: int(s, 0), required=True)
    ctx_p.add_argument("--limit", type=int, default=12)
    ctx_p.add_argument("--output")
    init_p = sub.add_parser("guard-init", help="create protected-target score state")
    init_p.add_argument("--state", required=True)
    init_p.add_argument("--lock", action="append", required=True)
    init_p.add_argument("--max-stalls", type=int, default=2)
    record_p = sub.add_parser("guard-record", help="check locked files, append matching score, halt on repeated stalls")
    record_p.add_argument("--state", required=True)
    record_p.add_argument("--score", type=float, required=True)
    record_p.add_argument("--label", required=True)
    a = parser.parse_args(argv)
    try:
        if a.cmd == "audit":
            result = check_manifest(load(a.manifest), a.binary)
        elif a.cmd == "context":
            if a.limit < 1 or a.limit > 100:
                raise ValueError("limit must be 1..100")
            result = context(load(a.manifest), a.manifest, a.bank, a.address, a.limit)
        elif a.cmd == "guard-init":
            if Path(a.state).exists():
                raise ValueError("guard state already exists; refusing to reset attempts")
            result = guard_init(a.lock, a.max_stalls)
            save_atomic(a.state, result)
        else:
            result = guard_record(load(a.state), a.score, a.label)
            save_atomic(a.state, result)
        if a.cmd in {"audit", "context"} and a.output:
            save_atomic(a.output, result)
        print(json.dumps(result, indent=2, sort_keys=True))
        if a.cmd == "audit" and not result["valid"]:
            return 2
        if a.cmd == "guard-record" and result["status"] == "STOP":
            return 3
        return 0
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
