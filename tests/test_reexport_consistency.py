"""Packages that re-export through ``__init__.py`` must stay importable.

The bug this pins: a module that does ``from .core import run`` and lists
``run`` in ``__all__`` was given a *fresh* obfuscated name for ``run``, while
the rewritten import statement used the name from the defining module. The
generated package therefore advertised an identifier that existed nowhere, so
``from pkg import *`` and any consumer reading ``__all__`` broke. Separately,
a package's exports were registered under its ``__init__`` module name, so a
consumer's ``from pkg import run`` resolved to nothing and was left untouched
while its call sites were renamed.

These tests execute the generated code rather than inspecting it, because the
failure mode was output that looked plausible and did not run.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from pyobfus.core.global_table import GlobalSymbolTable


def _build(root: Path, src: Path, out: Path, extra_args: Optional[List[str]] = None) -> None:
    home = root / "home"
    home.mkdir(exist_ok=True)
    env = dict(os.environ)
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)

    command = [sys.executable, "-m", "pyobfus", str(src), "-o", str(out)]
    command.extend(extra_args or [])
    proc = subprocess.run(
        command, capture_output=True, text=True, timeout=180, cwd=str(root), env=env
    )
    assert proc.returncode == 0, f"build failed: {proc.stderr}"


def _run(script: str, cwd: Path) -> str:
    proc = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, timeout=60, cwd=str(cwd)
    )
    assert proc.returncode == 0, f"generated code failed to run: {proc.stderr}"
    return proc.stdout.strip()


class TestAbsoluteReExport:
    def test_all_entries_exist_in_the_generated_package(self, tmp_path):
        src = tmp_path / "src"
        (src / "lib").mkdir(parents=True)
        (src / "lib" / "__init__.py").write_text(
            'from lib.math_utils import add\n__all__ = ["add"]\n', encoding="utf-8"
        )
        (src / "lib" / "math_utils.py").write_text(
            "def add(a, b):\n    return a + b\n", encoding="utf-8"
        )
        out = tmp_path / "out"

        _build(tmp_path, src, out)

        reported = _run(
            "import lib;"
            "print(all(hasattr(lib, name) for name in lib.__all__), len(lib.__all__))",
            out,
        )
        assert reported == "True 1"

    def test_star_import_reaches_the_re_exported_callable(self, tmp_path):
        src = tmp_path / "src"
        (src / "lib").mkdir(parents=True)
        (src / "lib" / "__init__.py").write_text(
            'from lib.math_utils import add\n__all__ = ["add"]\n', encoding="utf-8"
        )
        (src / "lib" / "math_utils.py").write_text(
            "def add(a, b):\n    return a + b\n", encoding="utf-8"
        )
        out = tmp_path / "out"

        _build(tmp_path, src, out)

        reported = _run(
            "import lib;"
            "names = {n: getattr(lib, n) for n in lib.__all__};"
            "print(next(iter(names.values()))(2, 3))",
            out,
        )
        assert reported == "5"


class TestConsumerImportingFromThePackage:
    def test_package_consumer_still_runs(self, tmp_path):
        """`from pkg import thing` in another module must resolve and run."""
        src = tmp_path / "src"
        (src / "pkg").mkdir(parents=True)
        (src / "pkg" / "__init__.py").write_text(
            'from pkg.core import run_pipeline\n__all__ = ["run_pipeline"]\n', encoding="utf-8"
        )
        (src / "pkg" / "core.py").write_text(
            "def run_pipeline(values, factor=2):\n"
            "    scaled = [value * factor for value in values]\n"
            "    return sum(scaled)\n",
            encoding="utf-8",
        )
        # Driven through __main__ rather than by calling a named function:
        # top-level names in the consumer are obfuscated too, which is correct,
        # so the test must not depend on one surviving.
        (src / "main.py").write_text(
            "from pkg import run_pipeline\n"
            "\n"
            "if __name__ == '__main__':\n"
            "    print(run_pipeline([1, 2, 3]))\n",
            encoding="utf-8",
        )
        out = tmp_path / "out"

        _build(tmp_path, src, out)

        proc = subprocess.run(
            [sys.executable, "main.py"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(out),
        )
        assert proc.returncode == 0, f"generated code failed to run: {proc.stderr}"
        assert proc.stdout.strip() == "12"


class TestRelativeReExport:
    def test_relative_re_export_resolves_to_the_defining_module(self, tmp_path):
        src = tmp_path / "src"
        (src / "pkg").mkdir(parents=True)
        (src / "pkg" / "__init__.py").write_text(
            'from .core import compute\n__all__ = ["compute"]\n', encoding="utf-8"
        )
        (src / "pkg" / "core.py").write_text(
            "def compute(value):\n    doubled = value * 2\n    return doubled\n",
            encoding="utf-8",
        )
        out = tmp_path / "out"

        _build(tmp_path, src, out)

        reported = _run(
            "import pkg;"
            "print(all(hasattr(pkg, n) for n in pkg.__all__), getattr(pkg, pkg.__all__[0])(21))",
            out,
        )
        assert reported == "True 42"


class TestChainedReExport:
    def test_a_chain_of_re_exports_resolves_to_one_name(self, tmp_path):
        """pkg -> pkg.api -> pkg.core must end at the definition's name."""
        src = tmp_path / "src"
        (src / "pkg").mkdir(parents=True)
        (src / "pkg" / "__init__.py").write_text(
            'from pkg.api import handle\n__all__ = ["handle"]\n', encoding="utf-8"
        )
        (src / "pkg" / "api.py").write_text(
            'from pkg.core import handle\n__all__ = ["handle"]\n', encoding="utf-8"
        )
        (src / "pkg" / "core.py").write_text(
            "def handle(value):\n    result = value + 1\n    return result\n",
            encoding="utf-8",
        )
        out = tmp_path / "out"
        mapping = tmp_path / "mapping.json"

        _build(tmp_path, src, out, ["--save-mapping", str(mapping)])

        reported = _run(
            "import pkg, pkg.api;"
            "print(pkg.__all__ == pkg.api.__all__, getattr(pkg, pkg.__all__[0])(41))",
            out,
        )
        assert reported == "True 42"


class TestExternalReExport:
    def test_a_name_from_another_package_is_left_alone(self, tmp_path):
        """Renaming it would break the import it came from, so it must not be."""
        src = tmp_path / "src"
        (src / "lib").mkdir(parents=True)
        (src / "lib" / "__init__.py").write_text(
            'from json import dumps\n__all__ = ["dumps"]\n', encoding="utf-8"
        )
        (src / "lib" / "local.py").write_text(
            "def helper(value):\n    doubled = value * 2\n    return doubled\n",
            encoding="utf-8",
        )
        out = tmp_path / "out"

        _build(tmp_path, src, out)

        generated = (out / "lib" / "__init__.py").read_text(encoding="utf-8")
        assert "from json import dumps" in generated
        assert "'dumps'" in generated or '"dumps"' in generated

        reported = _run("import lib; print(lib.dumps({'a': 1}))", out)
        assert reported == '{"a": 1}'


class TestSymbolTableSupport:
    def test_reexport_registration_is_not_treated_as_a_collision(self):
        table = GlobalSymbolTable()
        table.register_export(module="pkg.core", original_name="run", obfuscated_name="I0")

        table.register_reexport(module="pkg.__init__", original_name="run", obfuscated_name="I0")

        assert table.get_obfuscated_import("pkg.__init__", "run") == "I0"
        # The definition keeps ownership in the reverse mapping.
        assert table.get_reverse_mapping("I0") == ("pkg.core", "run")

    def test_package_alias_resolves_to_the_init_module(self):
        table = GlobalSymbolTable()
        table.register_export(module="pkg.__init__", original_name="run", obfuscated_name="I0")
        table.register_module_alias(alias="pkg", target="pkg.__init__")

        assert table.get_obfuscated_import("pkg", "run") == "I0"
        assert table.get_module_exports("pkg") == {"run": "I0"}

    def test_alias_never_shadows_a_real_module(self):
        table = GlobalSymbolTable()
        table.register_export(module="pkg", original_name="here", obfuscated_name="I0")
        table.register_export(module="pkg.__init__", original_name="there", obfuscated_name="I1")
        table.register_module_alias(alias="pkg", target="pkg.__init__")

        assert table.get_obfuscated_import("pkg", "here") == "I0"
