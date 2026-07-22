"""Build-pass AST transformer for P2-1 Selective Opacity.

Walks a module's AST top level, resolves each function's protection layer
via :class:`pyobfus_pro.opacity.patterns.Resolver`, and dispatches per
layer:

- **L0 transparent**: strip ``@opacity(...)`` decorator, leave body alone.
- **L1 ai_readable**: strip ``@opacity(...)`` decorator. Recorded in the
  returned assignment map so the build orchestrator can apply Core's
  rename-locals pass downstream.
- **L2 obfuscated**: strip ``@opacity(...)`` decorator. Recorded in the
  returned assignment map so Core's full pipeline applies downstream.
- **L3 encrypted**: compile the function's CodeType with ``dont_inherit=True``
  (P2-9 future-flag discipline), AES-256-GCM encrypt via
  :func:`pyobfus_pro.runtime.opacity._encrypt_code`, emit
  ``_CIPHER_<funcname> = b"..."`` as a module-level constant, replace the
  function body with a ``pass`` stub (preserving the docstring if any),
  and rewrite the decorator list so ``@opacity(...)`` becomes
  ``@_l3_dispatch(_CIPHER_<funcname>, _LAYER_KEY)``. A single per-build
  random ``_LAYER_KEY`` constant is emitted once at module top.

The transformer is a pure function: ``(source, config, layer_key?, module_qualname?)``
returns ``(transformed_source, layer_assignments)``. The ``layer_assignments``
map (``qualname -> Layer``) is the published interface for the build
orchestrator; it lets downstream Core configure per-symbol passes
(L1 / L2) without re-resolving.

W3-B v1 limitations (lifted in W3-W4 / P2-9.1):

- Module-level functions only. Class methods / nested defs raise
  :class:`OpacityBuildError` (same scope as ``seal``).
- L3 functions must have ``@opacity(...)`` as the only decorator. Mixed
  decorators on L3 functions raise :class:`OpacityBuildError` because
  decorator-order interaction with ``_l3_dispatch``'s ``__code__`` patching
  is non-trivial; the safe combinations are catalogued in P2-9.1.
- ``@opacity`` argument must be a string literal or a ``Layer.<MEMBER>``
  attribute. Other expressions (variables, calls) raise
  :class:`OpacityBuildError`.

Patent-gated. See ``../runtime/opacity.py`` for the runtime side and
``docs/P2-1_DESIGN.md`` + ``PATENT_NOTES.md`` for the inventive-step
framing.
"""

from __future__ import annotations

import ast
import secrets
import types
from collections.abc import Iterable

from pyobfus_pro.opacity.config import OpacityConfig
from pyobfus_pro.opacity.layers import LAYER_SPECS, Layer
from pyobfus_pro.opacity.patterns import Resolver
from pyobfus_pro.runtime.opacity import _encrypt_code

_RUNTIME_MODULE = "pyobfus_pro.runtime"
_RUNTIME_DISPATCH = "_l3_dispatch"
_LAYER_KEY_NAME = "_LAYER_KEY"
_CIPHER_PREFIX = "_CIPHER_"
_SOURCE_DECORATOR_NAME = "opacity"
_LAYER_KEY_SIZE = 32  # AES-256


class OpacityBuildError(ValueError):
    """Raised when the @opacity build pass cannot transform the source.

    Reasons include: unsupported location (class method / nested def),
    L3 function with extra decorators (decorator-order interaction with
    ``_l3_dispatch``'s ``__code__`` patching), unparseable
    ``@opacity(...)`` argument, missing function code object after compile.
    """


def transform_module(
    source_code: str,
    config: OpacityConfig | None = None,
    *,
    module_qualname: str = "",
    layer_key: bytes | None = None,
    filename: str = "<opacity-pass>",
) -> tuple[str, dict[str, Layer]]:
    """Apply the P2-1 Selective Opacity build pass to a module source.

    Args:
        source_code: Python source text.
        config: Parsed ``opacity.toml`` for config-channel layer assignment.
            ``None`` means "use built-in defaults" (default layer is OBFUSCATED,
            no rules).
        module_qualname: Dotted path used as the prefix when constructing each
            symbol's qualname for the resolver (``f"{module_qualname}.{name}"``).
            Empty string means "use bare function name as qualname" -- useful
            for tests but production callers should pass the real module path
            so glob patterns like ``myapp.crypto.*`` work.
        layer_key: 32-byte AES-256 key for L3 ciphertext. If ``None``, a fresh
            random key is generated per call. Production builds typically pass
            ``None`` (per-build random); the parameter exists for tests +
            future P2-8 ``--bind-device`` integration where the key is derived
            from a device fingerprint at runtime.
        filename: Used for ``compile()`` / ``ast.parse()`` error messages.

    Returns:
        ``(transformed_source, layer_assignments)`` where
        ``layer_assignments`` maps each top-level function's qualname to the
        resolved ``Layer``. The orchestrator uses this to configure Core's
        downstream rename / dead-code / CFF passes for L1 / L2 functions.

        If the module has no top-level functions, the source is returned
        unchanged with an empty assignment map.

    Raises:
        OpacityBuildError: on unsupported locations, unparseable decorator
            arguments, or L3 functions with extra decorators.
        SyntaxError: when ``source_code`` is not valid Python.
        ValueError: when ``layer_key`` is supplied but not 32 bytes.
    """
    if layer_key is not None and (
        not isinstance(layer_key, (bytes, bytearray)) or len(layer_key) != _LAYER_KEY_SIZE
    ):
        raise ValueError(
            f"layer_key must be exactly {_LAYER_KEY_SIZE} bytes, got "
            f"{len(layer_key) if isinstance(layer_key, (bytes, bytearray)) else type(layer_key).__name__}"
        )

    config = config or OpacityConfig()
    resolver = Resolver(config)

    tree = ast.parse(source_code, filename)
    _check_unsupported_locations(tree)

    targets = _collect_top_level_functions(tree)
    if not targets:
        return source_code, {}

    # Compute (qualname, Layer) per target -- decorator wins over config wins
    # over default. The decorator value is parsed statically from the AST so
    # the build never runs user code.
    assignments: dict[str, Layer] = {}
    target_layers: list[tuple[ast.FunctionDef | ast.AsyncFunctionDef, Layer]] = []
    for func_node in targets:
        qualname = _qualname(module_qualname, func_node.name)
        decorator_layer = _extract_opacity_decorator_layer(func_node)
        layer = resolver.resolve(qualname, decorator_layer)
        assignments[qualname] = layer
        target_layers.append((func_node, layer))

    l3_funcs = [node.name for node, layer in target_layers if layer is Layer.ENCRYPTED]

    # Compile the *unmodified* tree to extract each L3 function's CodeType.
    # dont_inherit=True is the P2-9 W1 finding: without it, ``compile()``
    # picks up future flags (e.g. CO_FUTURE_ANNOTATIONS) from the
    # transformer's own module, inflating co_flags on the produced code
    # objects. The user's source is later compiled by Python's normal import
    # path with no such inheritance, so the runtime decryption + materialization
    # would produce a code object whose flags differ from any build-time
    # comparison. Discipline shared with seal.py.
    func_codes: dict[str, types.CodeType] = {}
    if l3_funcs:
        module_code = compile(tree, filename, "exec", dont_inherit=True)
        func_codes = _extract_func_codes(module_code, l3_funcs)

    # Encrypt each L3 function's CodeType to ciphertext bytes. Single source
    # of truth shared with the runtime: build and runtime use the same
    # ``_encrypt_code`` / ``_decrypt_code`` pair from runtime/opacity.py.
    # Per-build ``_LAYER_KEY`` is generated once and reused for every L3
    # function in this module so a single module-level constant suffices.
    effective_key = layer_key if layer_key is not None else secrets.token_bytes(_LAYER_KEY_SIZE)
    cipher_blobs: dict[str, bytes] = {}
    for name, code in func_codes.items():
        cipher_blobs[name] = _encrypt_code(code, effective_key)

    # Mutate the AST in place: per-layer dispatch.
    new_body: list[ast.stmt] = []
    for stmt in tree.body:
        if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            new_body.append(stmt)
            continue

        resolved_layer: Layer | None = next(
            (candidate for node, candidate in target_layers if node is stmt), None
        )
        if resolved_layer is None:
            new_body.append(stmt)
            continue

        # Strip the @opacity(...) decorator on every layer.
        stmt.decorator_list = [d for d in stmt.decorator_list if not _is_opacity_decorator(d)]

        if resolved_layer is Layer.ENCRYPTED:
            cipher_const_name = f"{_CIPHER_PREFIX}{stmt.name}"
            cipher_assign = ast.Assign(
                targets=[ast.Name(id=cipher_const_name, ctx=ast.Store())],
                value=ast.Constant(value=cipher_blobs[stmt.name]),
            )
            new_body.append(cipher_assign)

            # @_l3_dispatch(_CIPHER_<funcname>, _LAYER_KEY)
            dispatch_call = ast.Call(
                func=ast.Name(id=_RUNTIME_DISPATCH, ctx=ast.Load()),
                args=[
                    ast.Name(id=cipher_const_name, ctx=ast.Load()),
                    ast.Name(id=_LAYER_KEY_NAME, ctx=ast.Load()),
                ],
                keywords=[],
            )
            stmt.decorator_list.append(dispatch_call)

            # Replace body with stub. Preserve a leading docstring if present
            # so help() / introspection of the unloaded stub still shows it
            # (the post-decrypt code carries its own docstring in co_consts[0]
            # and is restored on first call when ``stub.__code__`` is patched).
            stmt.body = _stub_body(stmt.body)

        new_body.append(stmt)
    tree.body = new_body

    # Inject the per-build LAYER_KEY constant + runtime import once. Place
    # both immediately after the leading import block so module-level user
    # code that runs at import time can rely on them being defined.
    if l3_funcs:
        _ensure_runtime_import(tree)
        _ensure_layer_key_constant(tree, effective_key)

    ast.fix_missing_locations(tree)
    return ast.unparse(tree), assignments


# ---------------------------------------------------------------------------
# Decorator detection / argument parsing
# ---------------------------------------------------------------------------


def _is_opacity_decorator(dec: ast.expr) -> bool:
    """Match ``@opacity(...)`` (bare name) or ``<anything>.opacity(...)``.

    Bare-name (``@opacity("...")``) and dotted form
    (``@pyobfus_pro.opacity("...")``) both qualify so users can import
    however they prefer. Decorators without a call (``@opacity``) are NOT
    matched -- ``opacity`` always takes a layer argument.
    """
    if not isinstance(dec, ast.Call):
        return False
    func = dec.func
    if isinstance(func, ast.Name):
        return func.id == _SOURCE_DECORATOR_NAME
    if isinstance(func, ast.Attribute):
        return func.attr == _SOURCE_DECORATOR_NAME
    return False


def _extract_opacity_decorator_layer(
    func_node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> Layer | None:
    """Statically parse the layer argument of ``@opacity(...)`` if present.

    Supports two argument forms:

    - String literal: ``@opacity("encrypted")``
    - Layer enum attribute: ``@opacity(Layer.ENCRYPTED)``

    Returns ``None`` if the function has no ``@opacity(...)`` decorator.
    Raises :class:`OpacityBuildError` on a recognized decorator with an
    unparseable argument (variable, call result, etc.) -- such forms can't
    be resolved at build time without running user code.
    """
    matches = [d for d in func_node.decorator_list if _is_opacity_decorator(d)]
    if not matches:
        return None
    if len(matches) > 1:
        raise OpacityBuildError(
            f"@opacity(...) appears multiple times on {func_node.name!r}; "
            f"only one layer assignment per symbol is allowed"
        )
    dec = matches[0]
    # ``_is_opacity_decorator`` only returns True for ast.Call nodes, so this
    # is type-safe by construction; the cast is for the type-checker only.
    if not isinstance(dec, ast.Call):  # pragma: no cover -- unreachable
        raise OpacityBuildError(f"@opacity on {func_node.name!r}: internal -- expected Call node")
    if len(dec.args) != 1 or dec.keywords:
        raise OpacityBuildError(
            f"@opacity(...) on {func_node.name!r} must take exactly one "
            f"positional argument (layer name string or Layer enum member)"
        )
    arg = dec.args[0]
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        try:
            return Layer.from_string(arg.value)
        except Exception as exc:  # noqa: BLE001 -- OpacityConfigError chain
            raise OpacityBuildError(
                f"@opacity({arg.value!r}) on {func_node.name!r}: {exc}"
            ) from exc
    if (
        isinstance(arg, ast.Attribute)
        and isinstance(arg.value, ast.Name)
        and arg.value.id == "Layer"
    ):
        # Layer.ENCRYPTED -> attr is "ENCRYPTED" -> Layer.ENCRYPTED.value
        try:
            member = Layer[arg.attr]
        except KeyError as exc:
            raise OpacityBuildError(
                f"@opacity(Layer.{arg.attr}) on {func_node.name!r}: " f"unknown Layer member"
            ) from exc
        return member
    raise OpacityBuildError(
        f"@opacity(...) argument on {func_node.name!r} is not statically "
        f"parseable; supported forms are a string literal "
        f'(e.g. "encrypted") or a Layer enum attribute '
        f"(e.g. Layer.ENCRYPTED)"
    )


# ---------------------------------------------------------------------------
# Location validation
# ---------------------------------------------------------------------------


def _check_unsupported_locations(tree: ast.Module) -> None:
    """Raise OpacityBuildError if @opacity appears in unsupported places.

    v1 supports module-level FunctionDef / AsyncFunctionDef only. Class
    methods, nested defs, and class-level decorators are deferred (see
    docs/P2-1_DESIGN.md Q3).
    """
    for stmt in tree.body:
        if isinstance(stmt, ast.ClassDef):
            if any(_is_opacity_decorator(d) for d in stmt.decorator_list):
                raise OpacityBuildError(
                    f"@opacity(...) on class {stmt.name!r} is not supported "
                    f"in v0.5; class-level layer assignment is planned for "
                    f"a future milestone (see docs/P2-1_DESIGN.md Q3)"
                )
            for item in ast.walk(stmt):
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(
                    _is_opacity_decorator(d) for d in item.decorator_list
                ):
                    raise OpacityBuildError(
                        f"@opacity(...) on class method "
                        f"{stmt.name}.{item.name} is not supported in v0.5"
                    )
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for item in ast.walk(stmt):
                if item is stmt:
                    continue
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(
                    _is_opacity_decorator(d) for d in item.decorator_list
                ):
                    raise OpacityBuildError(
                        f"@opacity(...) on nested function {item.name!r} "
                        f"(inside {stmt.name!r}) is not supported in v0.5"
                    )


def _collect_top_level_functions(
    tree: ast.Module,
) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    return [stmt for stmt in tree.body if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef))]


# ---------------------------------------------------------------------------
# CodeType extraction (L3 only)
# ---------------------------------------------------------------------------


def _extract_func_codes(
    module_code: types.CodeType, l3_func_names: Iterable[str]
) -> dict[str, types.CodeType]:
    """Locate each L3 function's CodeType in the compiled module's co_consts.

    For top-level functions in CPython, the function's CodeType is a constant
    in the enclosing module's ``co_consts``. The MAKE_FUNCTION + CALL bytecode
    in the module then wraps that code object in a function value; decorator
    application happens via the bytecode, so the function's *own* CodeType is
    independent of decorators.

    Each L3 function must be present in ``co_consts`` with a matching
    ``co_name``; an attacker who, e.g., wraps the def in an outer scope
    won't reach this code path because ``_check_unsupported_locations``
    rejected it.

    Also enforces "L3 must be the only decorator" v1 rule: if multiple
    @opacity-marked functions in module would conflict here, the assignment
    map already disambiguates above.
    """
    target_set = set(l3_func_names)
    found: dict[str, types.CodeType] = {}
    for const in module_code.co_consts:
        if isinstance(const, types.CodeType) and const.co_name in target_set:
            if const.co_name in found:
                raise OpacityBuildError(
                    f"Multiple top-level code objects named "
                    f"{const.co_name!r} in module; cannot disambiguate L3 "
                    f"target"
                )
            found[const.co_name] = const

    missing = target_set - set(found.keys())
    if missing:
        raise OpacityBuildError(
            f"Could not locate code object for L3 function(s): {sorted(missing)}"
        )
    return found


# ---------------------------------------------------------------------------
# Body / decorator rewrite helpers
# ---------------------------------------------------------------------------


def _stub_body(original_body: list[ast.stmt]) -> list[ast.stmt]:
    """Return a stub body, preserving a leading docstring if present.

    The docstring becomes ``stub.__doc__`` so introspection of the unloaded
    stub (before first call) still shows the original docstring. After the
    first call, ``stub.__code__`` is patched and ``__doc__`` is recomputed
    from the loaded code's ``co_consts[0]`` -- which is the original
    docstring again, since we encrypted the unmodified ``CodeType``.
    """
    if (
        original_body
        and isinstance(original_body[0], ast.Expr)
        and isinstance(original_body[0].value, ast.Constant)
        and isinstance(original_body[0].value.value, str)
    ):
        return [original_body[0], ast.Pass()]
    return [ast.Pass()]


def _ensure_runtime_import(tree: ast.Module) -> None:
    """Inject ``from pyobfus_pro.runtime import _l3_dispatch`` once.

    If the module already imports from ``pyobfus_pro.runtime``, the
    function appends ``_l3_dispatch`` to the existing alias list (so seal /
    scrub / opacity imports collapse into one line). Otherwise a new import
    is inserted after any leading import block.
    """
    for stmt in tree.body:
        if isinstance(stmt, ast.ImportFrom) and stmt.module == _RUNTIME_MODULE:
            if not any(alias.name == _RUNTIME_DISPATCH for alias in stmt.names):
                stmt.names.append(ast.alias(name=_RUNTIME_DISPATCH))
            return

    new_import = ast.ImportFrom(
        module=_RUNTIME_MODULE,
        names=[ast.alias(name=_RUNTIME_DISPATCH)],
        level=0,
    )
    insert_at = 0
    for i, stmt in enumerate(tree.body):
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            insert_at = i + 1
        else:
            break
    tree.body.insert(insert_at, new_import)


def _ensure_layer_key_constant(tree: ast.Module, layer_key: bytes) -> None:
    """Inject ``_LAYER_KEY = b"..."`` once, after the import block.

    Placed before any ``_CIPHER_<funcname>`` constants so the cipher
    constants and the L3-decorated function defs can both reference it
    without forward references.

    Idempotency: if a top-level ``_LAYER_KEY`` assignment already exists
    (e.g., a re-run of the transformer), it's left untouched. (Re-running
    the transformer on already-transformed source is not a documented
    workflow but the no-op behavior is harmless.)
    """
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == _LAYER_KEY_NAME:
                    return

    key_assign = ast.Assign(
        targets=[ast.Name(id=_LAYER_KEY_NAME, ctx=ast.Store())],
        value=ast.Constant(value=bytes(layer_key)),
    )
    insert_at = 0
    for i, stmt in enumerate(tree.body):
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            insert_at = i + 1
        else:
            break
    tree.body.insert(insert_at, key_assign)


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------


def _qualname(module_qualname: str, name: str) -> str:
    """Combine module path + symbol name into a dotted qualname for the resolver."""
    return f"{module_qualname}.{name}" if module_qualname else name


# Expose a tiny accessor for tests + downstream Core orchestrators that need
# to know which AST passes a given resolved layer wants. Wraps the static
# ``LAYER_SPECS`` mapping so callers don't import from ``opacity.layers``
# unless they have a specific reason to.
def layer_spec_for(layer: Layer):
    """Return the frozen ``LayerSpec`` for ``layer`` (re-export convenience)."""
    return LAYER_SPECS[layer]
