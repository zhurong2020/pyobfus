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
import subprocess
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
    components: List[Dict[str, Any]] = []
    dependencies: List[Dict[str, Any]] = []
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
        input_digest = sha256_file(input_file)
        if input_digest:
            record["input_sha256"] = input_digest
        output_digest = sha256_file(output_file)
        if output_digest:
            record["output_sha256"] = output_digest
        input_ref = f"input:{rel.as_posix()}"
        output_ref = f"output:{rel.as_posix()}"
        if input_digest:
            components.append(
                _cyclonedx_file_component(
                    bom_ref=input_ref,
                    name=rel.as_posix(),
                    path=input_file,
                    sha256=input_digest,
                    role="source-input",
                )
            )
        if output_digest:
            components.append(
                _cyclonedx_file_component(
                    bom_ref=output_ref,
                    name=rel.as_posix(),
                    path=output_file,
                    sha256=output_digest,
                    role="obfuscated-output",
                )
            )
            dependencies.append({"ref": output_ref, "dependsOn": [input_ref]})
        file_records.append(record)

    mapping_digest = sha256_file(mapping_path) if mapping_path else None
    if mapping_path and mapping_digest:
        mapping_ref = "mapping:mapping.json"
        components.append(
            _cyclonedx_file_component(
                bom_ref=mapping_ref,
                name=Path(mapping_path).name,
                path=Path(mapping_path),
                sha256=mapping_digest,
                role="debug-mapping",
            )
        )
        for dep in dependencies:
            dep["dependsOn"].append(mapping_ref)

    created_at = datetime.now(timezone.utc).isoformat()
    config_digest = config_hash(config)
    payload: Dict[str, Any] = {
        "version": PROVENANCE_FORMAT_VERSION,
        "pyobfus_version": PYOBFUS_VERSION,
        "created_at": created_at,
        "tool": {"name": "pyobfus", "version": PYOBFUS_VERSION},
        "input_root": str(input_root),
        "output_root": str(output_root),
        "mode": mode,
        "preset": preset,
        "config_hash": config_digest,
        "source_control": {
            "git_commit": git_commit_for_path(input_root),
        },
        "mapping": {
            "path": str(mapping_path) if mapping_path else None,
            "sha256": mapping_digest,
        },
        "files": file_records,
        "cyclonedx": {
            "bomFormat": "CycloneDX",
            "specVersion": "1.6",
            "version": 1,
            "metadata": {
                "timestamp": created_at,
                "tools": {
                    "components": [
                        {
                            "type": "application",
                            "name": "pyobfus",
                            "version": PYOBFUS_VERSION,
                        }
                    ]
                },
                "component": {
                    "type": "application",
                    "name": "pyobfus-obfuscated-output",
                    "version": "1",
                    "properties": [
                        {"name": "pyobfus:config-sha256", "value": config_digest},
                        {"name": "pyobfus:mode", "value": mode},
                    ],
                },
            },
            "components": components,
            "dependencies": dependencies,
        },
    }
    payload["integrity"] = _integrity_digest_for(payload)
    return payload


def git_commit_for_path(path: Union[str, Path]) -> Optional[str]:
    """Return the containing Git commit for a path, or None outside Git."""
    resolved = Path(path).resolve()
    git_cwd = resolved if resolved.is_dir() else resolved.parent
    try:
        proc = subprocess.run(
            ["git", "-C", str(git_cwd), "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    commit = proc.stdout.strip()
    return commit or None


def _cyclonedx_file_component(
    *,
    bom_ref: str,
    name: str,
    path: Path,
    sha256: str,
    role: str,
) -> Dict[str, Any]:
    return {
        "type": "file",
        "bom-ref": bom_ref,
        "name": name,
        "hashes": [{"alg": "SHA-256", "content": sha256}],
        "properties": [
            {"name": "pyobfus:path", "value": str(path)},
            {"name": "pyobfus:role", "value": role},
        ],
    }


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
