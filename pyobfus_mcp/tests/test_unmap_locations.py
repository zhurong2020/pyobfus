"""MCP frame restoration agrees with CLI on executed artifacts."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from pyobfus.core.mapping import ObfuscationMapping
from pyobfus_mcp.tools import unmap_stack_trace


def run(args, tmp_path):
    return subprocess.run(
        [sys.executable, *map(str, args)],
        text=True,
        capture_output=True,
        env=dict(os.environ, HOME=str(tmp_path), USERPROFILE=str(tmp_path)),
    )


@pytest.mark.parametrize("keep", [False, True])
@pytest.mark.parametrize("marker", [False, True])
def test_real_trace_cli_mcp_parity(tmp_path, keep, marker):
    source = tmp_path / "app.py"
    source.write_text(
        '"""Module docs."""\n'
        'def divide():\n    """Function docs."""\n'
        "    return (\n        1 / 0\n    )\n"
        'if __name__ == "__main__":\n    divide()\n'
    )
    out = tmp_path / "out.py"
    mapping = tmp_path / "mapping.json"
    flags = ["--keep-docstrings"] if keep else ["--remove-docstrings"]
    if marker:
        flags.append("--trace-marker")
    build = run(["-m", "pyobfus", source, "-o", out, "--save-mapping", mapping, *flags], tmp_path)
    assert build.returncode == 0, build.stderr
    crash = run([out], tmp_path)
    assert crash.returncode != 0
    trace = tmp_path / "trace.txt"
    trace.write_text(crash.stderr)
    cli = run(["-m", "pyobfus", "--unmap", trace, "--mapping", mapping, "--json"], tmp_path)
    assert cli.returncode == 0, cli.stderr
    expected = json.loads(cli.stdout)
    actual = unmap_stack_trace(crash.stderr, str(mapping))
    for key in ("frames", "line_map", "unmapped_trace", "mapping_stats", "original_trace"):
        assert actual[key] == expected[key]
    assert actual["line_map"] == "available"
    assert [f["original_line"] for f in actual["frames"]] == [8, 4]
    assert all(f["original_file"] == "app.py" for f in actual["frames"])
    assert "in divide" in actual["unmapped_trace"]
    assert "Code excerpts and caret indicators are unchanged" in actual["ai_hint"]
    assert actual["status"] == "success" and "next_tool" in actual

    # A different build's name is still detected even when locations resolve.
    wrong = unmap_stack_trace(crash.stderr + "NameError: I999999\n", str(mapping))
    assert wrong["unmatched_names"] == ["I999999"]
    assert "restored line locations" in wrong["ai_hint"]


def test_older_core_name_only_fallback(tmp_path, monkeypatch):
    mapping = ObfuscationMapping.from_single_file({"divide": "I0"})
    path = tmp_path / "mapping.json"
    mapping.save(path)
    # Simulate the oldest supported Core, without either new API or mismatch finder.
    monkeypatch.setattr(ObfuscationMapping, "unmap_trace", None)
    monkeypatch.setattr(ObfuscationMapping, "resolve_location", None)
    monkeypatch.setattr(ObfuscationMapping, "unmatched_names", None)
    trace = '  File "out.py", line 7, in I0\n    I0()\n'
    result = unmap_stack_trace(trace, str(path))
    assert result["unmapped_trace"] == '  File "out.py", line 7, in divide\n    divide()\n'
    assert result["frames"] == [] and result["line_map"] == "absent"
    assert result["unmatched_names"] == []
    assert "line numbers still point to the obfuscated" in result["ai_hint"]


def test_real_061_mapping_hint(tmp_path):
    source = tmp_path / "out.py"
    source.write_text("def I1():\n    return 1 / 0\nI1()\n")
    crash = run([source], tmp_path)
    assert crash.returncode != 0
    fixture = Path(__file__).resolve().parents[2] / "tests/fixtures/mapping_061.json"
    # The MCP sandbox only permits project-root paths; copy the checked-in fixture.
    path = tmp_path / "mapping.json"
    path.write_bytes(fixture.read_bytes())
    result = unmap_stack_trace(crash.stderr, str(path))
    assert "in compute_total" in result["unmapped_trace"]
    assert result["line_map"] == "absent"
    assert all(f["status"] == "unmapped" for f in result["frames"])
    assert "pyobfus > 0.6.1" in result["ai_hint"]
