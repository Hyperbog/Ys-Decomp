"""R1b diagnostic gates: pinned source patches, actual trace parsing and RAM offsets."""
import sys
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from diagnostics.live_sp_overlay import PATCHES, apply_overlay
from diagnostics.frame_and_ram_probe import first_ram_difference, mismatches, RAM_BYTES
from diagnostics.watch_pc_probe import HEADER as PC_HEADER, read_watch, difference
from verify_vdp_parity import HEADER, load


class R1bDiagnosticTests(unittest.TestCase):
    def test_pinned_overlay_changes_only_exact_anchor_sites(self):
        source = "\n".join(before for before, _ in PATCHES)
        patched = apply_overlay(source)
        for before, after in PATCHES:
            self.assertIn(after, patched)
            self.assertNotEqual(patched, source)
        with self.assertRaisesRegex(ValueError, "pinned upstream code mismatch"):
            apply_overlay(patched)
        with self.assertRaisesRegex(ValueError, "pinned upstream code mismatch"):
            apply_overlay(source.replace("static z80  g_hz;", "static z80 g_hz;"))

    def test_crlf_preserved(self):
        source = "\r\n".join(before for before, _ in PATCHES)
        patched = apply_overlay(source)
        self.assertNotIn("\n", patched.replace("\r\n", ""))

    def test_corrected_sp_is_compared_strictly(self):
        base = ("1", "a"*16, "b"*16, "c"*16, "d"*16,
                "00", "01", "02", "03", "dfee")
        other = (*base[:-1], "dff0")
        diffs = mismatches([base], [other])
        self.assertEqual(diffs["SP"], [1])
        self.assertEqual(diffs["WRAM"], [])

    def test_mismatch_frames_keep_all_state_fields(self):
        row = ["1", "a"*16, "b"*16, "c"*16, "d"*16,
               "00", "01", "02", "03", "dfee"]
        changed = list(row)
        changed[4] = "f"*16
        changed[9] = "dff0"
        result = mismatches([tuple(row)], [tuple(changed)])
        self.assertEqual(result["WRAM"], [1])
        self.assertEqual(result["SP"], [1])
        self.assertEqual(result["VRAM"], [])

    def test_ram_first_byte_cpu_mapping(self):
        data = bytearray(RAM_BYTES)
        other = bytearray(data)
        other[0x198] = 0x80
        self.assertEqual(first_ram_difference(data, other), (0xC198, 0, 0x80))
        self.assertIsNone(first_ram_difference(data, bytes(data)))
        with self.assertRaisesRegex(ValueError, "8192"):
            first_ram_difference(b"bad", b"bad")

    def test_matched_pc_watchpoint_registers_and_cycles(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "watch.csv"
            columns = ["0", "100", *["0"]*14]
            path.write_text(PC_HEADER + "\\n" + ",".join(columns) + "\\n")
            values = read_watch(path)
            self.assertEqual(len(values), 1)
            self.assertEqual(difference(values, values), "MATCHED 1 hits in 16 fields")
            changed = [list(values[0])]
            changed[0][12] = 4
            self.assertIn("field=sp", difference(values, changed))
            changed = [list(values[0])]
            changed[0][1] = 101
            self.assertIn("field=cyc", difference(values, changed))
            self.assertEqual(difference([], []), "NO_HITS")

    def test_watchpoint_rejects_bad_hit_and_nondecimal_registers(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "watch.csv"
            for token in ("999", "bad", "-1"):
                with self.subTest(value=token):
                    parts = [token, "100", *["0"]*14]
                    p.write_text(PC_HEADER + "\\n" + ",".join(parts) + "\\n")
                    with self.assertRaises(ValueError):
                        read_watch(p)

    def test_trace_loader_rejects_bad_frame(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "frame.csv"
            p.write_text(HEADER + "\n2," + ",".join(["0"*16]*4) +
                         ",00,00,00,00,dfee\n")
            with self.assertRaisesRegex(ValueError, "nonconsecutive"):
                load(p, 1)


if __name__ == "__main__":
    unittest.main()
