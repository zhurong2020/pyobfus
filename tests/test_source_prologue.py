"""Executable output metadata and final-text traceback regression coverage."""

import json
import os
import stat
import subprocess
import sys

import pytest
from click.testing import CliRunner

from pyobfus.cli import main
from pyobfus.core.source_prologue import source_prologue, copy_executable_bits
from pyobfus.core.mapping import ObfuscationMapping

SHEBANG = "#!/usr/bin/env python3"


@pytest.fixture
def build(tmp_path):
    def run(mode, source, flags=(), encoding="utf-8"):
        src = tmp_path / "src"
        src.mkdir(exist_ok=True)
        script = src / "entry.py"
        script.write_bytes(source.encode(encoding))
        out = tmp_path / ("out.py" if mode == "single" else "out")
        args = [str(script if mode == "single" else src), "-o", str(out), *flags]
        if mode == "legacy":
            args.append("--no-cross-file")
        result = CliRunner().invoke(main, args)
        assert result.exit_code == 0, result.output
        return script, out if mode == "single" else out / script.name, result

    return run


@pytest.mark.parametrize("mode", ["single", "directory", "legacy"])
@pytest.mark.parametrize("marker", [True, False])
@pytest.mark.parametrize("trace", [True, False])
@pytest.mark.parametrize(
    "prefix",
    [
        SHEBANG + "\n",
        "# -*- coding: UTF_8 -*-\n",
        SHEBANG + "\n# -*- coding: utf-8 -*-\n",
        "# leading comment\n# coding=utf8\n",
        "\n# coding: utf-8\n",
        SHEBANG + "\r\n# coding: utf-8\r\n",
    ],
)
def test_cli_preserves_prologue(build, tmp_path, mode, marker, trace, prefix):
    flags = ["--keep-docstrings", "--verify-syntax"]
    if not marker:
        flags.append("--no-community-marker")
    if trace:
        flags.extend(["--trace-marker", "--save-mapping", str(tmp_path / "map.json")])
    _, output, _ = build(mode, prefix + '"""Module docs."""\nprint("héllo")\n', flags)
    text = output.read_text(encoding="utf-8")
    assert text.startswith(prefix.replace("\r\n", "\n"))
    assert "Module docs." in text
    assert ("# pyobfus:generated" in text) == marker
    assert ("# pyobfus:obfuscated" in text) == (trace and mode != "legacy")
    product = subprocess.run([sys.executable, str(output)], capture_output=True, text=True)
    assert product.returncode == 0, product.stderr
    assert product.stdout == "héllo\n"


@pytest.mark.parametrize("mode", ["single", "directory", "legacy"])
@pytest.mark.parametrize("shebang", [False, True])
@pytest.mark.parametrize("marker", [False, True])
@pytest.mark.parametrize("trace", [False, True])
def test_latin1_is_decoded_and_cookie_dropped(build, tmp_path, mode, shebang, marker, trace):
    prefix = SHEBANG + "\n" if shebang else ""
    source = prefix + '# coding: latin-1\nprint("café")\n'
    flags = ["--verbose", "--verify-syntax"]
    if not marker:
        flags.append("--no-community-marker")
    if trace:
        flags.extend(["--trace-marker", "--save-mapping", str(tmp_path / "map.json")])
    script, output, result = build(mode, source, flags, "latin-1")
    assert "Encoding declaration 'latin-1' not kept: output is UTF-8" in result.output
    text = output.read_text(encoding="utf-8")
    assert "latin-1" not in text
    if shebang:
        assert text.splitlines()[0] == SHEBANG
    baseline = subprocess.run([sys.executable, str(script)], capture_output=True)
    product = subprocess.run([sys.executable, str(output)], capture_output=True)
    assert baseline.returncode == product.returncode == 0
    assert baseline.stdout == product.stdout


@pytest.mark.parametrize("mode", ["single", "directory", "legacy"])
def test_utf8_bom(build, mode):
    _, output, _ = build(mode, '# coding: utf-8\nprint("ok")\n', encoding="utf-8-sig")
    assert subprocess.check_output([sys.executable, str(output)]) == b"ok\n"


@pytest.mark.skipif(os.name == "nt", reason="POSIX executable bits")
@pytest.mark.parametrize("mode", ["single", "directory", "legacy"])
def test_direct_execution_and_exact_execute_bits(build, mode, tmp_path):
    script, output, _ = build(mode, SHEBANG + '\nprint("ok")\n')
    script.chmod(0o751)
    # Rebuild after adding execution bits (and preserve existing output read/write bits).
    output.chmod(0o640)
    args = [
        str(script if mode == "single" else script.parent),
        "-o",
        str(output if mode == "single" else output.parent),
    ]
    if mode == "legacy":
        args.append("--no-cross-file")
    result = CliRunner().invoke(main, args)
    assert result.exit_code == 0, result.output
    assert stat.S_IMODE(output.stat().st_mode) == 0o751
    assert os.access(output, os.X_OK)
    assert subprocess.check_output([str(output)]) == subprocess.check_output([str(script)])


@pytest.mark.parametrize("mode", ["single", "directory"])
@pytest.mark.parametrize("trace", [False, True])
def test_real_traceback_unmap_json(build, tmp_path, mode, trace):
    mapping = tmp_path / "map.json"
    flags = ["--save-mapping", str(mapping)]
    if trace:
        flags.append("--trace-marker")
    _, output, _ = build(
        mode,
        SHEBANG + '\n# coding: utf-8\ndef explode():\n    raise ValueError("boom")\nexplode()\n',
        flags,
    )
    crash = subprocess.run([sys.executable, str(output)], capture_output=True, text=True)
    assert crash.returncode != 0
    trace_file = tmp_path / "trace.txt"
    trace_file.write_text(crash.stderr, encoding="utf-8")
    result = CliRunner().invoke(
        main, ["--unmap", "--json", "--mapping", str(mapping), "--trace", str(trace_file)]
    )
    assert result.exit_code == 0, result.output
    frames = json.loads(result.stdout)["frames"]
    assert [frame["original_line"] for frame in frames] == [5, 4]
    saved = ObfuscationMapping.load(mapping)
    assert saved.files[output.name]["line_count"] == len(output.read_text().splitlines())
    for frame in frames:
        assert (
            saved.resolve_location(str(output), frame["obfuscated_line"]).line
            == frame["original_line"]
        )


@pytest.mark.parametrize("mode", ["single", "directory", "legacy"])
def test_dry_run_does_not_write(build, mode):
    _, output, result = build(mode, SHEBANG + '\nprint("ok")\n', ["--dry-run", "--verbose"])
    assert not output.exists()
    if mode != "directory":
        assert SHEBANG in result.output


@pytest.mark.skipif(os.name == "nt", reason="POSIX executable bits")
def test_incremental_preserves_metadata_and_rebuilds_on_chmod(build, tmp_path):
    flags = ["--incremental", "--save-mapping", str(tmp_path / "map.json"), "--trace-marker"]
    script, output, _ = build("directory", SHEBANG + '\nprint("ok")\n', flags)
    args = [str(script.parent), "-o", str(output.parent), *flags, "--json"]
    before = output.read_bytes()
    result = CliRunner().invoke(main, args)
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["stats"]["files_skipped"] == 1
    assert output.read_bytes() == before
    script.chmod(0o755)
    result = CliRunner().invoke(main, args)
    assert result.exit_code == 0, result.output
    assert output.stat().st_mode & 0o111 == 0o111
    assert subprocess.check_output([str(output)]) == b"ok\n"


@pytest.mark.parametrize("source", ['x = "coding: utf-8"\nprint(1)\n', "x = 1\n# coding: utf-8\n"])
def test_cookie_must_follow_pep263(source):
    assert source_prologue(source) == ("", None)


@pytest.mark.skipif(os.name == "nt", reason="POSIX executable bits")
def test_copy_changes_only_execution_bits(tmp_path):
    source, output = tmp_path / "src", tmp_path / "out"
    source.touch()
    output.touch()
    source.chmod(0o710)
    output.chmod(0o646)
    copy_executable_bits(source, output)
    assert stat.S_IMODE(output.stat().st_mode) == 0o756


@pytest.mark.parametrize("mode", ["single", "directory", "legacy"])
def test_pro_output_preserves_prologue(build, mode, monkeypatch):
    import pyobfus.cli as cli

    monkeypatch.setattr(cli, "is_trial_active", lambda: True)
    _, output, _ = build(
        mode, SHEBANG + '\n# coding: utf-8\nprint("ok")\n', ["--level", "pro", "--dead-code"]
    )
    assert output.read_text().startswith(SHEBANG + "\n# coding: utf-8\n")
    assert subprocess.check_output([sys.executable, str(output)]) == b"ok\n"


def test_pro_fusion_restores_prologue_after_text_passes(build, monkeypatch):
    import pyobfus.cli as cli

    monkeypatch.setattr(cli, "is_trial_active", lambda: True)
    _, output, _ = build(
        "single",
        SHEBANG + '\n# coding: utf-8\nprint("ok")\n',
        ["--level", "pro", "--expire-hard", "2099-01-01"],
    )
    assert output.read_text().startswith(SHEBANG + "\n# coding: utf-8\n")
    assert "_pyobfus_expire_check" in output.read_text()
    assert subprocess.check_output([sys.executable, str(output)]) == b"ok\n"


def test_single_file_invalid_encoding_is_a_parse_error(tmp_path):
    """Undecodable input is reported like any unparsable file, not as a crash."""
    source = tmp_path / "bad.py"
    source.write_bytes(b'X = "\xff\xfe"\n')
    result = CliRunner().invoke(main, [str(source), "-o", str(tmp_path / "out.py")])
    assert result.exit_code != 0
    assert "Failed to parse" in result.output
    assert "Unexpected error" not in result.output
