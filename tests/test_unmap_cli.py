"""Integration tests for --save-mapping + --unmap CLI flow."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from pyobfus.cli import main


def test_save_mapping_and_unmap_roundtrip(tmp_path: Path) -> None:
    """Obfuscate a file with --save-mapping, then --unmap a synthetic trace."""
    src = tmp_path / "src.py"
    src.write_text(
        "class Calculator:\n"
        "    def add(self, a, b):\n"
        "        return a + b\n"
        "\n"
        "def main():\n"
        "    calc = Calculator()\n"
        "    return calc.add(1, 2)\n",
        encoding="utf-8",
    )

    out = tmp_path / "out.py"
    mapping = tmp_path / "mapping.json"

    runner = CliRunner()
    result = runner.invoke(
        main,
        [str(src), "-o", str(out), "--save-mapping", str(mapping)],
    )
    assert result.exit_code == 0, result.output
    assert mapping.exists()

    data = json.loads(mapping.read_text(encoding="utf-8"))
    assert data["version"] == 1
    # We don't know the module key (file.stem), but at least one module should exist
    assert data["modules"]
    any_module = next(iter(data["modules"].values()))
    assert "Calculator" in any_module or "add" in any_module

    # Synthesize a fake trace using actual obfuscated names from the mapping
    obfuscated_for_calculator = any_module.get("Calculator")
    obfuscated_for_add = any_module.get("add")
    assert obfuscated_for_calculator and obfuscated_for_add

    trace = (
        f"Traceback (most recent call last):\n"
        f'  File "out.py", line 7, in main\n'
        f"    return calc.{obfuscated_for_add}(1, 2)\n"
        f"TypeError: {obfuscated_for_calculator}.{obfuscated_for_add}() missing 1 required argument\n"
    )
    trace_file = tmp_path / "trace.log"
    trace_file.write_text(trace, encoding="utf-8")

    result2 = runner.invoke(
        main,
        ["--unmap", "--trace", str(trace_file), "--mapping", str(mapping)],
    )
    assert result2.exit_code == 0, result2.output
    assert "in main" in result2.output  # untouched, real name
    assert "Calculator" in result2.output
    assert ".add(" in result2.output
    assert obfuscated_for_calculator not in result2.output


def test_unmap_json_output(tmp_path: Path) -> None:
    # Minimal hand-crafted mapping file
    mapping_path = tmp_path / "mapping.json"
    mapping_path.write_text(
        json.dumps(
            {
                "version": 1,
                "modules": {"m": {"foo": "I0", "bar": "I1"}},
                "global": {
                    "I0": {"module": "m", "original": "foo"},
                    "I1": {"module": "m", "original": "bar"},
                },
            }
        ),
        encoding="utf-8",
    )
    trace_path = tmp_path / "trace.log"
    trace_path.write_text("call to I0 at line 3; helper is I1", encoding="utf-8")

    result = CliRunner().invoke(
        main,
        [
            "--unmap",
            "--trace",
            str(trace_path),
            "--mapping",
            str(mapping_path),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["unmapped_trace"] == "call to foo at line 3; helper is bar"
    assert data["mapping_stats"]["unique_obfuscated"] == 2
    assert data["ai_hint"]


def test_unmap_without_mapping_fails_cleanly(tmp_path: Path) -> None:
    result = CliRunner().invoke(main, ["--unmap", "--trace", "-"], input="hi\n")
    assert result.exit_code == 2
    assert "--mapping" in result.output


def test_unmap_with_missing_trace_file_fails(tmp_path: Path) -> None:
    mapping = tmp_path / "m.json"
    mapping.write_text(json.dumps({"version": 1, "modules": {}, "global": {}}), encoding="utf-8")
    result = CliRunner().invoke(
        main,
        [
            "--unmap",
            "--trace",
            str(tmp_path / "does_not_exist.log"),
            "--mapping",
            str(mapping),
        ],
    )
    assert result.exit_code == 2
    assert "trace file not found" in result.output


def test_unmap_rejects_bad_mapping_version(tmp_path: Path) -> None:
    mapping = tmp_path / "m.json"
    mapping.write_text(json.dumps({"version": 999, "modules": {}}), encoding="utf-8")
    trace = tmp_path / "t.log"
    trace.write_text("x", encoding="utf-8")
    result = CliRunner().invoke(main, ["--unmap", "--trace", str(trace), "--mapping", str(mapping)])
    assert result.exit_code == 2
    assert "Unsupported mapping version" in result.output


def test_save_mapping_in_directory_mode(tmp_path: Path) -> None:
    """Ensure --save-mapping works with the cross-file orchestrator path."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("def helper():\n    return 1\n", encoding="utf-8")
    (src / "b.py").write_text(
        "from a import helper\n\ndef caller():\n    return helper()\n",
        encoding="utf-8",
    )
    out = tmp_path / "dist"
    mapping = tmp_path / "mapping.json"

    result = CliRunner().invoke(
        main,
        [str(src), "-o", str(out), "--save-mapping", str(mapping)],
    )
    assert result.exit_code == 0, result.output
    assert mapping.exists()

    data = json.loads(mapping.read_text(encoding="utf-8"))
    assert data["mode"] == "cross_file"
    # Expect both modules present
    module_keys = list(data["modules"].keys())
    # module names can be "a" and "b" or similar
    assert len(module_keys) >= 1
