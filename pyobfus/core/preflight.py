"""
Pre-flight risk checker for pyobfus.

Scans Python source for constructs that may break after obfuscation
(eval/exec, dynamic attribute access, framework reflection, __all__ exports,
name-string references) and emits compatibility advisories for common delivery
combinations (import-hook / encrypted-file tooling, compiled packaging,
ML/model-serving, Python 3.14+ remote-debug hardening). Produces a structured
report with severity levels,
per-file findings, and AI-consumable hints for the next command.

Optionally (``check_dependencies=True``) also runs the dependency-
hallucination advisory (`pyobfus/core/dependency_advisory.py`), which flags
declared dependencies that don't resolve on public PyPI — a signal of
AI-hallucinated ("slopsquatting") or typo'd package names. Off by default;
see that module's docstring for the network-access tradeoffs.

Used by the `pyobfus --check` CLI flag and by the MCP server tool
`check_obfuscation_risks`.
"""

from __future__ import annotations

import ast
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from pyobfus.core.parser import ASTParser
from pyobfus.exceptions import ParseError
from pyobfus.utils import filter_python_files

# Severity ordering (higher = more likely to break obfuscation)
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"
SEVERITY_INFO = "info"

_SEVERITY_RANK = {SEVERITY_INFO: 0, SEVERITY_LOW: 1, SEVERITY_MEDIUM: 2, SEVERITY_HIGH: 3}

# Python version at which PEP 768's remote debugging interface first ships.
_REMOTE_DEBUG_MIN = (3, 14)


def _parse_python_minor(spec: Optional[str]) -> Optional[Tuple[int, int]]:
    """Parse a ``"X.Y"`` (or ``"X.Y.Z"``) version string into ``(major, minor)``.

    Returns ``None`` for an empty or unparseable value so callers can fall back
    to another signal rather than raising on user-supplied config.
    """
    if not spec:
        return None
    parts = str(spec).strip().split(".")
    try:
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
    except (ValueError, IndexError):
        return None
    return (major, minor)


# Risk categories. Stable string IDs — used in JSON output and docs.
CAT_DYNAMIC_EXEC = "dynamic_exec"
CAT_DYNAMIC_ATTR = "dynamic_attr"
CAT_DYNAMIC_IMPORT = "dynamic_import"
CAT_INTROSPECTION = "runtime_introspection"
CAT_NAME_STRING = "name_string_reference"
CAT_ALL_EXPORT = "all_export"
CAT_FRAMEWORK = "framework_reflection"
CAT_ENTRY_POINT = "entry_point"
CAT_UNSAFE_DESERIALIZATION = "unsafe_deserialization"
CAT_MODEL_ARTIFACT_LITERAL = "model_artifact_literal"
CAT_COMPAT_ADVISORY = "compatibility_advisory"
CAT_DEPENDENCY_ADVISORY = "dependency_advisory"


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
    mitigated_by: Optional[str] = None
    _target_name: Optional[str] = field(default=None, repr=False)

    def to_dict(self) -> dict:
        data = asdict(self)
        data.pop("_target_name", None)
        if data["mitigated_by"] is None:
            data.pop("mitigated_by")
        return data


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
    files_excluded: int = 0
    excluded_risks: List[Risk] = field(default_factory=list)
    effective_config: Optional[Dict[str, object]] = None
    # Internal bookkeeping only -- not part of the public to_dict() contract.
    # Several _FRAMEWORK_SIGNATURES entries can share one display name (e.g.
    # torch/tensorflow/keras/transformers/sklearn/joblib all map to "ml"), so
    # `frameworks` dedupes by display name and loses which specific module(s)
    # actually triggered detection. Track the raw signature keys here so
    # _finalize can recover the correct per-module exclude glob(s).
    _preset_signature_keys: Dict[str, Set[str]] = field(default_factory=dict, repr=False)

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
        payload = {
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
        if self.effective_config is not None:
            payload["effective_config"] = self.effective_config
            payload["files_excluded"] = self.files_excluded
            excluded_severity = {
                SEVERITY_HIGH: 0,
                SEVERITY_MEDIUM: 0,
                SEVERITY_LOW: 0,
                SEVERITY_INFO: 0,
            }
            excluded_categories: Dict[str, int] = {}
            for risk in self.excluded_risks:
                excluded_severity[risk.severity] += 1
                excluded_categories[risk.category] = excluded_categories.get(risk.category, 0) + 1
            payload["excluded_findings"] = {
                "count": len(self.excluded_risks),
                "severity_counts": excluded_severity,
                "category_counts": excluded_categories,
                "sample": [risk.to_dict() for risk in self.excluded_risks[:10]],
            }
        return payload

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
    "torch": ("ML/model-serving", "ml", "**/checkpoints/**"),
    "tensorflow": ("ML/model-serving", "ml", "**/models/**"),
    "keras": ("ML/model-serving", "ml", "**/models/**"),
    "transformers": ("ML/model-serving", "ml", "**/models/**"),
    "sklearn": ("ML/model-serving", "ml", "**/models/**"),
    "joblib": ("ML/model-serving", "ml", "**/models/**"),
}

_MODEL_ARTIFACT_SUFFIXES = (
    ".pt",
    ".pth",
    ".pkl",
    ".pickle",
    ".joblib",
    ".onnx",
    ".safetensors",
    ".h5",
    ".keras",
    ".ckpt",
    ".bin",
)

# Delivery-combo detection for compatibility advisories. These flag tooling that
# pyobfus composes with (rather than competes against) so --check can point the
# user at the right cookbook. Severity is always low/info — these never block
# obfuscation or change the CLI exit code.
_COMPAT_IMPORT_HOOK = {"sourcedefender"}
_COMPAT_COMPILED = {"nuitka", "cython"}
_COMPAT_ENCRYPTED_SUFFIXES = (".pye",)
_COMPAT_COMPILED_SUFFIXES = (".pyx",)
_COMPAT_HOOK_BASES = {"metapathfinder", "loader", "fileloader", "sourcefileloader"}


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
            top = alias.name.split(".")[0]
            self.imports.add(top)
            self._check_compat_import(top, node)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            top = node.module.split(".")[0]
            self.imports.add(top)
            self._check_compat_import(top, node)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for base in node.bases:
            base_name = ""
            if isinstance(base, ast.Name):
                base_name = base.id
            elif isinstance(base, ast.Attribute):
                base_name = base.attr
            if base_name.lower() in _COMPAT_HOOK_BASES:
                self._add(
                    CAT_COMPAT_ADVISORY,
                    SEVERITY_LOW,
                    node,
                    "Custom import hook (importlib.abc subclass) detected.",
                    "Obfuscate the source BEFORE it is loaded through a custom "
                    "import hook. See docs/IMPORT_HOOK_COOKBOOK.md.",
                )
                break
        self.generic_visit(node)

    # ---- __all__ --------------------------------------------------------

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if self._is_sys_meta_path(target):
                self._add(
                    CAT_COMPAT_ADVISORY,
                    SEVERITY_LOW,
                    node,
                    "sys.meta_path assignment detected (custom import hook).",
                    "Obfuscate the source BEFORE registering a custom import hook. "
                    "See docs/IMPORT_HOOK_COOKBOOK.md.",
                )
            elif isinstance(target, ast.Name) and target.id == "__all__":
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

        # sys.meta_path.append/insert/register(...) — custom import hook.
        if isinstance(func, ast.Attribute) and func.attr in {"append", "insert", "register"}:
            if self._is_sys_meta_path(func.value):
                self._add(
                    CAT_COMPAT_ADVISORY,
                    SEVERITY_LOW,
                    node,
                    "sys.meta_path mutation detected (custom import hook).",
                    "Obfuscate the source BEFORE registering a custom import hook. "
                    "See docs/IMPORT_HOOK_COOKBOOK.md.",
                )

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
                risk = self._add(
                    CAT_DYNAMIC_ATTR,
                    SEVERITY_MEDIUM,
                    node,
                    f"{name}() with string literal — ensure the target name is preserved.",
                    "Add the literal name to 'exclude_names' in pyobfus.yaml.",
                )
                risk._target_name = _constant_attr_name(node)
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
        elif name == "load" and self._imported("pickle"):
            self._add_unsafe_deserialization(node, "pickle.load()")
        elif name == "loads" and self._imported("pickle"):
            self._add_unsafe_deserialization(node, "pickle.loads()")
        elif name == "load" and self._imported("joblib"):
            self._add_unsafe_deserialization(node, "joblib.load()")

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
        if isinstance(func.value, ast.Name):
            owner = func.value.id
            if owner == "pickle" and func.attr in {"load", "loads"}:
                self._add_unsafe_deserialization(node, f"pickle.{func.attr}()")
            elif owner == "joblib" and func.attr == "load":
                self._add_unsafe_deserialization(node, "joblib.load()")
            elif (
                owner == "torch"
                and func.attr == "load"
                and not _has_true_keyword(node, "weights_only")
            ):
                self._add_unsafe_deserialization(node, "torch.load() without weights_only=True")
            elif owner in {"tensorflow", "keras"} and func.attr == "load_model":
                self._add_unsafe_deserialization(node, f"{owner}.load_model()")

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str):
            if _looks_like_model_artifact(node.value):
                self._add(
                    CAT_MODEL_ARTIFACT_LITERAL,
                    SEVERITY_LOW,
                    node,
                    "Model artifact path literal detected.",
                    "For Pro builds, wrap model/weight paths with vault_secrets({...}) "
                    "and enable --vault so paths route through the Runtime String Vault.",
                )
            elif _looks_like_encrypted_file(node.value):
                self._add(
                    CAT_COMPAT_ADVISORY,
                    SEVERITY_LOW,
                    node,
                    "Encrypted-file / import-hook artifact path detected (.pye).",
                    "Obfuscate the source BEFORE encrypting / packaging it as an "
                    "import-hook artifact. See docs/IMPORT_HOOK_COOKBOOK.md.",
                )
            elif _looks_like_compiled_source(node.value):
                self._add(
                    CAT_COMPAT_ADVISORY,
                    SEVERITY_LOW,
                    node,
                    "Compiled-packaging source reference detected (.pyx).",
                    "Obfuscate the pure-Python module first, then compile. "
                    "See docs/COMPILED_PACKAGING_COOKBOOK.md.",
                )
        self.generic_visit(node)

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
    ) -> Risk:
        risk = Risk(
            category=category,
            severity=severity,
            file=self.filename,
            line=getattr(node, "lineno", 0),
            col=getattr(node, "col_offset", 0),
            message=message,
            suggestion=suggestion,
        )
        self.risks.append(risk)
        return risk

    def _is_sys_meta_path(self, node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Attribute)
            and node.attr == "meta_path"
            and isinstance(node.value, ast.Name)
            and node.value.id == "sys"
        )

    def _check_compat_import(self, module: str, node: ast.AST) -> None:
        low = module.lower()
        if low in _COMPAT_IMPORT_HOOK:
            self._add(
                CAT_COMPAT_ADVISORY,
                SEVERITY_LOW,
                node,
                f"Import-hook / encrypted-file tooling detected ({module}).",
                "Obfuscate your pure-Python source with pyobfus BEFORE it passes "
                "through the import hook / encryption layer. "
                "See docs/IMPORT_HOOK_COOKBOOK.md.",
            )
        elif low in _COMPAT_COMPILED:
            self._add(
                CAT_COMPAT_ADVISORY,
                SEVERITY_LOW,
                node,
                f"Compiled packaging detected ({module}).",
                f"Obfuscate pure-Python sources first, then compile with {module}. "
                "See docs/COMPILED_PACKAGING_COOKBOOK.md.",
            )

    def _add_unsafe_deserialization(self, node: ast.Call, call_name: str) -> None:
        self._add(
            CAT_UNSAFE_DESERIALIZATION,
            SEVERITY_HIGH,
            node,
            f"{call_name} can execute code when loading untrusted model artifacts.",
            "Prefer safetensors or ONNX where possible; for torch.load use "
            "weights_only=True and validate artifact provenance before loading.",
        )

    def _imported(self, module: str) -> bool:
        return module in self.imports


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


def _constant_attr_name(node: ast.Call) -> Optional[str]:
    if not _first_arg_is_constant_string(node):
        return None
    value = node.args[1]
    assert isinstance(value, ast.Constant)
    return value.value if isinstance(value.value, str) else None


def _has_true_keyword(node: ast.Call, keyword_name: str) -> bool:
    for kw in node.keywords:
        if kw.arg == keyword_name and isinstance(kw.value, ast.Constant) and kw.value.value is True:
            return True
    return False


def _looks_like_model_artifact(value: str) -> bool:
    lowered = value.lower()
    return lowered.endswith(_MODEL_ARTIFACT_SUFFIXES) or any(
        part in lowered for part in ("/models/", "/checkpoints/", "\\models\\", "\\checkpoints\\")
    )


def _looks_like_encrypted_file(value: str) -> bool:
    return value.lower().endswith(_COMPAT_ENCRYPTED_SUFFIXES)


def _looks_like_compiled_source(value: str) -> bool:
    return value.lower().endswith(_COMPAT_COMPILED_SUFFIXES)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


class PreflightChecker:
    """Scan a file or project and produce a PreflightReport."""

    def __init__(
        self,
        exclude_patterns: Optional[Sequence[str]] = None,
        *,
        check_dependencies: bool = False,
        offline: bool = False,
        preserve_names: Optional[Iterable[str]] = None,
        safe_preset: bool = False,
        report_excluded: bool = False,
        effective_config: Optional[Dict[str, object]] = None,
        protection_intent: bool = False,
        target_python_min: Optional[str] = None,
    ) -> None:
        self.exclude_patterns: List[str] = list(exclude_patterns or [])
        # Opt-in dependency-hallucination advisory (see
        # pyobfus/core/dependency_advisory.py). Off by default so existing
        # callers/tests that construct PreflightChecker() see no behavior
        # change; the CLI and MCP tool turn it on explicitly.
        self.check_dependencies = check_dependencies
        # When check_dependencies is True: skip the PyPI network lookups
        # (an explicit opt-out, produces no findings/caveats either way).
        self.offline = offline
        self.preserve_names = set(preserve_names or [])
        self.safe_preset = safe_preset
        self.report_excluded = report_excluded
        self.effective_config = effective_config
        # PEP 768 remote-debug advisory (narrow trigger): only when the build
        # both requests anti-debug protection (protection_intent) and targets
        # Python 3.14+ (target_python_min, else the running interpreter).
        self.protection_intent = protection_intent
        self.target_python_min = target_python_min

    def check_path(self, path: Path) -> PreflightReport:
        if path.is_file():
            return self._check_file(path, root=path)
        return self._check_directory(path)

    # ---- single file --------------------------------------------------

    def _check_file(self, file_path: Path, root: Path) -> PreflightReport:
        report = PreflightReport(root=str(root))
        report.effective_config = self.effective_config
        self._scan_one(file_path, report)
        self._finalize(report)
        return report

    # ---- directory ----------------------------------------------------

    def _check_directory(self, directory: Path) -> PreflightReport:
        report = PreflightReport(root=str(directory))
        report.effective_config = self.effective_config
        files = filter_python_files(directory, self.exclude_patterns)
        for f in files:
            self._scan_one(f, report)
        if self.report_excluded and self.exclude_patterns:
            included = set(files)
            for f in filter_python_files(directory, []):
                if f not in included:
                    self._scan_excluded(f, report)
        self._finalize(report)
        return report

    def _scan_excluded(self, file_path: Path, report: PreflightReport) -> None:
        try:
            tree = ASTParser.parse_file(file_path)
        except (ParseError, FileNotFoundError, ValueError):
            return
        visitor = _RiskVisitor(str(file_path))
        visitor.visit(tree)
        report.excluded_risks.extend(visitor.risks)
        report.files_excluded += 1

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
            mod_key = mod.lower()
            sig = _FRAMEWORK_SIGNATURES.get(mod_key)
            if not sig:
                continue
            name, preset, _exclude = sig
            report._preset_signature_keys.setdefault(preset, set()).add(mod_key)
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
        for risk in report.risks:
            if (
                risk.category == CAT_DYNAMIC_ATTR
                and risk.severity == SEVERITY_MEDIUM
                and risk._target_name in self.preserve_names
            ):
                risk.severity = SEVERITY_INFO
                risk.mitigated_by = "exclude_names"
                risk.message = (
                    f"{risk._target_name!r} is preserved by the effective exclude_names config."
                )
            elif risk.category == CAT_ALL_EXPORT and self.safe_preset:
                risk.severity = SEVERITY_INFO
                risk.mitigated_by = "preset:safe"
        # Framework-driven preset suggestion (first detected wins, highest priority first)
        priority = ["fastapi", "django", "flask", "pydantic", "click", "sqlalchemy", "ml"]
        # Map framework display name -> preset key via _FRAMEWORK_SIGNATURES
        # ("FastAPI" -> "fastapi", "Click CLI" -> "click", ...). Several
        # signature entries can share one display name (all six ML libraries
        # map to "ML/model-serving"), so `frameworks` (deduped by display
        # name) only tells us the preset, not which module(s) actually
        # triggered it — read that back from report._preset_signature_keys
        # (populated per-module during scanning) instead of matching the
        # first _FRAMEWORK_SIGNATURES entry with the same display name, which
        # would always resolve to whichever entry happens to be inserted
        # first regardless of what was really imported.
        framework_keys: Dict[str, FrameworkHit] = {}
        framework_excludes: Dict[str, List[str]] = {}
        for fw in report.frameworks:
            for name, preset, _e in _FRAMEWORK_SIGNATURES.values():
                if fw.name == name:
                    framework_keys[preset] = fw
                    break
        for preset, mod_keys in report._preset_signature_keys.items():
            globs = sorted(
                {
                    _FRAMEWORK_SIGNATURES[mod_key][2]
                    for mod_key in mod_keys
                    if _FRAMEWORK_SIGNATURES[mod_key][2]
                }
            )
            if globs:
                framework_excludes[preset] = globs

        for key in priority:
            if key in framework_keys:
                report.suggested_preset = key
                break

        # Suggested excludes based on detected frameworks
        seen_excludes: Set[str] = set()
        for key in framework_keys:
            for exclude_glob in framework_excludes.get(key, []):
                if exclude_glob not in seen_excludes:
                    report.suggested_excludes.append(exclude_glob)
                    seen_excludes.add(exclude_glob)

        # ML/model-serving compatibility advisory: keep the obfuscation mapping
        # so runtime tracebacks captured from a serving process still reverse.
        if "ml" in framework_keys:
            report.risks.append(
                Risk(
                    category=CAT_COMPAT_ADVISORY,
                    severity=SEVERITY_INFO,
                    file=report.root,
                    line=0,
                    col=0,
                    message="ML/model-serving detected — keep the obfuscation mapping "
                    "for reverse stack traces.",
                    suggestion="Use --trace-marker and --save-mapping; recover traces "
                    "with `pyobfus --unmap`. See docs/MODEL_SERVING_COOKBOOK.md.",
                )
            )

        # Python 3.14 (PEP 768) remote-debug hardening advisory.
        self._maybe_add_remote_debug_advisory(report)

        # Dependency-hallucination advisory (opt-in, see dependency_advisory.py).
        # Lazy import: dependency_advisory.py imports Risk/severity constants
        # from this module, so importing it at module load time would cycle.
        if self.check_dependencies:
            from pyobfus.core.dependency_advisory import check_dependency_hallucination

            result = check_dependency_hallucination(Path(report.root), offline=self.offline)
            report.risks.extend(result.risks)

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
                f"Low risk. Run: pyobfus {report.root} -o dist/ --preset {report.suggested_preset}"
            )
        else:
            report.ai_hint = f"Low risk. Run: pyobfus {report.root} -o dist/ --preset balanced"

        if report.excluded_risks:
            report.ai_hint += (
                f" {len(report.excluded_risks)} finding(s) in excluded files are reported "
                "separately and do not affect this result."
            )

    def _targets_python_314_plus(self) -> bool:
        """Whether the build targets Python 3.14+ (where PEP 768 ships).

        Prefer the declared ``--requires-python-min`` floor; when none is
        declared, fall back to the interpreter running the scan.
        """
        declared = _parse_python_minor(self.target_python_min)
        if declared is not None:
            return declared >= _REMOTE_DEBUG_MIN
        return sys.version_info[:2] >= _REMOTE_DEBUG_MIN

    def _maybe_add_remote_debug_advisory(self, report: PreflightReport) -> None:
        """Advise disabling PEP 768 remote debugging for hardened 3.14+ deploys.

        Narrow, opt-in trigger (design decision "A"): only when the effective
        build both requests anti-debug protection *and* targets Python 3.14+.
        This is an interpreter-startup deployment control — pyobfus's runtime
        anti-debug heuristics (``sys.gettrace`` / TracerPid) cannot disable the
        remote debugging interface, and the message says so rather than
        implying the obfuscator turns it off.
        """
        if not self.protection_intent:
            return
        if not self._targets_python_314_plus():
            return
        report.risks.append(
            Risk(
                category=CAT_COMPAT_ADVISORY,
                severity=SEVERITY_INFO,
                file=report.root,
                line=0,
                col=0,
                message=(
                    "Anti-debug protection is requested and the deployment targets "
                    "Python 3.14+. Runtime anti-debug heuristics do not disable the "
                    "PEP 768 remote debugging interface, which can only be turned off "
                    "at interpreter startup."
                ),
                suggestion=(
                    "Start the protected process with `-X disable_remote_debug` or "
                    "PYTHON_DISABLE_REMOTE_DEBUG=1 (or build CPython with "
                    "--without-remote-debug). Attaching a remote debugger also "
                    "normally requires OS-level privileges. "
                    "See docs/REMOTE_DEBUG_HARDENING.md."
                ),
            )
        )


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
    if report.effective_config is not None:
        config = report.effective_config
        label = config.get("config_path") or config.get("preset") or config.get("source")
        lines.append(f"  Effective config: {label} ({config.get('source')})")
        lines.append(
            f"  Excluded files: {report.files_excluded}; "
            f"findings reported separately: {len(report.excluded_risks)}"
        )

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
