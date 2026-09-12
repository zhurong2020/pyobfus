"""Contract tests for the versioned unified build report."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from pyobfus.cli import main


def test_build_report_unifies_plan_stats_verification_and_outputs(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    (source / "app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
    (source / "test_app.py").write_text("def test_answer():\n    pass\n", encoding="utf-8")
    output = tmp_path / "dist"
    report_path = tmp_path / "evidence" / "build-report.json"
    provenance_path = tmp_path / "evidence" / "provenance.json"

    result = CliRunner().invoke(
        main,
        [
            str(source),
            "-o",
            str(output),
            "--verify-syntax",
            "--provenance-manifest",
            str(provenance_path),
            "--build-report",
            str(report_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    envelope = json.loads(result.output)
    assert envelope["build_report"] == str(report_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["format"] == "pyobfus-build-report"
    assert report["version"] == 1
    assert report["state"] == "completed"
    assert report["mode"] == "cross_file"
    assert report["selection"]["selected_count"] == 1
    assert report["selection"]["excluded"][0]["reason"] == "exclude_pattern"
    assert report["transformations"]["files_processed"] == 1
    assert report["verification"]["syntax_valid"] is True
    assert report["verification"]["execution_performed"] is False
    assert report["outputs"]["file_count"] == 1
    assert report["outputs"]["files"][0]["path"] == "app.py"
    assert len(report["outputs"]["files"][0]["sha256"]) == 64
    assert report["provenance"]["manifest"] == "provenance.json"
    assert report["privacy"] == {
        "paths": "relative-or-basename",
        "source_content_included": False,
        "secrets_included": False,
    }

    serialized = report_path.read_text(encoding="utf-8")
    assert str(tmp_path) not in serialized
    assert "def answer" not in serialized


def test_build_report_is_byte_stable_for_unchanged_output(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    source.write_text("value = 7\n", encoding="utf-8")
    output = tmp_path / "out.py"
    report_path = tmp_path / "report.json"
    runner = CliRunner()

    one = runner.invoke(main, [str(source), "-o", str(output), "--build-report", str(report_path)])
    first_bytes = report_path.read_bytes()
    two = runner.invoke(main, [str(source), "-o", str(output), "--build-report", str(report_path)])

    assert one.exit_code == 0, one.output
    assert two.exit_code == 0, two.output
    assert first_bytes == report_path.read_bytes()


def test_dry_run_does_not_write_build_report(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    source.write_text("value = 7\n", encoding="utf-8")
    report_path = tmp_path / "report.json"

    result = CliRunner().invoke(
        main,
        [
            str(source),
            "-o",
            str(tmp_path / "out.py"),
            "--dry-run",
            "--build-report",
            str(report_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["build_report"] is None
    assert "build-report" in {artifact["kind"] for artifact in payload["plan"]["artifacts"]}
    assert not report_path.exists()


def test_build_report_records_unrequested_verification_honestly(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    source.write_text("value = 7\n", encoding="utf-8")
    report_path = tmp_path / "report.json"

    result = CliRunner().invoke(
        main,
        [str(source), "-o", str(tmp_path / "out.py"), "--build-report", str(report_path)],
    )

    assert result.exit_code == 0, result.output
    verification = json.loads(report_path.read_text(encoding="utf-8"))["verification"]
    assert verification == {
        "requested": False,
        "mode": "none",
        "execution_performed": False,
    }


def test_build_report_does_not_echo_user_authored_exclusion_patterns(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    source.write_text("value = 7\n", encoding="utf-8")
    sensitive_pattern = f"{tmp_path}/private-customer-tree/*.py"
    config = tmp_path / "pyobfus.yaml"
    config.write_text(f"exclude_patterns:\n  - {sensitive_pattern}\n", encoding="utf-8")
    report_path = tmp_path / "report.json"

    result = CliRunner().invoke(
        main,
        [
            str(source),
            "-o",
            str(tmp_path / "out.py"),
            "--config",
            str(config),
            "--build-report",
            str(report_path),
        ],
    )

    assert result.exit_code == 0, result.output
    serialized = report_path.read_text(encoding="utf-8")
    report = json.loads(serialized)
    assert sensitive_pattern not in serialized
    assert report["effective_config"]["exclude_patterns_count"] == 2


def test_build_report_refuses_to_overwrite_generated_output(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    source.write_text("value = 7\n", encoding="utf-8")
    output = tmp_path / "out.py"

    result = CliRunner().invoke(
        main,
        [str(source), "-o", str(output), "--build-report", str(output), "--json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["error_type"] == "PyObfusError"
    assert not output.exists()
