"""Tests for --json output across all CLI modes (P0-4)."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from pyobfus.cli import main


# ---------------------------------------------------------------------------
# Obfuscation success JSON
# ---------------------------------------------------------------------------


def test_obfuscate_success_json(tmp_path: Path) -> None:
    src = tmp_path / "a.py"
    src.write_text("def foo(): return 1\n", encoding="utf-8")
    out = tmp_path / "out.py"

    result = CliRunner().invoke(main, [str(src), "-o", str(out), "--json"])
    assert result.exit_code == 0, result.output

    # Output must be a single JSON object parseable without any prefix text
    data = json.loads(result.output)
    assert data["version"] == 1
    assert data["status"] == "success"
    assert data["input"] == str(src)
    assert data["output"] == str(out)
    assert data["dry_run"] is False
    assert isinstance(data["stats"], dict)
    assert "files_processed" in data["stats"]
    assert data["mapping"] is None
    assert "ai_hint" in data and data["ai_hint"]


def test_obfuscate_success_json_includes_mapping_path(tmp_path: Path) -> None:
    src = tmp_path / "a.py"
    src.write_text("def foo(): return 1\n", encoding="utf-8")
    out = tmp_path / "out.py"
    mapping = tmp_path / "m.json"

    result = CliRunner().invoke(
        main,
        [str(src), "-o", str(out), "--save-mapping", str(mapping), "--json"],
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["mapping"] == str(mapping)
    assert "--unmap" in data["ai_hint"]


def test_obfuscate_dry_run_json(tmp_path: Path) -> None:
    src = tmp_path / "a.py"
    src.write_text("def foo(): return 1\n", encoding="utf-8")
    out = tmp_path / "out.py"

    result = CliRunner().invoke(
        main, [str(src), "-o", str(out), "--dry-run", "--json"]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["dry_run"] is True
    # In dry-run mode the output file should NOT exist
    assert not out.exists()


def test_obfuscate_preset_flows_into_json(tmp_path: Path) -> None:
    src = tmp_path / "a.py"
    src.write_text(
        "from pydantic import BaseModel\nclass U(BaseModel): x: int\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.py"
    result = CliRunner().invoke(
        main, [str(src), "-o", str(out), "--preset", "pydantic", "--json"]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["preset"] == "pydantic"


# ---------------------------------------------------------------------------
# Obfuscation error JSON
# ---------------------------------------------------------------------------


def test_obfuscate_error_json_on_parse_failure(tmp_path: Path) -> None:
    src = tmp_path / "bad.py"
    src.write_text("def broken(:\n", encoding="utf-8")
    out = tmp_path / "out.py"

    result = CliRunner().invoke(main, [str(src), "-o", str(out), "--json"])
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["status"] == "error"
    assert data["error_type"]
    assert data["message"]
    assert data["ai_hint"]


def test_obfuscate_missing_output_json() -> None:
    result = CliRunner().invoke(main, ["nonexistent.py", "--json"])
    # click's own path-validation raises "exists" check before our handler
    # We only care that if we DO get to our handler it returns JSON.
    # For missing -o on a real file:
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# --check JSON (already covered by test_preflight; smoke-check consistency)
# ---------------------------------------------------------------------------


def test_check_json_output_shape(tmp_path: Path) -> None:
    src = tmp_path / "a.py"
    src.write_text("eval('x')\n", encoding="utf-8")

    result = CliRunner().invoke(main, ["--check", str(src), "--json"])
    assert result.exit_code == 1  # high-risk -> exit 1
    data = json.loads(result.output)
    assert data["version"] == 1
    assert "severity_counts" in data
    assert "ai_hint" in data
    assert "exit_code" in data


# ---------------------------------------------------------------------------
# --unmap JSON
# ---------------------------------------------------------------------------


def test_unmap_json_output_shape(tmp_path: Path) -> None:
    mapping = tmp_path / "m.json"
    mapping.write_text(
        json.dumps(
            {
                "version": 1,
                "modules": {"m": {"foo": "I0"}},
                "global": {"I0": {"module": "m", "original": "foo"}},
            }
        ),
        encoding="utf-8",
    )
    trace = tmp_path / "t.log"
    trace.write_text("I0 crashed", encoding="utf-8")

    result = CliRunner().invoke(
        main,
        ["--unmap", "--trace", str(trace), "--mapping", str(mapping), "--json"],
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["version"] == 1
    assert data["unmapped_trace"] == "foo crashed"
    assert data["ai_hint"]


# ---------------------------------------------------------------------------
# --json only emits one JSON object (no chatty prefix / suffix)
# ---------------------------------------------------------------------------


def test_json_output_has_no_text_prefix(tmp_path: Path) -> None:
    src = tmp_path / "a.py"
    src.write_text("x = 1\n", encoding="utf-8")
    out = tmp_path / "out.py"

    result = CliRunner().invoke(main, [str(src), "-o", str(out), "--json"])
    assert result.exit_code == 0, result.output
    # First non-whitespace char must be '{' — i.e., no log line before JSON
    stripped = result.output.lstrip()
    assert stripped.startswith("{")
    # Exactly one top-level JSON object
    data = json.loads(result.output)
    assert isinstance(data, dict)
