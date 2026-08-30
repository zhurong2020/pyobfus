"""Side-effect-free structured plans for ``--dry-run --json``."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from pyobfus.config import ObfuscationConfig
from pyobfus.core.provenance import config_hash
from pyobfus.utils import filter_python_files, should_exclude_file

BUILD_PLAN_VERSION = 1


def build_obfuscation_plan(
    *,
    input_path: Path,
    output_path: Path,
    config: ObfuscationConfig,
    config_source: str,
    config_path: Optional[Path],
    preset: Optional[str],
    cross_file: bool,
    mapping_path: Optional[str],
    provenance_manifest_path: Optional[str],
    trace_marker: bool,
    cwd: Path,
) -> Dict[str, Any]:
    """Describe a prospective build without exposing source or local secrets."""
    mode = "single_file" if input_path.is_file() else ("cross_file" if cross_file else "directory")
    selected: List[Dict[str, str]] = []
    excluded: List[Dict[str, str]] = []

    if input_path.is_file():
        selected.append(_file_record(input_path, input_path.parent, output_path.name))
    else:
        included = set(filter_python_files(input_path, config.exclude_patterns))
        for source_file in sorted(filter_python_files(input_path, [])):
            relative = source_file.relative_to(input_path).as_posix()
            if source_file in included:
                selected.append(_file_record(source_file, input_path, relative))
            else:
                matches = [
                    pattern
                    for pattern in config.exclude_patterns
                    if should_exclude_file(source_file, [pattern], input_path)
                ]
                excluded.append(
                    {
                        "path": relative,
                        "reason": "exclude_pattern",
                        "pattern": matches[0] if matches else "configured exclusion",
                    }
                )

    artifacts: List[Dict[str, str]] = [
        {
            "kind": "obfuscated-output",
            "role": "ship",
            "path": _safe_path_label(output_path, cwd),
        }
    ]
    if mapping_path:
        artifacts.append(
            {
                "kind": "debug-mapping",
                "role": "retain-internal",
                "path": _safe_path_label(Path(mapping_path), cwd),
            }
        )
    if provenance_manifest_path:
        artifacts.append(
            {
                "kind": "provenance-manifest",
                "role": "optional",
                "path": _safe_path_label(Path(provenance_manifest_path), cwd),
            }
        )
    if trace_marker:
        artifacts.append(
            {
                "kind": "trace-marker",
                "role": "ship",
                "path": "embedded-in-output",
            }
        )

    return {
        "version": BUILD_PLAN_VERSION,
        "mode": mode,
        "effective_config": {
            "source": config_source,
            "config_path": _safe_path_label(config_path, cwd) if config_path else None,
            "preset": preset.lower() if preset else None,
            "level": config.level,
            "config_hash": f"sha256:{config_hash(config)}",
            "exclude_patterns": list(config.exclude_patterns),
            "exclude_names_count": len(config.exclude_names),
        },
        "files": {
            "selected": selected,
            "excluded": excluded,
            "selected_count": len(selected),
            "excluded_count": len(excluded),
        },
        "artifacts": artifacts,
        "apply_supported": False,
    }


def _file_record(source_file: Path, root: Path, output_relative: str) -> Dict[str, str]:
    try:
        relative = source_file.relative_to(root).as_posix()
    except ValueError:
        relative = source_file.name
    return {"path": relative, "output": output_relative, "reason": "included"}


def _safe_path_label(path: Path, cwd: Path) -> str:
    """Return a cwd-relative label, falling back to a basename, never an absolute path."""
    try:
        return path.resolve().relative_to(cwd.resolve()).as_posix()
    except ValueError:
        return path.name
