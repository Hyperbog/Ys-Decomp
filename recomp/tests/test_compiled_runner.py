"""R1: compile/link four mock SmsRecomp outputs with the real C compiler.

Synthetic ABI fixture only. Original Ys-generated C is NOT exercised here.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
ADAPTER = ROOT / "shared_decomp/smsgg_recomp.py"
BUILDER = ROOT / "recomp/compile_generated.py"


class R1CompileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.p = Path(self.temp.name)
        self.rom = self.p / "owned.sms"
        self.rom.write_bytes(b"independent synthetic fixture")
        self.manifest = self.p / "manifest.json"
        self.manifest.write_text(json.dumps({
            "rom_bytes": len(self.rom.read_bytes()),
            "sha256": hashlib.sha256(self.rom.read_bytes()).hexdigest(),
        }))
        self.config = self.p / "game.toml"
        self.config.write_text('[game]\noutput_prefix="ystest"\nplatform="sms"\n'
                               'rom="owned.sms"\n[mapper]\nkind="sega"\n')
        self.tool = self.p / "mock-generator"
        self.tool.write_text('mock executable (never run by this test)')
        self.generated = self.p / "generated"
        self.build = self.p / "build"
        self.build.mkdir()
        self.upstream = self.p / "upstream"
        source = {
            "runner/main.c":
                '#include "sms_runtime.h"\n'
                'int main(void){ call_by_address(0); return g_z80.a==3?0:1; }\n',
            "runner/glue.c":
                '#include "sms_runtime.h"\n'
                'Z80State g_z80={0};\n'
                'uint8_t sms_read8(uint16_t a){(void)a;return 3;}\n'
                'void sms_write8(uint16_t a,uint8_t v){(void)a;(void)v;}\n'
                'void sms_dispatch_miss(uint16_t a){(void)a;}\n',
            "runner/video/sms_vdp.c": 'int fixture_video(void){return 0;}\n',
            "runner/audio/sn76489.c": 'int fixture_audio(void){return 0;}\n',
            "runner/external/superzazu/z80.c": 'int fixture_cpu(void){return 0;}\n',
            "runner/game_layout.h": 'typedef struct {int unused;} GameLayout;\n',
            "runner/include/sms_runtime.h":
                '#include <stdint.h>\n'
                'typedef struct {uint8_t a;} Z80State;\n'
                'extern Z80State g_z80;\n'
                'uint8_t sms_read8(uint16_t);\n'
                'void sms_write8(uint16_t,uint8_t);\n'
                'void sms_dispatch_miss(uint16_t);\n'
                'void call_by_address(uint16_t);\n',
            "external/z80-recomp-core/include/sms_runtime.h":
                '/* canonical ABI present in external repo */\n',
            "external/z80-recomp-core/include/z80_ops.h":
                '/* canonical Z80 helpers present in external repo */\n',
        }
        for name, body in source.items():
            target = self.upstream / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body)
        generated_text = {
            "ystest_funcs.h":
                '#include "sms_runtime.h"\n#include "z80_ops.h"\n'
                'void game_reset(void);\n',
            "ystest_full.c":
                '#include "ystest_funcs.h"\n'
                'void game_reset(void){ g_z80.a=sms_read8(0xc198);'
                'sms_write8(0xc199,4); }\n',
            "ystest_dispatch.c":
                '#include "ystest_funcs.h"\n'
                'void call_by_address(uint16_t a){if(a==0)game_reset();'
                'else sms_dispatch_miss(a);}\n',
            "ystest_layout.c":
                '#include "game_layout.h"\n'
                'const GameLayout g_game_layout={0};\n',
        }
        self.generated.mkdir()
        files = {}
        for name, body in generated_text.items():
            dest = self.generated / name
            dest.write_text(body)
            files[name] = {"bytes": dest.stat().st_size,
                           "sha256": hashlib.sha256(dest.read_bytes()).hexdigest()}
        # Independently exercise canonical provenance parser against fixture.
        # Manifest, mock tool, config and generated files all hashed exactly.
        sys.path.insert(0, str(ROOT / "shared_decomp"))
        import smsgg_recomp as adapter
        import zlib
        report = {
            "schema": "smsgg-recomp-codegen-v1",
            "stage": "generated-c-only", "runtime_verified": False,
            "rom_size": self.rom.stat().st_size,
            "rom_sha256": adapter.digest(self.rom),
            "rom_crc32": f"{zlib.crc32(self.rom.read_bytes()):08X}",
            "config_sha256": adapter.digest(self.config),
            "tool_sha256": adapter.digest(self.tool), "outputs": files,
        }
        (self.generated / "report.json").write_text(json.dumps(report))

    def invoke(self):
        return subprocess.run([
            sys.executable, str(BUILDER),
            "--rom", str(self.rom),
            "--manifest", str(self.manifest),
            "--config", str(self.config),
            "--tool", str(self.tool),
            "--upstream", str(self.upstream),
            "--generated", str(self.generated),
            "--prefix", "ystest",
            "--output", str(self.build / "test_runner"),
        ], text=True, capture_output=True, check=False)

    def test_compiles_links_and_executes_mock_generated_code(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        binary = self.build / "test_runner"
        self.assertEqual(subprocess.run([str(binary)], check=False).returncode, 0)
        evidence = json.loads((self.build / "compiled-report.json").read_text())
        self.assertEqual(evidence["compile_link"], "passed")
        self.assertFalse(evidence["executed"])
        self.assertFalse(evidence["runtime_verified"])

    def test_modified_generated_header_rejected(self):
        with (self.generated / "ystest_funcs.h").open("a") as file:
            file.write("\n/* tamper */")
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("integrity mismatch", result.stderr)

    def test_missing_header_rejected(self):
        (self.generated / "ystest_funcs.h").unlink()
        self.assertIn("Generated input", self.invoke().stderr)

    def test_missing_upstream_core_rejected(self):
        (self.upstream / "external/z80-recomp-core/include/z80_ops.h").unlink()
        self.assertIn("External shared Z80 ABI", self.invoke().stderr)

    def test_compiler_error_is_fatal(self):
        (self.generated / "ystest_full.c").write_text("not C source!\n")
        # update synthetic report to test the compiler, not integrity checking
        meta = self.generated / "report.json"
        raw = json.loads(meta.read_text())
        p = self.generated / "ystest_full.c"
        raw["outputs"][p.name] = {
            "bytes": p.stat().st_size,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
        meta.write_text(json.dumps(raw))
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.build / "compiled-report.json").exists())


if __name__ == "__main__":
    unittest.main()
