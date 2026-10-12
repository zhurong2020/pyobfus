"""Build-fusion option bookkeeping shared by the CLI and the build plan.

The Pro build-fusion passes (opacity, seal, vault, scrub, policy checks,
embedded data, key binding) run on generated single-file source. This module
only knows which ``ObfuscationConfig`` fields request them and which
combinations are contradictory; the mechanisms themselves stay in
``pyobfus_pro``. Checks run on the merged configuration so YAML and CLI values
are treated the same.
"""

from typing import Any, List, Tuple

# Config fields that request a build-fusion pass. Every field here is skipped
# in cross-file directory mode; keep in sync with pyobfus_pro.build_fusion.
FUSION_FIELDS: Tuple[str, ...] = (
    "selective_opacity",
    "opacity_config",
    "seal_code",
    "vault",
    "scrub_traceback",
    "fingerprint",
    "expire_hard",
    "period_max_runs",
    "bind_device",
    "bind_key_env",
    "requires_os",
    "requires_python_min",
    "requires_arch",
    "embed_data",
)


def requested_fusion_fields(config: Any) -> List[str]:
    """Return the fusion fields that are set on ``config``, in FUSION_FIELDS order."""
    return [name for name in FUSION_FIELDS if getattr(config, name, None)]


def _has_l3(config: Any) -> bool:
    return bool(
        getattr(config, "selective_opacity", False) or getattr(config, "opacity_config", None)
    )


def check_fusion_combinations(config: Any) -> Tuple[List[str], List[str]]:
    """Return ``(errors, warnings)`` for contradictory fusion settings.

    Errors are combinations that would ship something other than what was
    asked for (for example a vault key baked into the artifact while the user
    expects the application to supply it). Warnings are options that build but
    silently do nothing in the given combination.
    """
    errors: List[str] = []
    warnings: List[str] = []
    bind_key_env = getattr(config, "bind_key_env", None)
    bind_device = bool(
        getattr(config, "bind_device", False) or getattr(config, "bind_device_id", None)
    )
    fingerprint = getattr(config, "fingerprint", None)

    if bind_key_env:
        if bind_device:
            errors.append(
                "bind_key_env cannot be combined with bind_device / bind_device_id; "
                "they bind the same L3 key to different sources."
            )
        if not _has_l3(config):
            errors.append(
                "bind_key_env requires an L3 layer (selective_opacity or opacity_config)."
            )
        if getattr(config, "vault", False):
            errors.append(
                "bind_key_env does not yet cover Runtime String Vault keys; "
                "remove vault or use bind_device."
            )

    if fingerprint:
        if not _has_l3(config):
            warnings.append(
                "fingerprint has no effect without an L3 layer "
                "(selective_opacity or opacity_config); no buyer key is emitted."
            )
        elif bind_key_env or bind_device:
            warnings.append(
                "fingerprint has no effect together with bind_key_env / bind_device: "
                "the bound key replaces the per-buyer key, so the build cannot be "
                "matched to a buyer afterwards."
            )

    if getattr(config, "expire_warn_days", None) is not None and not getattr(
        config, "expire_hard", None
    ):
        errors.append("expire_warn_days requires expire_hard.")

    return errors, warnings
