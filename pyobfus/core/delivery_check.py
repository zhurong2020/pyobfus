"""Check what is about to be shipped, not the source it came from.

``--check`` scans source before a build. This module looks at the thing you
deliver (an output directory or a wheel) after packaging, and reports files
that should not be there or that the build did not produce:

- a pyobfus mapping file (it restores every original name),
- a private key (``--scrub-traceback`` writes one next to each output),
- an original source file (when a provenance manifest gives the input hashes),
- Python files the build report does not list as outputs,
- Pro protections the build report says were skipped.

It reads files and hashes them; it never imports or runs them, needs no
network, and never prints file contents. It is a check for known mistakes,
not a security scanner: an empty result does not mean the delivery is safe.
Use credential scanners (gitleaks, TruffleHog) and wheel linters
(check-wheel-contents) alongside it.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

DELIVERY_CHECK_FORMAT = "pyobfus-delivery-check"
DELIVERY_CHECK_VERSION = 1

# Finding codes. Consumers branch on these, not on the message text.
MAPPING_FILE = "delivery.mapping_file"
PRIVATE_KEY = "delivery.private_key"
ORIGINAL_SOURCE = "delivery.original_source"
UNRECORDED_PYTHON = "delivery.unrecorded_python"
MISSING_OUTPUT = "delivery.missing_output"
FUSION_SKIPPED = "delivery.fusion_skipped"
L3_PARTIAL = "delivery.l3_partial"
BYTECODE_PRESENT = "delivery.bytecode_present"
L3_BUILD_MISMATCH = "delivery.l3_build_mismatch"

_MAX_JSON_BYTES = 20 * 1024 * 1024
_PEM_PRIVATE_MARKER = b"PRIVATE KEY-----"  # PKCS#8, RSA, EC, OPENSSH
_WHEEL_METADATA_SUFFIXES = (".dist-info/RECORD", ".dist-info/WHEEL", ".dist-info/METADATA")

LIMITATIONS = (
    "Finds known pyobfus mistakes only; an empty result does not mean the delivery is safe.",
    "Does not look for credentials in strings; use gitleaks or TruffleHog.",
    "Original source is recognised only by exact hash, and only with --provenance-manifest.",
    "Files are read and hashed, never imported or executed.",
)


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str  # "high" | "medium" | "info"
    path: str  # path inside the delivery, or "" for build-level findings
    message: str


@dataclass(frozen=True)
class _Entry:
    path: str  # posix path relative to the delivery root
    data: bytes


def _iter_directory(root: Path) -> Iterator[_Entry]:
    for file in sorted(p for p in root.rglob("*") if p.is_file()):
        yield _Entry(file.relative_to(root).as_posix(), file.read_bytes())


def _iter_wheel(wheel: Path) -> Iterator[_Entry]:
    with zipfile.ZipFile(wheel) as archive:
        for info in sorted(archive.infolist(), key=lambda i: i.filename):
            if info.is_dir():
                continue
            yield _Entry(info.filename, archive.read(info))


def _is_mapping(entry: _Entry) -> bool:
    if not entry.path.endswith(".json") or len(entry.data) > _MAX_JSON_BYTES:
        return False
    try:
        data = json.loads(entry.data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return False
    return (
        isinstance(data, dict)
        and "pyobfus_version" in data
        and ("global" in data or "modules" in data)
    )


def _is_private_key(entry: _Entry) -> bool:
    if entry.path.endswith(".scrub.key.pem"):
        return True
    # A key *file* starts with its PEM header. Source code that merely mentions
    # the marker (cryptography's ssh.py does) is not a key file; keys embedded in
    # code are --check / credential-scanner territory.
    first_line = entry.data.lstrip()[:200].split(b"\n", 1)[0]
    return first_line.startswith(b"-----BEGIN") and _PEM_PRIVATE_MARKER in first_line


def _load_json(path: Optional[Path]) -> Optional[Dict[str, Any]]:
    if path is None:
        return None
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{path.name} is not a JSON object")
    return loaded


def check_delivery(
    target: Path,
    *,
    build_report: Optional[Path] = None,
    provenance_manifest: Optional[Path] = None,
) -> Dict[str, Any]:
    """Return the delivery-check result as a JSON-serialisable dict."""
    kind = "wheel" if target.is_file() and target.suffix == ".whl" else "directory"
    if kind == "directory" and not target.is_dir():
        raise ValueError(f"{target.name}: expected a directory or a .whl file")
    entries = _iter_wheel(target) if kind == "wheel" else _iter_directory(target)
    report = _load_json(build_report)
    manifest = _load_json(provenance_manifest)

    input_hashes: Dict[str, str] = {}
    if manifest is not None:
        for record in manifest.get("files", []):
            if isinstance(record, dict) and record.get("input_sha256"):
                input_hashes[record["input_sha256"]] = str(record.get("relative_path", ""))
    output_hashes: Dict[str, str] = {}
    if report is not None:
        for record in report.get("outputs", {}).get("files", []):
            if isinstance(record, dict) and record.get("sha256"):
                output_hashes[record["sha256"]] = str(record.get("path", ""))

    findings: List[Finding] = []
    seen_outputs: set = set()
    python_files = 0
    matched_outputs = 0
    bytecode: List[str] = []
    file_count = 0
    l3_manifest: Optional[Dict[str, Any]] = None
    observed: Dict[str, Tuple[str, bytes]] = {}
    for entry in entries:
        file_count += 1
        if kind == "wheel" and entry.path.endswith(_WHEEL_METADATA_SUFFIXES):
            continue
        digest = hashlib.sha256(entry.data).hexdigest()
        if entry.path == ".pyobfus-release.json":
            try:
                decoded = json.loads(entry.data)
                if not isinstance(decoded, dict):
                    raise ValueError("Release manifest must be an object")
                l3_manifest = decoded
            except (ValueError, UnicodeDecodeError):
                findings.append(
                    Finding(
                        L3_BUILD_MISMATCH, "high", entry.path, "Unreadable L3 release manifest."
                    )
                )
            continue
        if entry.path.endswith(".py"):
            observed[entry.path] = (digest, entry.data[:2048])
        if _is_mapping(entry):
            findings.append(
                Finding(
                    MAPPING_FILE,
                    "high",
                    entry.path,
                    "pyobfus mapping file: it restores every original name. Keep it out of "
                    "the delivery.",
                )
            )
            continue
        if _is_private_key(entry):
            findings.append(
                Finding(
                    PRIVATE_KEY,
                    "high",
                    entry.path,
                    "Private key (for example the --scrub-traceback key). Remove it and keep "
                    "it with your private build records.",
                )
            )
            continue
        # A build output can equal its input (nothing to rename, marker off);
        # that is a protected-as-built file, not a leaked original.
        if digest in input_hashes and digest not in output_hashes and entry.data.strip():
            findings.append(
                Finding(
                    ORIGINAL_SOURCE,
                    "high",
                    entry.path,
                    "Byte-identical to an original source file of this build "
                    f"({input_hashes[digest]}).",
                )
            )
            continue
        if entry.path.endswith((".pyc", ".pyo")):
            bytecode.append(entry.path)
            continue
        if entry.path.endswith(".py"):
            python_files += 1
            if digest in output_hashes:
                matched_outputs += 1
                seen_outputs.add(digest)
            elif report is not None:
                findings.append(
                    Finding(
                        UNRECORDED_PYTHON,
                        "medium",
                        entry.path,
                        "Python file that this build report does not list as an output: "
                        "unprotected, modified after the build, or from another build.",
                    )
                )

    needs_l3 = report is not None and isinstance(report.get("opacity"), dict)
    if l3_manifest is not None or needs_l3:
        try:
            if l3_manifest is None:
                raise ValueError("L3 release completion manifest is missing")
            build_id = l3_manifest["build_id"]
            if (
                l3_manifest.get("format") != "pyobfus-l3-release"
                or l3_manifest.get("version") != 1
                or l3_manifest.get("state") != "completed"
                or not isinstance(build_id, str)
                or not build_id
            ):
                raise ValueError("L3 release completion identity is invalid")
            if (
                report is not None
                and needs_l3
                and (report["build_id"] != build_id or report["opacity"]["build_id"] != build_id)
            ):
                raise ValueError("L3 build report and delivery identities differ")
            records = l3_manifest["files"]
            expected = {r["path"]: r["sha256"] for r in records}
            if len(expected) != len(records) or set(expected) != set(observed):
                raise ValueError("L3 release contains missing, duplicate or unrecorded files")
            marker = f"# pyobfus:l3-build {build_id}".encode("ascii")
            for path, (digest, header) in observed.items():
                if digest != expected[path] or marker not in header.splitlines():
                    raise ValueError("L3 delivery contains modified or mixed-build files")
            if report is not None and needs_l3:
                recorded = {r["path"]: r["sha256"] for r in report["outputs"]["files"]}
                if recorded != expected:
                    raise ValueError("L3 build report and release file digests differ")
        except (KeyError, TypeError, ValueError, UnicodeError):
            findings.append(
                Finding(
                    L3_BUILD_MISMATCH,
                    "high",
                    ".pyobfus-release.json",
                    "L3 completion identity, file membership or content digests do not match. "
                    "Rebuild and deliver one complete application; labels are not signatures.",
                )
            )

    if bytecode:
        findings.append(
            Finding(
                BYTECODE_PRESENT,
                "info",
                bytecode[0],
                f"{len(bytecode)} bytecode file(s). Bytecode decompiles to readable source; "
                "make sure it was compiled from the protected output, not the original.",
            )
        )

    if report is not None:
        for digest, path in sorted(output_hashes.items(), key=lambda item: item[1]):
            if digest not in seen_outputs:
                findings.append(
                    Finding(
                        MISSING_OUTPUT,
                        "info",
                        path,
                        "Listed as a build output but not found in the delivery with the same "
                        "content.",
                    )
                )
        skipped = [
            str(item.get("transform"))
            for item in report.get("disabled_transforms", [])
            if isinstance(item, dict)
        ]
        if skipped:
            findings.append(
                Finding(
                    FUSION_SKIPPED,
                    "medium",
                    "",
                    "The build report says these requested options did not run: "
                    + ", ".join(skipped)
                    + ".",
                )
            )
        transformations = report.get("transformations", {})
        partial = sum(
            int(transformations.get(key, 0) or 0)
            for key in ("l3_skipped_methods", "l3_skipped_nested")
        )
        if partial:
            findings.append(
                Finding(
                    L3_PARTIAL,
                    "medium",
                    "",
                    f"{partial} function(s) matched by opacity rules were not encrypted "
                    "(methods or nested functions).",
                )
            )

    counts = {severity: 0 for severity in ("high", "medium", "info")}
    for finding in findings:
        counts[finding.severity] += 1
    status, hint = _status_and_hint(counts, report is not None, manifest is not None)
    return {
        "format": DELIVERY_CHECK_FORMAT,
        "version": DELIVERY_CHECK_VERSION,
        "status": status,
        "ai_hint": hint,
        "target": {"name": target.name, "kind": kind, "files": file_count},
        "inputs": {
            "build_report": report is not None,
            "provenance_manifest": manifest is not None,
        },
        "summary": {
            "python_files": python_files,
            "matched_build_outputs": matched_outputs,
            "bytecode_files": len(bytecode),
            **counts,
        },
        "findings": [asdict(finding) for finding in findings],
        "limitations": list(LIMITATIONS),
    }


def _status_and_hint(
    counts: Dict[str, int], has_report: bool, has_manifest: bool
) -> Tuple[str, str]:
    if counts["high"]:
        return (
            "fail",
            "Remove the high-severity files from the delivery before shipping, then rerun.",
        )
    missing = []
    if not has_report:
        missing.append("--build-report")
    if not has_manifest:
        missing.append("--provenance-manifest")
    extra = (
        " Pass " + " and ".join(missing) + " from the build to also check outputs and originals."
        if missing
        else ""
    )
    if counts["medium"]:
        return "warn", "Review the medium findings; they may be intended." + extra
    return "ok", "No known delivery mistakes found (not a security guarantee)." + extra


def format_text(result: Dict[str, Any]) -> str:
    """Human-readable summary; paths only, never file contents."""
    target = result["target"]
    lines = [
        f"Delivery check: {target['name']} ({target['kind']}, {target['files']} files)",
        f"Status: {result['status'].upper()}",
    ]
    for finding in result["findings"]:
        where = f" {finding['path']}" if finding["path"] else ""
        lines.append(f"  [{finding['severity']}] {finding['code']}{where}: {finding['message']}")
    lines.append(f"Next: {result['ai_hint']}")
    lines.append("Limits: " + " ".join(result["limitations"]))
    return "\n".join(lines)
