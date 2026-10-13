"""--verify-names: static check that obfuscation leaves no global name unbound."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict
from unittest import mock

from click.testing import CliRunner

from pyobfus.cli import main
from pyobfus.core.name_verify import snapshot_source, undefined_globals, verify_generated_names


def _tree(root: Path, files: Dict[str, str]) -> Path:
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
            "message": "name 'I0' is used but never bound (NameError when reached)",
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
