"""Slice C of the multi-module L3 + application-key design: the Pro adapter.

This is the Pro, encryption-side counterpart to the Community planning layer in
``pyobfus.core.crossfile_opacity`` (slices A/B). It consumes an **explicit set
of final (already-renamed) target names** -- never re-matching ``opacity.toml``
on the short source or selecting by decorator name -- encrypts each target's
compiled code with the application key, and rewrites the module so each target
becomes an L3 stub that materializes lazily at first call.

Design contract honoured here (docs/CROSSFILE_OPACITY_DESIGN.md §4.4-§4.7, §5):

- The runtime key is referenced **directly** as a key expression
  ``<key> = provided_key("<ENV>")``. The raw key is used only in-process for
  build-time encryption; it never appears as a module constant, not even
  transiently as a ``_LAYER_KEY = b"..."`` literal that is later rewritten.
- Helper / cipher-constant / key / import-alias names are allocated from names
  not already used in the module, rather than reusing fixed spellings.
- The module docstring and ``__future__`` prologue stay ahead of injected code.
- Every target is round-tripped (encrypt -> decrypt -> compare) in the build
  process, and the emitted source is scanned so the key cannot leak.

The adapter only ``compile``s; it never executes the user module and never
calls the key provider. Wiring it into an end-to-end build is a later slice.
"""

from __future__ import annotations

import ast
import base64
import marshal
import types
from dataclasses import dataclass, field
from typing import Iterable, List, Tuple

from pyobfus.core.unparse import unparse
from pyobfus_runtime.opacity import _decrypt_code, _encrypt_code

_RUNTIME_MODULE = "pyobfus_runtime"
_DISPATCH_IMPORT = "_l3_dispatch"
_PROVIDED_KEY_IMPORT = "provided_key"
_KEY_SIZE = 32  # AES-256


class CrossfileOpacityAdapterError(ValueError):
    """Raised when the explicit target set cannot be encrypted safely."""


@dataclass(frozen=True)
class EncryptedTarget:
    final_name: str
    cipher_const: str


@dataclass(frozen=True)
class AdapterResult:
    source: str
    env_name: str
    key_name: str
    dispatch_alias: str
    provided_key_alias: str
    targets: Tuple[EncryptedTarget, ...] = field(default_factory=tuple)


def encrypt_targets(
    final_source: str,
    target_final_names: Iterable[str],
    *,
    key: bytes,
    env_name: str,
    filename: str = "<crossfile-opacity>",
) -> AdapterResult:
    """Encrypt an explicit set of top-level functions in already-renamed source.

    Args:
        final_source: the module source after Core's rename pass.
        target_final_names: the final (renamed) names to encrypt -- typically
            the ``final_name`` values from the slice-B correspondence. Each must
            resolve to exactly one top-level ``def`` and no other module-level
            binding of that name.
        key: the 32-byte application key, used only for build-time encryption.
        env_name: the environment-variable name the runtime key expression
            reads (``provided_key("<env_name>")``).
        filename: used for ``compile`` diagnostics only.

    Returns:
        An :class:`AdapterResult` with the transformed source and the names it
        allocated.

    Raises:
        CrossfileOpacityAdapterError: on an unknown/ambiguous target, a target
            with free variables, a failed round-trip, or a detected key leak.
        ValueError: when ``key`` is not 32 bytes.
    """
    if not isinstance(key, (bytes, bytearray)) or len(key) != _KEY_SIZE:
        raise ValueError(
            f"key must be exactly {_KEY_SIZE} bytes, got "
            f"{len(key) if isinstance(key, (bytes, bytearray)) else type(key).__name__}"
        )
    if not env_name:
        raise CrossfileOpacityAdapterError("env_name must be a non-empty string")

    targets = list(dict.fromkeys(target_final_names))  # de-dup, preserve order
    if not targets:
        raise CrossfileOpacityAdapterError("no targets requested")

    tree = ast.parse(final_source, filename)
    top_level = _top_level_function_index(tree)
    module_bindings = _module_level_binding_counts(tree)

    for name in targets:
        defs = top_level.get(name, [])
        if len(defs) != 1 or module_bindings.get(name, 0) != 1:
            raise CrossfileOpacityAdapterError(
                f"target {name!r} must resolve to exactly one top-level function "
                f"with no other module-level binding of that name "
                f"(found {len(defs)} top-level defs, {module_bindings.get(name, 0)} bindings)"
            )

    # Compile the unmodified tree once to extract each target's CodeType.
    module_code = compile(tree, filename, "exec", dont_inherit=True)
    original_codes = _extract_target_codes(module_code, targets)
    for name, code in original_codes.items():
        if code.co_freevars:
            raise CrossfileOpacityAdapterError(
                f"target {name!r} has free variables {code.co_freevars!r}; the first "
                f"release only supports self-contained top-level functions"
            )

    # Allocate names that do not collide with anything the module already uses.
    used = _used_identifiers(tree)
    gen = _FreshNames(used)
    dispatch_alias = gen.fresh("_pyobfus_dispatch")
    provided_key_alias = gen.fresh("_pyobfus_provided_key")
    key_name = gen.fresh("_pyobfus_l3_key")
    cipher_names = {name: gen.fresh(f"_pyobfus_cipher_{i}") for i, name in enumerate(targets)}

    # Encrypt each target's code with the in-memory key.
    cipher_blobs = {name: _encrypt_code(code, key) for name, code in original_codes.items()}

    # Build-process round-trip: decrypt and compare before emitting anything.
    for name, blob in cipher_blobs.items():
        _verify_round_trip(name, blob, key, original_codes[name])

    transformed = _rewrite_module(
        tree,
        targets=targets,
        cipher_blobs=cipher_blobs,
        cipher_names=cipher_names,
        dispatch_alias=dispatch_alias,
        provided_key_alias=provided_key_alias,
        key_name=key_name,
        env_name=env_name,
    )
    ast.fix_missing_locations(transformed)
    out_source = unparse(transformed)

    # Confirm the emitted module compiles and no longer carries the plaintext.
    _verify_emitted(out_source, filename, targets, original_codes)
    _assert_no_key_leak(out_source, key)

    return AdapterResult(
        source=out_source,
        env_name=env_name,
        key_name=key_name,
        dispatch_alias=dispatch_alias,
        provided_key_alias=provided_key_alias,
        targets=tuple(EncryptedTarget(final_name=n, cipher_const=cipher_names[n]) for n in targets),
    )


# ---------------------------------------------------------------------------
# AST inspection
# ---------------------------------------------------------------------------


def _top_level_function_index(tree: ast.Module) -> dict[str, List[ast.stmt]]:
    index: dict[str, List[ast.stmt]] = {}
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            index.setdefault(stmt.name, []).append(stmt)
    return index


def _module_level_binding_counts(tree: ast.Module) -> dict[str, int]:
    """Count every module-level binding of each name (defs, classes, assigns,
    imports, deletes), so a target that is also, say, imported or reassigned at
    module level is rejected as ambiguous."""
    counts: dict[str, int] = {}

    def bump(name: str) -> None:
        counts[name] = counts.get(name, 0) + 1

    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bump(stmt.name)
        elif isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                for n in _names_in_target(target):
                    bump(n)
        elif isinstance(stmt, ast.AnnAssign):
            if stmt.value is not None:
                for n in _names_in_target(stmt.target):
                    bump(n)
        elif isinstance(stmt, ast.AugAssign):
            for n in _names_in_target(stmt.target):
                bump(n)
        elif isinstance(stmt, (ast.Import, ast.ImportFrom)):
            for alias in stmt.names:
                bump(alias.asname or alias.name.split(".")[0])
        elif isinstance(stmt, ast.Delete):
            for target in stmt.targets:
                for n in _names_in_target(target):
                    bump(n)
    return counts


def _names_in_target(target: ast.AST) -> Iterable[str]:
    if isinstance(target, ast.Name):
        yield target.id
    elif isinstance(target, (ast.Tuple, ast.List)):
        for elt in target.elts:
            yield from _names_in_target(elt)
    elif isinstance(target, ast.Starred):
        yield from _names_in_target(target.value)


def _extract_target_codes(
    module_code: types.CodeType, targets: Iterable[str]
) -> dict[str, types.CodeType]:
    target_set = set(targets)
    found: dict[str, types.CodeType] = {}
    for const in module_code.co_consts:
        if isinstance(const, types.CodeType) and const.co_name in target_set:
            if const.co_name in found:
                raise CrossfileOpacityAdapterError(
                    f"multiple top-level code objects named {const.co_name!r}"
                )
            found[const.co_name] = const
    missing = target_set - set(found)
    if missing:
        raise CrossfileOpacityAdapterError(
            f"could not locate code object(s) for target(s): {sorted(missing)}"
        )
    return found


def _used_identifiers(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    return names


class _FreshNames:
    def __init__(self, used: set[str]) -> None:
        self._used = set(used)

    def fresh(self, base: str) -> str:
        candidate = base
        suffix = 0
        while candidate in self._used:
            suffix += 1
            candidate = f"{base}_{suffix}"
        self._used.add(candidate)
        return candidate


# ---------------------------------------------------------------------------
# Rewrite
# ---------------------------------------------------------------------------


def _rewrite_module(
    tree: ast.Module,
    *,
    targets: List[str],
    cipher_blobs: dict[str, bytes],
    cipher_names: dict[str, str],
    dispatch_alias: str,
    provided_key_alias: str,
    key_name: str,
    env_name: str,
) -> ast.Module:
    target_set = set(targets)
    new_body: List[ast.stmt] = []
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name in target_set:
            cipher_const = cipher_names[stmt.name]
            new_body.append(
                ast.Assign(
                    targets=[ast.Name(id=cipher_const, ctx=ast.Store())],
                    value=ast.Constant(value=cipher_blobs[stmt.name]),
                )
            )
            stmt.decorator_list = list(stmt.decorator_list) + [
                ast.Call(
                    func=ast.Name(id=dispatch_alias, ctx=ast.Load()),
                    args=[
                        ast.Name(id=cipher_const, ctx=ast.Load()),
                        ast.Name(id=key_name, ctx=ast.Load()),
                    ],
                    keywords=[],
                )
            ]
            stmt.body = _stub_body(stmt.body)
            new_body.append(stmt)
        else:
            new_body.append(stmt)
    tree.body = new_body

    insert_at = _after_leading_imports(tree)
    # import ... as <alias> for both dispatch and provided_key, in one statement
    import_stmt = ast.ImportFrom(
        module=_RUNTIME_MODULE,
        names=[
            ast.alias(name=_DISPATCH_IMPORT, asname=dispatch_alias),
            ast.alias(name=_PROVIDED_KEY_IMPORT, asname=provided_key_alias),
        ],
        level=0,
    )
    # <key_name> = <provided_key_alias>("<env_name>")  -- direct key expression
    key_assign = ast.Assign(
        targets=[ast.Name(id=key_name, ctx=ast.Store())],
        value=ast.Call(
            func=ast.Name(id=provided_key_alias, ctx=ast.Load()),
            args=[ast.Constant(value=env_name)],
            keywords=[],
        ),
    )
    tree.body.insert(insert_at, key_assign)
    tree.body.insert(insert_at, import_stmt)
    return tree


def _stub_body(original_body: List[ast.stmt]) -> List[ast.stmt]:
    if (
        original_body
        and isinstance(original_body[0], ast.Expr)
        and isinstance(original_body[0].value, ast.Constant)
        and isinstance(original_body[0].value.value, str)
    ):
        return [original_body[0], ast.Pass()]
    return [ast.Pass()]


def _after_leading_imports(tree: ast.Module) -> int:
    index = 0
    if (
        tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)
    ):
        index = 1
    while index < len(tree.body) and isinstance(tree.body[index], (ast.Import, ast.ImportFrom)):
        index += 1
    return index


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------


def _verify_round_trip(name: str, blob: bytes, key: bytes, original: types.CodeType) -> None:
    decrypted = _decrypt_code(blob, key)
    if decrypted.co_name != name:
        raise CrossfileOpacityAdapterError(
            f"round-trip for {name!r} produced co_name {decrypted.co_name!r}"
        )
    if decrypted.co_freevars:
        raise CrossfileOpacityAdapterError(f"round-trip for {name!r} introduced free variables")
    for attr in ("co_argcount", "co_posonlyargcount", "co_kwonlyargcount", "co_flags"):
        if getattr(decrypted, attr) != getattr(original, attr):
            raise CrossfileOpacityAdapterError(f"round-trip for {name!r} changed {attr}")
    # marshal is not byte-stable across a re-dump (object interning differs),
    # so compare the bytecode directly and the forms normalized through one
    # loads/dumps cycle, which is stable.
    if decrypted.co_code != original.co_code or _marshal_normal(decrypted) != _marshal_normal(
        original
    ):
        raise CrossfileOpacityAdapterError(
            f"round-trip for {name!r} did not reproduce the original code object"
        )


def _marshal_normal(code: types.CodeType) -> bytes:
    """Marshal form normalized through one loads/dumps cycle (interning-stable)."""
    return marshal.dumps(marshal.loads(marshal.dumps(code)))


def _verify_emitted(
    out_source: str,
    filename: str,
    targets: Iterable[str],
    original_codes: dict[str, types.CodeType],
) -> None:
    """Compile the emitted module and confirm each target now has a stub body
    (its shipped code object is no longer the plaintext)."""
    emitted_code = compile(out_source, filename, "exec", dont_inherit=True)
    emitted = {
        const.co_name: const
        for const in emitted_code.co_consts
        if isinstance(const, types.CodeType)
    }
    for name in targets:
        shipped = emitted.get(name)
        if shipped is None:
            raise CrossfileOpacityAdapterError(f"emitted module lost target {name!r}")
        if shipped.co_code == original_codes[name].co_code:
            raise CrossfileOpacityAdapterError(
                f"emitted module still contains the plaintext code for {name!r}"
            )


def _assert_no_key_leak(out_source: str, key: bytes) -> None:
    """Fail if the raw key appears in the emitted source in any common form.

    A regression guard, not a proof against arbitrary steganography: it checks
    the raw byte literal, base64, and hex spellings.
    """
    text = out_source
    representations = [
        repr(key),
        repr(bytes(key)),
        base64.b64encode(key).decode("ascii"),
        key.hex(),
    ]
    for rep in representations:
        if rep and rep in text:
            raise CrossfileOpacityAdapterError("the application key leaked into the emitted source")
