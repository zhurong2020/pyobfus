"""Deterministic, privacy-safe facts about a completed obfuscation build."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Union

from pyobfus import __version__ as PYOBFUS_VERSION

BUILD_REPORT_FORMAT = "pyobfus-build-report"
BUILD_REPORT_VERSION = 1


def build_report(
    *,
    plan: Mapping[str, Any],
    output_path: Path,
    stats: Mapping[str, int],
    verification: Optional[Mapping[str, Any]],
    provenance_manifest_path: Optional[Union[str, Path]],
    cwd: Path,
    cache_hit: bool = False,
) -> Dict[str, Any]:
    """Build the v1 fact model without exposing source text or absolute paths."""
    output_files = _output_records(output_path)
    manifest_label = (
        _safe_path_label(Path(provenance_manifest_path), cwd) if provenance_manifest_path else None
    )
    return {
        "format": BUILD_REPORT_FORMAT,
        "version": BUILD_REPORT_VERSION,
        "tool": {"name": "pyobfus", "version": PYOBFUS_VERSION},
        "state": "completed",
        "mode": plan["mode"],
        "effective_config": _effective_config_facts(plan["effective_config"]),
        "selection": _selection_facts(plan["files"]),
        "transformations": {key: stats[key] for key in sorted(stats)},
        "cache": {
            "hit": cache_hit,
            "files_processed": stats.get("files_processed", 0),
            "files_skipped": stats.get("files_skipped", 0),
            "reason": "inputs-and-config-unchanged" if cache_hit else "rebuilt",
        },
        "verification": (
            dict(verification)
            if verification is not None
            else {
                "requested": False,
                "mode": "none",
                "execution_performed": False,
            }
        ),
        "outputs": {
            "files": output_files,
            "file_count": len(output_files),
            "total_bytes": sum(record["size_bytes"] for record in output_files),
        },
        "artifacts": plan["artifacts"],
        "output_marker": plan["output_marker"],
        "provenance": {"manifest": manifest_label},
        "privacy": {
            "paths": "relative-or-basename",
            "source_content_included": False,
            "secrets_included": False,
        },
    }


def save_build_report(report: Mapping[str, Any], path: Union[str, Path]) -> None:
    """Atomically write a canonical, reproducible JSON report."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(encoded, encoding="utf-8")
        temporary.replace(destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def _output_records(output_path: Path) -> List[Dict[str, Any]]:
    if output_path.is_file():
        targets = [output_path]
        root = output_path.parent
    elif output_path.is_dir():
        targets = sorted(output_path.rglob("*.py"))
        root = output_path
    else:
        targets = []
        root = output_path.parent

    records: List[Dict[str, Any]] = []
    for target in targets:
        records.append(
            {
                "path": _safe_path_label(target, root),
                "sha256": _sha256_file(target),
                "size_bytes": target.stat().st_size,
                "role": "obfuscated-output",
            }
        )
    return records


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _effective_config_facts(config: Mapping[str, Any]) -> Dict[str, Any]:
    """Keep decision facts while excluding user-authored pattern contents."""
    return {
        "source": config.get("source"),
        "config_path": config.get("config_path"),
        "preset": config.get("preset"),
        "level": config.get("level"),
        "config_hash": config.get("config_hash"),
        "exclude_patterns_count": len(config.get("exclude_patterns", [])),
        "exclude_names_count": config.get("exclude_names_count", 0),
    }


def _selection_facts(files: Mapping[str, Any]) -> Dict[str, Any]:
    """Copy path/reason facts without echoing configured pattern strings."""
    selected = [
        {key: record[key] for key in ("path", "output", "reason") if key in record}
        for record in files.get("selected", [])
    ]
    excluded = [
        {key: record[key] for key in ("path", "reason") if key in record}
        for record in files.get("excluded", [])
    ]
    return {
        "selected": selected,
        "excluded": excluded,
        "selected_count": files.get("selected_count", len(selected)),
        "excluded_count": files.get("excluded_count", len(excluded)),
    }


def _safe_path_label(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name
