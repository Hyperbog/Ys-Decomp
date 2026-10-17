"""Independent strict/check-failure tests for pinned upstream frame trace."""
import sys
from pathlib import Path
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verify_vdp_parity import HEADER, compare


def row(frame, vram="a" * 16, wram="d" * 16):
    return f"{frame},{vram},{'b'*16},{'c'*16},{wram},00,01,02,03,fffe"


class FrameParityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        d = Path(self.temp.name)
        self.a, self.b = d / "recompiled.csv", d / "interpreter.csv"
        self.rows = [row(1), row(2)]
        self.write(self.rows, self.rows)

    def write(self, left, right):
        self.a.write_text("\n".join([HEADER, *left]) + "\n")
        self.b.write_text("\n".join([HEADER, *right]) + "\n")

    def test_matching_two_frames(self):
        self.assertIn("2 complete frame", compare(self.a, self.b, 2))

    def test_first_divergent_frame_and_field(self):
        self.write(self.rows, [self.rows[0], row(2, wram="e" * 16)])
        with self.assertRaisesRegex(ValueError, "frame=2, field=WRAM"):
            compare(self.a, self.b, 2)

    def test_corrupt_hash_is_rejected(self):
        self.write([row(1, vram="X" * 16), row(2)], self.rows)
        with self.assertRaisesRegex(ValueError, "invalid VRAM"):
            compare(self.a, self.b, 2)

    def test_duplicate_missing_or_truncated_frame_fails(self):
        for rows in ([row(1), row(1)], [row(1)], [row(1), "2,0"]):
            with self.subTest(rows=rows):
                self.write(rows, self.rows)
                with self.assertRaises(ValueError):
                    compare(self.a, self.b, 2)

    def test_unexpected_header_fails(self):
        self.a.write_text("frame,missing,columns\n" + "\n".join(self.rows))
        with self.assertRaisesRegex(ValueError, "header"):
            compare(self.a, self.b, 2)

    def test_invalid_frame_budget_fails(self):
        for n in (0, -1, 36001, True):
            with self.subTest(n=n):
                with self.assertRaises(ValueError):
                    compare(self.a, self.b, n)


if __name__ == "__main__":
    unittest.main()
