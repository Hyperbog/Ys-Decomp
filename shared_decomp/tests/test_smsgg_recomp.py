"""ROM-safe, independent smoke tests for the SMS/GG adapter."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zlib


SCRIPT = Path(__file__).resolve().parents[1] / "smsgg_recomp.py"


class SmsggAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.rom = self.root / "fixture.sms"
        self.rom.write_bytes(bytes(range(128)))
        self.manifest = self.root / "manifest.json"
        self.identity = {
            "sha256": hashlib.sha256(self.rom.read_bytes()).hexdigest(),
            "rom_bytes": 128,
        }
        self.write_manifest()
        self.config = self.root / "game.toml"
        self.config.write_text(
            '[game]\noutput_prefix = "ystest"\nplatform = "sms"\n'
            'rom = "external.sms"\n[mapper]\nkind = "sega"\n',
            encoding="utf-8",
        )
        self.tool = self.root / "fake-smsrecomp"
        self.tool.write_text(
            "#!/usr/bin/env python3\n"
            "from pathlib import Path\n"
            "import sys\n"
            "cfg = Path(sys.argv[sys.argv.index('--game') + 1])\n"
            "out = cfg.parent / 'generated'\n"
            "out.mkdir()\n"
            "for part in ('full', 'dispatch', 'layout'):\n"
            "    (out / ('ystest_' + part + '.c')).write_text('/* fixture */\\n')\n",
            encoding="utf-8",
        )
        self.tool.chmod(0o755)

    def write_manifest(self):
        self.manifest.write_text(json.dumps(self.identity), encoding="utf-8")

    def invoke(self, *extras):
        return subprocess.run(
            [
                sys.executable, str(SCRIPT),
                "--rom", str(self.rom),
                "--manifest", str(self.manifest),
                "--config", str(self.config),
                *extras,
            ],
            capture_output=True, text=True, check=False,
        )

    def test_preflight_uses_exact_hash_without_tool(self):
        result = self.invoke("--preflight")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(self.identity["sha256"], result.stdout)
        self.assertFalse((self.root / "generated").exists())

    def test_modified_rom_rejected(self):
        self.rom.write_bytes(self.rom.read_bytes() + b"!")
        result = self.invoke("--preflight")
        self.assertEqual(result.returncode, 2)
        self.assertIn("ROM identity mismatch", result.stderr)

    def test_preflight_rejects_manifest_crc_mismatch(self):
        self.identity["crc32"] = "00000000"
        self.write_manifest()
        result = self.invoke("--preflight")
        self.assertEqual(result.returncode, 2)
        self.assertIn("ROM CRC-32 mismatch", result.stderr)

    def test_preflight_rejects_config_crc_mismatch(self):
        self.config.write_text(self.config.read_text().replace(
            'rom = "external.sms"', 'rom = "external.sms"\ncrc32 = 0'),
            encoding="utf-8")
        result = self.invoke("--preflight")
        self.assertEqual(result.returncode, 2)
        self.assertIn("game.toml CRC-32 mismatch", result.stderr)

    def test_preflight_accepts_matching_crc(self):
        crc = zlib.crc32(self.rom.read_bytes())
        self.identity["crc32"] = f"{crc:08X}"
        self.write_manifest()
        self.config.write_text(self.config.read_text().replace(
            'rom = "external.sms"', f'rom = "external.sms"\ncrc32 = 0x{crc:08X}'),
            encoding="utf-8")
        result = self.invoke("--preflight")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"{crc:08X}", result.stdout)

    @unittest.skipIf(os.name == "nt", "mock executable is a POSIX script")
    def test_generates_three_outputs_and_evidence(self):
        result = self.invoke("--tool", str(self.tool))
        self.assertEqual(result.returncode, 0, result.stderr)
        out = self.root / "generated"
        report = json.loads((out / "report.json").read_text())
        self.assertEqual(report["stage"], "generated-c-only")
        self.assertFalse(report["runtime_verified"])
        self.assertEqual(len(report["outputs"]), 3)
        self.assertEqual(report["rom_crc32"], f"{zlib.crc32(self.rom.read_bytes()):08X}")
        self.assertEqual(self.invoke("--tool", str(self.tool),
                                     "--verify-generated").returncode, 0)
        for name, evidence in report["outputs"].items():
            self.assertEqual(hashlib.sha256((out / name).read_bytes()).hexdigest(),
                             evidence["sha256"])

    @unittest.skipIf(os.name == "nt", "mock executable is a POSIX script")
    def test_generated_output_tampering_is_detected(self):
        generated = self.invoke("--tool", str(self.tool))
        self.assertEqual(generated.returncode, 0, generated.stderr)
        target = self.root / "generated" / "ystest_dispatch.c"
        target.write_text("/* tampered */\n", encoding="utf-8")
        result = self.invoke("--tool", str(self.tool), "--verify-generated")
        self.assertEqual(result.returncode, 2)
        self.assertIn("generated output integrity mismatch", result.stderr)

    @unittest.skipIf(os.name == "nt", "mock executable is a POSIX script")
    def test_stale_outputs_not_accepted_after_config_change(self):
        generated = self.invoke("--tool", str(self.tool))
        self.assertEqual(generated.returncode, 0, generated.stderr)
        self.config.write_text(self.config.read_text() + "\n# changed config\n",
                               encoding="utf-8")
        result = self.invoke("--tool", str(self.tool), "--verify-generated")
        self.assertEqual(result.returncode, 2)
        self.assertIn("generated report config_sha256", result.stderr)

    @unittest.skipIf(os.name == "nt", "mock executable is a POSIX script")
    def test_missing_generated_file_rejected(self):
        text = self.tool.read_text().replace("('full', 'dispatch', 'layout')",
                                             "('full', 'layout')")
        self.tool.write_text(text)
        result = self.invoke("--tool", str(self.tool))
        self.assertEqual(result.returncode, 2)
        self.assertIn("did not produce ystest_dispatch.c", result.stderr)
        self.assertFalse((self.root / "generated").exists())


if __name__ == "__main__":
    unittest.main()
