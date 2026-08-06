"""Tests for pyobfus/config_validator.py, focused on the 2026-08-06 fix:
VALID_SCHEMA used to be hand-maintained and had drifted stale, missing
`preset` (the key `pyobfus --init` itself writes into every config it
generates) and every Pro field added since v0.5.0 -- reproduced
empirically before the fix:

    $ pyobfus --validate-config test_config.yaml
    [WARNING] Unknown configuration key: 'obfuscation.preset'
    [WARNING] Unknown configuration key: 'obfuscation.selective_opacity'
    [WARNING] Unknown configuration key: 'obfuscation.scrub_traceback'

See docs/VSCODE_EXTENSION_PLAN.md's M3 section for the full investigation.
"""

from __future__ import annotations

from pathlib import Path

from pyobfus.config_validator import validate_config_file


def _write(tmp_path: Path, text: str) -> Path:
    cfg = tmp_path / "pyobfus.yaml"
    cfg.write_text(text, encoding="utf-8")
    return cfg


def test_preset_key_is_not_flagged_unknown(tmp_path: Path) -> None:
    """The exact regression: `preset` used to be an unrecognized key even
    though `pyobfus --init` writes it into every config it generates."""
    cfg = _write(tmp_path, "obfuscation:\n  preset: balanced\n")
    result = validate_config_file(cfg)
    assert not any("preset" in w and "Unknown" in w for w in result.warnings)


def test_pro_fields_added_since_v050_are_not_flagged_unknown(tmp_path: Path) -> None:
    cfg = _write(
        tmp_path,
        "obfuscation:\n"
        "  level: pro\n"
        "  selective_opacity: true\n"
        "  scrub_traceback: true\n"
        "  vault: true\n"
        "  seal_code: true\n"
        "  requires_os: linux\n"
        "  embed_data: data.bin\n",
    )
    result = validate_config_file(cfg)
    unknown_key_warnings = [w for w in result.warnings if "Unknown configuration key" in w]
    assert unknown_key_warnings == []


def test_a_real_init_generated_config_validates_cleanly(tmp_path: Path) -> None:
    """End-to-end shape of the original bug report: --init's own output,
    fed straight into --validate-config, must produce zero warnings."""
    cfg = _write(
        tmp_path,
        "obfuscation:\n"
        "  preset: balanced\n"
        "  exclude_patterns:\n"
        "    - test_*.py\n"
        "    - '**/tests/**'\n"
        "  exclude_names: []\n"
        "  preserve_param_names: true\n"
        "  remove_docstrings: false\n",
    )
    result = validate_config_file(cfg)
    assert result.warnings == []
    assert result.errors == []


def test_genuinely_unknown_key_is_still_flagged(tmp_path: Path) -> None:
    """The fix must not turn off unknown-key detection entirely --
    something that was never a real field must still warn."""
    cfg = _write(tmp_path, "obfuscation:\n  this_key_has_never_existed: true\n")
    result = validate_config_file(cfg)
    assert any(
        "this_key_has_never_existed" in w and "Unknown" in w for w in result.warnings
    )


def test_invalid_preset_name_is_an_error(tmp_path: Path) -> None:
    cfg = _write(tmp_path, "obfuscation:\n  preset: not-a-real-preset\n")
    result = validate_config_file(cfg)
    assert any("preset" in e for e in result.errors)


def test_pro_field_without_level_pro_warns_for_every_pro_field_not_just_the_original_three(
    tmp_path: Path,
) -> None:
    """_check_pro_requirements used to hand-check only 3 fields
    (string_encryption/import_obfuscation/anti_debug). A Pro field added
    later (selective_opacity) must trigger the same "requires level: pro"
    warning now that the check is derived from config_schema instead."""
    cfg = _write(tmp_path, "obfuscation:\n  selective_opacity: true\n")
    result = validate_config_file(cfg)
    assert any("selective_opacity" in w and "level: pro" in w for w in result.warnings)


def test_level_pro_with_pro_field_produces_no_pro_requirement_warning(tmp_path: Path) -> None:
    cfg = _write(tmp_path, "obfuscation:\n  level: pro\n  selective_opacity: true\n")
    result = validate_config_file(cfg)
    assert not any("requires 'level: pro'" in w for w in result.warnings)
