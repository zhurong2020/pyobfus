"""Directory builds must keep PEP 695 type parameters on renamed definitions.

Up to and including 0.6.1, the cross-file exported-name pass rebuilt every
renamed top-level ``def`` / ``async def`` / ``class`` from a fixed list of
fields. ``type_params`` was not on the list, so ``def first[T](...) -> T``
came out as ``def I1(...) -> T`` and the module failed with NameError on
import. Single-file builds were not affected.

Rebuilding also dropped the statement's source-line marker, so a traceback
pointing at the ``def`` line of a renamed function was reported as generated.
"""

import ast
import subprocess
import sys

import pytest
from click.testing import CliRunner

from pyobfus.cli import main
from pyobfus.core.mapping import ObfuscationMapping

pytestmark = pytest.mark.skipif(sys.version_info < (3, 12), reason="PEP 695 syntax")

GENERICS = (
    "def first_of[T](items: list[T]) -> T:\n"
    "    return items[0]\n"
    "\n"
    "\n"
    "class Box[T]:\n"
    "    def __init__(self, item: T) -> None:\n"
    "        self.item = item\n"
    "\n"
    "    def get(self) -> T:\n"
    "        return self.item\n"
    "\n"
    "\n"
    "async def lookup[K, V](mapping: dict[K, V], key: K) -> V:\n"
    "    return mapping[key]\n"
    "\n"
    "\n"
    "type Pair[T] = tuple[T, T]\n"
)

APP = (
    "import asyncio\n"
    "from generics import Box, first_of, lookup\n"
    "print(first_of([1, 2]), Box(3).get(), asyncio.run(lookup({'a': 4}, 'a')))\n"
)


def _run(cwd):
    return subprocess.run(
        [sys.executable, "app.py"], cwd=cwd, capture_output=True, text=True, timeout=60
    )


def test_directory_build_keeps_type_parameters(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "generics.py").write_text(GENERICS, encoding="utf-8")
    (src / "app.py").write_text(APP, encoding="utf-8")
    expected = _run(src)
    assert expected.returncode == 0, expected.stderr

    out = tmp_path / "out"
    mapping_path = tmp_path / "mapping.json"
    result = CliRunner().invoke(
        main, [str(src), "-o", str(out), "--save-mapping", str(mapping_path)]
    )
    assert result.exit_code == 0, result.output

    built = (out / "generics.py").read_text(encoding="utf-8")
    for original in ("first_of", "Box", "lookup"):
        assert original not in built, original
    tree = ast.parse(built)
    definitions = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    assert len(definitions) == 3
    assert all(node.type_params for node in definitions)

    actual = _run(out)
    assert actual.returncode == 0, actual.stderr
    assert actual.stdout == expected.stdout

    # Each definition line maps back to its source statement, not "generated".
    mapping = ObfuscationMapping.load(mapping_path)
    located = [mapping.resolve_location("out/generics.py", node.lineno) for node in definitions]
    assert [(loc.status, loc.line) for loc in located if loc] == [
        ("mapped", 1),
        ("mapped", 5),
        ("mapped", 13),
    ]
