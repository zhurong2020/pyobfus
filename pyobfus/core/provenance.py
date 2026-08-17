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


def validate_provenance_manifest(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Validate pyobfus provenance manifest structure and local integrity."""
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(manifest, dict):
        return {
            "valid": False,
            "errors": ["Manifest root must be a JSON object."],
            "warnings": [],
            "summary": "Invalid provenance manifest: 1 error.",
        }

    for key in (
        "version",
        "pyobfus_version",
        "tool",
        "created_at",
        "input_root",
        "output_root",
        "config_hash",
        "mapping",
        "files",
        "cyclonedx",
        "integrity",
    ):
        if key not in manifest:
            errors.append(f"Missing required field: {key}")

    if manifest.get("version") != PROVENANCE_FORMAT_VERSION:
        errors.append(
            f"Unsupported provenance format version: {manifest.get('version')!r} "
            f"(expected {PROVENANCE_FORMAT_VERSION})"
        )

    tool = manifest.get("tool")
    if not isinstance(tool, dict) or tool.get("name") != "pyobfus":
        errors.append("tool.name must be 'pyobfus'.")

    files = manifest.get("files")
    if not isinstance(files, list):
        errors.append("files must be a list.")
        files = []
    elif not files:
        warnings.append("files is empty; no obfuscated file records are present.")

    for index, record in enumerate(files):
        if not isinstance(record, dict):
            errors.append(f"files[{index}] must be an object.")
            continue
        for key in ("input", "output", "relative_path"):
            if not isinstance(record.get(key), str) or not record.get(key):
                errors.append(f"files[{index}].{key} must be a non-empty string.")
        if not _looks_like_sha256(record.get("input_sha256")):
            errors.append(f"files[{index}].input_sha256 must be a SHA-256 hex digest.")
        if not _looks_like_sha256(record.get("output_sha256")):
            errors.append(f"files[{index}].output_sha256 must be a SHA-256 hex digest.")

    mapping = manifest.get("mapping")
    if not isinstance(mapping, dict):
        errors.append("mapping must be an object.")
    elif mapping.get("sha256") is not None and not _looks_like_sha256(mapping.get("sha256")):
        errors.append("mapping.sha256 must be null or a SHA-256 hex digest.")

    source_control = manifest.get("source_control")
    if source_control is None:
        warnings.append("source_control is missing; git commit provenance is unavailable.")
    elif not isinstance(source_control, dict):
        errors.append("source_control must be an object when present.")
    elif source_control.get("git_commit") is not None and not isinstance(
        source_control.get("git_commit"), str
    ):
        errors.append("source_control.git_commit must be a string or null.")

    _validate_cyclonedx_section(manifest.get("cyclonedx"), errors, warnings)

    if "integrity" in manifest and not verify_manifest_integrity(manifest):
        errors.append("integrity digest does not match manifest payload.")

    error_count = len(errors)
    warning_count = len(warnings)
    if error_count:
        summary = (
            f"Invalid provenance manifest: {error_count} error" f"{'' if error_count == 1 else 's'}"
        )
        if warning_count:
            summary += f", {warning_count} warning{'' if warning_count == 1 else 's'}"
        summary += "."
    elif warning_count:
        summary = (
            f"Valid provenance manifest with {warning_count} "
            f"warning{'' if warning_count == 1 else 's'}."
        )
    else:
        summary = "Valid provenance manifest."

    return {
        "valid": error_count == 0,
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
    }


def _validate_cyclonedx_section(cyclonedx: Any, errors: List[str], warnings: List[str]) -> None:
    if not isinstance(cyclonedx, dict):
        errors.append("cyclonedx must be an object.")
        return
    if cyclonedx.get("bomFormat") != "CycloneDX":
        errors.append("cyclonedx.bomFormat must be 'CycloneDX'.")
    if cyclonedx.get("specVersion") != "1.6":
        errors.append("cyclonedx.specVersion must be '1.6'.")

    components = cyclonedx.get("components")
    if not isinstance(components, list):
        errors.append("cyclonedx.components must be a list.")
        components = []
    elif not components:
        warnings.append("cyclonedx.components is empty.")

    component_refs = set()
    for index, component in enumerate(components):
        if not isinstance(component, dict):
            errors.append(f"cyclonedx.components[{index}] must be an object.")
            continue
        bom_ref = component.get("bom-ref")
        if not isinstance(bom_ref, str) or not bom_ref:
            errors.append(f"cyclonedx.components[{index}].bom-ref must be a non-empty string.")
            continue
        component_refs.add(bom_ref)
        hashes = component.get("hashes")
        if not isinstance(hashes, list) or not any(
            isinstance(item, dict)
            and item.get("alg") == "SHA-256"
            and _looks_like_sha256(item.get("content"))
            for item in hashes
        ):
            errors.append(f"cyclonedx.components[{index}] must include a SHA-256 hash entry.")

    dependencies = cyclonedx.get("dependencies")
    if not isinstance(dependencies, list):
        errors.append("cyclonedx.dependencies must be a list.")
        return
    for index, dependency in enumerate(dependencies):
        if not isinstance(dependency, dict):
            errors.append(f"cyclonedx.dependencies[{index}] must be an object.")
            continue
        ref = dependency.get("ref")
        if ref not in component_refs:
            errors.append(f"cyclonedx.dependencies[{index}].ref has no matching component.")
        depends_on = dependency.get("dependsOn")
        if not isinstance(depends_on, list):
            errors.append(f"cyclonedx.dependencies[{index}].dependsOn must be a list.")
            continue
        for dep_ref in depends_on:
            if dep_ref not in component_refs:
                errors.append(
                    f"cyclonedx.dependencies[{index}].dependsOn contains "
                    f"unknown component ref: {dep_ref!r}"
                )


def _looks_like_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(c in "0123456789abcdefABCDEF" for c in value)
    )


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
