"""Tests for the obfuscation provenance manifest."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from pyobfus.cli import main
from pyobfus.config import ObfuscationConfig
from pyobfus.core.provenance import (
    config_hash,
    validate_provenance_manifest,
    verify_manifest_integrity,
)


def test_config_hash_is_stable_for_equivalent_sets() -> None:
    a = ObfuscationConfig.preset_safe()
    b = ObfuscationConfig.preset_safe()
    b.exclude_names = set(reversed(sorted(b.exclude_names)))
    assert config_hash(a) == config_hash(b)


def test_cli_writes_provenance_manifest_with_mapping_digest(tmp_path: Path) -> None:
    src = tmp_path / "app.py"
    src.write_text("def predict(x):\n    return x + 1\n", encoding="utf-8")
    out = tmp_path / "out.py"
    mapping = tmp_path / "mapping.json"
    manifest_path = tmp_path / "provenance.json"

    result = CliRunner().invoke(
        main,
        [
            str(src),
            "-o",
            str(out),
            "--preset",
            "safe",
            "--save-mapping",
            str(mapping),
            "--provenance-manifest",
            str(manifest_path),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    assert manifest_path.exists()

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["version"] == 1
    assert data["tool"]["name"] == "pyobfus"
    assert data["preset"] == "safe"
    assert data["mapping"]["path"] == str(mapping)
    assert data["mapping"]["sha256"]
    assert data["files"][0]["input"] == str(src)
    assert data["files"][0]["output"] == str(out)
    assert data["files"][0]["input_sha256"]
    assert data["files"][0]["output_sha256"]
    assert "source_control" in data
    assert "git_commit" in data["source_control"]
    assert data["cyclonedx"]["bomFormat"] == "CycloneDX"
    assert data["cyclonedx"]["specVersion"] == "1.6"
    component_refs = {component["bom-ref"] for component in data["cyclonedx"]["components"]}
    assert component_refs == {"input:app.py", "output:app.py", "mapping:mapping.json"}
    assert data["cyclonedx"]["dependencies"] == [
        {"ref": "output:app.py", "dependsOn": ["input:app.py", "mapping:mapping.json"]}
    ]
    assert verify_manifest_integrity(data)

    payload = json.loads(result.output)
    assert payload["provenance_manifest"] == str(manifest_path)


def test_cli_writes_provenance_manifest_for_directory_input(tmp_path: Path) -> None:
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    (src_dir / "b.py").write_text("def g():\n    return 2\n", encoding="utf-8")
    out_dir = tmp_path / "dist"
    manifest_path = tmp_path / "provenance.json"

    result = CliRunner().invoke(
        main,
        [
            str(src_dir),
            "-o",
            str(out_dir),
            "--provenance-manifest",
            str(manifest_path),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(data["files"]) == 2
    relative_paths = {f["relative_path"] for f in data["files"]}
    assert relative_paths == {"a.py", "b.py"}
    for f in data["files"]:
        assert Path(f["output"]).exists()
        assert f["input_sha256"]
        assert f["output_sha256"]
    component_refs = {component["bom-ref"] for component in data["cyclonedx"]["components"]}
    assert component_refs == {"input:a.py", "output:a.py", "input:b.py", "output:b.py"}
    assert {dep["ref"] for dep in data["cyclonedx"]["dependencies"]} == {
        "output:a.py",
        "output:b.py",
    }
    assert verify_manifest_integrity(data)


def test_verify_manifest_integrity_detects_tampering(tmp_path: Path) -> None:
    src = tmp_path / "app.py"
    src.write_text("def predict(x):\n    return x + 1\n", encoding="utf-8")
    out = tmp_path / "out.py"
    manifest_path = tmp_path / "provenance.json"

    CliRunner().invoke(
        main,
        [str(src), "-o", str(out), "--provenance-manifest", str(manifest_path), "--json"],
    )
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert verify_manifest_integrity(data)

    # Tamper with the payload without recomputing the digest: this is what
    # verify_manifest_integrity is actually able to catch (accidental
    # corruption / a stale digest) -- see its docstring for what it does
    # NOT catch (a deliberate tamperer who recomputes the digest too).
    tampered = dict(data)
    tampered["files"] = []
    assert not verify_manifest_integrity(tampered)


def test_validate_provenance_manifest_reports_shape_and_integrity_errors(
    tmp_path: Path,
) -> None:
    src = tmp_path / "app.py"
    src.write_text("def predict(x):\n    return x + 1\n", encoding="utf-8")
    out = tmp_path / "out.py"
    manifest_path = tmp_path / "provenance.json"

    CliRunner().invoke(
        main,
        [str(src), "-o", str(out), "--provenance-manifest", str(manifest_path), "--json"],
    )
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert validate_provenance_manifest(data)["valid"]

    tampered = dict(data)
    tampered.pop("cyclonedx")
    tampered["files"] = []
    result = validate_provenance_manifest(tampered)

    assert not result["valid"]
    assert "Missing required field: cyclonedx" in result["errors"]
    assert "integrity digest does not match manifest payload." in result["errors"]
    assert result["warnings"] == ["files is empty; no obfuscated file records are present."]


def test_cli_verify_provenance_manifest_json_success(tmp_path: Path) -> None:
    src = tmp_path / "app.py"
    src.write_text("def predict(x):\n    return x + 1\n", encoding="utf-8")
    out = tmp_path / "out.py"
    manifest_path = tmp_path / "provenance.json"

    build = CliRunner().invoke(
        main,
        [str(src), "-o", str(out), "--provenance-manifest", str(manifest_path), "--json"],
    )
    assert build.exit_code == 0, build.output

    result = CliRunner().invoke(
        main,
        ["--verify-provenance-manifest", str(manifest_path), "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "success"
    assert payload["valid"] is True
    assert payload["manifest_path"] == str(manifest_path)
    assert payload["errors"] == []
    assert payload["summary"] == "Valid provenance manifest."


def test_cli_verify_provenance_manifest_json_error(tmp_path: Path) -> None:
    manifest_path = tmp_path / "bad.json"
    manifest_path.write_text("{not json", encoding="utf-8")

    result = CliRunner().invoke(
        main,
        ["--verify-provenance-manifest", str(manifest_path), "--json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["status"] == "error"
    assert payload["valid"] is False
    assert payload["errors"][0].startswith("Invalid JSON:")
    assert payload["exit_code"] == 1


def test_dry_run_does_not_write_provenance_manifest(tmp_path: Path) -> None:
    src = tmp_path / "app.py"
    src.write_text("x = 1\n", encoding="utf-8")
    manifest_path = tmp_path / "provenance.json"

    result = CliRunner().invoke(
        main,
        [
            str(src),
            "-o",
            str(tmp_path / "out.py"),
            "--dry-run",
            "--provenance-manifest",
            str(manifest_path),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    assert not manifest_path.exists()
    payload = json.loads(result.output)
    assert payload["provenance_manifest"] is None
