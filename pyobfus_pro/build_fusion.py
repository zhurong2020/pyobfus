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

Scoped for 0.5.1; ``--bind-device`` / ``--period`` (runtime key substitution +
counter file) and ``--opacity-config`` TOML pattern rules are deferred to 0.5.2.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional, Tuple

from .forensic import derive_layer_key
from .transformers import opacity as _t_opacity
from .transformers import scrub as _t_scrub
from .transformers import seal as _t_seal
from .transformers import vault as _t_vault


def fusion_enabled(config) -> bool:
    """True if any 0.5.1 Pro fusion flag is set on the config."""
    return bool(
        getattr(config, "vault", False)
        or getattr(config, "selective_opacity", False)
        or getattr(config, "seal_code", False)
        or getattr(config, "scrub_traceback", False)
        or getattr(config, "expire_hard", None)
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


def apply_pre_passes(source: str, config) -> str:
    """Source transforms that must run BEFORE the Core pipeline.

    Only vault: it rewrites ``vault_secrets({...})`` into an encrypted
    ``Vault(...)`` so the secret string literals never reach Core's
    string-encoder (which would otherwise mangle them into ``_decode_str``
    calls the vault pass can no longer recognise).
    """
    if getattr(config, "vault", False):
        source, _schemas = _t_vault.transform_module(source)
    return source


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
    assignments = None
    if getattr(config, "selective_opacity", False):
        source, assignments = _t_opacity.transform_module(
            source,
            None,  # decorator-driven; TOML config channel deferred to 0.5.2
            module_qualname=module_qualname,
            layer_key=_layer_key(config, module_qualname),
        )

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


def assignments_summary(source: str) -> Tuple[int, int]:
    """(encrypted_count, total_layered) — best-effort, for verbose stats."""
    enc = source.count("_l3_dispatch(")
    return enc, enc
