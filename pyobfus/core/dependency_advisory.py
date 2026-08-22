"""
Dependency-hallucination advisory.

Flags declared dependencies (in `requirements*.txt` / `pyproject.toml`) that
do not resolve on the public PyPI index — the exact signature of
"slopsquatting": an LLM hallucinates a plausible-looking package name, a
developer or an AI coding agent adds it to a dependency file, and if an
attacker has (or later does) register that name on PyPI, a routine
`pip install` silently pulls in malicious code. The term was coined by Seth
Larson, Security Developer-in-Residence at the Python Software Foundation,
in 2025; a 2026 cross-model study found sets of hallucinated package names
that multiple independent LLMs invented identically.

Honest scope: this check can only ever prove a *negative* usefully — "this
name does not exist yet, verify it before you rely on it." It cannot detect
the more dangerous case where an attacker has *already* registered a
hallucinated name (the package then correctly resolves as "exists", and this
check has nothing more to say about it — a supply-chain / provenance tool is
needed for that, this is not a substitute). It can also false-positive on
legitimate packages served from a private/custom index rather than public
PyPI; when a custom index directive is detected in a scanned file, the report
notes that explicitly so the caller can weigh the finding accordingly.

Network access: verifying against PyPI requires live HTTP requests. This is
opt-out (`offline=True` skips all network calls) rather than opt-in at the
CLI, but the MCP-exposed tool defaults to offline — see
`docs/MCP_SECURITY_SCAN.md` for why the MCP surface stays egress-free unless
a caller explicitly asks for the stronger check.

Used by `pyobfus --check` and the MCP tool `check_obfuscation_risks`.
"""

from __future__ import annotations

import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Set
from urllib.parse import quote

# Import locally to avoid a hard import-time cycle with preflight.py, which
# imports this module.
from pyobfus.core.preflight import CAT_DEPENDENCY_ADVISORY, SEVERITY_INFO, SEVERITY_MEDIUM, Risk

_PYPI_JSON_URL = "https://pypi.org/pypi/{name}/json"
_DEFAULT_TIMEOUT = 3.0
_DEFAULT_MAX_WORKERS = 8

# Lines that indicate dependencies may come from somewhere other than public
# PyPI — a hit here means "not found on PyPI" is a weaker signal (could be a
# private/internal package), so soften the message rather than suppress it.
_CUSTOM_INDEX_RE = re.compile(r"^\s*(-i\b|--index-url\b|--extra-index-url\b)")

# Requirement-file lines that name no installable PyPI package at all —
# these are skipped outright rather than mis-parsed as a package name.
_SKIP_LINE_RE = re.compile(r"^\s*(#|-r\b|--requirement\b|-c\b|--constraint\b|-e\b|--editable\b)")
_URL_REQ_RE = re.compile(r"^\s*[\w.+-]+://")

# A PEP 508 requirement string starts with a package name: letters, digits,
# '.', '-', '_'. Cut everything from the first character that can't be part
# of a bare name (version specifier, environment marker, extras bracket,
# inline comment, whitespace).
_NAME_HEAD_RE = re.compile(r"^([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)")


class DependencyCheckResult(NamedTuple):
    risks: List[Risk]
    checked: int
    skipped_offline: bool


def normalize_name(name: str) -> str:
    """PEP 503 normalization: lowercase, collapse runs of -_. to a single -."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _extract_name(requirement: str) -> Optional[str]:
    """Pull the bare package name out of a PEP 508 requirement string."""
    match = _NAME_HEAD_RE.match(requirement.strip())
    if not match:
        return None
    return match.group(1)


def _iter_requirements_txt(text: str) -> Set[str]:
    names: Set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.split(" #", 1)[0].strip()  # inline comment (space before '#')
        if not line or _SKIP_LINE_RE.match(line) or _URL_REQ_RE.match(line):
            continue
        # Strip environment markers (";...") before extracting the name.
        line = line.split(";", 1)[0].strip()
        name = _extract_name(line)
        if name:
            names.add(name)
    return names


def _has_custom_index(text: str) -> bool:
    return any(_CUSTOM_INDEX_RE.match(line) for line in text.splitlines())


def _load_toml(path: Path) -> Optional[dict]:
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ImportError:
            return None
    try:
        with open(path, "rb") as f:
            data: dict = tomllib.load(f)
            return data
    except Exception:
        return None


def _iter_pyproject_toml(path: Path) -> Set[str]:
    data = _load_toml(path)
    if not data:
        return set()
    names: Set[str] = set()
    project = data.get("project", {})
    if isinstance(project, dict):
        for req in project.get("dependencies", []) or []:
            name = _extract_name(str(req))
            if name:
                names.add(name)
        optional = project.get("optional-dependencies", {})
        if isinstance(optional, dict):
            for group in optional.values():
                for req in group or []:
                    name = _extract_name(str(req))
                    if name:
                        names.add(name)
    return names


def find_dependency_files(root: Path) -> List[Path]:
    """Locate requirements*.txt / pyproject.toml near `root`.

    `root` may be a file (dependency files are looked for in its parent
    directory) or a directory (looked for directly inside it). Top-level
    only — does not recurse into subdirectories or virtualenvs.
    """
    directory = root.parent if root.is_file() else root
    if not directory.is_dir():
        return []
    found: List[Path] = []
    try:
        entries = sorted(directory.iterdir())
    except OSError:
        return []
    for entry in entries:
        if not entry.is_file():
            continue
        if entry.name == "pyproject.toml" or (
            entry.name.startswith("requirements") and entry.name.endswith(".txt")
        ):
            found.append(entry)
    return found


def collect_declared_dependencies(root: Path) -> Dict[str, List[Path]]:
    """Map normalized package name -> dependency file(s) that declare it."""
    by_name: Dict[str, List[Path]] = {}
    for dep_file in find_dependency_files(root):
        try:
            text = dep_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if dep_file.name == "pyproject.toml":
            raw_names = _iter_pyproject_toml(dep_file)
        else:
            raw_names = _iter_requirements_txt(text)
        for raw_name in raw_names:
            by_name.setdefault(normalize_name(raw_name), []).append(dep_file)
    return by_name


def _pypi_exists(name: str, timeout: float) -> Optional[bool]:
    """True/False if PyPI definitively answered, None on network/lookup error."""
    url = _PYPI_JSON_URL.format(name=quote(name, safe=""))
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310
            status: int = resp.status
            return 200 <= status < 300
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        return None
    except (urllib.error.URLError, TimeoutError, OSError):
        return None


def check_dependency_hallucination(
    root: Path,
    *,
    offline: bool = False,
    timeout: float = _DEFAULT_TIMEOUT,
    max_workers: int = _DEFAULT_MAX_WORKERS,
) -> DependencyCheckResult:
    """Scan dependency files under `root` for names that don't exist on PyPI.

    Returns an empty result (no risks) if no dependency files are found, or
    if `offline=True` (an explicit opt-out produces no findings and no
    caveat — the caller asked for this).
    """
    by_name = collect_declared_dependencies(root)
    if not by_name:
        return DependencyCheckResult(risks=[], checked=0, skipped_offline=False)

    if offline:
        return DependencyCheckResult(risks=[], checked=0, skipped_offline=True)

    custom_index = any(
        _has_custom_index(f.read_text(encoding="utf-8", errors="replace"))
        for f in {p for paths in by_name.values() for p in paths}
        if f.name != "pyproject.toml"
    )

    names = sorted(by_name)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        results = list(pool.map(lambda n: (n, _pypi_exists(n, timeout)), names))

    risks: List[Risk] = []
    unverified = 0
    for name, exists in results:
        if exists is None:
            unverified += 1
            continue
        if exists:
            continue
        dep_file = by_name[name][0]
        caveat = (
            " A custom package index (-i / --index-url / --extra-index-url) "
            "was also detected in this project's requirements — if this "
            "package is served from there rather than public PyPI, this is "
            "a false positive."
            if custom_index
            else ""
        )
        risks.append(
            Risk(
                category=CAT_DEPENDENCY_ADVISORY,
                severity=SEVERITY_MEDIUM,
                file=str(dep_file),
                line=0,
                col=0,
                message=f"Declared dependency '{name}' does not exist on public PyPI.",
                suggestion=(
                    "Verify this is the package name you intended before installing. "
                    "A nonexistent name is exactly what AI-assisted package "
                    "hallucination ('slopsquatting') produces — if an attacker "
                    "registers it later, a routine `pip install` would silently "
                    "pull in malicious code." + caveat
                ),
            )
        )

    if unverified:
        risks.append(
            Risk(
                category=CAT_DEPENDENCY_ADVISORY,
                severity=SEVERITY_INFO,
                file=str(root),
                line=0,
                col=0,
                message=(
                    f"{unverified} of {len(names)} declared dependencies could not be "
                    "verified against PyPI (network error)."
                ),
                suggestion="Re-run with connectivity, or pass --offline to suppress this check.",
            )
        )

    return DependencyCheckResult(risks=risks, checked=len(names), skipped_offline=False)
