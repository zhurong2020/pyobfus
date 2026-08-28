"""Shared, side-effect-free resolution of effective obfuscation config."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from pyobfus.config import ObfuscationConfig
from pyobfus.config_validator import find_config_file
from pyobfus.core.provenance import config_hash


@dataclass(frozen=True)
class ConfigProvenance:
    source: str
    config_path: Optional[str]
    preset: Optional[str]
    level: str
    config_hash: Optional[str]
    exclude_patterns: Tuple[str, ...] = ()
    exclude_names_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["exclude_patterns"] = list(self.exclude_patterns)
        return data


def resolve_effective_config(
    *,
    config_path: Optional[str],
    preset: Optional[str],
    level: str,
    cwd: Path,
    no_config: bool = False,
) -> Tuple[ObfuscationConfig, ConfigProvenance]:
    """Resolve config using the build CLI's explicit/discovery/preset precedence."""
    if no_config:
        config = ObfuscationConfig.community_edition()
        return config, ConfigProvenance("none", None, None, level, None)

    selected_path = Path(config_path) if config_path else None
    source = "explicit-config" if selected_path else ""
    if selected_path is None:
        selected_path, _ = find_config_file(start_path=cwd)
        if selected_path is not None:
            source = "auto-discovered"

    selected_preset: Optional[str] = None
    if selected_path is not None:
        config = ObfuscationConfig.from_file(selected_path)
        selected_preset = _preset_from_config_file(selected_path)
    elif preset:
        selected_preset = preset.lower()
        config = ObfuscationConfig.get_preset(selected_preset)
        source = "preset"
    else:
        config = (
            ObfuscationConfig.pro_edition()
            if level == "pro"
            else ObfuscationConfig.community_edition()
        )
        source = "level-default"

    path_label: Optional[str] = None
    if selected_path is not None:
        try:
            path_label = selected_path.resolve().relative_to(cwd.resolve()).as_posix()
        except ValueError:
            path_label = selected_path.name

    provenance = ConfigProvenance(
        source=source,
        config_path=path_label,
        preset=selected_preset,
        level=config.level,
        config_hash=f"sha256:{config_hash(config)}",
        exclude_patterns=tuple(config.exclude_patterns),
        exclude_names_count=len(config.exclude_names),
    )
    return config, provenance


def _preset_from_config_file(path: Path) -> Optional[str]:
    """Return a YAML config's optional base preset without exposing raw values."""
    if path.suffix.lower() not in {".yaml", ".yml"}:
        return None
    try:
        import yaml

        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        value = (payload.get("obfuscation") or {}).get("preset")
    except (OSError, AttributeError, yaml.YAMLError):
        return None
    return str(value).lower() if value else None
