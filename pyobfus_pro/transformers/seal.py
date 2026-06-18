"""Build-pass AST transformer for @seal_code.

Reads source, finds @seal_code-decorated module-level functions, computes
each function's seal hash, and rewrites the module to:

1. Import _verify_seal from runtime
2. Emit per-function _SEAL_<name> = b"..." constants before each def
3. Replace @seal_code with @_verify_seal(_SEAL_<name>) (plaintext seal) OR
   @_verify_seal(_SEAL_<name>, target=_CIPHER_<name>) (P2-9.1 ciphertext
   seal, when the function is in P2-1's L3 layer)

Hashing uses ``runtime._compute_seal`` (plaintext path) or
``runtime._compute_seal_bytes`` (ciphertext path) so build-time and runtime
share the same deterministic rule per seal mode.

W1 v1 limitations (documented in docs/P2-9_DESIGN.md):
- Module-level functions only (class methods and nested defs raise SealBuildError)
- Build Python version must match deployment Python version (marshal output
  varies across versions; future ABI-tagged seals may lift this)

P2-9.1 layer-aware seal coupling (this milestone):

When called with ``layer_assignments`` (a ``{qualname: Layer}`` map produced
by P2-1's :func:`pyobfus_pro.transformers.opacity.transform_module`),
this transformer routes each sealed function to the appropriate seal mode:

- L3 (encrypted): hash the ``_CIPHER_<name>`` constant bytes directly
  (the function's code-object is now a ``pass`` stub and would be useless
  to hash). Detects tampering of the cipher constant *before* L3 dispatch
  attempts decryption -- defense in depth above AES-GCM tag verification.
- L0 / L1 / L2 / no assignment: current plaintext-seal behavior.

**Pass-order rule** (when both are used): opacity transformer MUST run
BEFORE seal transformer. Reason: seal extracts the cipher bytes from the
post-opacity AST (the ``_CIPHER_<name>`` Assign nodes), then bakes their
sha256 into the seal constant. If seal ran first, the cipher bytes wouldn't
exist yet, and there'd be no way to ciphertext-seal an L3 function.

Patent-gated. See ../runtime/seal.py for the runtime side and
``PATENT_NOTES.md`` P2-9 sub-finding "1.5 layer-aware seal" for the
inventive-step framing of the coupling.
"""

from __future__ import annotations

import ast
import types
from collections.abc import Iterable

from pyobfus_pro.opacity.layers import Layer
from pyobfus_pro.runtime.seal import _compute_seal, _compute_seal_bytes

_RUNTIME_MODULE = "pyobfus_pro.runtime"
_RUNTIME_VERIFIER = "_verify_seal"
_SEAL_CONSTANT_PREFIX = "_SEAL_"
_CIPHER_CONSTANT_PREFIX = "_CIPHER_"
_SOURCE_DECORATOR_NAME = "seal_code"


class SealBuildError(ValueError):
    """Raised when @seal_code usage cannot be transformed.

    Reasons include: function code object not found in compiled module,
    decoration on an unsupported location (class method or nested def in
    v0.5; planned for P2-9.1).
    """


def transform_module(
    source_code: str,
    *,
    layer_assignments: dict[str, Layer] | None = None,
    module_qualname: str = "",
    filename: str = "<seal-pass>",
) -> str:
    """Apply the @seal_code build pass to a module source.

    Args:
        source_code: Python source text.
        layer_assignments: P2-1 ``{qualname: Layer}`` map from a prior run of
            ``transformers.opacity.transform_module``. When provided, sealed
            functions assigned to ``Layer.ENCRYPTED`` use the ciphertext-seal
            path (hash the ``_CIPHER_<name>`` bytes); other layers and
            unmapped functions use the plaintext-seal path. When ``None``,
            all sealed functions use the plaintext-seal path (back-compat
            with pre-P2-9.1 callers).
        module_qualname: Used to look up entries in ``layer_assignments``.
            Empty string means "use bare function name". Match the value
            passed to ``opacity.transform_module``.
        filename: Used for compile() error messages.

    Returns:
        Transformed source. If the module has no @seal_code decorations,
        the source is returned unchanged.

    Raises:
        SealBuildError: if @seal_code appears in an unsupported location, or
            if a function is assigned to L3 in ``layer_assignments`` but the
            corresponding ``_CIPHER_<name>`` constant is missing from the
            source (which means opacity transformer didn't run first, in
            violation of the documented pass-order rule).
        SyntaxError: if source_code is not valid Python.
    """
    tree = ast.parse(source_code, filename)

    _check_unsupported_locations(tree)

    sealed_funcs = _collect_top_level_sealed_funcs(tree)
    if not sealed_funcs:
        return source_code

    # P2-9.1: partition sealed funcs into plaintext vs ciphertext seal targets
    # per the layer-aware coupling contract. Unmapped or non-L3 funcs default
    # to plaintext (current pre-P2-9.1 behavior).
    assignments = layer_assignments or {}
    plaintext_funcs: list[str] = []
    ciphertext_funcs: list[str] = []
    for name in sealed_funcs:
        qualname = f"{module_qualname}.{name}" if module_qualname else name
        layer = assignments.get(qualname)
        if layer is Layer.ENCRYPTED:
            ciphertext_funcs.append(name)
        else:
            plaintext_funcs.append(name)

    func_hashes: dict[str, bytes] = {}

    if plaintext_funcs:
        # dont_inherit=True is critical: without it, compile() picks up future
        # flags from THIS module (the transformer itself uses
        # `from __future__ import annotations`), inflating co_flags on the
        # produced code objects. The user's source is later compiled by Python's
        # normal import path with no such inheritance, so the runtime hash would
        # diverge from the build hash by exactly the inherited future-flag bits.
        module_code = compile(tree, filename, "exec", dont_inherit=True)
        func_hashes.update(_compute_func_hashes(module_code, plaintext_funcs))

    if ciphertext_funcs:
        cipher_blobs = _extract_cipher_constants(tree, ciphertext_funcs)
        for name, blob in cipher_blobs.items():
            func_hashes[name] = _compute_seal_bytes(blob)

    seal_modes: dict[str, str] = {name: "plaintext" for name in plaintext_funcs}
    seal_modes.update({name: "ciphertext" for name in ciphertext_funcs})

    _rewrite_decorators(tree, func_hashes, seal_modes)
    _insert_seal_constants(tree, func_hashes)
    _ensure_runtime_import(tree)

    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


def _is_seal_code_decorator(dec: ast.expr) -> bool:
    """Match `seal_code` (bare name) or `<anything>.seal_code` (attribute)."""
    if isinstance(dec, ast.Name):
        return dec.id == _SOURCE_DECORATOR_NAME
    if isinstance(dec, ast.Attribute):
        return dec.attr == _SOURCE_DECORATOR_NAME
    return False


def _check_unsupported_locations(tree: ast.Module) -> None:
    """Raise SealBuildError if @seal_code is on a class method or nested def."""
    for stmt in tree.body:
        if isinstance(stmt, ast.ClassDef):
            for item in ast.walk(stmt):
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if any(_is_seal_code_decorator(d) for d in item.decorator_list):
                        raise SealBuildError(
                            f"@seal_code on class method {stmt.name}.{item.name} "
                            f"is not supported in v0.5; planned for P2-9.1. "
                            f"See docs/P2-9_DESIGN.md."
                        )
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for item in ast.walk(stmt):
                if item is stmt:
                    continue
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if any(_is_seal_code_decorator(d) for d in item.decorator_list):
                        raise SealBuildError(
                            f"@seal_code on nested function {item.name} "
                            f"(inside {stmt.name}) is not supported in v0.5."
                        )


def _collect_top_level_sealed_funcs(tree: ast.Module) -> list[str]:
    names: list[str] = []
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if any(_is_seal_code_decorator(d) for d in stmt.decorator_list):
                names.append(stmt.name)
    return names


def _compute_func_hashes(
    module_code: types.CodeType, sealed_funcs: Iterable[str]
) -> dict[str, bytes]:
    """Find each sealed function's code object in the module's `co_consts`,
    then hash it with the same rule used at runtime.

    The function's code object is independent of decorator changes: the
    decorator application lives in the module's bytecode (MAKE_FUNCTION +
    CALL), not inside the function's own code. So the hash computed here
    matches what `runtime._compute_seal(func)` will compute at first call.
    """
    sealed_set = set(sealed_funcs)
    hashes: dict[str, bytes] = {}
    for const in module_code.co_consts:
        if isinstance(const, types.CodeType) and const.co_name in sealed_set:
            hashes[const.co_name] = _compute_seal(const)

    missing = sealed_set - set(hashes.keys())
    if missing:
        raise SealBuildError(
            f"Could not locate code object for sealed function(s): {sorted(missing)}"
        )
    return hashes


def _rewrite_decorators(
    tree: ast.Module,
    func_hashes: dict[str, bytes],
    seal_modes: dict[str, str],
) -> None:
    """Remove @seal_code, append @_verify_seal(...) on each sealed def.

    For ``seal_modes[name] == "plaintext"`` (default / L0 / L1 / L2):
        ``@_verify_seal(_SEAL_<name>)``
    For ``seal_modes[name] == "ciphertext"`` (P2-9.1 L3 coupling):
        ``@_verify_seal(_SEAL_<name>, target=_CIPHER_<name>)``

    The ciphertext-mode decorator is positioned at the END of decorator_list
    (innermost wrapper), placing it inside ``@_l3_dispatch(...)`` if also
    present -- so the seal verifies cipher integrity *before* dispatch
    attempts decryption. Pass-order guarantees opacity ran first, so
    ``@_l3_dispatch`` is already innermost; ``cleaned.append(verify_call)``
    puts the seal between l3_dispatch and any other outer user decorators.

    Wait -- subtle point: appending to cleaned puts seal LAST in
    decorator_list = INNERMOST. If l3_dispatch is also in cleaned (as
    INNERMOST after opacity stripped @opacity and appended @_l3_dispatch),
    then we want seal to be ABOVE l3_dispatch (outer) so seal runs first
    on call. To achieve that we INSERT the seal call BEFORE the existing
    l3_dispatch, not append. For plaintext path no l3_dispatch exists so
    appending is fine. Detect by mode and position accordingly.
    """
    for stmt in tree.body:
        if not (
            isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name in func_hashes
        ):
            continue

        cleaned = [d for d in stmt.decorator_list if not _is_seal_code_decorator(d)]
        seal_const = ast.Name(
            id=f"{_SEAL_CONSTANT_PREFIX}{stmt.name}",
            ctx=ast.Load(),
        )
        if seal_modes.get(stmt.name) == "ciphertext":
            cipher_name = ast.Name(
                id=f"{_CIPHER_CONSTANT_PREFIX}{stmt.name}",
                ctx=ast.Load(),
            )
            verify_call = ast.Call(
                func=ast.Name(id=_RUNTIME_VERIFIER, ctx=ast.Load()),
                args=[seal_const],
                keywords=[ast.keyword(arg="target", value=cipher_name)],
            )
            # Seal must wrap OUTSIDE _l3_dispatch so the seal check runs
            # before dispatch attempts decryption. AST decorator_list is
            # source-order top->bottom, applied bottom->top: the LAST entry
            # is innermost. _l3_dispatch from the opacity pass is innermost
            # (last). Insert seal at len-1 to land just OUTSIDE l3_dispatch.
            l3_index = _index_of_l3_dispatch(cleaned)
            if l3_index is not None:
                cleaned.insert(l3_index, verify_call)
            else:
                # Layer assignment said L3 but no _l3_dispatch decorator
                # present -- pass-order rule violated (opacity didn't run,
                # or function was reassigned). Fall back to outermost.
                cleaned.insert(0, verify_call)
        else:
            verify_call = ast.Call(
                func=ast.Name(id=_RUNTIME_VERIFIER, ctx=ast.Load()),
                args=[seal_const],
                keywords=[],
            )
            cleaned.append(verify_call)

        stmt.decorator_list = cleaned


def _index_of_l3_dispatch(decorators: list[ast.expr]) -> int | None:
    """Return the index of ``@_l3_dispatch(...)`` in a decorator list, or None.

    Matches bare-name and dotted forms. Used by the ciphertext-seal path to
    place the seal verifier just outside the L3 dispatch wrapper.
    """
    for i, dec in enumerate(decorators):
        if not isinstance(dec, ast.Call):
            continue
        func = dec.func
        if isinstance(func, ast.Name) and func.id == "_l3_dispatch":
            return i
        if isinstance(func, ast.Attribute) and func.attr == "_l3_dispatch":
            return i
    return None


def _extract_cipher_constants(tree: ast.Module, l3_funcs: Iterable[str]) -> dict[str, bytes]:
    """Walk top-level Assign nodes for ``_CIPHER_<name> = b"..."``.

    Returns ``{funcname: cipher_blob_bytes}`` for each requested L3 function.

    Raises:
        SealBuildError: if any requested ``_CIPHER_<name>`` constant is
            missing or not a bytes constant. Means opacity transformer
            didn't run before seal (pass-order rule violated) or somebody
            tampered with the post-opacity AST.
    """
    target_names = {f"{_CIPHER_CONSTANT_PREFIX}{name}": name for name in l3_funcs}
    found: dict[str, bytes] = {}
    for stmt in tree.body:
        if not isinstance(stmt, ast.Assign):
            continue
        for target in stmt.targets:
            if not isinstance(target, ast.Name):
                continue
            if target.id not in target_names:
                continue
            if not (isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, bytes)):
                raise SealBuildError(
                    f"{target.id!r} is present but not a bytes constant; "
                    f"P2-9.1 expects the value emitted by opacity "
                    f"transformer's L3 path"
                )
            found[target_names[target.id]] = stmt.value.value
    missing = set(target_names.values()) - set(found.keys())
    if missing:
        raise SealBuildError(
            f"P2-9.1 layer-aware seal requested ciphertext-mode for "
            f"{sorted(missing)}, but no _CIPHER_<name> constants found in "
            f"the module. Pass-order rule violated: run "
            f"transformers.opacity.transform_module BEFORE "
            f"transformers.seal.transform_module."
        )
    return found


def _insert_seal_constants(tree: ast.Module, func_hashes: dict[str, bytes]) -> None:
    """Insert `_SEAL_<name> = b"..."` immediately before each sealed function def."""
    new_body: list[ast.stmt] = []
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name in func_hashes:
            seal_assign = ast.Assign(
                targets=[
                    ast.Name(
                        id=f"{_SEAL_CONSTANT_PREFIX}{stmt.name}",
                        ctx=ast.Store(),
                    )
                ],
                value=ast.Constant(value=func_hashes[stmt.name]),
            )
            new_body.append(seal_assign)
        new_body.append(stmt)
    tree.body = new_body


def _ensure_runtime_import(tree: ast.Module) -> None:
    """Ensure `from pyobfus_pro.runtime import _verify_seal` is present.

    If `pyobfus_pro.runtime` is already imported, the function appends
    `_verify_seal` to its alias list (if not already there). Otherwise a new
    import is inserted after any leading imports.
    """
    for stmt in tree.body:
        if isinstance(stmt, ast.ImportFrom) and stmt.module == _RUNTIME_MODULE:
            if not any(alias.name == _RUNTIME_VERIFIER for alias in stmt.names):
                stmt.names.append(ast.alias(name=_RUNTIME_VERIFIER))
            return

    new_import = ast.ImportFrom(
        module=_RUNTIME_MODULE,
        names=[ast.alias(name=_RUNTIME_VERIFIER)],
        level=0,
    )
    insert_at = 0
    for i, stmt in enumerate(tree.body):
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            insert_at = i + 1
        else:
            break
    tree.body.insert(insert_at, new_import)
