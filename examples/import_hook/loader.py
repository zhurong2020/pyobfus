"""Minimal stdlib custom import hook demonstrating the
obfuscate-then-hook workflow from docs/IMPORT_HOOK_COOKBOOK.md.

This is NOT a security control — it exists only to show that pyobfus output
(still ordinary Python) loads cleanly through a custom MetaPathFinder/Loader,
and that the names the hook sees are already mangled. For a real
encrypted-file workflow, substitute SOURCEdefender's `.pye` layer for this
loader (steps in the cookbook).
"""

import importlib.abc
import importlib.machinery
import sys
from pathlib import Path


class ExampleLoader(importlib.abc.Loader):
    def __init__(self, path: Path) -> None:
        self.path = path

    def create_module(self, spec):
        return None

    def exec_module(self, module) -> None:
        source = self.path.read_text(encoding="utf-8")
        exec(compile(source, str(self.path), "exec"), module.__dict__)


class ExampleFinder(importlib.abc.MetaPathFinder):
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir

    def find_spec(self, fullname, path, target=None):
        candidate = self.base_dir / f"{fullname}.py"
        if candidate.exists():
            loader = ExampleLoader(candidate)
            return importlib.machinery.ModuleSpec(
                fullname, loader, origin=str(candidate)
            )
        return None


def load_obfuscated(module_name: str, base_dir: Path):
    sys.meta_path.insert(0, ExampleFinder(base_dir))
    return __import__(module_name)


if __name__ == "__main__":
    # Point the hook at the OBFUSCATED directory produced by `pyobfus`.
    obf_dir = Path(__file__).parent / "obf"
    load_obfuscated("app", obf_dir)
    print("loaded obfuscated module via custom import hook")
