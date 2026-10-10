"""Regression coverage for F: retain keyword binding in single-file output."""

import ast
import json
import os
import subprocess
import sys
from dataclasses import asdict

import pytest
from click.testing import CliRunner

from pyobfus.cli import main
from pyobfus.config import ObfuscationConfig
from pyobfus.config_templates import get_template
from pyobfus.core.preflight import PreflightChecker

KEYWORDS = """def scale(value, factor=2):
    return value * factor
print(scale(1, factor=3))
"""
MIXED = """def kinds(value, /, factor=2, *args, offset=0, **kwargs):
    return value * factor + sum(args) + offset + kwargs.get('bonus', 0)
print(kinds(1, 3, 4, offset=5, bonus=7))
"""
PRESETS = [
    "safe",
    "balanced",
    "aggressive",
    "fastapi",
    "django",
    "flask",
    "pydantic",
    "click",
    "sqlalchemy",
    "ml",
    "trial",
    "commercial",
    "library",
    "maximum",
]


@pytest.mark.parametrize("preset", PRESETS)
def test_each_preset_preserves_parameters(preset):
    assert set(PRESETS) == set(ObfuscationConfig.list_presets())
    assert ObfuscationConfig.get_preset(preset).preserve_param_names is True


def test_default_and_editions_preserve_parameters():
    for config in [
        ObfuscationConfig(),
        ObfuscationConfig.community_edition(),
        ObfuscationConfig.pro_edition(),
    ]:
        assert config.preserve_param_names is True
        assert "_explicit_param_names" not in asdict(config)


@pytest.mark.parametrize("preset", [None, "safe", "balanced", "aggressive", "fastapi", "library"])
@pytest.mark.parametrize("source", [KEYWORDS, MIXED], ids=["keyword", "mixed-signature"])
def test_singlefile_subprocess_equivalence(tmp_path, preset, source):
    original = tmp_path / "app.py"
    output = tmp_path / "out.py"
    original.write_text(source)
    env = dict(os.environ, HOME=str(tmp_path / "home"), USERPROFILE=str(tmp_path / "home"))
    command = [sys.executable, "-m", "pyobfus", str(original), "-o", str(output), "--no-config"]
    if preset:
        command += ["--preset", preset]
    # Exercise library's parameter policy without license-controlled transforms.
    command += ["--level", "community"]
    built = subprocess.run(command, cwd=tmp_path, env=env, capture_output=True, text=True)
    assert built.returncode == 0, built.stdout + built.stderr
    expected = subprocess.run(
        [sys.executable, str(original)], env=env, capture_output=True, text=True
    )
    actual = subprocess.run([sys.executable, str(output)], env=env, capture_output=True, text=True)
    assert actual.returncode == expected.returncode == 0, actual.stderr
    assert actual.stdout == expected.stdout
    assert [n.arg for n in ast.walk(ast.parse(output.read_text())) if isinstance(n, ast.arg)] == [
        n.arg for n in ast.walk(ast.parse(source)) if isinstance(n, ast.arg)
    ]


@pytest.mark.parametrize("choice", ["yaml", "cli", "omitted", "override"])
@pytest.mark.parametrize("json_output", [False, True])
def test_explicit_false_warning_and_contract(tmp_path, choice, json_output):
    src = tmp_path / "app.py"
    out = tmp_path / "out.py"
    cfg = tmp_path / "config.yml"
    src.write_text(KEYWORDS)
    cfg.write_text(
        "obfuscation:\n"
        + (
            "  preserve_param_names: false\n"
            if choice in {"yaml", "override"}
            else "  remove_comments: true\n"
        )
    )
    args = [str(src), "-o", str(out), "--config", str(cfg)]
    if choice == "cli":
        args += ["--no-preserve-param-names"]
    elif choice == "override":
        args += ["--preserve-param-names"]
    if json_output:
        args += ["--json"]
    result = CliRunner().invoke(main, args)
    assert result.exit_code == 0, result.output
    unsafe = choice in {"yaml", "cli"}
    assert ("signature compatibility are unverified" in result.stderr) == unsafe
    params = {n.arg for n in ast.walk(ast.parse(out.read_text())) if isinstance(n, ast.arg)}
    assert ("factor" not in params) == unsafe
    if json_output:
        payload = json.loads(result.stdout)
        assert set(payload) == {
            "version",
            "status",
            "input",
            "output",
            "preset",
            "level",
            "dry_run",
            "stats",
            "mapping",
            "provenance_manifest",
            "build_report",
            "trace_marker_id",
            "ai_hint",
        }
        assert ("warnings" in payload["stats"]) == unsafe
        if unsafe:
            assert len(payload["stats"]["warnings"]) == 1
            assert "--preserve-param-names" in payload["stats"]["warnings"][0]


@pytest.mark.parametrize(
    "source", [KEYWORDS, "def scale(value): return value\nprint(scale(**{'value': 1}))\n"]
)
def test_check_advisory(tmp_path, source):
    src = tmp_path / "app.py"
    src.write_text(source)
    report = PreflightChecker(preserve_param_names=False).check_path(src)
    risks = [r for r in report.risks if "parameter renaming enabled" in r.message]
    assert len(risks) == 1
    assert risks[0].severity == "medium"  # Syntactic candidate, not resolved identity.
    assert report.exit_code() == 0
    assert not PreflightChecker().check_path(src).risks
    result = CliRunner().invoke(
        main,
        [str(src), "--check", "--offline", "--no-config", "--no-preserve-param-names", "--json"],
    )
    assert result.exit_code == 0
    assert any(
        "parameter renaming enabled" in r["message"] for r in json.loads(result.stdout)["risks"]
    )


def test_crossfile_preservation_unchanged(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text(MIXED)
    out = tmp_path / "out"
    result = CliRunner().invoke(
        main, [str(src), "-o", str(out), "--no-config", "--no-preserve-param-names"]
    )
    assert result.exit_code == 0, result.output
    assert {
        n.arg for n in ast.walk(ast.parse((out / "app.py").read_text())) if isinstance(n, ast.arg)
    } == {"value", "factor", "args", "offset", "kwargs"}
    checked = CliRunner().invoke(
        main,
        [str(src), "--check", "--offline", "--no-config", "--no-preserve-param-names", "--json"],
    )
    assert checked.exit_code == 0
    assert not json.loads(checked.stdout)["risks"]


def test_init_template_preserves_parameters(tmp_path, monkeypatch):
    # Assert both the legacy template and actual --init output.
    import yaml

    assert yaml.safe_load(get_template("general"))["obfuscation"]["preserve_param_names"] is True
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(main, ["--init"])
    assert result.exit_code == 0, result.output
    assert (
        yaml.safe_load((tmp_path / "pyobfus.yaml").read_text())["obfuscation"][
            "preserve_param_names"
        ]
        is True
    )


def test_inherited_false_is_not_explicit_choice(tmp_path, monkeypatch):
    config = ObfuscationConfig(preserve_param_names=False)
    monkeypatch.setattr(ObfuscationConfig, "community_edition", lambda: config)
    src = tmp_path / "app.py"
    src.write_text(KEYWORDS)
    result = CliRunner().invoke(
        main, [str(src), "-o", str(tmp_path / "out.py"), "--no-config", "--json"]
    )
    assert result.exit_code == 0, result.output
    assert "warnings" not in json.loads(result.stdout)["stats"]
    assert "signature compatibility are unverified" not in result.stderr
