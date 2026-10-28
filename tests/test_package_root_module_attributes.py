"""A package passed directly as the directory input keeps its import identity."""

import os
import subprocess
import sys

from click.testing import CliRunner

from pyobfus.cli import main
from pyobfus.config import ObfuscationConfig
from pyobfus.core.orchestrator import CrossFileOrchestrator
from pyobfus.core.preflight import PreflightChecker


def test_package_root_reports_unproved_member_and_preserved_name_runs(tmp_path):
    source = tmp_path / "source" / "pkg"
    source.mkdir(parents=True)
    (source / "__init__.py").write_text("from .decoder import read\n")
    (source / "decoder.py").write_text(
        "from pkg import scanner\ndef read():\n    return scanner.make_scanner()\n"
    )
    (source / "scanner.py").write_text("make_scanner = lambda: 7\n")

    config = ObfuscationConfig(max_workers=1)
    orchestrator = CrossFileOrchestrator(config)
    orchestrator.phase1_scan(source)
    assert {file.module_name for file in orchestrator.files} == {
        "pkg.__init__",
        "pkg.decoder",
        "pkg.scanner",
    }
    assert orchestrator.module_attribute_accesses_unproved == 1
    findings = PreflightChecker(obfuscation_config=config).check_path(source).risks
    assert any(
        risk.category == "compatibility_advisory" and "scanner.make_scanner" in risk.message
        for risk in findings
    )

    safe_config = ObfuscationConfig(
        max_workers=1,
        exclude_names=["read"],
        preserve_unproved_module_attributes=True,
    )
    artifact = tmp_path / "artifact" / "pkg"
    safe_orchestrator = CrossFileOrchestrator(safe_config)
    result = safe_orchestrator.obfuscate(source, artifact)
    assert result.success, result.errors
    assert safe_orchestrator.module_attribute_accesses_unproved == 0
    assert any("make_scanner" in warning for warning in result.warnings)
    script = "import sys; sys.path.insert(0, sys.argv[1]); import pkg; print(pkg.read())"
    env = dict(os.environ, HOME=str(tmp_path), USERPROFILE=str(tmp_path))
    run = subprocess.run(
        [sys.executable, "-I", "-c", script, str(artifact.parent)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.returncode == 0, run.stderr
    assert run.stdout.strip() == "7"

    cli = CliRunner()
    cli_result = cli.invoke(
        main,
        [
            str(source),
            "-o",
            str(tmp_path / "cli-artifact" / "pkg"),
            "--no-config",
            "--offline",
            "--preserve-unproved-module-attributes",
            "--json",
        ],
    )
    assert cli_result.exit_code == 0, cli_result.output
    assert '"module_attribute_accesses_unproved": 0' in cli_result.output
