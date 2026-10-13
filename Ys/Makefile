# Ys SMS decomp: use your locally owned ROM, never commit a ROM image.
PYTHON ?= python3
ROM ?=

.PHONY: verify smoke build-verify wla-prepare wla-verify
smoke:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tools/run_regressions_phase21.py "$(ROM)" --suite phase20 --suite phase21 --suite full_rom_overlay
verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tools/run_system_m12_regressions.py "$(ROM)" $(if $(EMULICIOUS_JAR),--external-jar "$(EMULICIOUS_JAR)",) --timeout 600 --jobs 4
build-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tools/build_system_m10.py --check --verify-rom "$(ROM)"
wla-prepare:
	$(PYTHON) tools/wla_system_m10.py --prepare
wla-verify:
	$(PYTHON) tools/wla_system_m10.py --run

.PHONY: data-verify
data-verify:
	$(PYTHON) tools/phase21_semantic_sources.py --verify

# Whole-system policy: validate source-only full banks before further byte-count phases.
.PHONY: wholebank07 wholebank07-verify wholebank07-wla-prepare wholebank07-wla-verify whole-system-verify
wholebank07:
	$(PYTHON) tools/whole_bank07.py --verify-mixed
wholebank07-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tests_whole_bank07.py "$(ROM)"
	$(PYTHON) tools/build_whole_bank07.py "$(ROM)" --check
wholebank07-wla-prepare:
	$(PYTHON) tools/wla_whole_bank07.py --prepare
wholebank07-wla-verify:
	$(PYTHON) tools/wla_whole_bank07.py --run
whole-system-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tools/run_system_m8_regressions.py "$(ROM)" --jobs 4 --timeout 240

.PHONY: wholebank03 wholebank03-verify two-bank-source whole-system-wla-prepare whole-system-wla-verify whole-rom-verify
wholebank03:
	$(PYTHON) tools/whole_bank03.py --verify-mixed
wholebank03-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tests_whole_bank03.py "$(ROM)"
two-bank-source:
	$(PYTHON) tools/build_whole_system.py --standalone-banks
whole-rom-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tools/build_system_m8.py "$(ROM)" --check
whole-system-wla-prepare:
	$(PYTHON) tools/wla_system_m4.py --prepare
whole-system-wla-verify:
	$(PYTHON) tools/wla_system_m4.py --run

# Architecture-neutral AI evidence controls; these do not certify source-only assembly.
.PHONY: ai-audit ai-tool-tests
ai-audit:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) ../shared_decomp/workflow.py audit --manifest ../shared_decomp/examples/ys_sms_manifest.json --binary "$(ROM)"
ai-tool-tests:
	$(PYTHON) -m unittest discover -s ../shared_decomp/tests -v

# Whole-system CFG/evidence inventory; all code bytes are checked against the ROM.
# This does not confer emulator runtime confidence or recover unknown regions.
.PHONY: system-graph system-graph-context system-graph-frontier
system-graph:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tools/build_system_graph.py "$(ROM)" --output whole_system/evidence_graph.json --check
	$(PYTHON) tests_system_graph.py "$(ROM)"
system-graph-context:
	$(PYTHON) tools/query_system_graph.py --bank 0 --cpu 0x0089 --radius 5
system-graph-frontier:
	$(PYTHON) tools/build_graph_frontier.py --check

# Whole-system Milestone 3: source-only fixed bank0 + existing banks3/7.
.PHONY: three-bank-source bank00-source bank00-verify three-bank-rom-verify three-bank-graph three-bank-wla-prepare three-bank-wla-verify system-m3-verify
three-bank-source:
	$(PYTHON) tools/build_system_m3.py --standalone-banks
bank00-source:
	$(PYTHON) tools/whole_bank00.py --verify-mixed
bank00-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tests_whole_bank00.py "$(ROM)"
three-bank-rom-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tools/build_system_m3.py "$(ROM)" --check
three-bank-graph:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tools/build_system_graph_m3.py "$(ROM)" --check
three-bank-wla-prepare:
	$(PYTHON) tools/wla_system_m3.py --prepare
three-bank-wla-verify:
	$(PYTHON) tools/wla_system_m3.py --run
system-m3-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tools/run_system_m3_regressions.py "$(ROM)" --jobs 4 --timeout 120

.PHONY: three-bank-frontier
three-bank-frontier:
	$(PYTHON) tools/build_frontier_m3.py --check

# Whole-system Milestone 4: independent sprite/object physical bank6.
.PHONY: four-bank-source four-bank-rom-verify bank06-source bank06-verify bank06-assets-verify four-bank-wla-prepare four-bank-wla-verify system-m4-verify
four-bank-source:
	$(PYTHON) tools/build_system_m4.py --standalone-banks
four-bank-rom-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tools/build_system_m4.py "$(ROM)" --check
bank06-source:
	$(PYTHON) tools/whole_bank06.py --verify-mixed
bank06-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tests_whole_bank06.py "$(ROM)"
bank06-assets-verify:
	$(PYTHON) tools/build_sprite_asset_ledger_m4.py --check
four-bank-wla-prepare:
	$(PYTHON) tools/wla_system_m4.py --prepare
four-bank-wla-verify:
	$(PYTHON) tools/wla_system_m4.py --run
system-m4-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tools/run_system_m4_regressions.py "$(ROM)" --jobs 4 --timeout 120

# Whole-system M5: complete physical sound bank02 and five ROM-free bank builds.
.PHONY: five-bank-source bank02-source bank02-verify five-bank-rom-verify five-bank-wla-prepare five-bank-wla-verify system-m5-verify
five-bank-source:
	$(PYTHON) tools/build_system_m5.py --standalone-banks
bank02-source:
	$(PYTHON) tools/whole_bank02.py --verify-mixed
bank02-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tests_whole_bank02.py "$(ROM)"
five-bank-rom-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tools/build_system_m5.py "$(ROM)" --check
five-bank-wla-prepare:
	$(PYTHON) tools/wla_system_m5.py --prepare
five-bank-wla-verify:
	$(PYTHON) tools/wla_system_m5.py --run
system-m5-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tools/run_system_m5_regressions.py "$(ROM)" --jobs 4 --timeout 120

.PHONY: bank02-sound-links
bank02-sound-links:
	$(PYTHON) tools/build_sound_ledger_m5.py --check

# Whole-system Milestone 6: physical bank1 source-only plus banks0/2/3/6/7.
.PHONY: six-bank-source bank01-source bank01-verify six-bank-rom-verify six-bank-wla-prepare six-bank-wla-verify system-m6-verify
six-bank-source:
	$(PYTHON) tools/build_system_m6.py --standalone-banks
bank01-source:
	$(PYTHON) tools/whole_bank01.py --verify-mixed
bank01-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tests_whole_bank01.py "$(ROM)"
six-bank-rom-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tools/build_system_m6.py "$(ROM)" --check
six-bank-wla-prepare:
	$(PYTHON) tools/wla_system_m6.py --prepare
six-bank-wla-verify:
	$(PYTHON) tools/wla_system_m6.py --run
system-m6-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tools/run_system_m6_regressions.py "$(ROM)" --jobs 4 --timeout 120

.PHONY: bank01-static-links
bank01-static-links:
	$(PYTHON) tools/build_bank01_static_ledger.py --check

# Whole-System M7: bank4 source closure and bounded bank1->bank4 collision evidence.
.PHONY: seven-bank-source bank04-source bank04-verify seven-bank-rom-verify bank04-collision-verify bank04-crossbank-verify seven-bank-wla-prepare seven-bank-wla-verify system-m7-verify
seven-bank-source:
	$(PYTHON) tools/build_system_m7.py --standalone-banks
bank04-source:
	$(PYTHON) tools/whole_bank04.py --verify-mixed
bank04-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tests_whole_bank04.py "$(ROM)"
seven-bank-rom-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tools/build_system_m8.py "$(ROM)" --check
bank04-collision-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tools/bank04_collision_trace.py "$(ROM)" --check
bank04-crossbank-verify:
	$(PYTHON) tools/bank04_crossbank_ledger.py --check
seven-bank-wla-prepare:
	$(PYTHON) tools/wla_system_m8.py --prepare
seven-bank-wla-verify:
	$(PYTHON) tools/wla_system_m8.py --run
system-m7-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tools/run_system_m8_regressions.py "$(ROM)" --jobs 4 --timeout 240

# Whole-System Milestone 8: source-only banks 8 and 10, decimal VDP writer.
.PHONY: nine-bank-source bank08-10-verify system-m8-verify
nine-bank-source:
	$(PYTHON) tools/build_system_m8.py --standalone-banks
bank08-10-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tests_whole_banks08_10.py "$(ROM)"
system-m8-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tools/run_system_m8_regressions.py "$(ROM)" --jobs 4 --timeout 240

# Whole-System Milestone 9: 12 of 16 banks can be built with no owner ROM.
.PHONY: twelve-bank-source bank09-11-12-source bank09-11-12-verify twelve-bank-wla-prepare twelve-bank-wla-verify system-m9-verify
twelve-bank-source:
	$(PYTHON) tools/build_system_m9.py --standalone-banks
bank09-11-12-source:
	$(PYTHON) tools/whole_banks09_11_12.py --verify-mixed
bank09-11-12-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tests_whole_banks09_11_12.py "$(ROM)"
twelve-bank-wla-prepare:
	$(PYTHON) tools/wla_system_m10.py --prepare
twelve-bank-wla-verify:
	$(PYTHON) tools/wla_system_m10.py --run
system-m9-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tools/run_system_m9_regressions.py "$(ROM)" --jobs 4 --timeout 600

# Milestone 10: ROM-independent whole-cartridge build (does not need ROM=).
.PHONY: source-cartridge source-cartridge-check source-cartridge-wla-prepare source-cartridge-wla-verify system-m10-verify
source-cartridge:
	$(PYTHON) tools/build_system_m10.py
source-cartridge-check:
	$(PYTHON) tools/build_system_m10.py --check
source-cartridge-wla-prepare:
	$(PYTHON) tools/wla_system_m10.py --prepare
source-cartridge-wla-verify:
	$(PYTHON) tools/wla_system_m10.py --run
system-m10-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/Ys.sms' >&2; exit 2)
	$(PYTHON) tools/run_system_m10_regressions.py "$(ROM)" --jobs 4 --timeout 600

# M11: actual third-party emulator boot and title-render comparison.
# Requires a separately supplied Emulicious.jar; never vendor the emulator or ROM.
EMULICIOUS_JAR ?=
.PHONY: emulator-verify emulator-smoke-tests
emulator-verify:
	@test -n "$(EMULICIOUS_JAR)" || (echo 'Set EMULICIOUS_JAR=/path/to/Emulicious.jar' >&2; exit 2)
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/owned-Ys.sms for independent baseline' >&2; exit 2)
	$(PYTHON) tools/emulicious_smoke_m11.py --jar "$(EMULICIOUS_JAR)" --reference-rom "$(ROM)" --report whole_system/emulicious_report_m11.json
emulator-smoke-tests:
	$(PYTHON) tests_emulicious_m11.py

# Public, pinned upstream by default. An optional ZIP works offline. External files
# are cached outside Git and neither the vendor tree nor ROM is committed.
WLA_SOURCE_ZIP ?=
WLA_WORKDIR ?= $(HOME)/.cache/ys-decomp/wla-dx-v10.7
.PHONY: wla-build-native wla-native-tests
wla-build-native:
	$(PYTHON) tools/wla_native_m11.py $(if $(strip $(WLA_SOURCE_ZIP)),"$(WLA_SOURCE_ZIP)",) --workdir "$(WLA_WORKDIR)"
wla-native-tests:
	$(PYTHON) tests_wla_native_m11.py

# M12: actual third-party opcode assembly using user-provided Emulicious.jar.
# Unlike WLA's pending full linker check, this verifies only instruction bytes.
.PHONY: emulicious-assembler-verify emulicious-assembler-tests
emulicious-assembler-verify:
	@test -n "$(EMULICIOUS_JAR)" || (echo 'Set EMULICIOUS_JAR=/path/to/Emulicious.jar' >&2; exit 2)
	$(PYTHON) tools/verify_emulicious_assembler_m12.py --jar "$(EMULICIOUS_JAR)" $(if $(ROM),--reference-rom "$(ROM)",) --report whole_system/emulicious_assembler_report_m12.json
emulicious-assembler-tests:
	$(PYTHON) tests_emulicious_assembler_m12.py
.PHONY: system-m12-verify
system-m12-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/owned-Ys.sms' >&2; exit 2)
	$(PYTHON) tools/run_system_m12_regressions.py "$(ROM)" $(if $(EMULICIOUS_JAR),--external-jar "$(EMULICIOUS_JAR)",) --jobs 4 --timeout 600

# M13: fail-closed semantic debt inventory. A source-backed DB byte is NOT
# considered semantically decoded merely because the cartridge hash matches.
.PHONY: semantic-audit semantic-audit-tests
semantic-audit:
	$(PYTHON) tools/semantic_debt_m13.py --check
semantic-audit-tests:
	$(PYTHON) -m unittest tests_semantic_debt_m13 -v

# M14: bounded, reversible Bank 13 RLE asset interpretation and 4bpp test.
.PHONY: bank13-rle-audit bank13-rle-tests
bank13-rle-audit:
	$(PYTHON) tools/bank13_rle_m14.py --check
bank13-rle-tests:
	$(PYTHON) -m unittest tests_bank13_rle_m14 -v

# Opt-in static native C generation via an EXTERNAL SMS/GG Recomp installation.
# This is separate from the checked source cartridge and native C11 runtime.
SMS_RECOMP ?=
.PHONY: recomp-preflight recomp-generate recomp-verify recomp-tests
recomp-preflight:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/owned/Ys.sms' >&2; exit 2)
	$(PYTHON) ../shared_decomp/smsgg_recomp.py --rom "$(ROM)" --manifest manifest.json --config recomp/game.toml --preflight
recomp-generate:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/owned/Ys.sms' >&2; exit 2)
	@test -n "$(SMS_RECOMP)" || (echo 'Set SMS_RECOMP=/path/to/SmsRecomp' >&2; exit 2)
	$(PYTHON) ../shared_decomp/smsgg_recomp.py --rom "$(ROM)" --manifest manifest.json --config recomp/game.toml --tool "$(SMS_RECOMP)"
recomp-verify:
	@test -n "$(ROM)" || (echo 'Set ROM=/path/to/owned/Ys.sms' >&2; exit 2)
	@test -n "$(SMS_RECOMP)" || (echo 'Set SMS_RECOMP=/path/to/SmsRecomp' >&2; exit 2)
	$(PYTHON) ../shared_decomp/smsgg_recomp.py --rom "$(ROM)" --manifest manifest.json --config recomp/game.toml --tool "$(SMS_RECOMP)" --verify-generated
recomp-tests:
	$(PYTHON) -m unittest discover -s ../shared_decomp/tests -p test_smsgg_recomp.py -v
