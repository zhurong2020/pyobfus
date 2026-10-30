"""Adversarial synthetic delivery inputs: never execute or extract payloads."""

import json
import os
from pathlib import Path
import stat
import zipfile

from click.testing import CliRunner
import pytest

from pyobfus.cli import main
from pyobfus.core import delivery_check as dc


def assert_cli_error(target, *extra):
    result = CliRunner().invoke(main, ["--check-delivery", str(target), "--json", *extra])
    assert result.exit_code == 2, result.output
    data = json.loads(result.output)
    assert data["status"] == "error" and data["ai_hint"]
    return data


@pytest.mark.parametrize("name", ["../escape.py", "/root.py", "C:/root.py", "a/./b.py", "a//b.py"])
def test_unsafe_wheel_paths_are_errors(tmp_path, name):
    wheel = tmp_path / "bad.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(name, "raise AssertionError('must not execute')")
    assert_cli_error(wheel)
    assert list(tmp_path.iterdir()) == [wheel]


def test_backslash_wheel_path_is_rejected_even_when_zipfile_normalizes(tmp_path):
    wheel = tmp_path / "bad.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("a/../b.py", "raise AssertionError('must not execute')")
    # Windows zipfile normalizes a backslash in writestr's filename to `/`.
    # Patch both same-length ZIP filename fields to model an archive from an
    # untrusted producer that stores a literal backslash.
    data = wheel.read_bytes()
    assert data.count(b"a/../b.py") == 2
    wheel.write_bytes(data.replace(b"a/../b.py", b"a\\..\\b.py"))
    assert_cli_error(wheel)
    assert list(tmp_path.iterdir()) == [wheel]


def test_duplicate_wheel_names_are_not_ambiguous_source_evidence(tmp_path):
    wheel = tmp_path / "bad.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("app.py", "x=1")
        with pytest.warns(UserWarning, match="Duplicate"):
            archive.writestr("app.py", "x=2")
    assert_cli_error(wheel)


def test_wheel_symlink_is_not_read_as_a_regular_file(tmp_path):
    wheel = tmp_path / "bad.whl"
    info = zipfile.ZipInfo("app.py")
    info.create_system = 3
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(info, "../outside.py")
    assert_cli_error(wheel)


@pytest.mark.parametrize("kind", ["directory", "wheel"])
@pytest.mark.parametrize("limit", ["entry", "total", "count"])
def test_small_limits_reject_before_unbounded_reads(tmp_path, monkeypatch, kind, limit):
    monkeypatch.setattr(dc, "_MAX_ENTRY_BYTES", 5 if limit == "entry" else 20)
    monkeypatch.setattr(dc, "_MAX_TOTAL_BYTES", 10 if limit == "total" else 100)
    monkeypatch.setattr(dc, "_MAX_DELIVERY_ENTRIES", 1 if limit == "count" else 10)
    target = tmp_path / ("bad.whl" if kind == "wheel" else "dist")
    if kind == "wheel":
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("a.py", "a" * 6)
            archive.writestr("b.py", "b" * 6)
    else:
        target.mkdir()
        (target / "a.py").write_text("a" * 6)
        (target / "b.py").write_text("b" * 6)
    assert "limit" in assert_cli_error(target)["error"]


def test_outside_symlink_is_never_read(tmp_path, monkeypatch):
    outside = tmp_path / "outside.py"
    outside.write_text("sensitive synthetic content")
    target = tmp_path / "dist"
    target.mkdir()
    try:
        (target / "link.py").symlink_to(outside)
    except OSError:
        pytest.skip("symlinks unavailable")
    real_open = Path.open

    def guarded_open(path, *args, **kwargs):
        assert path.name not in ("link.py", "outside.py"), "outside content was read"
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    assert_cli_error(target)


def test_in_root_file_symlink_remains_supported(tmp_path):
    (tmp_path / "a.py").write_text("x=1")
    try:
        (tmp_path / "b.py").symlink_to("a.py")
    except OSError:
        pytest.skip("symlinks unavailable")
    assert dc.check_delivery(tmp_path)["target"]["files"] == 2


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="POSIX only")
def test_fifo_is_rejected_without_opening(tmp_path):
    os.mkfifo(tmp_path / "pipe")
    assert_cli_error(tmp_path)


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="POSIX only")
def test_evidence_fifo_is_rejected_without_opening(tmp_path):
    target = tmp_path / "dist"
    target.mkdir()
    evidence = tmp_path / "pipe"
    os.mkfifo(evidence)
    assert_cli_error(target, "--build-report", str(evidence))


@pytest.mark.parametrize(
    "report",
    [
        {"outputs": []},
        {"outputs": {"files": None}},
        {"outputs": {"files": [{"sha256": []}]}},
        {"transformations": []},
        {"transformations": {"l3_skipped_methods": []}},
        {"disabled_transforms": None},
    ],
)
def test_malformed_evidence_returns_structured_error(tmp_path, report):
    target = tmp_path / "dist"
    target.mkdir()
    evidence = tmp_path / "report.json"
    evidence.write_text(json.dumps(report))
    assert_cli_error(target, "--build-report", str(evidence))


def test_evidence_size_limit(tmp_path, monkeypatch):
    target = tmp_path / "dist"
    target.mkdir()
    evidence = tmp_path / "report.json"
    evidence.write_text('{"padding": "' + "x" * 50 + '"}')
    monkeypatch.setattr(dc, "_MAX_JSON_BYTES", 20)
    assert_cli_error(target, "--build-report", str(evidence))


def test_corrupt_zip_and_truncated_bytecode(tmp_path):
    wheel = tmp_path / "bad.whl"
    wheel.write_bytes(b"PK truncated")
    assert_cli_error(wheel)
    wheel.unlink()
    (tmp_path / "app.pyc").write_bytes(b"bad")
    result = dc.check_delivery(tmp_path)
    assert result["status"] == "warn"
    assert result["inspection"]["bytecode"]["unknown"] == 1


def test_corrupt_member_crc_returns_structured_error(tmp_path):
    wheel = tmp_path / "corrupt.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("app.py", b"value = 1\n")
    data = bytearray(wheel.read_bytes())
    data[30 + len("app.py")] ^= 1  # Stored member payload; leave its CRC unchanged.
    wheel.write_bytes(data)
    assert_cli_error(wheel)


def test_deep_evidence_returns_structured_error(tmp_path):
    target = tmp_path / "dist"
    target.mkdir()
    evidence = tmp_path / "report.json"
    evidence.write_text("[" * 2000 + "0" + "]" * 2000)
    assert_cli_error(target, "--build-report", str(evidence))


def test_source_comparison_read_is_bounded(tmp_path, monkeypatch):
    source = tmp_path / "app.py"
    source.write_bytes(b"x" * 100)
    monkeypatch.setattr(dc, "_MAX_SOURCE_COMPARE_BYTES", 10)
    assert len(dc._read_delivery_source(tmp_path, "directory", "app.py")) == 11
    wheel = tmp_path / "app.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("app.py", source.read_bytes())
    assert len(dc._read_delivery_source(wheel, "wheel", "app.py")) == 11
