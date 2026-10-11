"""Environment pruning is shared by checks, plans, builds and cache signatures."""

import json
import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from pyobfus.cli import main
from pyobfus.config import ObfuscationConfig
from pyobfus.core.preflight import PreflightChecker, format_report_text
from pyobfus.utils import ENVIRONMENT_TOOL_DIRS, filter_python_files


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "project"
    for directory in [
        ".venv",
        "custom-python",
        "conda",
        *sorted(ENVIRONMENT_TOOL_DIRS),
        "nested/site-packages",
        "venv",
        "env",
        "build",
        "dist",
    ]:
        folder = root / directory
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "module.py").write_text("value = 42\n", encoding="utf-8")
    (root / ".venv" / "pyvenv.cfg").touch()
    (root / "custom-python" / "pyvenv.cfg").touch()
    (root / "conda" / "conda-meta").mkdir()
    (root / "app.py").write_text("answer = 42\n", encoding="utf-8")
    return root


def paths(root, files):
    return [f.relative_to(root).as_posix() for f in files]


SELECTED = ["app.py", "build/module.py", "dist/module.py", "env/module.py", "venv/module.py"]


def invoke(args):
    result = CliRunner().invoke(main, args)
    assert result.exit_code == 0, result.output
    return json.loads(result.stdout)


def test_prunes_before_traversal(project, monkeypatch):
    visited = []
    original = os.scandir

    def scandir(path):
        visited.append(Path(path))
        return original(path)

    monkeypatch.setattr(os, "scandir", scandir)
    skipped = []
    files = filter_python_files(project, skipped_directories=skipped)
    assert paths(project, files) == SELECTED
    assert skipped == sorted(
        [".venv", "custom-python", "conda", "nested/site-packages", *ENVIRONMENT_TOOL_DIRS]
    )
    assert all(project / name not in visited for name in skipped)
    report = PreflightChecker(report_excluded=True, exclude_patterns=["app.py"]).check_path(project)
    assert report.files_scanned == 4
    assert report.files_excluded == 1
    assert report.skipped_directories == skipped
    payload = report.to_dict()
    assert payload["skipped_directories"] == skipped[:10]
    assert payload["skipped_directories_count"] == len(skipped)
    text = format_report_text(report)
    assert "Skipped environment/tool directories:" in text
    assert "..." in text


@pytest.mark.parametrize("cross_file", [True, False])
@pytest.mark.parametrize("skip", [True, False])
def test_cli_build_check_plan_and_reproducibility(project, tmp_path, cross_file, skip):
    config = tmp_path / "settings.yaml"
    config.write_text(f"obfuscation:\n  skip_environment_dirs: {str(skip).lower()}\n")
    args = [str(project), "--config", str(config), "--json"]
    if not cross_file:
        args.append("--no-cross-file")
    expected = SELECTED if skip else paths(project, sorted(project.rglob("*.py")))
    check = invoke([*args, "--check", "--offline"])
    assert check["files_scanned"] == len(expected)
    assert bool(check["skipped_directories_count"]) == skip
    plan = invoke([*args, "--dry-run", "-o", str(tmp_path / "plan")])["plan"]
    assert [item["path"] for item in plan["files"]["selected"]] == expected
    assert not plan["files"]["excluded"]
    outputs = []
    for i in range(2):
        out = tmp_path / f"output{i}"
        result = invoke([*args, "-o", str(out), "--verbose"])
        assert result["stats"]["files_processed"] == len(expected)
        outputs.append({f.relative_to(out).as_posix(): f.read_bytes() for f in out.rglob("*.py")})
    assert set(outputs[0]) == set(expected)
    assert outputs[0] == outputs[1]


def test_incremental_ignores_environment_changes(project, tmp_path):
    args = [str(project), "-o", str(tmp_path / "out"), "--incremental", "--json"]
    assert invoke(args)["stats"]["files_processed"] == len(SELECTED)
    (project / ".venv" / "module.py").write_text("new_value = 100\n")
    (project / ".venv" / "new.py").write_text("another_value = 200\n")
    result = invoke(args)
    assert result["stats"]["files_processed"] == 0
    assert result["stats"]["files_skipped"] == len(SELECTED)


@pytest.mark.parametrize("root_name", ["site-packages", "site-packages/somepkg", ".venv", "conda"])
def test_explicit_root_and_single_file(tmp_path, root_name):
    root = tmp_path / root_name
    root.mkdir(parents=True)
    (root / "pyvenv.cfg").touch()
    (root / "conda-meta").mkdir()
    source = root / "app.py"
    source.write_text("value = 1\n")
    assert filter_python_files(root) == [source]
    assert PreflightChecker().check_path(root).files_scanned == 1
    assert (
        invoke([str(root), "-o", str(tmp_path / "out"), "--json"])["stats"]["files_processed"] == 1
    )
    assert invoke([str(source), "--check", "--offline", "--json"])["files_scanned"] == 1


def test_verbose_reports_skipped_directories(project, tmp_path):
    result = CliRunner().invoke(main, [str(project), "-o", str(tmp_path / "out"), "--verbose"])
    assert result.exit_code == 0, result.output
    assert result.output.count("Skipped environment/tool directories:") == 1
    assert ".venv" in result.output


def test_yaml_opt_out(project, tmp_path):
    config = tmp_path / "pyobfus.yaml"
    config.write_text("obfuscation:\n  skip_environment_dirs: false\n")
    cfg = ObfuscationConfig.from_file(config)
    assert cfg.skip_environment_dirs is False
    assert filter_python_files(project, skip_environment_dirs=False) == sorted(
        project.rglob("*.py")
    )


def test_init_sets_skip_and_keeps_build_output_excludes(project):
    """--init writes an explicit, editable config: it turns pruning on and
    still excludes build/dist so rebuilding into dist/ never re-obfuscates
    previous output. Only the built-in defaults avoid excluding by name."""
    from pyobfus.core.init_config import build_init_result

    result = build_init_result(project)
    assert "skip_environment_dirs: true" in result.yaml_text
    for pattern in ("**/venv/**", "**/build/**", "**/dist/**"):
        assert pattern in result.excludes
