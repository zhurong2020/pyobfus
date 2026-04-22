"""
Pre-flight risk checker for pyobfus.

Scans Python source for constructs that may break after obfuscation
(eval/exec, dynamic attribute access, framework reflection, __all__ exports,
name-string references). Produces a structured report with severity levels,
per-file findings, and AI-consumable hints for the next command.

Used by the `pyobfus --check` CLI flag and by the MCP server tool
`check_obfuscation_risks`.
"""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

from pyobfus.core.parser import ASTParser
from pyobfus.exceptions import ParseError
from pyobfus.utils import filter_python_files

# Severity ordering (higher = more likely to break obfuscation)
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"
SEVERITY_INFO = "info"

_SEVERITY_RANK = {SEVERITY_INFO: 0, SEVERITY_LOW: 1, SEVERITY_MEDIUM: 2, SEVERITY_HIGH: 3}


# Risk categories. Stable string IDs — used in JSON output and docs.
CAT_DYNAMIC_EXEC = "dynamic_exec"
CAT_DYNAMIC_ATTR = "dynamic_attr"
CAT_DYNAMIC_IMPORT = "dynamic_import"
CAT_INTROSPECTION = "runtime_introspection"
CAT_NAME_STRING = "name_string_reference"
CAT_ALL_EXPORT = "all_export"
CAT_FRAMEWORK = "framework_reflection"
CAT_ENTRY_POINT = "entry_point"


@dataclass
class Risk:
    """A single detected risk in one source file."""

    category: str
    severity: str
    file: str
    line: int
    col: int
    message: str
    suggestion: str
    snippet: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FrameworkHit:
    """Detected framework usage in the scanned project."""

    name: str
    evidence: str
    files: List[str] = field(default_factory=list)


@dataclass
class PreflightReport:
    """Aggregated pre-flight scan result."""

    root: str
    files_scanned: int = 0
    parse_errors: List[str] = field(default_factory=list)
    risks: List[Risk] = field(default_factory=list)
    frameworks: List[FrameworkHit] = field(default_factory=list)
    suggested_preset: Optional[str] = None
    suggested_excludes: List[str] = field(default_factory=list)
    ai_hint: str = ""

    # ---- summaries ---------------------------------------------------

    def severity_counts(self) -> Dict[str, int]:
        counts = {SEVERITY_HIGH: 0, SEVERITY_MEDIUM: 0, SEVERITY_LOW: 0, SEVERITY_INFO: 0}
        for r in self.risks:
            counts[r.severity] = counts.get(r.severity, 0) + 1
        return counts

    def category_counts(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for r in self.risks:
            out[r.category] = out.get(r.category, 0) + 1
        return out

    def exit_code(self) -> int:
        """0 = safe, 1 = high-severity risks found, 2 = parse errors."""
        if self.parse_errors:
            return 2
        if self.severity_counts().get(SEVERITY_HIGH, 0) > 0:
            return 1
        return 0

    # ---- serialization -----------------------------------------------

    def to_dict(self) -> dict:
        return {
            "version": 1,
            "root": self.root,
            "files_scanned": self.files_scanned,
            "parse_errors": self.parse_errors,
            "severity_counts": self.severity_counts(),
            "category_counts": self.category_counts(),
            "frameworks": [asdict(f) for f in self.frameworks],
            "suggested_preset": self.suggested_preset,
            "suggested_excludes": self.suggested_excludes,
            "risks": [r.to_dict() for r in self.risks],
            "ai_hint": self.ai_hint,
            "exit_code": self.exit_code(),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


# ---------------------------------------------------------------------------
# AST visitor
# ---------------------------------------------------------------------------


# Names that matter for obfuscation-breaking patterns.
_DYNAMIC_ATTR_BUILTINS = {"getattr", "setattr", "hasattr", "delattr"}
_DYNAMIC_EXEC_BUILTINS = {"eval", "exec", "compile"}
_INTROSPECTION_BUILTINS = {"vars", "locals", "globals", "dir"}
_NAME_ATTRS = {"__name__", "__qualname__", "__class__"}

# Framework detection by import prefix -> (name, preset, canonical exclude glob)
_FRAMEWORK_SIGNATURES: Dict[str, Tuple[str, str, str]] = {
    "fastapi": ("FastAPI", "fastapi", "**/routers/**"),
    "django": ("Django", "django", "**/migrations/**"),
    "flask": ("Flask", "flask", "**/views/**"),
    "pydantic": ("Pydantic", "pydantic", "**/models/**"),
    "click": ("Click CLI", "click", ""),
    "sqlalchemy": ("SQLAlchemy", "sqlalchemy", "**/models/**"),
}


class _RiskVisitor(ast.NodeVisitor):
    """Walk one AST module collecting risks for a single file."""

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.risks: List[Risk] = []
        self.imports: Set[str] = set()  # top-level module names seen
        self.has_all_export = False
        self.has_entry_point = False  # `if __name__ == "__main__"`

    # ---- imports --------------------------------------------------------

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.add(alias.name.split(".")[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self.imports.add(node.module.split(".")[0])
        self.generic_visit(node)

    # ---- __all__ --------------------------------------------------------

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                self.has_all_export = True
                self._add(
                    CAT_ALL_EXPORT,
                    SEVERITY_MEDIUM,
                    node,
                    "Module defines __all__ — public API surface.",
                    "Ensure names in __all__ match preserved patterns, "
                    "or use --preset safe for automatic preservation.",
                )
        self.generic_visit(node)

    # ---- if __name__ == "__main__" -------------------------------------

    def visit_If(self, node: ast.If) -> None:
        if _is_main_guard(node.test):
            self.has_entry_point = True
            self._add(
                CAT_ENTRY_POINT,
                SEVERITY_INFO,
                node,
                "Entry-point guard detected (__name__ == '__main__').",
                "Do not obfuscate '__name__'; pyobfus excludes dunder names by default.",
            )
        self.generic_visit(node)

    # ---- calls ----------------------------------------------------------

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func

        # Bare-name builtins: eval(...), getattr(...), __import__(...)
        if isinstance(func, ast.Name):
            self._check_named_call(func.id, node)

        # Attribute calls: importlib.import_module(...), inspect.getmembers(...)
        elif isinstance(func, ast.Attribute):
            self._check_attr_call(func, node)

        self.generic_visit(node)

    def _check_named_call(self, name: str, node: ast.Call) -> None:
        if name in _DYNAMIC_EXEC_BUILTINS:
            self._add(
                CAT_DYNAMIC_EXEC,
                SEVERITY_HIGH,
                node,
                f"Call to {name}() — dynamic code execution cannot be obfuscated safely.",
                f"Exclude this file via 'exclude_patterns' in pyobfus.yaml, "
                f"or refactor away from {name}().",
            )
        elif name in _DYNAMIC_ATTR_BUILTINS:
            if not _first_arg_is_constant_string(node):
                self._add(
                    CAT_DYNAMIC_ATTR,
                    SEVERITY_HIGH,
                    node,
                    f"{name}() with non-constant attribute name will break after obfuscation.",
                    "Use 'exclude_names' for the referenced attributes, "
                    "or rewrite to static attribute access.",
                )
            else:
                self._add(
                    CAT_DYNAMIC_ATTR,
                    SEVERITY_MEDIUM,
                    node,
                    f"{name}() with string literal — ensure the target name is preserved.",
                    "Add the literal name to 'exclude_names' in pyobfus.yaml.",
                )
        elif name == "__import__":
            self._add(
                CAT_DYNAMIC_IMPORT,
                SEVERITY_HIGH,
                node,
                "__import__() — dynamic import may reference modules that get renamed.",
                "Use static 'import' statements where possible.",
            )
        elif name in _INTROSPECTION_BUILTINS:
            self._add(
                CAT_INTROSPECTION,
                SEVERITY_MEDIUM,
                node,
                f"{name}() — runtime introspection exposes obfuscated names.",
                "Review output carefully; obfuscated names will leak through.",
            )

    def _check_attr_call(self, func: ast.Attribute, node: ast.Call) -> None:
        # importlib.import_module, importlib.__import__
        if isinstance(func.value, ast.Name) and func.value.id == "importlib":
            if func.attr in {"import_module", "__import__"}:
                self._add(
                    CAT_DYNAMIC_IMPORT,
                    SEVERITY_HIGH,
                    node,
                    f"importlib.{func.attr}() — dynamic import of modules.",
                    "Verify imported module names are in 'preserve_names' or use static imports.",
                )
        # inspect.getmembers / inspect.getattr_static etc.
        if isinstance(func.value, ast.Name) and func.value.id == "inspect":
            self._add(
                CAT_INTROSPECTION,
                SEVERITY_MEDIUM,
                node,
                f"inspect.{func.attr}() — runtime reflection.",
                "Review if the reflected names need preservation.",
            )

    # ---- name-string references ----------------------------------------

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # obj.__name__, cls.__class__.__name__ — these return a STRING that
        # may be compared to the original (pre-obfuscation) symbol name.
        if node.attr in _NAME_ATTRS:
            self._add(
                CAT_NAME_STRING,
                SEVERITY_LOW,
                node,
                f"Access to .{node.attr} — returns obfuscated string at runtime.",
                "If this string is compared to a literal, obfuscation will break it. "
                "Exclude affected names or refactor the comparison.",
            )
        self.generic_visit(node)

    # ---- helpers --------------------------------------------------------

    def _add(
        self, category: str, severity: str, node: ast.AST, message: str, suggestion: str
    ) -> None:
        self.risks.append(
            Risk(
                category=category,
                severity=severity,
                file=self.filename,
                line=getattr(node, "lineno", 0),
                col=getattr(node, "col_offset", 0),
                message=message,
                suggestion=suggestion,
            )
        )


def _is_main_guard(test: ast.expr) -> bool:
    """Detect `__name__ == "__main__"` in any argument order."""
    if not isinstance(test, ast.Compare) or len(test.ops) != 1:
        return False
    if not isinstance(test.ops[0], ast.Eq):
        return False
    left = test.left
    right = test.comparators[0]
    return _is_main_comparison_pair(left, right) or _is_main_comparison_pair(right, left)


def _is_main_comparison_pair(a: ast.expr, b: ast.expr) -> bool:
    return (
        isinstance(a, ast.Name)
        and a.id == "__name__"
        and isinstance(b, ast.Constant)
        and b.value == "__main__"
    )


def _first_arg_is_constant_string(node: ast.Call) -> bool:
    """True if call's 2nd positional arg (attribute name) is a string literal."""
    if len(node.args) < 2:
        return False
    arg = node.args[1]
    return isinstance(arg, ast.Constant) and isinstance(arg.value, str)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


class PreflightChecker:
    """Scan a file or project and produce a PreflightReport."""

    def __init__(self, exclude_patterns: Optional[Sequence[str]] = None) -> None:
        self.exclude_patterns: List[str] = list(exclude_patterns or [])

    def check_path(self, path: Path) -> PreflightReport:
        if path.is_file():
            return self._check_file(path, root=path)
        return self._check_directory(path)

    # ---- single file --------------------------------------------------

    def _check_file(self, file_path: Path, root: Path) -> PreflightReport:
        report = PreflightReport(root=str(root))
        self._scan_one(file_path, report)
        self._finalize(report)
        return report

    # ---- directory ----------------------------------------------------

    def _check_directory(self, directory: Path) -> PreflightReport:
        report = PreflightReport(root=str(directory))
        files = filter_python_files(directory, self.exclude_patterns)
        for f in files:
            self._scan_one(f, report)
        self._finalize(report)
        return report

    # ---- core scan ----------------------------------------------------

    def _scan_one(self, file_path: Path, report: PreflightReport) -> None:
        try:
            tree = ASTParser.parse_file(file_path)
        except (ParseError, FileNotFoundError, ValueError) as e:
            report.parse_errors.append(f"{file_path}: {e}")
            return

        visitor = _RiskVisitor(str(file_path))
        visitor.visit(tree)
        report.risks.extend(visitor.risks)
        report.files_scanned += 1

        # Fold framework detection into the aggregate report.
        for mod in visitor.imports:
            sig = _FRAMEWORK_SIGNATURES.get(mod.lower())
            if not sig:
                continue
            name, _preset, _exclude = sig
            existing = next((f for f in report.frameworks if f.name == name), None)
            if existing:
                if str(file_path) not in existing.files:
                    existing.files.append(str(file_path))
            else:
                report.frameworks.append(
                    FrameworkHit(name=name, evidence=f"imports {mod}", files=[str(file_path)])
                )

    # ---- finalize: suggested preset + ai_hint -------------------------

    def _finalize(self, report: PreflightReport) -> None:
        # Framework-driven preset suggestion (first detected wins, highest priority first)
        priority = ["fastapi", "django", "flask", "pydantic", "click", "sqlalchemy"]
        # Map framework display name -> preset key via _FRAMEWORK_SIGNATURES
        # ("FastAPI" -> "fastapi", "Click CLI" -> "click", ...)
        framework_keys: Dict[str, FrameworkHit] = {}
        for fw in report.frameworks:
            for key, (name, _p, _e) in _FRAMEWORK_SIGNATURES.items():
                if fw.name == name:
                    framework_keys[key] = fw
                    break

        for key in priority:
            if key in framework_keys:
                report.suggested_preset = key
                break

        # Suggested excludes based on detected frameworks
        seen_excludes: Set[str] = set()
        for key in framework_keys:
            _name, _preset, exclude_glob = _FRAMEWORK_SIGNATURES[key]
            if exclude_glob and exclude_glob not in seen_excludes:
                report.suggested_excludes.append(exclude_glob)
                seen_excludes.add(exclude_glob)

        # AI hint: the single next command the user (or an AI agent) should run.
        counts = report.severity_counts()
        if report.parse_errors:
            report.ai_hint = (
                f"{len(report.parse_errors)} file(s) failed to parse. "
                "Fix syntax errors before obfuscating."
            )
        elif counts[SEVERITY_HIGH] > 0 and report.suggested_preset:
            report.ai_hint = (
                f"High-risk patterns found. Start with: "
                f"pyobfus {report.root} -o dist/ --preset {report.suggested_preset} --dry-run"
            )
        elif counts[SEVERITY_HIGH] > 0:
            report.ai_hint = (
                "High-risk patterns found. Review risks, add 'exclude_names' / "
                "'exclude_patterns' to pyobfus.yaml, then re-run --check."
            )
        elif report.suggested_preset:
            report.ai_hint = (
                f"Low risk. Run: "
                f"pyobfus {report.root} -o dist/ --preset {report.suggested_preset}"
            )
        else:
            report.ai_hint = f"Low risk. Run: pyobfus {report.root} -o dist/ --preset balanced"


# ---------------------------------------------------------------------------
# Text formatter (human-readable output)
# ---------------------------------------------------------------------------


def format_report_text(report: PreflightReport, show_risks_limit: int = 20) -> str:
    """Render a PreflightReport as a terminal-friendly text block."""
    lines: List[str] = []
    lines.append("")
    lines.append("=" * 60)
    lines.append("  pyobfus pre-flight check")
    lines.append("=" * 60)
    lines.append(f"  Root: {report.root}")
    lines.append(f"  Files scanned: {report.files_scanned}")

    counts = report.severity_counts()
    lines.append(
        f"  Risks: high={counts[SEVERITY_HIGH]} "
        f"medium={counts[SEVERITY_MEDIUM]} "
        f"low={counts[SEVERITY_LOW]} "
        f"info={counts[SEVERITY_INFO]}"
    )

    if report.frameworks:
        fw_names = ", ".join(sorted({f.name for f in report.frameworks}))
        lines.append(f"  Frameworks detected: {fw_names}")
    if report.suggested_preset:
        lines.append(f"  Suggested preset: --preset {report.suggested_preset}")
    if report.suggested_excludes:
        lines.append(f"  Suggested excludes: {', '.join(report.suggested_excludes)}")

    if report.parse_errors:
        lines.append("")
        lines.append("  Parse errors:")
        for err in report.parse_errors[:5]:
            lines.append(f"    - {err}")
        if len(report.parse_errors) > 5:
            lines.append(f"    ... and {len(report.parse_errors) - 5} more")

    # Sort risks by severity rank desc, then file, then line
    sorted_risks = sorted(
        report.risks,
        key=lambda r: (-_SEVERITY_RANK.get(r.severity, 0), r.file, r.line),
    )

    if sorted_risks:
        lines.append("")
        lines.append("  Findings (top {}):".format(min(show_risks_limit, len(sorted_risks))))
        lines.append("  " + "-" * 58)
        for risk in sorted_risks[:show_risks_limit]:
            lines.append(
                f"  [{risk.severity.upper():6}] {risk.category} "
                f"({Path(risk.file).name}:{risk.line})"
            )
            lines.append(f"           {risk.message}")
            lines.append(f"           suggest: {risk.suggestion}")
        if len(sorted_risks) > show_risks_limit:
            lines.append(
                f"  ... and {len(sorted_risks) - show_risks_limit} more. Use --json for full list."
            )

    lines.append("")
    lines.append(f"  Next: {report.ai_hint}")
    lines.append("=" * 60)
    lines.append("")
    return "\n".join(lines)
