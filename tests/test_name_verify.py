"""--verify-names: static check that obfuscation leaves no global name unbound."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict
from unittest import mock

import pytest
from click.testing import CliRunner

from pyobfus.cli import main
from pyobfus.core.name_verify import snapshot_source, undefined_globals, verify_generated_names


def _tree(root: Path, files: Dict[str, str]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


ALIAS_SOURCE = {
    "pkg/__init__.py": "",
    "pkg/helpers.py": "def stage(text):\n    return 'stage:' + text\n",
    "pkg/user.py": (
        "from pkg.helpers import stage as progress_stage\n\n"
        "def run():\n    return progress_stage('x')\n"
    ),
}


def test_undefined_globals_covers_common_bindings() -> None:
    source = (
        "import os\nfrom typing import List\nCONST = 1\n\n"
        "class A:\n    attr: List[int] = []\n    def m(self):\n        return A, __class__\n\n"
        "def f(x, *args, **kw):\n    global LATE\n    LATE = x\n"
        "    for i in range(3):\n        pass\n"
        "    with open(os.sep) as fh:\n        pass\n"
        "    return [y for y in args], lambda z: z, CONST, i, fh\n\n"
        "def g():\n    return LATE, missing_name\n"
    )
    assert undefined_globals(source) == {"missing_name"}


def test_star_import_and_syntax_errors_are_not_judged() -> None:
    assert undefined_globals("from os import *\nprint(sep)\n") is None
    assert undefined_globals("def broken(:\n") is None


def test_reports_the_aliased_import_defect(tmp_path: Path) -> None:
    """The shape a real downstream build hit: call site renamed, alias left as is."""
    source = _tree(tmp_path / "src", ALIAS_SOURCE)
    baseline = snapshot_source(source, sorted(source.rglob("*.py")))
    output = _tree(
        tmp_path / "out",
        {
            "pkg/__init__.py": "",
            "pkg/helpers.py": "def I0(text):\n    return 'stage:' + text\n",
            "pkg/user.py": (
                "from pkg.helpers import I0 as progress_stage\n\n" "def I1():\n    return I0('x')\n"
            ),
        },
    )

    result = verify_generated_names(baseline, source, output)

    assert result["names_valid"] is False
    assert result["files_checked"] == 3
    assert result["errors"] == [
        {
            "path": "pkg/user.py",
            "line": 4,
            "name": "I0",
            "message": "name 'I0' has no static global binding (possible NameError)",
        }
    ]
    assert result["execution_performed"] is False


def test_names_already_unbound_in_the_source_are_not_reported(tmp_path: Path) -> None:
    files = {"m.py": "def f():\n    return injected_at_runtime\n"}
    source = _tree(tmp_path / "src", files)
    output = _tree(tmp_path / "out", files)
    baseline = snapshot_source(source, [source / "m.py"])
    assert verify_generated_names(baseline, source, output)["names_valid"] is True


def test_single_file_build_is_compared_with_its_source(tmp_path: Path) -> None:
    src = tmp_path / "a.py"
    src.write_text("def f():\n    return 1\n", encoding="utf-8")
    out = tmp_path / "out.py"
    out.write_text("def I0():\n    return I1\n", encoding="utf-8")
    baseline = snapshot_source(src, [src])
    result = verify_generated_names(baseline, src, out)
    assert [e["name"] for e in result["errors"]] == ["I1"]


def test_cli_directory_build_passes(tmp_path: Path) -> None:
    source = _tree(tmp_path / "src", ALIAS_SOURCE)
    out = tmp_path / "out"
    result = CliRunner().invoke(main, [str(source), "-o", str(out), "--verify-names"])
    assert result.exit_code == 0, result.output
    assert "Name verification passed: 3 generated module(s)" in result.output


def test_cli_in_place_build_still_has_a_baseline(tmp_path: Path) -> None:
    """-o equal to the input overwrites the source; the baseline is taken first."""
    source = _tree(tmp_path / "src", ALIAS_SOURCE)
    result = CliRunner().invoke(main, [str(source), "-o", str(source), "--verify-names"])
    assert result.exit_code == 0, result.output
    assert "Name verification passed: 3 generated module(s)" in result.output


def test_cli_failure_is_structured_and_blocking(tmp_path: Path) -> None:
    source = _tree(tmp_path / "src", ALIAS_SOURCE)
    out = tmp_path / "out"
    failed = {
        "mode": "names",
        "names_valid": False,
        "files_checked": 3,
        "files_skipped": 0,
        "errors": [{"path": "pkg/user.py", "line": 4, "name": "I0", "message": "m"}],
        "execution_performed": False,
    }
    with mock.patch("pyobfus.core.name_verify.verify_generated_names", return_value=failed):
        human = CliRunner().invoke(main, [str(source), "-o", str(out), "--verify-names"])
        machine = CliRunner().invoke(
            main, [str(source), "-o", str(out), "--verify-names", "--json"]
        )
    assert human.exit_code == 1
    assert "pkg/user.py:4" in human.output
    assert machine.exit_code == 1
    payload = json.loads(machine.output)
    assert payload["error_type"] == "NameVerificationError"
    assert payload["verification"] == failed


def test_cli_rejects_dry_run(tmp_path: Path) -> None:
    src = tmp_path / "a.py"
    src.write_text("value = 1\n", encoding="utf-8")
    out = tmp_path / "out.py"
    result = CliRunner().invoke(
        main, [str(src), "-o", str(out), "--dry-run", "--verify-names", "--json"]
    )
    assert result.exit_code == 1
    assert json.loads(result.output)["error_type"] == "UsageError"
    assert not out.exists()


@pytest.mark.parametrize(
    "source, expected",
    [
        ("def f():\n    global missing\n    return missing\n", {"missing"}),
        (
            "print(__class__, __module__, __qualname__, __dict__)\n",
            {"__class__", "__module__", "__qualname__", "__dict__"},
        ),
        ("class C:\n    print(__module__, __qualname__)\n", set()),
        ("class C:\n    print(__class__, __dict__)\n", {"__class__", "__dict__"}),
        (
            "class C:\n    def f(self):\n        return __module__, __qualname__\n",
            {"__module__", "__qualname__"},
        ),
        ("class C:\n    def f(self):\n        return __class__\n", set()),
        (
            "def set_value():\n    global value\n    value = 1\n"
            "def get_value():\n    return value\n",
            set(),
        ),
        (
            "def set_value():\n    global mod\n    import os as mod\n"
            "def get_value():\n    return mod\n",
            set(),
        ),
        ("class C:\n    value = 1\n    def f(self):\n        return value\n", {"value"}),
        ("value = 1\nitems = [value for value in range(3)]\nprint(value)\n", set()),
    ],
)
def test_scope_boundaries(source: str, expected: set) -> None:
    assert undefined_globals(source) == expected


@pytest.mark.parametrize("single", [False, True])
def test_missing_output_is_a_verification_failure(tmp_path: Path, single: bool) -> None:
    root = _tree(tmp_path / "src", {"m.py": "value = 1\n"})
    source = root / "m.py" if single else root
    baseline = snapshot_source(source, [root / "m.py"])
    output = tmp_path / "missing.py" if single else tmp_path / "missing"
    result = verify_generated_names(baseline, source, output)
    assert result["names_valid"] is False
    assert result["errors"][0]["path"] == "m.py"
    assert "read" in result["errors"][0]["message"].lower()


def test_invalid_output_is_a_verification_failure(tmp_path: Path) -> None:
    source = _tree(tmp_path / "src", {"m.py": "value = 1\n"})
    output = _tree(tmp_path / "out", {"m.py": "def broken(:\n"})
    result = verify_generated_names(snapshot_source(source, [source / "m.py"]), source, output)
    assert result["names_valid"] is False
    assert "parse" in result["errors"][0]["message"].lower()


def test_source_read_failure_is_not_a_zero_file_pass(tmp_path: Path) -> None:
    source = _tree(tmp_path / "src", {"m.py": "value = 1\n"})
    with mock.patch("tokenize.open", side_effect=OSError("not readable")):
        baseline = snapshot_source(source, [source / "m.py"])
    output = _tree(tmp_path / "out", {"m.py": "value = 1\n"})
    result = verify_generated_names(baseline, source, output)
    assert result["names_valid"] is False
    assert "source" in result["errors"][0]["message"].lower()


def test_pep263_and_utf8_bom_sources_are_checked(tmp_path: Path) -> None:
    source = _tree(tmp_path / "src", {})
    (source / "latin.py").write_bytes(b"# coding: latin-1\nvalue = 'caf\xe9'\n")
    (source / "bom.py").write_bytes(b"\xef\xbb\xbfvalue = 1\n")
    output = _tree(
        tmp_path / "out", {"latin.py": "value = missing\n", "bom.py": "value = absent\n"}
    )
    result = verify_generated_names(snapshot_source(source, source.glob("*.py")), source, output)
    assert result["files_checked"] == 2
    assert {e["name"] for e in result["errors"]} == {"missing", "absent"}


def test_star_imports_report_partial_coverage(tmp_path: Path) -> None:
    source = _tree(tmp_path / "src", {"m.py": "from os import *\nprint(sep)\n"})
    result = CliRunner().invoke(
        main, [str(source), "-o", str(tmp_path / "out"), "--verify-names", "--json"]
    )
    assert result.exit_code == 0, result.output
    names = json.loads(result.output)["name_verification"]
    assert names["files_checked"] == 0
    assert names["files_skipped"] == 1
    assert names["coverage_complete"] is False
    assert names["skipped"] == [{"path": "m.py", "reason": "source_star_import"}]
    assert "partial" in json.loads(result.output)["ai_hint"].lower()
    human = CliRunner().invoke(main, [str(source), "-o", str(tmp_path / "human"), "--verify-names"])
    assert "partial" in human.output.lower()
    assert "m.py" in human.output
    assert "Name verification passed" not in human.output


@pytest.mark.parametrize("single", [False, True])
@pytest.mark.parametrize("syntax", [False, True])
def test_success_records_names_in_json_and_build_report(
    tmp_path: Path, single: bool, syntax: bool
) -> None:
    root = _tree(tmp_path / "src", {"m.py": "def answer():\n    return 42\n"})
    source = root / "m.py" if single else root
    output = tmp_path / "renamed.py" if single else tmp_path / "out"
    report = tmp_path / "report.json"
    args = [
        str(source),
        "-o",
        str(output),
        "--verify-names",
        "--build-report",
        str(report),
        "--json",
    ]
    if syntax:
        args.append("--verify-syntax")
    result = CliRunner().invoke(main, args)
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["name_verification"]["files_checked"] == 1
    assert payload["name_verification"]["coverage_complete"] is True
    facts = json.loads(report.read_text())
    assert facts["name_verification"] == payload["name_verification"]
    assert facts["verification"].get("syntax_valid", False) is syntax
    assert str(tmp_path) not in report.read_text()


def test_incremental_cache_hit_keeps_names_evidence(tmp_path: Path) -> None:
    source = _tree(tmp_path / "src", {"m.py": "def answer():\n    return 42\n"})
    args = [str(source), "-o", str(tmp_path / "out"), "--incremental", "--verify-names", "--json"]
    first = CliRunner().invoke(main, args)
    second = CliRunner().invoke(main, args)
    assert first.exit_code == second.exit_code == 0
    assert json.loads(second.output)["name_verification"]["files_checked"] == 1
    assert json.loads(second.output)["stats"]["files_processed"] == 0


def test_checker_never_executes_source_or_output(tmp_path: Path) -> None:
    source = _tree(tmp_path / "src", {"m.py": "raise RuntimeError('must not execute')\n"})
    output = _tree(tmp_path / "out", {"m.py": "raise RuntimeError('must not execute')\n"})
    result = verify_generated_names(snapshot_source(source, [source / "m.py"]), source, output)
    assert result["names_valid"] is True
    assert result["execution_performed"] is False


def test_global_declaration_does_not_hide_generated_defect(tmp_path: Path) -> None:
    source = _tree(tmp_path / "src", {"m.py": "value = 1\ndef f():\n    return value\n"})
    output = _tree(
        tmp_path / "out", {"m.py": "value = 1\ndef f():\n    global I0\n    return I0\n"}
    )
    result = verify_generated_names(snapshot_source(source, [source / "m.py"]), source, output)
    assert [e["name"] for e in result["errors"]] == ["I0"]


def test_names_valid_on_actual_transformed_runtime_injection(tmp_path: Path) -> None:
    """Preserved runtime-injected members must pass name verification."""
    source = tmp_path / "app.py"
    source.write_text(
        "from enum import global_enum, IntEnum\n@global_enum\nclass Color(IntEnum):\n    RED = 1\nprint(RED)\n"
    )
    result = CliRunner().invoke(
        main,
        [
            str(source),
            "-o",
            str(tmp_path / "out.py"),
            "--verify-syntax",
            "--verify-names",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["name_verification"]["names_valid"]


def test_unrequested_names_leave_existing_json_contract_unchanged(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    source.write_text("value = 42\n")
    report = tmp_path / "report.json"
    result = CliRunner().invoke(
        main, [str(source), "-o", str(tmp_path / "out.py"), "--build-report", str(report), "--json"]
    )
    assert result.exit_code == 0, result.output
    assert "name_verification" not in json.loads(result.output)
    assert "name_verification" not in json.loads(report.read_text())
