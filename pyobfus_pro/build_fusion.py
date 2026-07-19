"""v0.5.1 build-orchestrator fusion.

Wires the v0.5 source-string Pro passes into the Core obfuscation pipeline at
the points proven correct by the 2026-06-18 design probe (see
``docs/V0.5_RELEASE_PLAN.md``):

    vault            -> PRE-pass  (before Core parse/mangle, so the secret
                                    literals are turned into encrypted bytes
                                    before Core's string-encoder runs)
    [ Core pipeline: mangle / string-encode / numeric / Pro AST passes ]
    opacity / seal   -> POST-pass (after Core generates the final source, so L3
                                    encryption and seal hashing capture the
                                    *final, mangled* bytecode)
    scrub / expire   -> POST-pass (independent excepthook / module-top check)

Markers in user source must use import-surviving forms so Core's name-mangler
leaves them intact: ``@opacity(Layer.ENCRYPTED)`` (enum, not a string literal),
``@seal_code``, and ``vault_secrets({...})`` (consumed by the pre-pass).

0.5.1 shipped the vault/opacity/seal/scrub/expire/fingerprint passes; 0.5.3
adds ``--period`` (module-top run-counter guard via ``period_check`` +
``default_counter_path``) and ``--opacity-config`` (opacity.toml pattern rules,
resolved PRE-mangle and applied by injecting ``@opacity(Layer.ENCRYPTED)`` so
glob patterns match original qualnames without any mangled->original name-map)
and ``--bind-device`` (encrypts the L3 layer key with a device fingerprint at
build, then rewrites the emitted ``_LAYER_KEY`` literal into a runtime
``bind_device_key(current_machine_id(), salt)`` re-derivation, so decryption only
succeeds on the bound device — supplied ``--bind-device-id`` or the build machine).

0.5.4 extends ``--bind-device`` to the String Vault: with ``--vault`` set, each
vault's ``_VAULT_KEY_<name>`` is likewise encrypted with a per-vault
device-derived key at build and rewritten into a runtime re-derivation, so vault
keys no longer ship as at-rest literals either. This runs in the vault PRE-pass
(see :func:`_apply_vault_device_binding`) because Core preserves the
``_VAULT_KEY_<name>`` constant names and imported symbols through mangling.
"""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
from typing import Optional, Tuple

from .forensic import derive_layer_key
from .transformers import opacity as _t_opacity
from .transformers import scrub as _t_scrub
from .transformers import seal as _t_seal
from .transformers import vault as _t_vault

_BUILD_SALT_SIZE = 32  # random salt per build for bind_device_key (>= 16 required)


def fusion_enabled(config) -> bool:
    """True if any 0.5.1 Pro fusion flag is set on the config."""
    return bool(
        getattr(config, "vault", False)
        or getattr(config, "selective_opacity", False)
        or getattr(config, "seal_code", False)
        or getattr(config, "scrub_traceback", False)
        or getattr(config, "expire_hard", None)
        or getattr(config, "period_max_runs", None)
        or getattr(config, "opacity_config", None)
        or getattr(config, "bind_device", False)
    )


def _layer_key(config, module_qualname: str) -> Optional[bytes]:
    """Per-buyer deterministic L3 key when ``--fingerprint`` is set, else None.

    0.5.1 anchors the watermark to ``buyer_id`` + module path (a stable,
    per-buyer-per-module key). Coupling the key to the full opacity
    assignment-hash is a 0.5.2 refinement.
    """
    fp = getattr(config, "fingerprint", None)
    if not fp:
        return None
    # derive_layer_key expects a 32-byte assignment hash. 0.5.1 uses a stable
    # per-module sha256 surrogate; the true opacity assignment-hash coupling is
    # a 0.5.2 refinement.
    module_hash = hashlib.sha256(module_qualname.encode("utf-8")).digest()
    return derive_layer_key(fp, module_hash)


def _device_key_and_salt(config) -> tuple[Optional[bytes], Optional[bytes]]:
    """``(device_key, build_salt)`` when ``--bind-device`` is set, else ``(None, None)``.

    A fresh 32-byte salt is generated per build; the key is
    ``bind_device_key(target_id, salt)`` where ``target_id`` is the supplied
    ``--bind-device-id`` (bind to a specific customer device) or, absent that,
    the build machine's own id (``current_machine_id()``; the build-on-target
    model). The ciphertext gets encrypted with this key and the emitted
    ``_LAYER_KEY`` literal is later rewritten to re-derive it at runtime.
    """
    if not getattr(config, "bind_device", False):
        return None, None
    import secrets

    from .license_binding import bind_device_key, current_machine_id

    salt = secrets.token_bytes(_BUILD_SALT_SIZE)
    target_id = getattr(config, "bind_device_id", None) or current_machine_id()
    return bind_device_key(target_id, salt), salt


def _substitute_layer_key_binding(source: str, salt: bytes) -> str:
    """Rewrite the opacity pass's ``_LAYER_KEY = b"..."`` into a runtime device
    derivation, so the raw key never ships.

    Replaces the baked constant with
    ``_LAYER_KEY = bind_device_key(current_machine_id(), _pyobfus_build_salt)``
    and inserts ``_pyobfus_build_salt`` + the import immediately before it. No-op
    if the module has no ``_LAYER_KEY`` (``--bind-device`` alone, without an L3
    layer active, has nothing to bind). Runtime decryption then only succeeds on
    the device whose id was used at build.
    """
    tree = ast.parse(source)
    idx = None
    for i, node in enumerate(tree.body):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "_LAYER_KEY"
        ):
            idx = i
            break
    if idx is None:
        return source

    # Mutate the existing assignment's RHS in place (node identity survives the
    # list-splice below, so the index shift doesn't matter).
    tree.body[idx].value = ast.Call(  # type: ignore[attr-defined]
        func=ast.Name(id="_pyobfus_bind_device_key", ctx=ast.Load()),
        args=[
            ast.Call(func=ast.Name(id="_pyobfus_machine_id", ctx=ast.Load()), args=[], keywords=[]),
            ast.Name(id="_pyobfus_build_salt", ctx=ast.Load()),
        ],
        keywords=[],
    )

    imp = ast.ImportFrom(
        module="pyobfus_pro",
        names=[
            ast.alias(name="bind_device_key", asname="_pyobfus_bind_device_key"),
            ast.alias(name="current_machine_id", asname="_pyobfus_machine_id"),
        ],
        level=0,
    )
    salt_assign = ast.Assign(
        targets=[ast.Name(id="_pyobfus_build_salt", ctx=ast.Store())],
        value=ast.Constant(value=salt),
    )
    tree.body[idx:idx] = [imp, salt_assign]

    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


_VAULT_KEY_PREFIX = "_VAULT_KEY_"


def _apply_vault_device_binding(source: str, config) -> str:
    """Run the vault PRE-pass with per-vault **device-derived** keys and rewrite
    each emitted ``_VAULT_KEY_<name>`` literal into a runtime re-derivation.

    Mirrors opacity's ``--bind-device`` handling for the *constant*
    materialization channel: each vault gets a fresh 32-byte salt, its blob is
    encrypted at build with ``bind_device_key(target_id, salt)`` (``target_id``
    = ``--bind-device-id`` or the build machine), and the baked
    ``_VAULT_KEY_<name> = b"..."`` is replaced with
    ``_VAULT_KEY_<name> = bind_device_key(current_machine_id(), _pyobfus_vault_salt_<name>)``
    so the raw key never ships and each vault decrypts only on the bound device.

    Per-vault salts (not one shared salt) keep the vault keys mutually
    independent, preserving the transformer's per-vault-key design under device
    binding. No-op device binding when the module has no vaults.
    """
    import secrets

    from .license_binding import bind_device_key, current_machine_id

    names = _t_vault.collect_vault_names(source)
    if not names:
        # --bind-device --vault on a module with no vault_secrets({...}): the
        # plain transform is a no-op too, but call it for parity / import shape.
        transformed, _schemas = _t_vault.transform_module(source)
        return transformed

    salts = {name: secrets.token_bytes(_BUILD_SALT_SIZE) for name in names}
    target_id = getattr(config, "bind_device_id", None) or current_machine_id()
    vault_keys = {name: bind_device_key(target_id, salts[name]) for name in names}
    transformed, _schemas = _t_vault.transform_module(source, vault_keys=vault_keys)
    return _substitute_vault_key_bindings(transformed, salts)


def _vault_key_target_name(node: ast.stmt) -> Optional[str]:
    """Return ``<name>`` for a ``_VAULT_KEY_<name> = ...`` assignment, else None."""
    if (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id.startswith(_VAULT_KEY_PREFIX)
    ):
        return node.targets[0].id[len(_VAULT_KEY_PREFIX) :]
    return None


def _substitute_vault_key_bindings(source: str, salts: dict) -> str:
    """Rewrite each ``_VAULT_KEY_<name> = b"..."`` into a device re-derivation.

    For every vault named in ``salts`` the baked key literal becomes
    ``bind_device_key(current_machine_id(), _pyobfus_vault_salt_<name>)`` and a
    ``_pyobfus_vault_salt_<name> = b"..."`` assignment is inserted immediately
    before it. A single import of the two runtime helpers is prepended once
    (after any ``from __future__`` imports). No-op if no matching key literal is
    present.
    """
    tree = ast.parse(source)
    new_body: list[ast.stmt] = []
    injected = False
    for node in tree.body:
        vault_name = _vault_key_target_name(node)
        if vault_name is not None and vault_name in salts:
            salt_name = f"_pyobfus_vault_salt_{vault_name}"
            new_body.append(
                ast.Assign(
                    targets=[ast.Name(id=salt_name, ctx=ast.Store())],
                    value=ast.Constant(value=salts[vault_name]),
                )
            )
            node.value = ast.Call(  # type: ignore[attr-defined]
                func=ast.Name(id="_pyobfus_bind_device_key", ctx=ast.Load()),
                args=[
                    ast.Call(
                        func=ast.Name(id="_pyobfus_machine_id", ctx=ast.Load()),
                        args=[],
                        keywords=[],
                    ),
                    ast.Name(id=salt_name, ctx=ast.Load()),
                ],
                keywords=[],
            )
            injected = True
        new_body.append(node)

    if not injected:
        return source

    tree.body = new_body
    _ensure_bind_device_import(tree)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


def _ensure_bind_device_import(tree: ast.Module) -> None:
    """Prepend ``from pyobfus_pro import bind_device_key as _pyobfus_bind_device_key,
    current_machine_id as _pyobfus_machine_id`` once, after any ``from __future__``
    imports. Idempotent on the aliased names."""
    have = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                have.add(alias.asname or alias.name)
    if {"_pyobfus_bind_device_key", "_pyobfus_machine_id"} <= have:
        return
    imp = ast.ImportFrom(
        module="pyobfus_pro",
        names=[
            ast.alias(name="bind_device_key", asname="_pyobfus_bind_device_key"),
            ast.alias(name="current_machine_id", asname="_pyobfus_machine_id"),
        ],
        level=0,
    )
    insert_at = 0
    for i, node in enumerate(tree.body):
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            insert_at = i + 1
        else:
            break
    tree.body.insert(insert_at, imp)


def apply_pre_passes(source: str, config, *, module_qualname: str = "") -> str:
    """Source transforms that must run BEFORE the Core pipeline.

    - **vault**: rewrites ``vault_secrets({...})`` into an encrypted
      ``Vault(...)`` so the secret string literals never reach Core's
      string-encoder (which would otherwise mangle them into ``_decode_str``
      calls the vault pass can no longer recognise).
    - **opacity-config**: resolves each top-level function's layer against the
      ``opacity.toml`` rules using its *pre-mangle* qualname, then injects an
      ``@opacity(Layer.ENCRYPTED)`` decorator on ENCRYPTED matches. Running here
      (before Core mangles) is what lets glob patterns match original qualnames;
      the injected decorator survives mangling and is consumed by the opacity
      POST-pass exactly like a hand-written one. This sidesteps any
      mangled->original name-map coupling.

    When ``--bind-device`` is set the vault pass encrypts each vault with a
    device-derived key and rewrites its emitted ``_VAULT_KEY_<name>`` literal
    into a runtime re-derivation (see :func:`_apply_vault_device_binding`), so
    the vault keys never ship as at-rest constants. The rewrite is done here in
    the PRE-pass rather than the POST-pass because Core preserves both the
    ``_VAULT_KEY_<name>`` constant names and imported symbols unchanged, so the
    injected ``bind_device_key(...)`` derivation survives mangling intact.
    """
    if getattr(config, "vault", False):
        if getattr(config, "bind_device", False):
            source = _apply_vault_device_binding(source, config)
        else:
            source, _schemas = _t_vault.transform_module(source)
    if getattr(config, "opacity_config", None):
        source = _apply_opacity_config_prepass(source, config, module_qualname)
    return source


def _is_opacity_decorator_node(dec: ast.expr) -> bool:
    """True for ``@opacity(...)`` / ``<x>.opacity(...)`` (mirrors the opacity pass)."""
    if not isinstance(dec, ast.Call):
        return False
    func = dec.func
    if isinstance(func, ast.Name):
        return func.id == "opacity"
    if isinstance(func, ast.Attribute):
        return func.attr == "opacity"
    return False


def _apply_opacity_config_prepass(source: str, config, module_qualname: str) -> str:
    """Inject ``@opacity(Layer.ENCRYPTED)`` on top-level functions the opacity
    config resolves to the ENCRYPTED layer (matched by *pre-mangle* qualname).

    Functions that already carry a hand-written ``@opacity(...)`` are left alone
    (the explicit decorator wins). If no function resolves to ENCRYPTED the
    source is returned unchanged. Emits ``from pyobfus_pro import opacity, Layer``
    once when at least one decorator is injected. Non-ENCRYPTED layers are not
    acted on here (in fusion ordering the opacity pass runs post-mangle and only
    materialises L3 encryption; other layers fall through to Core's default
    mangling).
    """
    from .opacity.config import OpacityConfig
    from .opacity.layers import Layer
    from .opacity.patterns import Resolver

    cfg_path = getattr(config, "opacity_config", None)
    if not cfg_path:  # defensive: apply_pre_passes only calls us when set
        return source
    opacity_cfg = OpacityConfig.from_toml(cfg_path)
    resolver = Resolver(opacity_cfg)

    tree = ast.parse(source)
    injected = 0
    for stmt in tree.body:
        if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if any(_is_opacity_decorator_node(d) for d in stmt.decorator_list):
            continue  # hand-written @opacity wins; don't double-assign
        qualname = f"{module_qualname}.{stmt.name}" if module_qualname else stmt.name
        if resolver.resolve(qualname, decorator_layer=None) is Layer.ENCRYPTED:
            stmt.decorator_list.insert(
                0,
                ast.Call(
                    func=ast.Name(id="opacity", ctx=ast.Load()),
                    args=[
                        ast.Attribute(
                            value=ast.Name(id="Layer", ctx=ast.Load()),
                            attr="ENCRYPTED",
                            ctx=ast.Load(),
                        )
                    ],
                    keywords=[],
                ),
            )
            injected += 1

    if not injected:
        return source

    _ensure_opacity_imports(tree)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


def _ensure_opacity_imports(tree: ast.Module) -> None:
    """Prepend ``from pyobfus_pro import opacity, Layer`` unless both names are
    already imported. Inserted after any ``from __future__`` imports (which must
    stay first)."""
    have = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                have.add(alias.asname or alias.name)
    if {"opacity", "Layer"} <= have:
        return
    imp = ast.ImportFrom(
        module="pyobfus_pro",
        names=[ast.alias(name="opacity", asname=None), ast.alias(name="Layer", asname=None)],
        level=0,
    )
    insert_at = 0
    for i, node in enumerate(tree.body):
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            insert_at = i + 1
        else:
            break
    tree.body.insert(insert_at, imp)


def apply_post_passes(
    source: str,
    config,
    *,
    module_qualname: str = "",
    scrub_key_path: Optional[Path] = None,
) -> str:
    """Source transforms that must run AFTER Core generates the final source.

    Order: opacity (encrypt final mangled bytecode) -> seal (hash final
    bytecode / ciphertext for L3) -> scrub (excepthook) -> expire check.
    """
    # --bind-device: derive the L3 layer key from a device fingerprint. The
    # ciphertext is encrypted at build with bind_device_key(target_id, salt), and
    # the emitted `_LAYER_KEY = b"..."` literal is rewritten (below) into a
    # runtime re-derivation, so the raw key never ships and decryption only
    # succeeds on the matching device (P2-8).
    device_key, device_salt = _device_key_and_salt(config)

    assignments = None
    if getattr(config, "selective_opacity", False) or getattr(config, "opacity_config", None):
        # Decorator-driven: both hand-written @opacity and the decorators the
        # opacity-config PRE-pass injected (by pre-mangle qualname) are consumed
        # here. Passing config=None keeps this pass purely decorator-based; the
        # TOML rules already did their work pre-mangle.
        effective_key = (
            device_key if device_key is not None else _layer_key(config, module_qualname)
        )
        source, assignments = _t_opacity.transform_module(
            source,
            None,
            module_qualname=module_qualname,
            layer_key=effective_key,
        )
        if device_key is not None and device_salt is not None:
            source = _substitute_layer_key_binding(source, device_salt)

    if getattr(config, "seal_code", False):
        source = _t_seal.transform_module(
            source,
            layer_assignments=assignments,
            module_qualname=module_qualname,
        )

    if getattr(config, "scrub_traceback", False):
        if scrub_key_path is None:
            raise ValueError("scrub_traceback requires scrub_key_path")
        _priv_pem, pub_pem = _t_scrub.load_or_generate_keypair(scrub_key_path)
        source = _t_scrub.transform_module(source, pub_pem)

    expire = getattr(config, "expire_hard", None)
    if expire:
        source = _inject_expire_check(source, expire)

    period = getattr(config, "period_max_runs", None)
    if period:
        source = _inject_period_check(source, module_qualname, int(period))

    return source


def _inject_expire_check(source: str, expire_iso: str) -> str:
    """Inject a module-top ``expire_check("<iso>")`` (P2-8 expiry subset).

    Refuses to import past the date; raises ``LicenseExpired`` from
    ``pyobfus_pro.license_binding``. Idempotent on a marker comment.
    """
    marker = "# pyobfus:expire"
    if marker in source:
        return source
    header = (
        f"{marker}\n"
        "from pyobfus_pro import expire_check as _pyobfus_expire_check\n"
        f"_pyobfus_expire_check({expire_iso!r})\n"
    )
    # Place after a leading shebang / encoding cookie / module docstring block
    # is unnecessary here: expire must run at import, and a plain module-top
    # statement is fine because Core has already emitted a clean module.
    return header + source


def _inject_period_check(source: str, module_qualname: str, max_runs: int) -> str:
    """Inject a module-top ``period_check(default_counter_path(id), N)`` (P2-8 run-counter subset).

    Refuses to import once the artifact's run counter exceeds ``max_runs``;
    raises ``LicenseExpired`` from ``pyobfus_pro.license_binding``. The counter
    path is resolved at *runtime* on the end-user's machine (never baked in at
    build time) via ``default_counter_path``, keyed by a stable per-module
    artifact id (truncated sha256 of the qualname), so distinct modules keep
    independent counters. Idempotent on a marker comment.
    """
    marker = "# pyobfus:period"
    if marker in source:
        return source
    artifact_id = hashlib.sha256((module_qualname or "module").encode("utf-8")).hexdigest()[:16]
    header = (
        f"{marker}\n"
        "from pyobfus_pro import period_check as _pyobfus_period_check, "
        "default_counter_path as _pyobfus_counter_path\n"
        f"_pyobfus_period_check(_pyobfus_counter_path({artifact_id!r}), {int(max_runs)})\n"
    )
    return header + source


def assignments_summary(source: str) -> Tuple[int, int]:
    """(encrypted_count, total_layered) — best-effort, for verbose stats."""
    enc = source.count("_l3_dispatch(")
    return enc, enc
