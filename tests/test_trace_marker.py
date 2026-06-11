"""Tests for the --trace-marker auto-unmap convention.

A stable `# pyobfus:obfuscated` header is stamped onto obfuscated files so an
AI agent that lands in one from a traceback knows to reverse the names with
`pyobfus --unmap`. Covers: the marker header, the mapping's stable `marker_id`,
shebang / encoding-cookie preservation, idempotency, and the
no-op-without-mapping guard.
"""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from pyobfus.cli import (
    _apply_trace_markers,
    _insert_after_prologue,
    _trace_marker_block,
    main,
)
from pyobfus.constants import TRACE_MARKER_PREFIX
from pyobfus.core.mapping import ObfuscationMapping


def test_marker_id_is_stable_and_short() -> None:
    m = ObfuscationMapping.from_single_file({"add": "I0", "Calc": "I1"}, module="m")
    mid = m.marker_id()
    assert len(mid) == 8
    # Deterministic: same names → same id, independent of object identity.
    again = ObfuscationMapping.from_single_file({"add": "I0", "Calc": "I1"}, module="m")
    assert again.marker_id() == mid
    # Different names → different id.
    other = ObfuscationMapping.from_single_file({"add": "I9"}, module="m")
    assert other.marker_id() != mid


def test_to_json_includes_marker_id(tmp_path: Path) -> None:
    m = ObfuscationMapping.from_single_file({"add": "I0"}, module="m")
    p = tmp_path / "map.json"
    m.save(p)
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["marker_id"] == m.marker_id()


def test_insert_after_prologue_keeps_shebang_and_coding() -> None:
    text = "#!/usr/bin/env python\n# -*- coding: utf-8 -*-\nx = 1\n"
    block = "# MARKER\n"
    out = _insert_after_prologue(text, block)
    lines = out.splitlines()
    assert lines[0].startswith("#!")
    assert "coding" in lines[1]
    assert lines[2] == "# MARKER"
    assert lines[3] == "x = 1"


def test_trace_marker_block_shape() -> None:
    block = _trace_marker_block("abcd1234", "m.json")
    assert block.startswith(TRACE_MARKER_PREFIX)
    assert "id=abcd1234" in block
    assert "mapping=m.json" in block
    assert "pyobfus --unmap" in block


def test_cli_trace_marker_stamps_output(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "calc.py").write_text("def add_numbers(a, b):\n    return a + b\n", encoding="utf-8")
    out = tmp_path / "dist"
    mapping = tmp_path / "m.json"

    runner = CliRunner()
    result = runner.invoke(
        main,
        [str(src), "-o", str(out), "--save-mapping", str(mapping), "--trace-marker"],
    )
    assert result.exit_code == 0, result.output

    marked = (out / "calc.py").read_text(encoding="utf-8")
    assert marked.startswith(TRACE_MARKER_PREFIX)
    marker_id = json.loads(mapping.read_text(encoding="utf-8"))["marker_id"]
    assert f"id={marker_id}" in marked
    assert "mapping=m.json" in marked
    # Output still byte-compiles (marker is comment-only).
    import py_compile

    py_compile.compile(str(out / "calc.py"), doraise=True)


def test_cli_trace_marker_is_idempotent(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "calc.py").write_text("def f(a):\n    return a\n", encoding="utf-8")
    out = tmp_path / "dist"
    mapping = tmp_path / "m.json"
    args = [str(src), "-o", str(out), "--save-mapping", str(mapping), "--trace-marker"]

    runner = CliRunner()
    assert runner.invoke(main, args).exit_code == 0
    # Re-applying to the already-marked output must not double-stamp.
    second = _apply_trace_markers(out, str(mapping))
    assert second == json.loads(mapping.read_text())["marker_id"]
    assert (out / "calc.py").read_text().count(TRACE_MARKER_PREFIX) == 1


def test_cli_trace_marker_without_mapping_is_noop(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "calc.py").write_text("def f(a):\n    return a\n", encoding="utf-8")
    out = tmp_path / "dist"

    runner = CliRunner()
    result = runner.invoke(main, [str(src), "-o", str(out), "--trace-marker"])
    assert result.exit_code == 0
    assert "--trace-marker has no effect without --save-mapping" in result.output
    assert TRACE_MARKER_PREFIX not in (out / "calc.py").read_text(encoding="utf-8")
