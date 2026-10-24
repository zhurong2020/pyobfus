"""Slice A of the multi-module L3 + application-key design: preflight and the
stable binding plan.

This module is the Community, crypto-free planning layer for the opt-in
``crossfile_opacity`` mode described in
``docs/CROSSFILE_OPACITY_DESIGN.md`` (§2-§4, §11). It does two things and
nothing more:

1. ``preflight`` rejects a configuration that is not inside the first-release
   envelope (valid Pro level, directory/cross-file input, TOML-only selection
   via ``opacity_config``, an application key source via ``bind_key_env``,
   ``--jobs 1``, and the 14 ``FUSION_FIELDS`` plus their dependency fields all
   at their defaults unless explicitly allowed). It also rejects a build
   interpreter the first release does not emit for (non-CPython), and module
   import-identity collisions such as ``pkg.py`` next to ``pkg/__init__.py``.

2. ``plan_module_targets`` computes, from the *original* AST, the set of stable
   top-level plain synchronous functions eligible to be selected later, plus a
   reason for every rejected function.

No ciphertext, no key material, no TOML layer resolution, and no new directory
protection happens here. The Pro adapter that consumes this plan (slices C-E)
does not exist yet; enabling the mode therefore fails after preflight rather
than silently falling back to an ordinary build.
"""

from __future__ import annotations

import ast
import hashlib
import sys
from dataclasses import dataclass, field
from typing import Any, Iterable, List, Optional, Tuple

from pyobfus.core.fusion_options import FUSION_FIELDS

# Fusion fields the new mode legitimately consumes. ``selective_opacity`` is
# allowed only as the coupled companion of ``opacity_config`` (the CLI sets it
# whenever an opacity config is supplied); on its own it means the hand-written
# ``@opacity`` marker path, which the first release does not support.
_ALLOWED_FUSION_FIELDS = frozenset({"selective_opacity", "opacity_config", "bind_key_env"})

# Dependency fields outside FUSION_FIELDS that must also stay at their defaults.
_DEPENDENCY_FIELDS: Tuple[str, ...] = ("bind_device_id", "expire_warn_days")

_FuncDef = (ast.FunctionDef, ast.AsyncFunctionDef)


# Rejection reason codes (stable strings; not secrets, safe for reports).
REASON_ASYNC = "async_function"
REASON_DECORATED = "decorated_function"
REASON_TYPE_PARAMS = "generic_type_params"
REASON_GENERATOR = "generator_function"
REASON_NESTED_DEFINITION = "nested_def_or_class"
REASON_DUPLICATE_BINDING = "duplicate_module_binding"
REASON_REASSIGNED = "rebound_at_module_level"
REASON_DELETED = "deleted_at_module_level"
REASON_SHADOWED_BY_IMPORT = "shadowed_by_import"
REASON_GLOBAL_WRITE = "global_write_elsewhere"


class CrossfileOpacityError(Exception):
    """Raised when the opt-in mode is requested outside its supported envelope.

    Carries the full list of reasons so the caller can print every problem at
    once rather than one per run.
    """

    def __init__(self, reasons: Iterable[str]) -> None:
        self.reasons: List[str] = list(reasons)
        super().__init__("; ".join(self.reasons) if self.reasons else "crossfile opacity rejected")


@dataclass(frozen=True)
class BindingId:
    """Stable identity of an original top-level function binding.

    ``source_digest`` is a sha256 over the function's original source segment
    (or its unparsed form when no segment is available), so the identity
    survives Core's rename/unparse and does not rely on AST node identity.
    """

    module: str
    name: str
    lineno: int
    source_digest: str


@dataclass(frozen=True)
class TargetRejection:
    module: str
    name: str
    lineno: int
    reason: str


@dataclass(frozen=True)
class ModulePlan:
    module: str
    import_identity: str
    selected: Tuple[BindingId, ...] = field(default_factory=tuple)
    rejected: Tuple[TargetRejection, ...] = field(default_factory=tuple)


def import_identity(module_name: str) -> str:
    """Return the runtime import path for a Core module name.

    ``pkg.a`` -> ``pkg.a``; ``pkg.__init__`` -> ``pkg``; bare ``__init__`` ->
    ``""`` (the input root as a package). This is the identity two files must
    not share.
    """
    if module_name == "__init__":
        return ""
    suffix = ".__init__"
    if module_name.endswith(suffix):
        return module_name[: -len(suffix)]
    return module_name


def preflight(
    config: Any,
    *,
    cross_file: bool,
    input_is_dir: bool,
    incremental: bool = False,
    module_names: Optional[Iterable[str]] = None,
) -> None:
    """Validate a ``crossfile_opacity`` request; raise on any problem.

    ``config`` is the merged ``ObfuscationConfig``. ``module_names`` (when
    given) is checked for import-identity collisions. Reads no license file and
    no filesystem state: the Pro level is taken from ``config.level`` exactly as
    the rest of the build does.
    """
    reasons: List[str] = []

    if getattr(config, "level", "community") != "pro":
        reasons.append(
            "crossfile_opacity requires a Pro license or active trial "
            "(effective level is not 'pro')."
        )

    if not input_is_dir:
        reasons.append("crossfile_opacity requires a directory input, not a single file.")
    if not cross_file:
        reasons.append(
            "crossfile_opacity requires cross-file mode; it cannot run with --no-cross-file."
        )

    if not getattr(config, "opacity_config", None):
        reasons.append(
            "crossfile_opacity requires TOML-only selection via --opacity-config; "
            "hand-written @opacity markers are not supported in the first release."
        )
    elif not getattr(config, "selective_opacity", False):
        # opacity_config set but the opacity pass somehow not enabled.
        reasons.append("opacity_config is set but selective_opacity is not enabled.")

    if not getattr(config, "bind_key_env", None):
        reasons.append(
            "crossfile_opacity requires an application key source via --bind-key-env NAME."
        )

    # First release is strictly serial. max_workers: None=auto, 1=sequential.
    if getattr(config, "max_workers", None) != 1:
        reasons.append("crossfile_opacity requires --jobs 1 (serial) in the first release.")

    if incremental:
        reasons.append(
            "crossfile_opacity rebuilds fully and cannot be combined with --incremental."
        )

    # Allowlist over every fusion field + its dependency fields. Anything set
    # that is not explicitly allowed is rejected rather than silently ignored.
    disallowed = [
        name
        for name in FUSION_FIELDS
        if name not in _ALLOWED_FUSION_FIELDS and getattr(config, name, None)
    ]
    disallowed += [name for name in _DEPENDENCY_FIELDS if getattr(config, name, None) is not None]
    if disallowed:
        reasons.append(
            "crossfile_opacity does not support these options in the first release: "
            + ", ".join(sorted(disallowed))
            + "."
        )

    # Interpreter envelope: the first release emits L3 artifacts for CPython
    # only (same implementation / minor / GIL mode at run time).
    if sys.implementation.name != "cpython":
        reasons.append(
            "crossfile_opacity builds are supported on CPython only in the first "
            f"release (build interpreter is {sys.implementation.name!r})."
        )

    if module_names is not None:
        reasons.extend(_identity_collisions(module_names))

    if reasons:
        raise CrossfileOpacityError(reasons)


def _identity_collisions(module_names: Iterable[str]) -> List[str]:
    """Reject files that resolve to the same runtime import path."""
    seen: dict[str, str] = {}
    collisions: List[str] = []
    for module in module_names:
        identity = import_identity(module)
        prior = seen.get(identity)
        if prior is not None and prior != module:
            collisions.append(
                f"modules {prior!r} and {module!r} share import identity "
                f"{identity or '<root package>'!r}; the first release rejects such collisions."
            )
        else:
            seen[identity] = module
    return collisions


def plan_module_targets(module_name: str, source: str, *, filename: str = "<module>") -> ModulePlan:
    """Return the stable-target plan for one module's *original* source.

    Selected bindings are module-level plain synchronous functions with no
    decorators, no generic type parameters, no ``yield`` in their own scope, no
    nested ``def`` / ``class``, and a single stable module-level binding.
    Everything else is reported with a reason. No user code runs; selection is
    a pure function of the AST.
    """
    tree = ast.parse(source, filename)

    counts = _module_level_name_counts(tree)
    reassigned = _rebound_names(tree)
    deleted = _deleted_names(tree)
    imported = _imported_names(tree)
    global_writes = _global_write_names(tree)

    selected: List[BindingId] = []
    rejected: List[TargetRejection] = []

    for stmt in tree.body:
        if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        name = stmt.name
        lineno = getattr(stmt, "lineno", 0)

        reason = _reject_reason(stmt, name, counts, reassigned, deleted, imported, global_writes)
        if reason is not None:
            rejected.append(TargetRejection(module_name, name, lineno, reason))
            continue

        selected.append(
            BindingId(
                module=module_name,
                name=name,
                lineno=lineno,
                source_digest=_binding_digest(source, stmt),
            )
        )

    return ModulePlan(
        module=module_name,
        import_identity=import_identity(module_name),
        selected=tuple(selected),
        rejected=tuple(rejected),
    )


def _reject_reason(
    stmt: "ast.FunctionDef | ast.AsyncFunctionDef",
    name: str,
    counts: dict[str, int],
    reassigned: set[str],
    deleted: set[str],
    imported: set[str],
    global_writes: set[str],
) -> Optional[str]:
    if isinstance(stmt, ast.AsyncFunctionDef):
        return REASON_ASYNC
    if stmt.decorator_list:
        return REASON_DECORATED
    if getattr(stmt, "type_params", []):
        return REASON_TYPE_PARAMS
    if _has_own_yield(stmt):
        return REASON_GENERATOR
    if _has_nested_definition(stmt):
        return REASON_NESTED_DEFINITION
    if counts.get(name, 0) > 1:
        return REASON_DUPLICATE_BINDING
    if name in reassigned:
        return REASON_REASSIGNED
    if name in deleted:
        return REASON_DELETED
    if name in imported:
        return REASON_SHADOWED_BY_IMPORT
    if name in global_writes:
        return REASON_GLOBAL_WRITE
    return None


def _has_own_yield(func: "ast.FunctionDef | ast.AsyncFunctionDef") -> bool:
    """True if the function's own scope contains yield / yield-from.

    Nested function and lambda scopes are not descended into; a generator
    expression is its own scope and does not make the enclosing function a
    generator, so neither counts here.
    """
    for child in func.body:
        for node in _walk_own_scope(child):
            if isinstance(node, (ast.Yield, ast.YieldFrom)):
                return True
    return False


def _walk_own_scope(node: ast.AST) -> Iterable[ast.AST]:
    """Yield ``node`` and descendants that share its (function) scope.

    Stops at nested scope boundaries: ``def`` / ``async def`` / ``lambda`` and
    the comprehension forms, which each introduce their own scope.
    """
    yield node
    for child in ast.iter_child_nodes(node):
        if isinstance(
            child,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.Lambda,
                ast.ListComp,
                ast.SetComp,
                ast.DictComp,
                ast.GeneratorExp,
            ),
        ):
            continue
        yield from _walk_own_scope(child)


def _has_nested_definition(func: "ast.FunctionDef | ast.AsyncFunctionDef") -> bool:
    for child in func.body:
        for node in _walk_own_scope(child):
            if node is func:
                continue
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                return True
    return False


def _module_level_name_counts(tree: ast.Module) -> dict[str, int]:
    counts: dict[str, int] = {}
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            counts[stmt.name] = counts.get(stmt.name, 0) + 1
    return counts


def _rebound_names(tree: ast.Module) -> set[str]:
    """Module-level names bound by assignment (any kind), which are not stable."""
    names: set[str] = set()
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                names.update(_assigned_names(target))
        elif isinstance(stmt, (ast.AugAssign, ast.AnnAssign)):
            if stmt.value is not None or isinstance(stmt, ast.AugAssign):
                names.update(_assigned_names(stmt.target))
    return names


def _assigned_names(target: ast.AST) -> set[str]:
    names: set[str] = set()
    if isinstance(target, ast.Name):
        names.add(target.id)
    elif isinstance(target, (ast.Tuple, ast.List)):
        for elt in target.elts:
            names.update(_assigned_names(elt))
    elif isinstance(target, ast.Starred):
        names.update(_assigned_names(target.value))
    return names


def _deleted_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for stmt in tree.body:
        if isinstance(stmt, ast.Delete):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
    return names


def _imported_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for stmt in tree.body:
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            for alias in stmt.names:
                bound = alias.asname or alias.name.split(".")[0]
                names.add(bound)
    return names


def _global_write_names(tree: ast.Module) -> set[str]:
    """Names declared ``global`` inside any function that then assigns them.

    Conservative: a ``global x`` paired with any binding of ``x`` in the same
    function marks ``x`` as written from elsewhere, so a module-level function
    of that name is not a stable target.
    """
    names: set[str] = set()
    for func in ast.walk(tree):
        if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        declared: set[str] = set()
        for node in ast.walk(func):
            if isinstance(node, ast.Global):
                declared.update(node.names)
        if not declared:
            continue
        for node in ast.walk(func):
            if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
                if node.id in declared:
                    names.add(node.id)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node is not func and node.name in declared:
                    names.add(node.name)
    return names


def _binding_digest(source: str, node: ast.AST) -> str:
    segment = ast.get_source_segment(source, node)
    if segment is None:
        segment = ast.unparse(node)
    return hashlib.sha256(segment.encode("utf-8")).hexdigest()
