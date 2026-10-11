"""Statement provenance and final-output alignment (Community)."""

import ast
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional


def statements(tree: ast.AST) -> Iterator[ast.stmt]:
    """Depth-first preorder, including statements inside compound statements."""
    if isinstance(tree, ast.stmt):
        yield tree
    for child in ast.iter_child_nodes(tree):
        yield from statements(child)


def mark_source_statements(tree: ast.AST) -> None:
    """Mark original statements; newly constructed nodes remain synthetic."""
    for node in statements(tree):
        node._pyobfus_src_line = node.lineno  # type: ignore[attr-defined]


@dataclass(frozen=True)
class Location:
    """Resolved source location, or a generated output line."""

    source: str
    line: Optional[int]
    module: str
    status: str


def compress_lines(values: List[Optional[int]]) -> List[List[Optional[int]]]:
    runs: List[List[Optional[int]]] = []
    for line, value in enumerate(values, 1):
        if not runs or runs[-1][1] != value:
            runs.append([line, value])
    return runs


def build_line_map(
    tree: ast.AST, text: str, source: str, module: str, reason: Optional[str] = None
) -> Dict[str, Any]:
    """Align statements against the actual output; fail closed on mismatch."""
    record: Dict[str, Any] = {
        "source": source,
        "module": module,
        "line_count": len(text.splitlines()),
        "lines": None,
    }
    if reason is None:
        try:
            before = list(statements(tree))
            after = list(statements(ast.parse(text)))
            if len(before) != len(after) or any(
                type(a) is not type(b) for a, b in zip(before, after)
            ):
                reason = "statement alignment mismatch"
            else:
                values: List[Optional[int]] = [None] * record["line_count"]
                for old, new in zip(before, after):
                    start = min(
                        [new.lineno] + [d.lineno for d in getattr(new, "decorator_list", [])]
                    )
                    end = new.end_lineno or new.lineno
                    values[start - 1 : end] = [getattr(old, "_pyobfus_src_line", None)] * (
                        end - start + 1
                    )
                record["lines"] = compress_lines(values)
        except (SyntaxError, ValueError, TypeError) as exc:
            reason = f"final text alignment failed: {type(exc).__name__}"
    if reason:
        record["reason"] = reason
    return record


def shift_line_map(record: Dict[str, Any], after_line: int, count: int) -> None:
    """Account for a generated marker inserted after a prologue."""
    runs = record.get("lines")
    if runs is not None:
        values: List[Optional[int]] = []
        for idx, (start, source) in enumerate(runs):
            end = runs[idx + 1][0] - 1 if idx + 1 < len(runs) else record["line_count"]
            values.extend([source] * (end - start + 1))
        values[after_line:after_line] = [None] * count
        record["lines"] = compress_lines(values)
    record["line_count"] += count
