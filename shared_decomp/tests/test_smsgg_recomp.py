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
            "    (out / ('ystest_' + part + '.c')).write_text('/* fixture */\\n')\n"
            "    (out / 'ystest_funcs.h').write_text('/* prototypes */\\n')\n",
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
    def test_generates_four_outputs_and_evidence(self):
        result = self.invoke("--tool", str(self.tool))
        self.assertEqual(result.returncode, 0, result.stderr)
        out = self.root / "generated"
        report = json.loads((out / "report.json").read_text())
        self.assertEqual(report["stage"], "generated-c-only")
        self.assertFalse(report["runtime_verified"])
        self.assertEqual(len(report["outputs"]), 4)
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


    @unittest.skipIf(os.name == "nt", "mock executable is a POSIX script")
    def test_missing_required_header_is_rejected(self):
        self.tool.write_text("".join(line for line in
            self.tool.read_text().splitlines(keepends=True)
            if "ystest_funcs.h" not in line))
        result = self.invoke("--tool", str(self.tool))
        self.assertEqual(result.returncode, 2)
        self.assertIn("did not produce ystest_funcs.h", result.stderr)
        self.assertFalse((self.root / "generated").exists())

    def test_manifest_boolean_size_rejected(self):
        self.identity["rom_bytes"] = True
        self.write_manifest()
        result = self.invoke("--preflight")
        self.assertEqual(result.returncode, 2)
        self.assertIn("exact ROM size", result.stderr)

    @unittest.skipIf(os.name == "nt", "POSIX symbolic links")
    def test_generated_report_symlink_rejected(self):
        result = self.invoke("--tool", str(self.tool))
        self.assertEqual(result.returncode, 0, result.stderr)
        report = self.root / "generated" / "report.json"
        original = self.root / "saved-report.json"
        original.write_bytes(report.read_bytes())
        report.unlink()
        report.symlink_to(original)
        outcome = self.invoke("--tool", str(self.tool), "--verify-generated")
        self.assertEqual(outcome.returncode, 2)
        self.assertIn("symbolic links", outcome.stderr)

    @unittest.skipIf(os.name == "nt", "POSIX symbolic links")
    def test_generated_output_directory_symlink_rejected(self):
        alternative = self.root / "elsewhere" / "generated"
        alternative.mkdir(parents=True)
        (self.root / "generated").symlink_to(alternative, target_is_directory=True)
        result = self.invoke("--tool", str(self.tool))
        self.assertEqual(result.returncode, 2)
        self.assertIn("must not be a symbolic link", result.stderr)
        self.assertEqual(list(alternative.iterdir()), [])

    @unittest.skipIf(os.name == "nt", "mock executable is a POSIX script")
    def test_generator_symlink_source_is_rejected(self):
        # Start from the known-working fake generator, then replace one
        # completed output with a symlink to the staged game.toml.
        # This tests adapter rejection, not parsing of a new mock script.
        self.tool.write_text(
            self.tool.read_text()
            + chr(10) + "(out / 'ystest_dispatch.c').unlink()"
            + chr(10) + "(out / 'ystest_dispatch.c').symlink_to(cfg)"
            + chr(10)
        )
        result = self.invoke("--tool", str(self.tool))
        self.assertEqual(result.returncode, 2)
        self.assertIn("did not produce ystest_dispatch.c", result.stderr)
        self.assertFalse((self.root / "generated").exists())

    @unittest.skipIf(os.name == "nt", "POSIX symbolic links")
    def test_preexisting_temp_symlink_not_followed(self):
        out = self.root / "generated"
        out.mkdir()
        secret = self.root / "sentinel.txt"
        secret.write_text("do not overwrite")
        (out / "ystest_dispatch.c.tmp").symlink_to(secret)
        result = self.invoke("--tool", str(self.tool))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(secret.read_text(), "do not overwrite")
        self.assertTrue((out / "ystest_dispatch.c.tmp").is_symlink())
        self.assertEqual(self.invoke("--tool", str(self.tool),
                                     "--verify-generated").returncode, 0)


if __name__ == "__main__":
    unittest.main()
