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
import tokenize
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, TypedDict

# Module globals supplied by Python. Class-only names are handled per scope.
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
    "__debug__",
}


class SourceAnalysis(TypedDict):
    undefined_globals: Optional[Set[str]]
    skip_reason: Optional[str]


def undefined_globals(source: str, label: str = "<module>") -> Optional[Set[str]]:
    """Return global names this module uses but never binds.

    ``None`` means the module cannot be judged statically: it does not parse,
    or it uses ``from x import *``, which binds names nobody can list.
    """
    return _analyze_source(source, label)[0]


def _analyze_source(source: str, label: str) -> Tuple[Optional[Set[str]], Optional[str]]:
    try:
        tree = ast.parse(source)
        top = symtable.symtable(source, label, "exec")
    except (SyntaxError, ValueError):
        return None, "syntax_error"
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and any(alias.name == "*" for alias in node.names):
            return None, "star_import"

    bound = {
        symbol.get_name()
        for symbol in top.get_symbols()
        if symbol.is_assigned() or symbol.is_imported() or symbol.is_namespace()
    }
    used: Set[str] = set()

    def visit(table: symtable.SymbolTable, is_module: bool) -> None:
        for symbol in table.get_symbols():
            # A global declaration alone is not a binding. Actual global
            # assignments/imports in child scopes can populate the module.
            if symbol.is_global() and (
                symbol.is_assigned() or symbol.is_imported() or symbol.is_namespace()
            ):
                bound.add(symbol.get_name())
            if not symbol.is_referenced():
                continue
            if table.get_type() == "class" and symbol.get_name() in {"__module__", "__qualname__"}:
                continue
            if is_module:
                if not (symbol.is_assigned() or symbol.is_imported() or symbol.is_namespace()):
                    used.add(symbol.get_name())
            elif symbol.is_global():
                used.add(symbol.get_name())
        for child in table.get_children():
            visit(child, False)

    visit(top, True)
    return {name for name in used if name not in bound and name not in _IMPLICIT}, None


def snapshot_source(input_path: Path, files: Iterable[Path]) -> Dict[str, SourceAnalysis]:
    """Record undefined globals of each source file, keyed by output-relative path."""
    root = input_path.parent if input_path.is_file() else input_path
    baseline: Dict[str, SourceAnalysis] = {}
    for path in files:
        key = _label(path, root)
        try:
            with tokenize.open(path) as stream:
                text = stream.read()
        except (OSError, UnicodeError, SyntaxError):
            baseline[key] = {"undefined_globals": None, "skip_reason": "read_error"}
            continue
        names, reason = _analyze_source(text, key)
        baseline[key] = {"undefined_globals": names, "skip_reason": reason}
    return baseline


def verify_generated_names(
    baseline: Dict[str, SourceAnalysis], input_path: Path, output_path: Path
) -> Dict[str, Any]:
    """Compare generated modules with the source baseline taken before writing."""
    if input_path.is_file():
        targets = {key: output_path for key in baseline}
    else:
        targets = {key: output_path / key for key in baseline}

    errors: List[Dict[str, Any]] = []
    checked = 0
    skipped: List[Dict[str, str]] = []
    for key, target in sorted(targets.items()):
        entry = baseline[key]
        before = entry["undefined_globals"]
        if entry["skip_reason"] == "read_error":
            errors.append(_file_error(key, "Cannot read source for name verification."))
            continue
        try:
            with tokenize.open(target) as stream:
                text = stream.read()
        except (OSError, UnicodeError, SyntaxError):
            errors.append(_file_error(key, "Cannot read generated output for name verification."))
            continue
        after, after_reason = _analyze_source(text, key)
        if after_reason == "syntax_error":
            errors.append(_file_error(key, "Cannot parse generated output for name verification."))
            continue
        if before is None:
            skipped.append({"path": key, "reason": "source_" + str(entry["skip_reason"])})
            continue
        if after is None:
            skipped.append({"path": key, "reason": "output_" + str(after_reason)})
            continue
        checked += 1
        for name in sorted(after - before):
            errors.append(
                {
                    "path": key,
                    "line": _first_use(text, name),
                    "name": name,
                    "message": f"name {name!r} has no static global binding (possible NameError)",
                }
            )

    if not baseline:
        errors.append(
            _file_error(output_path.name, "No source modules available for name verification.")
        )
    errors.sort(key=lambda e: (e["path"], e["line"] or 0, e["name"] or ""))
    return {
        "mode": "names",
        "names_valid": not errors,
        "files_checked": checked,
        "files_skipped": len(skipped),
        "files_expected": len(baseline),
        "coverage_complete": not skipped and checked == len(baseline) and bool(baseline),
        "skipped": skipped,
        "errors": errors,
        "execution_performed": False,
    }


def _file_error(path: str, message: str) -> Dict[str, Any]:
    return {"path": path, "line": None, "name": None, "message": message}


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
