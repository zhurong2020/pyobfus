"""
Incremental-build cache for pyobfus.

Scope of this MVP: **project-level skip-if-unchanged**. When the user
passes `--incremental`, a manifest at `<output_dir>/.pyobfus-cache/
manifest.json` records the set of input files, their content hashes,
and the obfuscation config that produced the last build. On the next
run, if nothing relevant changed *and* every output file still exists,
pyobfus skips the obfuscation step entirely. Otherwise it falls back
to a full rebuild and refreshes the manifest.

Why project-level and not per-file: with cross-file obfuscation the
global symbol table depends on every file. Reusing a single file's
obfuscated output while its peers changed is unsafe — the renamed
identifiers must stay consistent across imports. Project-level
incremental is the largest safe unit.

Typical win: zero-change CI reruns become ~O(scan) instead of
O(scan + transform + write). File-level caching can layer on top in
a future release.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from pyobfus import __version__ as PYOBFUS_VERSION

CACHE_DIR_NAME = ".pyobfus-cache"
MANIFEST_NAME = "manifest.json"
MANIFEST_VERSION = 1


@dataclass
class CacheHit:
    """Returned when a previous build can be reused verbatim."""

    files_skipped: int
    manifest_path: Path


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _config_signature(config_fields: Dict) -> str:
    """Stable hash of the config fields that influence output bytes."""
    payload = json.dumps(config_fields, sort_keys=True, default=_json_default)
    return _sha256_text(payload)


def _json_default(obj: object) -> object:
    # Sets aren't JSON-serializable; convert to sorted lists for stability.
    if isinstance(obj, set):
        return sorted(obj)
    if isinstance(obj, frozenset):
        return sorted(obj)
    raise TypeError(f"Unserializable type for config signature: {type(obj)!r}")


def _extract_config_fields(config: object) -> Dict:
    """Pull out every field of ObfuscationConfig that can affect output."""
    # These are the knobs that change the obfuscator's behavior. Missing
    # attributes are tolerated so this stays forward-compatible.
    keys = (
        "level",
        "exclude_patterns",
        "exclude_names",
        "name_prefix",
        "remove_docstrings",
        "remove_comments",
        "string_encoding",
        "preserve_param_names",
        "string_encryption",
        "anti_debug",
        "control_flow_flattening",
        "dead_code_injection",
        "license_expire",
        "license_bind_machine",
        "license_max_runs",
    )
    out: Dict = {}
    for key in keys:
        if hasattr(config, key):
            value = getattr(config, key)
            # Normalize unordered containers
            if isinstance(value, set):
                value = sorted(value)
            elif isinstance(value, list):
                value = list(value)
            out[key] = value
    return out


class BuildCache:
    """Project-level skip-if-unchanged cache."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = Path(output_dir)
        self.cache_dir = self.output_dir / CACHE_DIR_NAME
        self.manifest_path = self.cache_dir / MANIFEST_NAME

    # ---- signatures --------------------------------------------------

    def build_signature(
        self,
        input_dir: Path,
        input_files: Iterable[Path],
        config: object,
    ) -> Dict:
        """Compute a dict of hashes describing the inputs + config.

        The dict itself (sorted keys) is the signature; callers compare it
        to the one stored in the manifest.
        """
        files_map: Dict[str, str] = {}
        for f in sorted(input_files, key=lambda p: str(p)):
            try:
                rel = str(f.relative_to(input_dir))
            except ValueError:
                rel = str(f)
            files_map[rel] = _sha256_file(f)

        return {
            "pyobfus_version": PYOBFUS_VERSION,
            "input_dir": str(input_dir),
            "config": _extract_config_fields(config),
            "files": files_map,
        }

    # ---- manifest I/O ------------------------------------------------

    def load_manifest(self) -> Optional[Dict]:
        if not self.manifest_path.exists():
            return None
        try:
            data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if data.get("version") != MANIFEST_VERSION:
            return None
        return data

    def save_manifest(self, signature: Dict, output_files: List[str]) -> None:
        """Persist the manifest after a successful full build."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": MANIFEST_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "signature": signature,
            "output_files": sorted(output_files),
        }
        self.manifest_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )

    # ---- hit detection ----------------------------------------------

    def can_reuse(
        self,
        current_signature: Dict,
    ) -> Tuple[bool, str, Optional[List[str]]]:
        """Return (hit, reason, cached_outputs)."""
        manifest = self.load_manifest()
        if manifest is None:
            return False, "no manifest (first run or cache cleared)", None

        if manifest.get("signature") != current_signature:
            return False, "inputs or config changed", None

        cached_outputs: List[str] = manifest.get("output_files", [])
        # Verify every cached output file still exists on disk
        missing = [p for p in cached_outputs if not Path(p).exists()]
        if missing:
            return (
                False,
                f"{len(missing)} cached output file(s) missing",
                None,
            )

        return True, "inputs, config, and outputs all unchanged", cached_outputs
