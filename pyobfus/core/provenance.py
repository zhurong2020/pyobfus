"""Build provenance manifest for obfuscation runs.

The manifest is intentionally local and offline-verifiable. It records the
inputs/outputs, effective configuration hash, pyobfus version, and the digest
of a mapping.json when one was produced. A canonical SHA-256 integrity digest
covers the manifest payload without requiring a network service or new
dependency.

This digest is NOT a cryptographic signature: it only proves the manifest is
internally self-consistent (the payload matches its own recorded digest). It
does not prove who produced the manifest or stop someone who can edit the
manifest file from recomputing a matching digest after tampering with it.
Real signing (e.g. sigstore) is future work; see docs/ROADMAP.md P2-17.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

from pyobfus import __version__ as PYOBFUS_VERSION
from pyobfus.config import ObfuscationConfig

PROVENANCE_FORMAT_VERSION = 1


def sha256_file(path: Union[str, Path]) -> Optional[str]:
    """Return the SHA-256 hex digest of a file, or None when it is absent."""
    p = Path(path)
    if not p.exists() or not p.is_file():
        return None
    digest = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def config_hash(config: ObfuscationConfig) -> str:
    """Hash the effective obfuscation config with stable JSON normalization."""
    payload = _normalize(config)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_provenance_manifest(
    *,
    input_root: Path,
    output_root: Path,
    config: ObfuscationConfig,
    files: Iterable[Path],
    mapping_path: Optional[Union[str, Path]],
    preset: Optional[str],
    mode: str,
) -> Dict[str, Any]:
    """Build a v1 provenance manifest payload with a local integrity digest."""
    file_records: List[Dict[str, str]] = []
    for input_file in sorted(files):
        try:
            rel = input_file.relative_to(input_root if input_root.is_dir() else input_root.parent)
        except ValueError:
            rel = Path(input_file.name)
        output_file = (
            output_root / rel if output_root.is_dir() or input_root.is_dir() else output_root
        )
        record: Dict[str, str] = {
            "input": str(input_file),
            "output": str(output_file),
            "relative_path": rel.as_posix(),
        }
        output_digest = sha256_file(output_file)
        if output_digest:
            record["output_sha256"] = output_digest
        file_records.append(record)

    mapping_digest = sha256_file(mapping_path) if mapping_path else None
    payload: Dict[str, Any] = {
        "version": PROVENANCE_FORMAT_VERSION,
        "pyobfus_version": PYOBFUS_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": {"name": "pyobfus", "version": PYOBFUS_VERSION},
        "input_root": str(input_root),
        "output_root": str(output_root),
        "mode": mode,
        "preset": preset,
        "config_hash": config_hash(config),
        "mapping": {
            "path": str(mapping_path) if mapping_path else None,
            "sha256": mapping_digest,
        },
        "files": file_records,
    }
    payload["integrity"] = _integrity_digest_for(payload)
    return payload


def save_provenance_manifest(manifest: Dict[str, Any], path: Union[str, Path]) -> None:
    """Write a provenance manifest to disk."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8"
    )


def verify_manifest_integrity(manifest: Dict[str, Any]) -> bool:
    """Check the manifest's payload matches its own recorded integrity digest.

    This detects accidental corruption (a byte flipped in transit, a partial
    write) — it is NOT tamper detection. Anyone who can edit the manifest
    file can recompute a matching digest after changing the payload, since
    there is no private key involved. Do not describe a `True` result as
    "verified" or "signed" in user-facing text.
    """
    integrity = manifest.get("integrity")
    if not isinstance(integrity, dict):
        return False
    expected = _integrity_digest_for({k: v for k, v in manifest.items() if k != "integrity"})
    return integrity == expected


def _integrity_digest_for(payload: Dict[str, Any]) -> Dict[str, str]:
    canonical = dict(payload)
    canonical.pop("integrity", None)
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return {
        "type": "sha256-canonical-json",
        "digest": digest,
        "note": (
            "Self-consistency digest, not a cryptographic signature. Detects "
            "accidental corruption; does not prove authenticity or resist "
            "deliberate tampering by anyone who can edit this file."
        ),
    }


def _normalize(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _normalize(asdict(value))
    if isinstance(value, dict):
        return {
            str(k): _normalize(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    if isinstance(value, set):
        return sorted(_normalize(v) for v in value)
    if isinstance(value, Path):
        return str(value)
    return value
