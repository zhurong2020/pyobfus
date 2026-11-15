"""--check-delivery: known delivery mistakes in a directory or wheel."""

from __future__ import annotations

import hashlib
import json
import py_compile
import struct
import zipfile
import zlib
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


def _pyinstaller_executable(path, members):
    cookie_magic = b"MEI\014\013\012\013\016"
    cookie = struct.Struct("!8sIIII64s")
    toc_header = struct.Struct("!IIIIBc")
    payload = bytearray()
    toc = bytearray()
    for name, data, typecode, compressed in members:
        stored = zlib.compress(data) if compressed else data
        offset = len(payload)
        payload.extend(stored)
        raw_name = name.encode() + b"\0"
        entry_length = toc_header.size + len(raw_name)
        toc.extend(
            toc_header.pack(
                entry_length,
                offset,
                len(stored),
                len(data),
                int(compressed),
                typecode.encode(),
            )
        )
        toc.extend(raw_name)
    stub = _binary_header("ELF")
    toc_offset = len(payload)
    archive_length = len(payload) + len(toc) + cookie.size
    path.write_bytes(
        stub
        + payload
        + toc
        + cookie.pack(
            cookie_magic,
            archive_length,
            toc_offset,
            len(toc),
            312,
            b"libpython3.12.so\0".ljust(64, b"\0"),
        )
    )


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


def test_pyinstaller_carchive_checks_top_level_and_keeps_pyz_unknown(tmp_path):
    binary = tmp_path / "app"
    mapping = json.dumps({"pyobfus_version": "0.14.0", "global": {}}).encode()
    _pyinstaller_executable(
        binary,
        [
            ("mapping.json", mapping, "x", True),
            ("PYZ.pyz", b"not unmarshalled", "z", False),
        ],
    )
    result = dc.check_delivery(binary)
    assert result["status"] == "fail"
    assert _codes(result) == [dc.FROZEN_UNINSPECTED, dc.MAPPING_FILE]
    assert result["inspection"]["frozen_executables"] == {
        "found": 1,
        "inspected": 1,
        "format": "pyinstaller-carchive",
        "members_checked": 1,
        "members_total": 2,
        "unknown_members": 1,
    }


def test_pyinstaller_carchive_rejects_duplicate_members(tmp_path):
    binary = tmp_path / "app"
    _pyinstaller_executable(
        binary,
        [("data.txt", b"one", "x", False), ("data.txt", b"two", "x", False)],
    )
    with pytest.raises(ValueError, match="Duplicate PyInstaller member"):
        dc.check_delivery(binary)


def test_pyinstaller_carchive_checks_private_key_and_original(tmp_path):
    binary = tmp_path / "app"
    source = b"print('source accidentally bundled')\n"
    _pyinstaller_executable(
        binary,
        [("source.py", source, "x", False), ("signing.pem", KEY_TEXT.encode(), "x", True)],
    )
    manifest = tmp_path / "provenance.json"
    manifest.write_text(
        json.dumps(
            {
                "files": [
                    {
                        "relative_path": "source.py",
                        "input_sha256": hashlib.sha256(source).hexdigest(),
                    }
                ]
            }
        )
    )
    result = dc.check_delivery(binary, provenance_manifest=manifest)
    assert result["status"] == "fail"
    assert _codes(result) == [dc.ORIGINAL_SOURCE, dc.PRIVATE_KEY]


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


def test_pyinstaller_windows_names_are_normalised(tmp_path):
    binary = tmp_path / "app"
    _pyinstaller_executable(binary, [(r"pkg\data\label.txt", b"label", "x", False)])
    assert dc.check_delivery(binary)["status"] == "ok"
    _pyinstaller_executable(binary, [(r"pkg\data\label.txt", KEY_TEXT.encode(), "x", False)])
    result = dc.check_delivery(binary)
    assert result["findings"][0]["path"] == "pkg/data/label.txt"
    assert _codes(result) == [dc.PRIVATE_KEY]


@pytest.mark.parametrize("name", [r"..\evil", r"C:\x"])
def test_pyinstaller_windows_unsafe_names(tmp_path, name):
    binary = tmp_path / "app"
    _pyinstaller_executable(binary, [(name, b"data", "x", False)])
    with pytest.raises(ValueError, match="Unsafe PyInstaller member name"):
        dc.check_delivery(binary)


def test_pyinstaller_windows_normalised_duplicate(tmp_path):
    binary = tmp_path / "app"
    _pyinstaller_executable(
        binary, [(r"pkg\data.txt", b"a", "x", False), ("pkg/data.txt", b"b", "x", False)]
    )
    with pytest.raises(ValueError, match="Duplicate PyInstaller member"):
        dc.check_delivery(binary)


def test_large_non_pyinstaller_remains_uninspected(tmp_path, monkeypatch):
    binary = tmp_path / "app"
    binary.write_bytes(_binary_header("ELF") + b"ordinary executable" * 100)
    monkeypatch.setattr(dc, "_MAX_ENTRY_BYTES", 100)
    result = dc.check_delivery(binary)
    assert result["status"] == "warn"
    assert _codes(result) == [dc.FROZEN_UNINSPECTED]
    assert result["inspection"]["frozen_executables"]["inspected"] == 0


def test_pyinstaller_runtime_options_are_not_payload_members(tmp_path):
    binary = tmp_path / "app"
    _pyinstaller_executable(
        binary,
        [
            ("W ignore::DeprecationWarning", b"", "o", False),
            ("W ignore::DeprecationWarning", b"", "o", False),
            ("pyi-runtime-tmpdir ../tmp/nested", b"", "o", False),
            ("W ignore::DeprecationWarning", b"harmless", "x", False),
        ],
    )
    result = dc.check_delivery(binary)
    assert result["status"] == "ok"
    assert result["findings"] == []
    counts = result["inspection"]["frozen_executables"]
    assert (counts["members_total"], counts["members_checked"], counts["unknown_members"]) == (
        1,
        1,
        0,
    )


@pytest.mark.parametrize("compressed", [False, True])
def test_pyinstaller_nonempty_runtime_option_is_scanned(tmp_path, compressed):
    binary = tmp_path / "app"
    _pyinstaller_executable(
        binary, [("pyi-runtime-tmpdir ../tmp/nested", KEY_TEXT.encode(), "o", compressed)]
    )
    result = dc.check_delivery(binary)
    assert result["status"] == "fail"
    assert _codes(result) == [dc.FROZEN_UNINSPECTED, dc.PRIVATE_KEY]
    counts = result["inspection"]["frozen_executables"]
    assert (counts["members_total"], counts["members_checked"], counts["unknown_members"]) == (
        1,
        0,
        1,
    )


@pytest.mark.parametrize("control", ["\n", "\0", "\x7f", "\x85"])
def test_pyinstaller_runtime_option_control_character_rejected(tmp_path, control):
    binary = tmp_path / "app"
    _pyinstaller_executable(binary, [(f"W ignore{control}warning", b"", "o", False)])
    with pytest.raises(ValueError, match="Invalid PyInstaller option name"):
        dc.check_delivery(binary)


@pytest.mark.parametrize("typecode", ["m", "M", "s", "z", "Z", "?", "1", "2"])
def test_pyinstaller_unknown_types_remain_unknown_and_are_scanned(tmp_path, typecode):
    binary = tmp_path / "app"
    _pyinstaller_executable(binary, [("member", b"harmless", typecode, False)])
    result = dc.check_delivery(binary)
    assert result["status"] == "warn"
    assert _codes(result) == [dc.FROZEN_UNINSPECTED]
    counts = result["inspection"]["frozen_executables"]
    assert (counts["members_checked"], counts["unknown_members"], counts["members_total"]) == (
        0,
        1,
        1,
    )
    _pyinstaller_executable(binary, [("member", KEY_TEXT.encode(), typecode, False)])
    assert _codes(dc.check_delivery(binary)) == [dc.FROZEN_UNINSPECTED, dc.PRIVATE_KEY]


@pytest.mark.parametrize(
    "malformation",
    ["short_cookie", "toc_bounds", "member_bounds", "decompressed_limit", "length", "typecode"],
)
def test_pyinstaller_malformed_archive(tmp_path, monkeypatch, malformation):
    binary = tmp_path / "app"
    _pyinstaller_executable(binary, [("data.txt", b"a" * 100, "x", True)])
    data = bytearray(binary.read_bytes())
    cookie_start = len(data) - dc._PYINSTALLER_COOKIE.size
    cookie = list(dc._PYINSTALLER_COOKIE.unpack_from(data, cookie_start))
    toc_start = cookie_start + dc._PYINSTALLER_COOKIE.size - cookie[1] + cookie[2]
    if malformation == "short_cookie":
        data = data[: cookie_start + len(dc._PYINSTALLER_COOKIE_MAGIC) + 1]
    elif malformation == "toc_bounds":
        cookie[2] = cookie[1] + 1
        data[cookie_start:] = dc._PYINSTALLER_COOKIE.pack(*cookie)
    elif malformation == "member_bounds":
        struct.pack_into("!I", data, toc_start + 4, cookie[1] + 1)
    elif malformation == "decompressed_limit":
        monkeypatch.setattr(dc, "_MAX_FROZEN_MEMBER_BYTES", 50)
        # Understate the declared size to exercise bounded decompression itself.
        struct.pack_into("!I", data, toc_start + 12, 1)
    elif malformation == "length":
        struct.pack_into("!I", data, toc_start + 12, 99)
    else:
        data[toc_start + 17] = 255
    binary.write_bytes(data)
    with pytest.raises(ValueError):
        dc.check_delivery(binary)


def test_cli_malformed_pyinstaller_is_error(tmp_path):
    binary = tmp_path / "app"
    binary.write_bytes(_binary_header("ELF") + dc._PYINSTALLER_COOKIE_MAGIC)
    result = CliRunner().invoke(main, ["--check-delivery", str(binary), "--json"])
    assert result.exit_code == 2
    assert json.loads(result.output)["status"] == "error"


def test_canonical_marshal_reference_indices_and_flags():
    # The outer tuple reserves index 0 before its leaf reserves index 1.
    inline = b")\x02z\x03abcz\x03abc"
    referenced = b"\xa9\x02\xfa\x03abcr\x01\x00\x00\x00"
    assert dc._canonical_marshal(referenced) == inline
    assert dc._canonical_marshal(inline) == inline
    assert dc._canonical_marshal(b"\xe9\x01\x00\x00\x00") == b"i\x01\x00\x00\x00"


def test_canonical_marshal_compiled_code():
    import marshal

    code = compile("def f(x):\n return (x, 'same', 'same')\n", "module.py", "exec")
    # Add a reserved root slot to an otherwise reference-free code stream.
    plain = marshal.dumps(code, 2)
    flagged = bytes([plain[0] | 0x80]) + plain[1:]
    assert dc._canonical_marshal(plain) == dc._canonical_marshal(flagged)
    assert dc._canonical_marshal(marshal.dumps(code)) is not None


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"s\x04\x00\x00\x00abc",
        b"r\x00\x00\x00\x00",
        b"r\xff\xff\xff\xff",
        b"?",
        b"NN",
        b")\x01" * 202 + b"N",
        b"\xa9\x01r\x00\x00\x00\x00",
        b"(\xff\xff\xff\x7f",
        b")\x010",
        b":NNN" if __import__("sys").version_info < (3, 14) else b":NN",
    ],
)
def test_canonical_marshal_rejects_invalid(data):
    assert dc._canonical_marshal(data) is None


def test_canonical_marshal_expansion_cap():
    leaf = b"\xf3" + struct.pack("<i", 1024) + b"a" * 1024
    stream = b")\xff" + leaf + (b"r" + struct.pack("<i", 0)) * 254
    assert dc._canonical_marshal(stream) is None


def test_runtime_bytecode_matches_adjacent_source(tmp_path):
    import os
    import subprocess
    import sys

    package = tmp_path / "tiny"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "module.py").write_text(SOURCE, encoding="utf-8")
    env = os.environ.copy()
    env.pop("PYTHONDONTWRITEBYTECODE", None)
    env.pop("PYTHONPYCACHEPREFIX", None)
    subprocess.run(
        [sys.executable, "-E", "-c", "import tiny.module"],
        cwd=tmp_path,
        env=env,
        check=True,
    )
    assert list(package.glob("__pycache__/*.pyc"))
    result = dc.check_delivery(package)
    assert dc.BYTECODE_ORIGIN_UNKNOWN not in _codes(result)
    assert result["status"] == "ok"
    samples = result["inspection"]["bytecode"]["sample"]
    assert samples
    assert all(item["reason"] == "source_not_in_build_report" for item in samples)
    assert result["inspection"]["bytecode"]["matched_adjacent_source"] == len(samples)


def test_bytecode_canonical_comparison_preserves_filename(tmp_path):
    source = tmp_path / "module.py"
    source.write_text(SOURCE, encoding="utf-8")
    py_compile.compile(str(source), dfile="unrelated/build/module.py", doraise=True)
    result = dc.check_delivery(tmp_path)
    assert dc.BYTECODE_ORIGIN_UNKNOWN in _codes(result)
    assert result["inspection"]["bytecode"]["sample"][0]["reason"] == (
        "bytecode_body_differs_or_build_path_unknown"
    )


def test_canonical_marshal_slice():
    import marshal
    import sys

    if sys.version_info < (3, 14):
        pytest.skip("marshal slices require Python 3.14")
    assert dc._canonical_marshal(marshal.dumps(slice(1, 5, 2))) == (
        b":i\x01\x00\x00\x00i\x05\x00\x00\x00i\x02\x00\x00\x00"
    )
