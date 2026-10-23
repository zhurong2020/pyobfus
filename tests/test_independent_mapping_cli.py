"""Independent mappings follow actual successful CLI outputs and builds."""

import inspect
import json
import os
import subprocess
import sys

import pytest

from click.testing import CliRunner

from pyobfus.cli import _apply_trace_markers, main
from pyobfus.constants import TRACE_MARKER_PREFIX
from pyobfus.core.mapping import ObfuscationMapping


def invoke(source, output, *flags):
    runner = CliRunner(
        **({"mix_stderr": False} if "mix_stderr" in inspect.signature(CliRunner).parameters else {})
    )
    result = runner.invoke(
        main, [str(source), "-o", str(output), "--no-cross-file", *map(str, flags)]
    )
    assert result.exit_code == 0, result.output
    return result


def test_incremental_mapping_always_rebuilds(tmp_path):
    source = tmp_path / "src"
    source.mkdir()
    app = source / "app.py"
    app.write_text("def calculate():\n    return 1\ncalculate()\n")
    output = tmp_path / "out"
    path = tmp_path / "mapping.json"
    invoke(source, output, "--incremental")
    assert not path.exists()
    result = invoke(source, output, "--incremental", "--save-mapping", path)
    assert "rebuild to ensure current mapping metadata" in result.output
    first = ObfuscationMapping.load(path)
    # Even an existing mapping with matching cached outputs must be refreshed.
    path.write_text("invalid old mapping")
    result = invoke(source, output, "--incremental", "--save-mapping", path)
    assert "rebuild to ensure current mapping metadata" in result.output
    assert ObfuscationMapping.load(path).marker_id() == first.marker_id()
    app.write_text("\n\ndef calculate():\n    return 1\ncalculate()\n")
    invoke(source, output, "--incremental", "--save-mapping", path)
    changed = ObfuscationMapping.load(path)
    assert changed.marker_id() != first.marker_id()
    assert changed.files["app.py"]["source_sha256"] != first.files["app.py"]["source_sha256"]


def test_dry_run_writes_no_independent_artifacts(tmp_path):
    source = tmp_path / "src"
    source.mkdir()
    (source / "app.py").write_text("answer = 42\n")
    output = tmp_path / "out"
    path = tmp_path / "mapping.json"
    result = invoke(source, output, "--dry-run", "--save-mapping", path, "--trace-marker", "--json")
    assert json.loads(result.stdout)["status"] == "success"
    assert not path.exists()
    assert not output.exists()


def test_partial_build_stamps_only_current_successes(tmp_path):
    source = tmp_path / "src"
    source.mkdir()
    (source / "good.py").write_text("def calculate():\n    return 1\n")
    (source / "bad.py").write_text("def invalid(:\n")
    output = tmp_path / "out"
    output.mkdir()
    stale = {"bad.py": "old = 1\n", "removed.py": "old = 2\n"}
    for name, text in stale.items():
        (output / name).write_text(text)
    path = tmp_path / "mapping.json"
    result = invoke(source, output, "--save-mapping", path, "--trace-marker")
    assert "Failed to obfuscate" in result.stderr
    mapping = ObfuscationMapping.load(path)
    assert set(mapping.file_names) == set(mapping.files) == {"good.py"}
    assert TRACE_MARKER_PREFIX in (output / "good.py").read_text()
    for name, text in stale.items():
        assert (output / name).read_text() == text
    first = path.read_bytes()
    assert _apply_trace_markers(output, str(path)) == mapping.marker_id()
    assert path.read_bytes() == first


def test_all_failed_build_saves_empty_v2(tmp_path):
    source = tmp_path / "src"
    source.mkdir()
    (source / "bad.py").write_text("def invalid(:\n")
    path = tmp_path / "mapping.json"
    invoke(source, tmp_path / "out", "--save-mapping", path, "--trace-marker")
    data = json.loads(path.read_text())
    assert data["version"] == 2
    assert data["file_names"] == {}


def test_failed_and_stale_nested_outputs_cannot_borrow_sibling_mapping(tmp_path):
    source = tmp_path / "src"
    (source / "pkg").mkdir(parents=True)
    (source / "util.py").write_text("def calculate():\n    return 1 / 0\ncalculate()\n")
    (source / "pkg/util.py").write_text("def broken(:\n")
    output = tmp_path / "out"
    (output / "pkg").mkdir(parents=True)
    (output / "pkg/util.py").write_text("def I0():\n    return 1 / 0\nI0()\n")
    (output / "removed.py").write_text("print(1)\n")
    path = tmp_path / "mapping.json"
    result = invoke(source, output, "--save-mapping", path, "--json")
    assert any(
        "Mapping excludes" in warning for warning in json.loads(result.stdout)["stats"]["warnings"]
    )
    mapping = ObfuscationMapping.load(path)
    assert set(mapping.unmapped_files) == {"pkg/util.py", "removed.py"}
    trace = f'  File "{output / "pkg/util.py"}", line 2, in I0\n'
    assert mapping.unmap_trace(trace)["unmapped_trace"] == trace


def test_optional_metadata_failure_preserves_successful_output(tmp_path, monkeypatch):
    import pyobfus.core.line_map as line_map

    def fail(*args, **kwargs):
        raise RuntimeError("synthetic metadata failure")

    monkeypatch.setattr(line_map, "build_line_map", fail)
    source = tmp_path / "src"
    source.mkdir()
    (source / "app.py").write_text("def calculate():\n    return 1 / 0\ncalculate()\n")
    output = tmp_path / "out"
    path = tmp_path / "mapping.json"
    result = invoke(source, output, "--save-mapping", path)
    assert "line mapping unavailable" in result.stderr
    mapping = ObfuscationMapping.load(path)
    assert mapping.files["app.py"]["lines"] is None
    trace = f'  File "{output / "app.py"}", line 3, in I0\n'
    result = mapping.unmap_trace(trace)
    assert "in calculate" in result["unmapped_trace"]
    assert result["frames"][0]["resolved_file"] == "app.py"


@pytest.mark.skipif(os.name == "nt", reason="POSIX-only filename spelling")
@pytest.mark.parametrize("filename", ["a:b.py", "a\\b.py"])
def test_nonportable_posix_filename_does_not_fail_build(tmp_path, filename):
    source = tmp_path / "src"
    source.mkdir()
    (source / filename).write_text("print(42)\n")
    output = tmp_path / "out"
    path = tmp_path / "mapping.json"
    result = invoke(source, output, "--save-mapping", path)
    assert (output / filename).exists()
    assert "portable mapping" in result.stderr
    mapping = ObfuscationMapping.load(path)
    assert filename in mapping.unmapped_files


@pytest.mark.parametrize("prefix", ["I", "λ", "K", "a\u0301"])
def test_colliding_names_restore_from_real_traceback(tmp_path, prefix):
    source = tmp_path / "src"
    for rel, function in (("a/util.py", "calculate_total"), ("b/util.py", "parse_amount")):
        app = source / rel
        app.parent.mkdir(parents=True)
        app.write_text(f"def {function}():\n    return 1 / 0\n{function}()\n")
    output = tmp_path / "out"
    path = tmp_path / "mapping.json"
    invoke(source, output, "--save-mapping", path, "--trace-marker", "--name-prefix", prefix)
    mapping = ObfuscationMapping.load(path)
    import unicodedata

    obfuscated = unicodedata.normalize("NFKC", prefix + "0")
    assert mapping.file_names["a/util.py"][obfuscated] == ["calculate_total"]
    assert mapping.file_names["b/util.py"][obfuscated] == ["parse_amount"]
    env = dict(os.environ, HOME=str(tmp_path), USERPROFILE=str(tmp_path))
    for rel, function in (("a/util.py", "calculate_total"), ("b/util.py", "parse_amount")):
        crashed = subprocess.run(
            [sys.executable, "-X", "utf8", "-I", str(output / rel)],
            env=env,
            encoding="utf-8",
            capture_output=True,
        )
        assert crashed.returncode != 0
        assert f"in {obfuscated}" in crashed.stderr
        trace = tmp_path / "trace.txt"
        trace.write_text(crashed.stderr, encoding="utf-8")
        runner = CliRunner(
            **(
                {"mix_stderr": False}
                if "mix_stderr" in inspect.signature(CliRunner).parameters
                else {}
            )
        )
        result = runner.invoke(
            main, ["--unmap", "--trace", str(trace), "--mapping", str(path), "--json"]
        )
        assert result.exit_code == 0, result.output
        restored = json.loads(result.stdout)
        assert f"in {function}" in restored["unmapped_trace"]
        assert restored["frames"][-1]["original_file"] == rel
        assert restored["frames"][-1]["original_line"] == 2
