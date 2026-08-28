from pathlib import Path

from pyobfus.core.config_resolve import resolve_effective_config


def test_explicit_config_wins_over_preset(tmp_path: Path) -> None:
    config_path = tmp_path / "custom.yaml"
    config_path.write_text(
        "obfuscation:\n  preset: safe\n  exclude_names: [kept_name]\n",
        encoding="utf-8",
    )

    config, provenance = resolve_effective_config(
        config_path=str(config_path),
        preset="aggressive",
        level="community",
        cwd=tmp_path,
    )

    assert "kept_name" in config.exclude_names
    assert provenance.source == "explicit-config"
    assert provenance.config_path == "custom.yaml"
    assert provenance.preset == "safe"
    assert provenance.config_hash and provenance.config_hash.startswith("sha256:")


def test_discovery_and_hash_are_stable(tmp_path: Path) -> None:
    (tmp_path / "pyobfus.yaml").write_text(
        "obfuscation:\n  exclude_patterns: [generated/**]\n",
        encoding="utf-8",
    )

    first_config, first = resolve_effective_config(
        config_path=None, preset=None, level="community", cwd=tmp_path
    )
    second_config, second = resolve_effective_config(
        config_path=None, preset=None, level="community", cwd=tmp_path
    )

    assert first.source == "auto-discovered"
    assert first_config.exclude_patterns == second_config.exclude_patterns
    assert first.config_hash == second.config_hash


def test_preset_level_default_and_no_config_sources(tmp_path: Path) -> None:
    _, preset = resolve_effective_config(
        config_path=None, preset="safe", level="community", cwd=tmp_path
    )
    _, default = resolve_effective_config(
        config_path=None, preset=None, level="community", cwd=tmp_path
    )
    _, disabled = resolve_effective_config(
        config_path=None,
        preset="safe",
        level="community",
        cwd=tmp_path,
        no_config=True,
    )

    assert (preset.source, preset.preset) == ("preset", "safe")
    assert default.source == "level-default"
    assert disabled.source == "none"
    assert disabled.config_hash is None
