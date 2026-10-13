"""Static check that obfuscation did not leave a global name unbound.

``--verify-syntax`` proves the output parses. It cannot see the defect class
that has recurred in directory builds: a name renamed at its use but not where
it is bound (an aliased import, a decorator, a class-body reference), which
compiles fine and raises ``NameError`` only when that line runs. This module
records, per source module, the global names it uses without binding, then
reports names the generated module uses without binding that the source did
not. Nothing is imported or executed.

The baseline must be taken before output is written, so an in-place build
(``-o`` equal to the input) is still compared against its real source.
"""

from __future__ import annotations

import ast
import builtins
import symtable
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

# Names Python provides to every module or class body without a binding.
_IMPLICIT = set(dir(builtins)) | {
    "__file__",
    "__name__",
    "__doc__",
    "__spec__",
    "__loader__",
    "__package__",
    "__builtins__",
    "__path__",
    "__cached__",
    "__annotations__",
    "__dict__",
    "__module__",
    "__qualname__",
    "__class__",
    "__debug__",
}


def undefined_globals(source: str, label: str = "<module>") -> Optional[Set[str]]:
    """Return global names this module uses but never binds.

    ``None`` means the module cannot be judged statically: it does not parse,
    or it uses ``from x import *``, which binds names nobody can list.
    """
    try:
        tree = ast.parse(source)
        top = symtable.symtable(source, label, "exec")
    except (SyntaxError, ValueError):
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and any(alias.name == "*" for alias in node.names):
            return None

    bound = {
        symbol.get_name()
        for symbol in top.get_symbols()
        if symbol.is_assigned() or symbol.is_imported() or symbol.is_namespace()
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Global):
            bound.update(node.names)

    used: Set[str] = set()

    def visit(table: symtable.SymbolTable, is_module: bool) -> None:
        for symbol in table.get_symbols():
            if not symbol.is_referenced():
                continue
            if is_module:
                if not (symbol.is_assigned() or symbol.is_imported() or symbol.is_namespace()):
                    used.add(symbol.get_name())
            elif symbol.is_global():
                used.add(symbol.get_name())
        for child in table.get_children():
            visit(child, False)

    visit(top, True)
    return {name for name in used if name not in bound and name not in _IMPLICIT}


def snapshot_source(input_path: Path, files: Iterable[Path]) -> Dict[str, Optional[Set[str]]]:
    """Record undefined globals of each source file, keyed by output-relative path."""
    root = input_path.parent if input_path.is_file() else input_path
    baseline: Dict[str, Optional[Set[str]]] = {}
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        baseline[_label(path, root)] = undefined_globals(text, str(path))
    return baseline


def verify_generated_names(
    baseline: Dict[str, Optional[Set[str]]], input_path: Path, output_path: Path
) -> Dict[str, Any]:
    """Compare generated modules with the source baseline taken before writing."""
    if input_path.is_file():
        targets = [output_path]
        root = output_path.parent
        keys = {output_path: next(iter(baseline), output_path.name)}
    else:
        targets = sorted(output_path.rglob("*.py")) if output_path.exists() else []
        root = output_path
        keys = {target: _label(target, root) for target in targets}

    errors: List[Dict[str, Any]] = []
    checked = 0
    skipped = 0
    for target in targets:
        key = keys[target]
        if key not in baseline:
            continue  # not a module pyobfus generated from the source tree
        before = baseline[key]
        try:
            text = target.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        after = undefined_globals(text, str(target))
        if before is None or after is None:
            skipped += 1
            continue
        checked += 1
        for name in sorted(after - before):
            errors.append(
                {
                    "path": key,
                    "line": _first_use(text, name),
                    "name": name,
                    "message": f"name {name!r} is used but never bound (NameError when reached)",
                }
            )

    errors.sort(key=lambda e: (e["path"], e["line"] or 0, e["name"]))
    return {
        "mode": "names",
        "names_valid": not errors,
        "files_checked": checked,
        "files_skipped": skipped,
        "errors": errors,
        "execution_performed": False,
    }


def _first_use(text: str, name: str) -> Optional[int]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    lines = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id == name and isinstance(node.ctx, ast.Load)
    ]
    return min(lines) if lines else None


def _label(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name
