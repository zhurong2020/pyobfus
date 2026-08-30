"""Syntax-only verification for generated Python source files."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


def verify_generated_syntax(input_path: Path, output_path: Path) -> Dict[str, Any]:
    """Compile generated sources in memory without importing or executing them."""
    if input_path.is_file():
        targets = [output_path]
        root = output_path.parent
    else:
        targets = sorted(output_path.rglob("*.py")) if output_path.exists() else []
        root = output_path

    errors: List[Dict[str, Any]] = []
    checked = 0
    for target in targets:
        try:
            source = target.read_text(encoding="utf-8")
            label = _relative_label(target, root)
            compile(source, label, "exec", dont_inherit=True)
            checked += 1
        except (OSError, UnicodeError) as exc:
            errors.append(_error_record(target, root, None, None, str(exc)))
        except SyntaxError as exc:
            errors.append(_error_record(target, root, exc.lineno, exc.offset, exc.msg))

    if not targets:
        errors.append(
            _error_record(
                output_path,
                output_path.parent,
                None,
                None,
                "No generated Python files found to verify.",
            )
        )

    return {
        "mode": "syntax-only",
        "syntax_valid": not errors,
        "files_checked": checked,
        "errors": errors,
        "execution_performed": False,
        "pycache_written": False,
    }


def _error_record(path: Path, root: Path, line: Any, offset: Any, message: str) -> Dict[str, Any]:
    return {
        "path": _relative_label(path, root),
        "line": line,
        "offset": offset,
        "message": message,
    }


def _relative_label(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name
