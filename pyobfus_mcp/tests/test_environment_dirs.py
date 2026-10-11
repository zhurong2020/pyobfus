"""Real MCP scan/build entry points share environment directory discovery."""

from pathlib import Path

from pyobfus_mcp.tools import check_obfuscation_risks, protect_project


def test_mcp_scan_and_build_prune_environments(tmp_path, monkeypatch):
    # The build launches the real CLI; bind subprocess state lookups as well.
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    root = tmp_path / "project"
    root.mkdir()
    (root / "app.py").write_text("print(42)\n")
    for directory in [
        ".venv",
        "conda",
        "node_modules",
        ".git",
        "__pycache__",
        "nested/site-packages",
    ]:
        child = root / directory
        child.mkdir(parents=True)
        # Malformed syntax would fail preflight/build if discovery included it.
        (child / "vendor.py").write_text("def broken(:\n")
    (root / ".venv" / "pyvenv.cfg").touch()
    (root / "conda" / "conda-meta").mkdir()
    scan = check_obfuscation_risks(str(root))
    assert scan["status"] != "error", scan
    assert scan["files_scanned"] == 1
    assert scan["skipped_directories_count"] == 6
    out = tmp_path / "out"
    result = protect_project(str(root), str(out), preset="balanced")
    assert result["status"] != "error", result
    assert list(out.rglob("*.py")) == [out / "app.py"]


def test_mcp_project_config_can_restore_discovery(tmp_path):
    root = tmp_path / "project"
    child = root / ".venv"
    child.mkdir(parents=True)
    (child / "pyvenv.cfg").touch()
    (root / "app.py").write_text("value = 1\n")
    (child / "vendor.py").write_text("value = 2\n")
    (root / "pyobfus.yaml").write_text("obfuscation:\n  skip_environment_dirs: false\n")
    scan = check_obfuscation_risks(str(root))
    assert scan["files_scanned"] == 2
    assert scan["skipped_directories_count"] == 0
    assert check_obfuscation_risks(str(root), use_project_config=False)["files_scanned"] == 1


def test_auxiliary_literal_scan_obeys_environment_setting(tmp_path):
    import re

    from pyobfus.config import ObfuscationConfig
    from pyobfus_mcp.tools import _count_pattern_matches

    environment = tmp_path / ".venv"
    environment.mkdir()
    (environment / "pyvenv.cfg").touch()
    (environment / "vendor.py").write_text("marker = 42\n")
    patterns = (re.compile("marker"),)
    assert _count_pattern_matches(tmp_path, patterns) == 0
    config = ObfuscationConfig(skip_environment_dirs=False)
    assert _count_pattern_matches(tmp_path, patterns, config=config) == 1
