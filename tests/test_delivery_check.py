"""--check-delivery: known delivery mistakes in a directory or wheel."""

from __future__ import annotations

import json
import py_compile
import zipfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from pyobfus.cli import main
from pyobfus.core import delivery_check as dc

SOURCE = "def area(width, height):\n    return width * height\n"
# Fake PEM text, assembled at run time so the repository's credential hook
# (which matches PEM headers in tracked files) does not see a key-shaped line.
_PEM = "-" * 5
KEY_TEXT = f"{_PEM}BEGIN PRIVATE KEY{_PEM}\nTOPSECRETKEYMATERIAL\n{_PEM}END PRIVATE KEY{_PEM}\n"


@pytest.fixture
def build(tmp_path):
    """A real Community build with mapping, provenance and build report kept outside dist/."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "shapes.py").write_text(SOURCE, encoding="utf-8")
    private = tmp_path / "private"
    result = CliRunner().invoke(
        main,
        [
            str(src),
            "-o",
            str(tmp_path / "dist"),
            "--save-mapping",
            str(private / "mapping.json"),
            "--provenance-manifest",
            str(private / "provenance.json"),
            "--build-report",
            str(private / "report.json"),
        ],
    )
    assert result.exit_code == 0, result.output
    return tmp_path


def _check(build_dir: Path, target: Path, **kwargs):
    return dc.check_delivery(
        target,
        build_report=build_dir / "private" / "report.json",
        provenance_manifest=build_dir / "private" / "provenance.json",
        **kwargs,
    )


def _codes(result):
    return sorted(f["code"] for f in result["findings"])


def _binary_header(kind: str) -> bytes:
    if kind == "PE":
        header = bytearray(128)
        header[:2] = b"MZ"
        header[60:64] = (64).to_bytes(4, "little")
        header[64:68] = b"PE\x00\x00"
        return bytes(header)
    if kind == "ELF":
        return b"\x7fELF\x02\x01" + b"\x00" * 10
    return b"\xfe\xed\xfa\xcf"


def test_clean_delivery_is_ok(build):
    result = _check(build, build / "dist")
    assert result["status"] == "ok"
    assert result["findings"] == []
    assert result["summary"]["matched_build_outputs"] == result["summary"]["python_files"] == 1
    assert "not a security guarantee" in result["ai_hint"]


def test_mapping_key_and_original_are_high(build):
    dist = build / "dist"
    (dist / "mapping.json").write_bytes((build / "private" / "mapping.json").read_bytes())
    (dist / "shapes.py.scrub.key.pem").write_text(KEY_TEXT, encoding="utf-8")
    (dist / "copy_of_source.py").write_text(SOURCE, encoding="utf-8")
    result = _check(build, dist)
    assert result["status"] == "fail"
    assert _codes(result) == [dc.MAPPING_FILE, dc.ORIGINAL_SOURCE, dc.PRIVATE_KEY]
    assert "TOPSECRET" not in json.dumps(result)


def test_source_mentioning_a_pem_header_is_not_a_key(build):
    (build / "dist" / "ssh_support.py").write_text(
        f'MARKER = b"{_PEM}BEGIN OPENSSH PRIVATE KEY{_PEM}"\n', encoding="utf-8"
    )
    (build / "dist" / "id_server").write_text(KEY_TEXT, encoding="utf-8")
    result = _check(build, build / "dist")
    keys = [f["path"] for f in result["findings"] if f["code"] == dc.PRIVATE_KEY]
    assert keys == ["id_server"]


def test_output_identical_to_input_is_not_a_leak(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "__init__.py").write_text("", encoding="utf-8")
    (src / "consts.py").write_text("__all__ = []\n", encoding="utf-8")
    private = tmp_path / "private"
    res = CliRunner().invoke(
        main,
        [
            str(src),
            "-o",
            str(tmp_path / "dist"),
            "--provenance-manifest",
            str(private / "provenance.json"),
            "--build-report",
            str(private / "report.json"),
            "--config",
            str(_marker_off(tmp_path)),
        ],
    )
    assert res.exit_code == 0, res.output
    result = _check(tmp_path, tmp_path / "dist")
    assert not [f for f in result["findings"] if f["code"] == dc.ORIGINAL_SOURCE]


def _marker_off(tmp_path):
    cfg = tmp_path / "pyobfus.yaml"
    cfg.write_text('obfuscation:\n  community_marker: "off"\n', encoding="utf-8")
    return cfg


def test_mapping_detected_by_content_not_name(build):
    dist = build / "dist"
    (dist / "settings.json").write_bytes((build / "private" / "mapping.json").read_bytes())
    (dist / "data.json").write_text('{"modules": [], "version": 1}', encoding="utf-8")
    assert _codes(_check(build, dist)) == [dc.MAPPING_FILE]


def test_unrecorded_python_and_missing_output(build):
    dist = build / "dist"
    (dist / "shapes.py").write_text("# edited after the build\n", encoding="utf-8")
    result = _check(build, dist)
    assert result["status"] == "warn"
    assert _codes(result) == [dc.MISSING_OUTPUT, dc.UNRECORDED_PYTHON]


def test_build_level_findings_from_report(build):
    report_path = build / "private" / "report.json"
    report = json.loads(report_path.read_text())
    report["disabled_transforms"] = [{"transform": "selective_opacity", "reason": "x"}]
    report["transformations"]["l3_skipped_methods"] = 2
    report_path.write_text(json.dumps(report), encoding="utf-8")
    result = _check(build, build / "dist")
    assert _codes(result) == [dc.FUSION_SKIPPED, dc.L3_PARTIAL]
    assert result["status"] == "warn"


def test_bytecode_is_info_only(build):
    dist = build / "dist"
    cache = dist / "__pycache__"
    cache.mkdir()
    py_compile.compile(
        str(dist / "shapes.py"), cfile=str(cache / "shapes.cpython-312.pyc"), doraise=True
    )
    result = _check(build, build / "dist")
    assert _codes(result) == [dc.BYTECODE_PRESENT]
    assert result["status"] == "ok"
    assert result["inspection"]["bytecode"]["matched_recorded_output"] == 1


def test_bytecode_unknown_warns_without_unmarshalling(build):
    dist = build / "dist"
    (dist / "shapes.pyc").write_bytes(b"\x00" * 16)
    result = _check(build, dist)
    assert result["status"] == "warn"
    assert _codes(result) == [dc.BYTECODE_ORIGIN_UNKNOWN, dc.BYTECODE_PRESENT]
    assert result["inspection"]["bytecode"]["unknown"] == 1
    assert (
        result["inspection"]["bytecode"]["sample"][0]["reason"]
        == "different_interpreter_or_invalid_magic"
    )


@pytest.mark.parametrize("kind", ["PE", "ELF", "Mach-O"])
def test_frozen_executable_is_explicitly_uninspected(tmp_path, kind):
    binary = tmp_path / "app"
    binary.write_bytes(_binary_header(kind) + b"not a real archive")
    result = dc.check_delivery(binary)
    assert result["status"] == "warn"
    assert result["target"]["kind"] == "executable"
    assert _codes(result) == [dc.FROZEN_UNINSPECTED]
    assert result["inspection"]["frozen_executables"] == {"found": 1, "inspected": 0}


def test_onedir_executable_does_not_claim_inner_payload_was_checked(tmp_path):
    directory = tmp_path / "dist"
    directory.mkdir()
    (directory / "app").write_bytes(_binary_header("ELF") + b"not a real archive")
    result = dc.check_delivery(directory)
    assert result["status"] == "warn"
    assert _codes(result) == [dc.FROZEN_UNINSPECTED]


def test_executable_prefix_without_valid_header_is_rejected(tmp_path):
    binary = tmp_path / "not-an-app"
    binary.write_bytes(b"MZ only a text prefix")
    with pytest.raises(ValueError, match="expected a directory"):
        dc.check_delivery(binary)


def test_wheel_is_checked_without_extracting(build, tmp_path):
    wheel = tmp_path / "app-1.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("app/shapes.py", (build / "dist" / "shapes.py").read_bytes())
        archive.writestr("app/mapping.json", (build / "private" / "mapping.json").read_bytes())
        archive.writestr("app-1.0.dist-info/RECORD", "app/shapes.py,,\n")
    result = _check(build, wheel)
    assert result["target"]["kind"] == "wheel"
    assert _codes(result) == [dc.MAPPING_FILE]
    assert result["summary"]["matched_build_outputs"] == 1


def test_without_build_evidence_hint_asks_for_it(build):
    result = dc.check_delivery(build / "dist")
    assert result["status"] == "ok"
    assert "--build-report" in result["ai_hint"] and "--provenance-manifest" in result["ai_hint"]


def test_cli_exit_codes_and_json(build):
    dist = build / "dist"
    args = [
        "--check-delivery",
        str(dist),
        "--build-report",
        str(build / "private" / "report.json"),
        "--json",
    ]
    ok = CliRunner().invoke(main, args)
    assert ok.exit_code == 0, ok.output
    payload = json.loads(ok.output)
    assert payload["status"] == "ok" and "ai_hint" in payload

    (dist / "mapping.json").write_bytes((build / "private" / "mapping.json").read_bytes())
    bad = CliRunner().invoke(main, args)
    assert bad.exit_code == 1
    assert json.loads(bad.output)["status"] == "fail"


def test_cli_error_on_unreadable_target(tmp_path):
    not_wheel = tmp_path / "notes.txt"
    not_wheel.write_text("x", encoding="utf-8")
    res = CliRunner().invoke(main, ["--check-delivery", str(not_wheel), "--json"])
    assert res.exit_code == 2
    assert json.loads(res.output)["status"] == "error"


def test_check_delivery_writes_nothing(build):
    before = sorted(p.relative_to(build) for p in build.rglob("*"))
    CliRunner().invoke(main, ["--check-delivery", str(build / "dist")])
    assert sorted(p.relative_to(build) for p in build.rglob("*")) == before
