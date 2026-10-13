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
        self.state = {"schema_version": 1, "checkpoint": "M28",
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
        self.assertEqual(path.name, "ys-m28-dev-linux-x64-aaaaaaaa.zip")
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            self.assertEqual(names, {"bin/ys-native-info", "bin/ys-native-probe",
                                     "bin/ys-native-trace", "bin/ys-native-preview",
                                     "bin/ys-native-frames", "bin/ys-native-timing",
                                     "README.txt", "manifest.json",
                                     "SHA256SUMS.txt"})
            manifest = json.loads(archive.read("manifest.json"))
            self.assertFalse(manifest["playable"])
            self.assertFalse(manifest["rom_included"])
            self.assertEqual(manifest["channel"], "dev")
            self.assertEqual(manifest["checkpoint"], "M28")
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

    def test_windows_release_bin_layout(self):
        for name in release.EXE_NAMES:
            (self.build / "Release").mkdir(exist_ok=True)
            (self.build / "Release" / (name + ".exe")).write_bytes(b"MZ-test")
        archive = release.package("dev", "windows-x64", self.build, self.output,
                                  self.gates, "b" * 40)
        with zipfile.ZipFile(archive) as z:
            for name in release.EXE_NAMES:
                self.assertIn("bin/" + name + ".exe", z.namelist())


if __name__ == "__main__":
    unittest.main()
