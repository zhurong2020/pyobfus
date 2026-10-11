"""Integration tests for --save-mapping + --unmap CLI flow."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from pyobfus.cli import _handle_unmap, main


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


def _write_minimal_mapping(tmp_path: Path) -> Path:
    mapping_path = tmp_path / "mapping.json"
    mapping_path.write_text(
        json.dumps(
            {
                "version": 1,
                "modules": {"m": {"foo": "I0"}},
                "global": {"I0": {"module": "m", "original": "foo"}},
            }
        ),
        encoding="utf-8",
    )
    return mapping_path


def test_unmap_accepts_positional_trace_path(tmp_path: Path) -> None:
    """`pyobfus --unmap trace.txt --mapping m.json` reads the positional file."""
    mapping_path = _write_minimal_mapping(tmp_path)
    trace_file = tmp_path / "trace.txt"
    trace_file.write_text('  File "m.py", line 3, in I0\n', encoding="utf-8")

    result = CliRunner().invoke(main, ["--unmap", str(trace_file), "--mapping", str(mapping_path)])
    assert result.exit_code == 0, result.output
    assert "in foo" in result.output


def test_unmap_rejects_positional_and_trace_together(tmp_path: Path) -> None:
    mapping_path = _write_minimal_mapping(tmp_path)
    trace_file = tmp_path / "trace.txt"
    trace_file.write_text("in I0\n", encoding="utf-8")

    result = CliRunner().invoke(
        main,
        ["--unmap", str(trace_file), "--trace", str(trace_file), "--mapping", str(mapping_path)],
    )
    assert result.exit_code == 2
    assert "not both" in result.output


def test_unmap_without_trace_on_terminal_does_not_wait(tmp_path: Path, monkeypatch, capsys) -> None:
    """With no trace and an interactive stdin, fail fast instead of blocking."""
    mapping_path = _write_minimal_mapping(tmp_path)

    class _Tty(io.StringIO):
        def isatty(self) -> bool:
            return True

    monkeypatch.setattr("sys.stdin", _Tty(""))
    with pytest.raises(SystemExit) as exc:
        _handle_unmap(trace_path=None, mapping_path=str(mapping_path))
    assert exc.value.code == 2
    assert "needs a trace" in capsys.readouterr().err


def test_unmap_warns_when_trace_has_names_missing_from_mapping(tmp_path: Path) -> None:
    """A mapping from another build must not be applied silently."""
    mapping_path = _write_minimal_mapping(tmp_path)
    trace_file = tmp_path / "trace.txt"
    trace_file.write_text("in I0\n    I5 = I7 * 2\n", encoding="utf-8")

    result = CliRunner().invoke(
        main, ["--unmap", "--trace", str(trace_file), "--mapping", str(mapping_path)]
    )
    assert result.exit_code == 0
    # result.output: click < 8.2 (Python 3.9) cannot capture stderr separately.
    assert "in foo" in result.output
    assert "Warning: 2 obfuscated name(s)" in result.output
    assert "I5, I7" in result.output

    as_json = CliRunner().invoke(
        main,
        ["--unmap", "--trace", str(trace_file), "--mapping", str(mapping_path), "--json"],
    )
    payload = json.loads(as_json.stdout)
    assert payload["unmatched_names"] == ["I5", "I7"]
    assert "different build" in payload["warning"]


def test_unmap_no_warning_when_mapping_covers_trace(tmp_path: Path) -> None:
    mapping_path = _write_minimal_mapping(tmp_path)
    trace_file = tmp_path / "trace.txt"
    trace_file.write_text("in I0 (see MyI9Thing)\n", encoding="utf-8")

    result = CliRunner().invoke(
        main,
        ["--unmap", "--trace", str(trace_file), "--mapping", str(mapping_path), "--json"],
    )
    payload = json.loads(result.stdout)
    assert payload["unmatched_names"] == []
    assert "warning" not in payload


@pytest.mark.parametrize("path", ["/deploy/pkg/out.py", r"C:\app\pkg\out.py", "pkg/out.py"])
def test_location_paths_and_partial_metadata(tmp_path, path):
    from pyobfus.core.mapping import ObfuscationMapping

    mapping = ObfuscationMapping.from_single_file({"divide": "I0"})
    mapping.files = {
        "pkg/out.py": {
            "source": "pkg/core.py",
            "module": "pkg.core",
            "line_count": 7,
            "lines": [[1, None], [5, 15]],
        },
        "unsupported.py": {
            "source": "other.py",
            "module": "other",
            "line_count": 5,
            "lines": None,
            "reason": "Pro fusion text passes enabled",
        },
    }
    mapping_path = tmp_path / "mapping.json"
    mapping.save(mapping_path)
    trace = (
        f'  File "{path}", line 7, in I0\r\n'
        "    I0()\r\n    ^^^^\r\n"
        '  File "foreign.py", line 1, in external\r\n'
        "custom log: pkg/out.py:7 I0\r\n"
    )
    # Core preserves line endings; Click's text stdin normalizes CRLF.
    direct = mapping.unmap_trace(trace)
    assert "    divide()\r\n    ^^^^\r\n" in direct["unmapped_trace"]
    result = CliRunner().invoke(
        main, ["--unmap", "--trace", "-", "--mapping", str(mapping_path), "--json"], input=trace
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["line_map"] == "partial"
    assert payload["frames"] == [
        {
            "obfuscated_file": path,
            "obfuscated_line": 7,
            "original_file": "pkg/core.py",
            "original_line": 15,
            "status": "mapped",
        },
        {
            "obfuscated_file": "foreign.py",
            "obfuscated_line": 1,
            "original_file": None,
            "original_line": None,
            "status": "unmapped",
        },
    ]
    assert 'File "pkg/core.py", line 15, in divide' in payload["unmapped_trace"]
    assert "    divide()\n    ^^^^\n" in payload["unmapped_trace"]
    assert '  File "foreign.py", line 1, in external\n' in payload["unmapped_trace"]
    assert "custom log: pkg/out.py:7 divide\n" in payload["unmapped_trace"]
    assert "incomplete" in payload["ai_hint"]


def test_mismatch_warns_about_line_restoration(tmp_path):
    from pyobfus.core.mapping import ObfuscationMapping

    mapping = ObfuscationMapping.from_single_file({"divide": "I0"})
    mapping.files["out.py"] = {
        "source": "app.py",
        "module": "app",
        "line_count": 1,
        "lines": [[1, 25]],
    }
    path = tmp_path / "mapping.json"
    mapping.save(path)
    result = CliRunner().invoke(
        main,
        ["--unmap", "--mapping", str(path), "--json"],
        input='  File "out.py", line 1, in I999\n',
    )
    payload = json.loads(result.stdout)
    assert payload["frames"][0]["status"] == "mapped"
    assert payload["unmatched_names"] == ["I999"]
    assert "different build" in payload["warning"]
    assert "line restoration may be untrustworthy" in payload["ai_hint"]


def test_ambiguous_and_nonstandard_frames(tmp_path):
    from pyobfus.core.mapping import ObfuscationMapping

    mapping = ObfuscationMapping.from_single_file({"divide": "I0"})
    for package in ("a", "b"):
        mapping.files[f"{package}/util.py"] = {
            "source": f"{package}/util.py",
            "module": package,
            "line_count": 5,
            "lines": [[1, 2]],
        }
    trace = '  File "util.py", line 3, in I0\nFile "a/util.py", line 3\n'
    restored = mapping.unmap_trace(trace)
    assert (
        restored["unmapped_trace"]
        == '  File "util.py", line 3, in divide\nFile "a/util.py", line 3\n'
    )
    assert len(restored["frames"]) == 1
    assert restored["frames"][0]["status"] == "unmapped"
    assert restored["line_map"] == "partial"


def _root_mapping(keys):
    from pyobfus.core.mapping import ObfuscationMapping

    mapping = ObfuscationMapping.from_single_file({"compute_price": "I0", "total": "I2"})
    for key in keys:
        mapping.files[key] = {
            "source": key,
            "module": "app",
            "line_count": 12,
            "lines": [[1, None], [5, 20]],
        }
    return mapping


def test_excerpt_names_and_indicators():
    mapping = _root_mapping(["main.py"])
    excerpt = "    I2 = vendorlib.main.run_hooks(I0)\r\n"
    indicator = "    ~~~~~~~~~~~~^^^^^^^^^^^\r\n"
    trace = '  File "/deploy/main.py", line 7, in I0\r\n' + excerpt + indicator
    result = mapping.unmap_trace(trace)
    assert mapping.unmap_text(excerpt) in result["unmapped_trace"]
    assert indicator in result["unmapped_trace"]
    assert "column positions" in result["ai_hint"]


@pytest.mark.parametrize("third_party_line", [3, 7])
@pytest.mark.parametrize("windows", [False, True])
def test_deployment_root_majority(third_party_line, windows):
    mapping = _root_mapping(["main.py"])
    user = r"C:\deploy\main.py" if windows else "/deploy/main.py"
    # Different drive-letter case still belongs to the same deployment root.
    second = r"c:\deploy\main.py" if windows else user
    vendor = r"C:\site\vendorlib\main.py" if windows else "/site/vendorlib/main.py"
    foreign_frame = f'  File "{vendor}", line {third_party_line}, in I0\r\n'
    trace = (
        f'  File "{user}", line 7, in I0\r\n'
        f'  File "{second}", line 8, in I0\r\n' + foreign_frame
    )
    result = mapping.unmap_trace(trace)
    assert [f["status"] for f in result["frames"]] == ["mapped", "mapped", "unmapped"]
    assert foreign_frame in result["unmapped_trace"]
    assert "[generated by pyobfus]" not in result["unmapped_trace"]


@pytest.mark.parametrize(
    "keys,paths",
    [
        (["main.py"], ["/deploy/main.py", "/site/vendorlib/main.py"]),
        (["__init__.py"], ["/deploy/__init__.py", "/stdlib/json/__init__.py"]),
        (["main.py"], [r"C:\deploy\main.py", r"C:\site\vendorlib\main.py"]),
    ],
)
def test_deployment_root_tie(keys, paths):
    mapping = _root_mapping(keys)
    trace = "".join(f'  File "{path}", line 3, in I0\n' for path in paths)
    result = mapping.unmap_trace(trace)
    assert result["unmapped_trace"] == trace
    assert all(f["status"] == "unmapped" for f in result["frames"])
    assert "Cannot determine the deployment root" in result["ai_hint"]


def test_full_file_key_and_duplicate_filenames():
    mapping = _root_mapping(["app/a/util.py", "app/b/util.py", "pkg/__init__.py"])
    paths = ["/deploy/app/a/util.py", "/deploy/app/b/util.py", "/stdlib/json/__init__.py"]
    trace = "".join(f'  File "{path}", line 7, in external\n' for path in paths)
    result = mapping.unmap_trace(trace)
    assert [f["status"] for f in result["frames"]] == ["mapped", "mapped", "unmapped"]
    assert result["frames"][0]["original_file"] == "app/a/util.py"
    assert result["frames"][1]["original_file"] == "app/b/util.py"
    assert trace.splitlines()[-1] in result["unmapped_trace"]
    assert mapping.resolve_location("/deploy/b/util.py", 7) is None
    assert mapping.resolve_location("/stdlib/json/__init__.py", 7) is None
