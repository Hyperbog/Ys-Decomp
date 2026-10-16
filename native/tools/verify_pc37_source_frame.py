#!/usr/bin/env python3
"""PC-37: verify an unchanged PC-34/36 source-run VDP frame export.

The frame is a single register/VRAM/CRAM snapshot rendered offline.
It is not an independently authenticated LCD/CRT output or gameplay frame.
"""
import json
from pathlib import Path
import sys
import zlib

HEADER = b"P6\n256 192\n255\n"
SIZE = 256 * 192 * 3
KEYS = {
    "schema", "source", "continued_steps", "stop_pc", "stop_irq",
    "stop_vblank", "captures", "completed", "display_enabled_captures",
    "selected_pc", "selected_step", "selected_irq", "selected_vblank",
    "selected_slot2", "selected_selector", "selected_display_enabled",
    "reg0", "reg1", "reg5", "reg6", "vram_crc32", "cram_crc32",
    "registers_crc32", "rgb_crc32", "sprite_overflow_lines",
    "sprite_collision_pixels"
}
BOOL = {"selected_display_enabled"}
STR = {"schema", "source", "stop_pc", "selected_pc"}
CRC = ("rgb_crc32", "vram_crc32", "cram_crc32", "registers_crc32")


def validate(frame_file, meta_file, pc34_file, pc35_file, pc36_file):
    frame = Path(frame_file).read_bytes()
    assert len(frame) == len(HEADER) + SIZE, "bad RGB frame length"
    assert frame.startswith(HEADER), "bad PPM P6 header"
    frame_crc = zlib.crc32(frame[len(HEADER):])
    meta = json.loads(Path(meta_file).read_text(encoding="utf-8"))
    p34 = json.loads(Path(pc34_file).read_text(encoding="utf-8"))
    p35 = json.loads(Path(pc35_file).read_text(encoding="utf-8"))
    p36 = json.loads(Path(pc36_file).read_text(encoding="utf-8"))
    assert set(meta) == KEYS, ("unexpected PC-37 fields", set(meta) ^ KEYS)
    assert meta["schema"] == "ys-pc37-original-vdp-frame-v1"
    assert meta["source"] == "pc34-same-run"
    assert meta["selected_pc"] == "053F"
    for key in KEYS - BOOL - STR:
        assert type(meta[key]) is int and meta[key] >= 0, key
    assert type(meta["selected_display_enabled"]) is bool
    for field in ("continued_steps", "stop_pc", "stop_irq", "stop_vblank"):
        assert meta[field] == p34[field] == p35[field] == p36[field], field
    assert meta["captures"] == meta["completed"] == p36["completed"] == 27
    assert p36["matched"] == p36["completed"] and p36["mismatched"] == 0
    assert p36["bytes_compared"] == 5184 and p36["bytes_different"] == 0
    # Fixed original ROM and fixed PC-34 controller schedule: reject
    # self-consistent but changed source/renderer output, as PC-36 does.
    assert meta["display_enabled_captures"] == 26
    assert meta["selected_step"] == 162573
    assert meta["rgb_crc32"] == 0x9FB8BB1E
    assert 0 <= meta["display_enabled_captures"] <= meta["captures"]
    assert meta["selected_display_enabled"] == (
        meta["display_enabled_captures"] > 0)
    assert meta["selected_display_enabled"] == (
        bool(meta["reg0"] & 0x04) and bool(meta["reg1"] & 0x40))
    assert 0 <= meta["selected_step"] < meta["continued_steps"]
    assert meta["selected_irq"] <= meta["stop_irq"]
    assert meta["selected_vblank"] <= meta["stop_vblank"]
    assert 0 <= meta["selected_slot2"] < 16
    assert 0 <= meta["selected_selector"] < 256
    for field in ("reg0", "reg1", "reg5", "reg6"):
        assert meta[field] < 256, field
    for field in CRC:
        assert meta[field] <= 0xFFFFFFFF, field
    assert meta["rgb_crc32"] == frame_crc, "rendered image CRC mismatch"
    assert meta["sprite_overflow_lines"] <= 192
    assert meta["sprite_collision_pixels"] <= 256 * 192
    print("PASS PC-37: actual Z80 source run, 27 SAT captures, "
          "bounded VDP frame fingerprint and independent PC-34/35/36 provenance")
    print("PC-37: display-eligible SAT captures={display_enabled_captures}, "
          "snapshot step={selected_step}, RGB CRC32={rgb_crc32:08X}".format(**meta))


if __name__ == "__main__":
    try:
        if len(sys.argv) != 6:
            raise ValueError(
                "usage: verify_pc37_source_frame.py FRAME.ppm PC37.json "
                "PC34.json PC35.json PC36.json")
        validate(*sys.argv[1:])
    except (ValueError, AssertionError, OSError, KeyError, TypeError) as err:
        sys.exit("FAIL PC-37 source frame evidence: " + str(err))
