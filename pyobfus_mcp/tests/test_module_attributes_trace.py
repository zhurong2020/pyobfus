"""Restore a real trace from PR 1 module-attribute output using the MCP tool."""

import os
import subprocess
import sys

from pyobfus.config import ObfuscationConfig
from pyobfus.core.mapping import ObfuscationMapping
from pyobfus.core.orchestrator import CrossFileOrchestrator
from pyobfus_mcp.tools import unmap_stack_trace


def test_module_attribute_generated_trace(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("PYOBFUS_MCP_PROJECT_ROOT", str(tmp_path))
    src = tmp_path / "src"
    (src / "pkg").mkdir(parents=True)
    (src / "pkg/__init__.py").write_text("")
    (src / "pkg/mod.py").write_text("def scale():\n    raise ValueError('trace')\n")
    (src / "app.py").write_text("from pkg import mod\nmod.scale()\n")
    out = tmp_path / "out"
    ob = CrossFileOrchestrator(ObfuscationConfig(crossfile_module_attributes=True, max_workers=2))
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
