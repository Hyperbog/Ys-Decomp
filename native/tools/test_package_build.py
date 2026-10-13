"""Local tests of release labels, evidence gates, packaging and ROM exclusion."""
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import package_build as release


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.build = self.base / "build"
        self.build.mkdir()
        self.output = self.base / "dist"
        self.gates = self.base / "gates.json"
        self.state = {"schema_version": 1, "checkpoint": "M40",
                      "gates": {name: {"passed": False, "evidence": ""}
                                for group in release.REQUIRED.values()
                                for name in group}}
        self.save_gates()
        for name in release.EXE_NAMES:
            (self.build / name).write_bytes(b"fixture-executable:" + name.encode())

    def save_gates(self):
        self.gates.write_text(json.dumps(self.state), encoding="utf-8")

    def archive(self, channel="dev"):
        return release.package(channel, "linux-x64", self.build, self.output,
                               self.gates, "a" * 40)

    def test_development_bundle_contains_diagnostics_and_hashes(self):
        path = self.archive()
        self.assertEqual(path.name, "ys-m40-dev-linux-x64-aaaaaaaa.zip")
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            self.assertEqual(names, {"bin/ys-native-info", "bin/ys-native-probe",
                                     "bin/ys-native-trace", "bin/ys-native-preview",
                                     "bin/ys-native-frames", "bin/ys-native-timing",
                                     "bin/ys-native-timed-rom",
                                     "README.txt", "manifest.json",
                                     "SHA256SUMS.txt"})
            manifest = json.loads(archive.read("manifest.json"))
            self.assertFalse(manifest["playable"])
            self.assertFalse(manifest["rom_included"])
            self.assertEqual(manifest["channel"], "dev")
            self.assertEqual(manifest["checkpoint"], "M40")
            self.assertEqual(manifest["entrypoint"], "bin/ys-native-info")
            self.assertIsNone(manifest["graphical_diagnostic"])
            self.assertIn(b"NOT A PLAYABLE PC GAME", archive.read("README.txt"))
            self.assertIn(b"ys-native-preview synthetic.ppm",archive.read("README.txt"))
            for name, digest in manifest["sha256"].items():
                self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(),
                                 digest)
            self.assertFalse(any(name.lower().endswith((".sms", ".nes", ".rom"))
                                 for name in names))

    def test_promotion_blocked_without_verified_evidence(self):
        for channel in ("alpha", "beta", "final"):
            with self.subTest(channel=channel):
                with self.assertRaisesRegex(ValueError, "unmet evidence gates"):
                    self.archive(channel)

    def test_passed_without_evidence_still_blocks(self):
        for name in release.REQUIRED["alpha"]:
            self.state["gates"][name]["passed"] = True
        self.save_gates()
        with self.assertRaisesRegex(ValueError, "unmet evidence gates"):
            self.archive("alpha")

    def test_proven_alpha_requires_real_native_game_binary(self):
        for name in release.REQUIRED["alpha"]:
            self.state["gates"][name] = {
                "passed": True, "evidence": "tests/recorded-case-for-" + name}
        self.save_gates()
        with self.assertRaisesRegex(FileNotFoundError, "ys-native-game"):
            self.archive("alpha")
        (self.build / "ys-native-game").write_bytes(b"test-only-fake-game")
        path = self.archive("alpha")
        with zipfile.ZipFile(path) as archive:
            self.assertTrue(json.loads(archive.read("manifest.json"))["playable"])
            self.assertIn("bin/ys-native-game", archive.namelist())

    def test_beta_final_require_all_lower_stage_gates(self):
        for name in release.REQUIRED["alpha"]:
            self.state["gates"][name] = {"passed": True, "evidence": "checked"}
        self.save_gates()
        missing = release.promotion_errors("beta", self.state)
        self.assertEqual(set(missing), set(release.REQUIRED["beta"]))
        for name in release.REQUIRED["beta"]:
            self.state["gates"][name] = {"passed": True, "evidence": "checked"}
        self.save_gates()
        self.assertEqual(set(release.promotion_errors("final", self.state)),
                         set(release.REQUIRED["final"]))

    def test_invalid_metadata_rejected(self):
        for bad in ("bad/path", "..", "with spaces"):
            with self.subTest(value=bad):
                with self.assertRaises(ValueError):
                    release.package("dev", bad, self.build, self.output,
                                    self.gates, "a" * 40)
        self.state["checkpoint"] = "../unsafe"
        self.save_gates()
        with self.assertRaises(ValueError):
            self.archive()

    def test_optional_sdl_viewer_is_not_mandatory(self):
        # The headless distribution is complete without system SDL2.
        path = self.archive()
        with zipfile.ZipFile(path) as z:
            self.assertNotIn("bin/ys-native-display",z.namelist())
        (self.build / "ys-native-display").write_bytes(b"SDL2 fixture executable")
        path = self.archive()
        with zipfile.ZipFile(path) as z:
            self.assertIn("bin/ys-native-display",z.namelist())
            manifest=json.loads(z.read("manifest.json"))
            self.assertFalse(manifest["playable"])
            self.assertIn("bin/ys-native-display",manifest["sha256"])

    def test_windows_exe_requires_functioning_gui_target(self):
        for name in release.EXE_NAMES:
            (self.build / "Release").mkdir(exist_ok=True)
            (self.build / "Release" / (name + ".exe")).write_bytes(b"MZ-test")
        with self.assertRaisesRegex(FileNotFoundError, "ys-native-window"):
            release.package("dev", "windows-x64", self.build, self.output,
                            self.gates, "b" * 40)

        (self.build / "Release" / "ys-native-window.exe").write_bytes(b"MZ-gui-test")
        archive = release.package("dev", "windows-x64", self.build, self.output,
                                  self.gates, "b" * 40)
        with zipfile.ZipFile(archive) as z:
            for name in (*release.EXE_NAMES, "ys-native-window"):
                self.assertIn("bin/" + name + ".exe", z.namelist())
            self.assertIn("START_HERE.cmd", z.namelist())
            self.assertIn("README.txt", z.namelist())
            self.assertIn("manifest.json", z.namelist())
            self.assertIn("SHA256SUMS.txt", z.namelist())
            self.assertIn(b"EXTRACT THE ENTIRE ZIP", z.read("README.txt"))
            self.assertIn(b"choice /C 123456", z.read("START_HERE.cmd"))
            self.assertIn(b"pause", z.read("START_HERE.cmd"))
            self.assertIn(b"ys-native-timed-rom.exe", z.read("START_HERE.cmd"))
            self.assertIn(b"--frame", z.read("START_HERE.cmd"))
            self.assertIn(b"--ppm", z.read("START_HERE.cmd"))
            manifest = json.loads(z.read("manifest.json"))
            self.assertEqual(manifest["entrypoint"], "START_HERE.cmd")
            self.assertEqual(manifest["graphical_diagnostic"],
                             "bin/ys-native-window.exe")
            self.assertFalse(manifest["playable"])
            self.assertFalse(manifest["rom_included"])
            self.assertIn("START_HERE.cmd", manifest["sha256"])
            self.assertIn("bin/ys-native-window.exe", manifest["sha256"])


if __name__ == "__main__":
    unittest.main()
