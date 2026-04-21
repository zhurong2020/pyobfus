"""Tests for `pyobfus --init` (P0-5)."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import yaml
from click.testing import CliRunner

from pyobfus.cli import main
from pyobfus.config import ObfuscationConfig
from pyobfus.core.init_config import build_init_result


def _write(tmp_path: Path, name: str, src: str) -> Path:
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(src).lstrip(), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Library layer: build_init_result()
# ---------------------------------------------------------------------------


def test_build_init_result_picks_fastapi(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "app.py",
        """
        from fastapi import FastAPI
        app = FastAPI()
        """,
    )
    result = build_init_result(tmp_path)
    assert result.preset == "fastapi"
    assert "FastAPI" in result.frameworks_detected
    assert "**/routers/**" in result.excludes
    assert result.files_scanned == 1


def test_build_init_result_defaults_to_balanced(tmp_path: Path) -> None:
    _write(tmp_path, "plain.py", "x = 1\n")
    result = build_init_result(tmp_path)
    assert result.preset == "balanced"
    assert result.frameworks_detected == []


def test_build_init_result_baseline_excludes_present(tmp_path: Path) -> None:
    _write(tmp_path, "a.py", "x = 1\n")
    result = build_init_result(tmp_path)
    for pattern in ("test_*.py", "**/tests/**", "**/__pycache__/**"):
        assert pattern in result.excludes


def test_build_init_result_preset_override(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "api.py",
        """
        from fastapi import FastAPI
        app = FastAPI()
        """,
    )
    result = build_init_result(tmp_path, preset_override="aggressive")
    assert result.preset == "aggressive"


def test_build_init_result_reports_risk_count(tmp_path: Path) -> None:
    _write(tmp_path, "bad.py", "x = eval('1+1')\n")
    result = build_init_result(tmp_path)
    assert result.high_risk_findings >= 1


# ---------------------------------------------------------------------------
# Generated YAML is well-formed and parsable
# ---------------------------------------------------------------------------


def test_generated_yaml_is_valid_and_loadable(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "app.py",
        """
        from django.db import models
        class Post(models.Model):
            pass
        """,
    )
    result = build_init_result(tmp_path)

    data = yaml.safe_load(result.yaml_text)
    assert "obfuscation" in data
    obf = data["obfuscation"]
    assert obf["preset"] == "django"
    assert "**/migrations/**" in obf["exclude_patterns"]
    assert obf["preserve_param_names"] is True


def test_generated_yaml_loads_into_obfuscation_config(tmp_path: Path) -> None:
    """The file written by --init must be loadable by ObfuscationConfig.from_file."""
    _write(
        tmp_path,
        "m.py",
        """
        from pydantic import BaseModel
        class U(BaseModel): x: int
        """,
    )
    result = build_init_result(tmp_path)

    config_file = tmp_path / "pyobfus.yaml"
    config_file.write_text(result.yaml_text, encoding="utf-8")

    # Must round-trip through ObfuscationConfig.from_file without raising
    cfg = ObfuscationConfig.from_file(config_file)
    assert cfg.preserve_param_names is True


# ---------------------------------------------------------------------------
# CLI layer
# ---------------------------------------------------------------------------


def test_cli_init_generates_yaml(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "api.py",
        """
        from fastapi import FastAPI
        app = FastAPI()
        """,
    )
    runner = CliRunner()
    result = runner.invoke(main, ["--init", str(tmp_path)])
    assert result.exit_code == 0, result.output
    config_file = tmp_path / "pyobfus.yaml"
    assert config_file.exists()

    # Human-mode output
    assert "Generated" in result.output
    assert "fastapi" in result.output
    assert "Next steps" in result.output


def test_cli_init_json_output(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "app.py",
        """
        import click
        @click.command()
        def cli(): pass
        """,
    )
    runner = CliRunner()
    result = runner.invoke(main, ["--init", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["status"] == "success"
    assert data["preset"] == "click"
    assert data["written"] is True
    assert data["ai_hint"]
    assert "config_path" in data


def test_cli_init_json_flags_high_risk(tmp_path: Path) -> None:
    _write(tmp_path, "bad.py", "eval('x')\n")
    result = CliRunner().invoke(main, ["--init", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["high_risk_findings"] >= 1
    assert "--check" in data["ai_hint"]


def test_cli_init_json_overwrites_existing_file(tmp_path: Path) -> None:
    _write(tmp_path, "a.py", "x = 1\n")
    existing = tmp_path / "pyobfus.yaml"
    existing.write_text("# will be overwritten\n", encoding="utf-8")

    result = CliRunner().invoke(main, ["--init", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    new = existing.read_text(encoding="utf-8")
    assert "# will be overwritten" not in new
    assert "generated by `pyobfus --init`" in new
