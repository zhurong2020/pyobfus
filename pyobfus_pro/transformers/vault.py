"""Build-pass AST transformer for P2-11 Runtime String Vault (W3-C).

Walks a module's AST top-level for the marker pattern::

    SECRETS = vault_secrets({
        "STRIPE_KEY": "sk_live_xxx",
        "DB_PASS":   "hunter2",
    })

and replaces the marker call with three baked statements::

    _VAULT_KEY_SECRETS  = b"<32 random bytes>"
    _VAULT_BLOB_SECRETS = {"STRIPE_KEY": b"<nonce||cipher||tag>", ...}
    SECRETS = Vault(_VAULT_BLOB_SECRETS, _VAULT_KEY_SECRETS)

The build-baked key persists across process restarts so the same obfuscated
artifact decrypts the same secrets every run, in contrast to the development
behavior of :func:`pyobfus_pro.runtime.vault_secrets` (per-process
random key).

Single source of truth for the encryption rule: this transformer calls
:meth:`Vault.encrypt_entries` from the runtime module rather than
re-implementing AES-GCM here, so build and runtime cannot drift on
nonce-size, key-size, or GCM-tag layout. Same family-rule discipline as
P2-1 W3-B (`_encrypt_code` shared with `_l3_dispatch`) and P2-9 W1
(`_compute_seal` shared between transformer and runtime).

Coupling to P2-1 (constant-materialization channel):

This transformer is the *constant* analogue of :func:`opacity.transform_module`'s
*function-body* L3 path. Both share the AES-256-GCM construction (12-byte
nonce, 32-byte key, GCM tag) but emit different module shapes:

- ``opacity`` L3: per-function ``_CIPHER_<name>`` bytes constant +
  ``_LAYER_KEY`` shared module key + body replaced with stub +
  ``@_l3_dispatch`` decorator.
- ``vault`` (this module): per-vault ``_VAULT_BLOB_<name>`` dict-of-bytes
  constant + per-vault ``_VAULT_KEY_<name>`` 32-byte constant + Vault
  construction call.

P2-1's ``LayerSpec.materialization`` field (``"function_body"`` vs
``"constant"``) is the static contract that names the two channels. The
patent main combination claim spans both -- a single layer framework with
two materialization modalities. See PATENT_NOTES.md P2-1 / P2-11 sections.

W3-C v1 limitations (lifted in future milestones):

- Only top-level ``<NAME> = vault_secrets({...literal...})`` patterns are
  detected. Computed dicts, dict-merges, dynamic keys, or nested-call
  arguments raise :class:`VaultBuildError`.
- All entry keys + values must be string literals. Numbers, bytes, None,
  or expressions raise.
- One vault per module attribute name. Re-assigning the same name twice
  raises (avoids ambiguous build state).

Patent-gated. See ``../runtime/vault.py`` for the runtime side and
``PATENT_NOTES.md`` P2-11 section for the inventive-step framing.
"""

from __future__ import annotations

import ast
import secrets
from collections.abc import Iterable

from pyobfus_pro.runtime.vault import Vault

_RUNTIME_MODULE = "pyobfus_pro.runtime"
_RUNTIME_VAULT_CLASS = "Vault"
_MARKER_NAME = "vault_secrets"
_VAULT_KEY_PREFIX = "_VAULT_KEY_"
_VAULT_BLOB_PREFIX = "_VAULT_BLOB_"
_VAULT_KEY_SIZE = 32  # AES-256


class VaultBuildError(ValueError):
    """Raised when the vault_secrets build pass cannot transform the source.

    Reasons include: non-literal dict argument, non-string key or value,
    duplicate vault attribute name in the same module.
    """


def transform_module(
    source_code: str,
    *,
    vault_keys: dict[str, bytes] | None = None,
    filename: str = "<vault-pass>",
) -> tuple[str, dict[str, list[str]]]:
    """Apply the P2-11 W3-C vault build pass to a module source.

    Args:
        source_code: Python source text.
        vault_keys: Optional ``{vault_name: 32-byte-key}`` mapping. When a
            name is present, that key is used; when absent, a fresh random
            key is generated. Production builds typically pass ``None``
            (per-build random per vault); the parameter exists for tests +
            future P2-8 ``--bind-device`` integration where the key is
            derived from a device fingerprint.
        filename: Used for ``ast.parse`` error messages.

    Returns:
        ``(transformed_source, vault_schemas)`` where ``vault_schemas`` maps
        each vault attribute name to its list of entry names. The schema is
        the published interface for downstream tooling that wants to know
        what secret names exist without decrypting (matches the
        ``Vault.names()`` schema-without-decryption discipline).

        If no ``vault_secrets({...})`` patterns are found, the source is
        returned unchanged with an empty schema map.

    Raises:
        VaultBuildError: on non-literal dict, non-string entries, or
            duplicate vault names.
        SyntaxError: when ``source_code`` is not valid Python.
        ValueError: when a supplied ``vault_keys`` value is not 32 bytes.
    """
    keys_input = vault_keys or {}
    for name, key in keys_input.items():
        if not isinstance(key, (bytes, bytearray)) or len(key) != _VAULT_KEY_SIZE:
            raise ValueError(f"vault_keys[{name!r}] must be exactly {_VAULT_KEY_SIZE} bytes")

    tree = ast.parse(source_code, filename)
    targets = _collect_vault_assignments(tree)
    if not targets:
        return source_code, {}

    # Build emitted statements per vault target. Maintain insertion order
    # so the ast.unparse output is stable.
    schemas: dict[str, list[str]] = {}
    encrypted_artifacts: dict[
        ast.Assign,
        tuple[str, bytes, dict[str, bytes], list[str]],
    ] = {}
    for assign_node, (vault_name, plaintext_entries) in targets.items():
        if vault_name in schemas:
            raise VaultBuildError(
                f"vault attribute {vault_name!r} is assigned more than once "
                f"in this module; v1 requires a single vault per name"
            )
        key = keys_input.get(vault_name) or secrets.token_bytes(_VAULT_KEY_SIZE)
        encrypted_blob = Vault.encrypt_entries(plaintext_entries, key)
        schemas[vault_name] = list(plaintext_entries.keys())
        encrypted_artifacts[assign_node] = (
            vault_name,
            bytes(key),
            encrypted_blob,
            list(plaintext_entries.keys()),
        )

    new_body: list[ast.stmt] = []
    for stmt in tree.body:
        if not (isinstance(stmt, ast.Assign) and stmt in encrypted_artifacts):
            new_body.append(stmt)
            continue

        vault_name, key_bytes, encrypted_blob, entry_names = encrypted_artifacts[stmt]
        key_const_name = f"{_VAULT_KEY_PREFIX}{vault_name}"
        blob_const_name = f"{_VAULT_BLOB_PREFIX}{vault_name}"

        # _VAULT_KEY_<name> = b"..."
        key_assign = ast.Assign(
            targets=[ast.Name(id=key_const_name, ctx=ast.Store())],
            value=ast.Constant(value=key_bytes),
        )
        # _VAULT_BLOB_<name> = {entry_name: cipher_bytes, ...}
        # Preserves the insertion order of the original literal so callers
        # who rely on Vault.names() ordering see the same shape.
        blob_assign = ast.Assign(
            targets=[ast.Name(id=blob_const_name, ctx=ast.Store())],
            value=ast.Dict(
                keys=[ast.Constant(value=name) for name in entry_names],
                values=[ast.Constant(value=encrypted_blob[name]) for name in entry_names],
            ),
        )
        # <NAME> = Vault(_VAULT_BLOB_<name>, _VAULT_KEY_<name>)
        construct_assign = ast.Assign(
            targets=[ast.Name(id=vault_name, ctx=ast.Store())],
            value=ast.Call(
                func=ast.Name(id=_RUNTIME_VAULT_CLASS, ctx=ast.Load()),
                args=[
                    ast.Name(id=blob_const_name, ctx=ast.Load()),
                    ast.Name(id=key_const_name, ctx=ast.Load()),
                ],
                keywords=[],
            ),
        )
        new_body.extend([key_assign, blob_assign, construct_assign])

    tree.body = new_body
    _ensure_vault_class_import(tree)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree), schemas


# ---------------------------------------------------------------------------
# Pattern detection
# ---------------------------------------------------------------------------


def _is_vault_secrets_call(node: ast.expr) -> bool:
    """Match ``vault_secrets(...)`` (bare) or ``<...>.vault_secrets(...)``."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name):
        return func.id == _MARKER_NAME
    if isinstance(func, ast.Attribute):
        return func.attr == _MARKER_NAME
    return False


def _collect_vault_assignments(
    tree: ast.Module,
) -> dict[ast.Assign, tuple[str, dict[str, str]]]:
    """Find top-level ``<NAME> = vault_secrets({...literal...})`` assignments.

    Returns ``{Assign-node: (vault_name, plaintext_entries_dict)}``. Each
    Assign's RHS is validated and normalized: literal Dict, all-string
    keys, all-string values. Anything else raises ``VaultBuildError``.
    """
    result: dict[ast.Assign, tuple[str, dict[str, str]]] = {}
    for stmt in tree.body:
        if not isinstance(stmt, ast.Assign):
            continue
        if not _is_vault_secrets_call(stmt.value):
            continue
        # v1 scope: single Name target on the LHS.
        if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
            raise VaultBuildError(
                f"vault_secrets(...) assignment must target a single "
                f"module attribute name; got "
                f"{ast.dump(stmt.targets[0]) if stmt.targets else 'no target'}"
            )
        vault_name = stmt.targets[0].id
        call = stmt.value
        # ``_is_vault_secrets_call`` only returns True for ast.Call nodes,
        # so this check is type-safe by construction; the cast is for
        # the type-checker (and, less importantly, ruff S101).
        if not isinstance(call, ast.Call):  # pragma: no cover -- unreachable
            raise VaultBuildError(
                f"vault_secrets on {vault_name!r}: internal -- " f"expected Call node"
            )
        if len(call.args) != 1 or call.keywords:
            raise VaultBuildError(
                f"vault_secrets(...) on {vault_name!r} must take exactly "
                f"one positional dict argument"
            )
        dict_node = call.args[0]
        if not isinstance(dict_node, ast.Dict):
            raise VaultBuildError(
                f"vault_secrets(...) on {vault_name!r} argument must be a "
                f"dict literal at build time; got "
                f"{type(dict_node).__name__}. Computed dicts are not "
                f"supported in v1."
            )
        plaintext = _validate_literal_str_dict(vault_name, dict_node)
        result[stmt] = (vault_name, plaintext)
    return result


def _validate_literal_str_dict(vault_name: str, node: ast.Dict) -> dict[str, str]:
    """Walk a Dict literal, requiring all-string keys and all-string values.

    Returns ``{plaintext_key: plaintext_value}`` preserving source order.
    Raises ``VaultBuildError`` on any non-literal-string entry.
    """
    if any(k is None for k in node.keys):
        raise VaultBuildError(
            f"vault_secrets({vault_name!r}) does not support **-unpacking " f"in the dict literal"
        )
    out: dict[str, str] = {}
    for key_node, value_node in zip(node.keys, node.values, strict=True):
        if not (isinstance(key_node, ast.Constant) and isinstance(key_node.value, str)):
            raise VaultBuildError(
                f"vault_secrets({vault_name!r}) entry key must be a string "
                f"literal; got {type(key_node).__name__}"
            )
        if not (isinstance(value_node, ast.Constant) and isinstance(value_node.value, str)):
            raise VaultBuildError(
                f"vault_secrets({vault_name!r}) entry {key_node.value!r} "
                f"value must be a string literal; got "
                f"{type(value_node).__name__}"
            )
        if key_node.value in out:
            raise VaultBuildError(
                f"vault_secrets({vault_name!r}) has duplicate entry name " f"{key_node.value!r}"
            )
        out[key_node.value] = value_node.value
    return out


# ---------------------------------------------------------------------------
# Import injection
# ---------------------------------------------------------------------------


def _ensure_vault_class_import(tree: ast.Module) -> None:
    """Inject ``from pyobfus_pro.runtime import Vault`` once.

    If ``pyobfus_pro.runtime`` is already imported, append ``Vault`` to
    its alias list; otherwise insert a new import after the leading import
    block. Aligns with the ``_ensure_runtime_import`` helpers in seal.py /
    opacity.py.
    """
    for stmt in tree.body:
        if isinstance(stmt, ast.ImportFrom) and stmt.module == _RUNTIME_MODULE:
            if not any(alias.name == _RUNTIME_VAULT_CLASS for alias in stmt.names):
                stmt.names.append(ast.alias(name=_RUNTIME_VAULT_CLASS))
            return

    new_import = ast.ImportFrom(
        module=_RUNTIME_MODULE,
        names=[ast.alias(name=_RUNTIME_VAULT_CLASS)],
        level=0,
    )
    insert_at = 0
    for i, stmt in enumerate(tree.body):
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            insert_at = i + 1
        else:
            break
    tree.body.insert(insert_at, new_import)


__all__: Iterable[str] = ("VaultBuildError", "transform_module")
