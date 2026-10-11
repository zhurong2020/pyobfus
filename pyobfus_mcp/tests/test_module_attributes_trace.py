"""Restore a real trace from PR 1 module-attribute output using the MCP tool."""

import os
import subprocess
import sys

import pytest

from pyobfus.config import ObfuscationConfig
from pyobfus.core.mapping import ObfuscationMapping
from pyobfus.core.orchestrator import CrossFileOrchestrator
from pyobfus_mcp.tools import unmap_stack_trace


@pytest.mark.parametrize("style", ["alias", "dotted", "relative", "reexport"])
@pytest.mark.parametrize("failure", ["raise ValueError('trace')", "return object().MISSING"])
@pytest.mark.parametrize("workers", [1, 2])
@pytest.mark.parametrize("locals_enabled", [False, True])
def test_module_attribute_generated_trace(
    tmp_path, monkeypatch, style, workers, locals_enabled, failure
):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("PYOBFUS_MCP_PROJECT_ROOT", str(tmp_path))
    src = tmp_path / "src"
    (src / "pkg").mkdir(parents=True)
    (src / "pkg/__init__.py").write_text("")
    (src / "pkg/mod.py").write_text(f"def scale():\n    {failure}\n")
    (src / "app.py").write_text("from pkg import mod\nmod.scale()\n")
    if style == "dotted":
        (src / "app.py").write_text("import pkg.mod\npkg.mod.scale()\n")
    elif style == "relative":
        (src / "app.py").write_text("import pkg.entry\n")
        (src / "pkg/entry.py").write_text("from . import mod\nmod.scale()\n")
    elif style == "reexport":
        (src / "pkg/__init__.py").write_text("from .mod import scale\n__all__ = ['scale']\n")
        (src / "app.py").write_text("import pkg\npkg.scale()\n")
    out = tmp_path / "out"
    ob = CrossFileOrchestrator(
        ObfuscationConfig(max_workers=workers, crossfile_local_names=locals_enabled)
    )
    result = ob.obfuscate(src, out)
    assert result.success, result.errors
    mapping = ObfuscationMapping.from_global_table(ob.global_table)
    mapping.files = ob.file_line_maps
    path = tmp_path / "mapping.json"
    mapping.save(path)
    trace = subprocess.run(
        [sys.executable, str(out / "app.py")], env=dict(os.environ), capture_output=True, text=True
    )
    assert trace.returncode == 1
    restored = unmap_stack_trace(trace.stderr, str(path))
    assert restored["status"] == "success"
    assert "scale" in restored["unmapped_trace"]
    assert any(frame.get("original_line") == 2 for frame in restored["frames"])
    assert restored["unmatched_names"] == []
    assert restored["next_tool"]["tool"] is None


def test_module_attribute_scan_default_and_yaml_rollback(tmp_path, monkeypatch):
    from pyobfus_mcp.tools import check_obfuscation_risks

    monkeypatch.setenv("PYOBFUS_MCP_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg/__init__.py").write_text("")
    (tmp_path / "pkg/mod.py").write_text("LIMIT = 7\n")
    (tmp_path / "app.py").write_text("from pkg import mod\nprint(mod.LIMIT)\n")
    scanned = check_obfuscation_risks(str(tmp_path))
    assert scanned["status"] == "success"
    assert not any("attribute access through a module" in r["message"] for r in scanned["risks"])
    (tmp_path / "pyobfus.yaml").write_text("obfuscation:\n  crossfile_module_attributes: false\n")
    scanned = check_obfuscation_risks(str(tmp_path))
    assert any("attribute access through a module" in r["message"] for r in scanned["risks"])
