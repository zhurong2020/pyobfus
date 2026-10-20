"""The 3.15 control spelling must not change older/eager lexical semantics."""

import os
import subprocess
import sys

import pytest

from pyobfus.config import ObfuscationConfig
from pyobfus.core.orchestrator import CrossFileOrchestrator


@pytest.mark.parametrize("local", [False, True])
def test_lazy_control_preserves_eager_module_proofs(tmp_path, local):
    if not local and sys.version_info >= (3, 15):
        pytest.skip("Module control enables lazy imports on 3.15")
    src, out = tmp_path / "src", tmp_path / "out"
    (src / "pkg").mkdir(parents=True)
    (src / "pkg/__init__.py").write_text("", encoding="utf-8")
    (src / "pkg/mod.py").write_text('print("LOADED")\nLIMIT = 7\n', encoding="utf-8")
    control = '__lazy_modules__ = ["pkg.mod"]\n'
    if local:
        control = 'def unused():\n    __lazy_modules__ = ["pkg.mod"]\n'
    (src / "app.py").write_text(
        control + 'import pkg.mod\nprint("START")\nprint(pkg.mod.LIMIT)\n', encoding="utf-8"
    )
    planner = CrossFileOrchestrator(ObfuscationConfig(max_workers=1))
    result = planner.obfuscate(src, out)
    assert result.success, result.errors
    env = dict(os.environ, HOME=str(tmp_path), USERPROFILE=str(tmp_path))
    for directory in (src, out):
        run = subprocess.run(
            [sys.executable, "app.py"],
            cwd=directory,
            env=env,
            text=True,
            capture_output=True,
            timeout=30,
        )
        assert run.returncode == 0, run.stderr
        assert run.stdout.splitlines() == ["LOADED", "START", "7"]
    assert planner.attribute_plans["app"].edits


@pytest.mark.parametrize(
    "source, module_control",
    [
        ('__lazy_modules__ = ["os"]', True),
        ("from policy import __lazy_modules__", True),
        ("def change():\n    global __lazy_modules__\n    __lazy_modules__ = []", True),
        ("def function():\n    __lazy_modules__ = []", False),
        ("class Container:\n    __lazy_modules__ = []", False),
        ("import os", False),
    ],
)
def test_control_belongs_to_module_and_supported_interpreter(source, module_control):
    import ast

    from pyobfus.core.import_resolution import has_lazy_module_control

    assert has_lazy_module_control(ast.parse(source)) is (
        module_control and "is_lazy" in ast.Import._fields
    )
