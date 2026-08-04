"""Tool-description integrity manifest (P2-21): rug-pull resistance.

The #1 threat named in the 2026 MCP security baseline (OWASP MCP Cheat
Sheet; Practical DevSecOps 2026) is tool poisoning / "rug-pulls" -- a
server whose tool descriptions or schemas silently change after a user
(or an agent host) has already reviewed and trusted them. For a
PyPI-distributed local-stdio server like pyobfus-mcp, the realistic
vector isn't a live server mutating itself mid-session (there's no
"live server" -- each launch re-execs the installed package); it's a
**supply-chain drift between what a user reviewed and what actually
ships** -- an accidental mismatch between a release's documented tool
surface and its real one, or, in a worse case, a compromised release
that changes tool behavior without changing what it visibly claims to
do.

This module gives that a concrete, checkable shape: `tool_manifest.json`
(committed to the package, generated via `pyobfus-mcp-verify --generate`
before each release) freezes the name/description/input-schema/meta of
every tool `server.py` actually registers, plus a SHA-256
self-consistency digest over that canonical form. `pyobfus-mcp-verify`
(no args) recomputes the manifest from the *live*, currently-installed
registration and compares it against the shipped one.

Honesty note, matching this project's P2-17 provenance-manifest
precedent: this is a self-consistency digest, not a cryptographic
signature. It proves "the installed package's tools match what its own
maintainers say they registered", not "this file was produced by a
specific keyholder" -- there's no private key or third-party trust
anchor involved. A user who wants supply-chain assurance beyond that
should compare against the digest published in the GitHub Release notes
for the version they installed (a compromised PyPI upload wouldn't be
able to also rewrite an already-published GitHub Release).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_MANIFEST_FILENAME = "tool_manifest.json"


def _manifest_path() -> Path:
    return Path(__file__).parent / _MANIFEST_FILENAME


def _canonicalize(tools: List[Dict[str, Any]]) -> str:
    """Deterministic JSON serialization for digesting -- sorted keys, no
    whitespace, so the digest depends only on content, not formatting."""
    return json.dumps(tools, sort_keys=True, separators=(",", ":"))


def compute_live_manifest() -> Dict[str, Any]:
    """Introspect the actually-registered MCP tools right now.

    Builds the real FastMCP app (`server._build_server()`) and reads back
    its tool registry via the SDK's own `list_tools()` -- the same data a
    connecting client would see -- rather than re-deriving it from
    `tools.py` docstrings, which could drift from what `server.py` actually
    registers.

    Returns:
        ``{"tools": [{"name", "description", "input_schema", "meta"}, ...],
        "digest": "<sha256 hex>"}``. Tools are sorted by name so the digest
        is independent of registration order.
    """
    from .server import _build_server

    app = _build_server()
    live_tools = asyncio.run(app.list_tools())

    entries: List[Dict[str, Any]] = []
    for t in sorted(live_tools, key=lambda tool: tool.name):
        meta = getattr(t, "meta", None) or getattr(t, "_meta", None) or {}
        entries.append(
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.inputSchema,
                "meta": dict(meta),
            }
        )

    digest = hashlib.sha256(_canonicalize(entries).encode("utf-8")).hexdigest()
    return {"tools": entries, "digest": digest}


def load_shipped_manifest() -> Dict[str, Any]:
    """Load the manifest frozen into the installed package at release time.

    Raises:
        FileNotFoundError: dev/editable installs that never ran
            ``--generate``, or a corrupted/incomplete package.
    """
    return dict(json.loads(_manifest_path().read_text(encoding="utf-8")))


def _diff_manifests(
    shipped_tools: List[Dict[str, Any]], live_tools: List[Dict[str, Any]]
) -> List[str]:
    """Human-readable per-tool differences between two manifest tool lists."""
    shipped_by_name = {t["name"]: t for t in shipped_tools}
    live_by_name = {t["name"]: t for t in live_tools}
    diffs: List[str] = []
    for name in sorted(set(shipped_by_name) | set(live_by_name)):
        if name not in live_by_name:
            diffs.append(f"tool {name!r} was removed")
        elif name not in shipped_by_name:
            diffs.append(f"tool {name!r} is new (not in the shipped manifest)")
        elif shipped_by_name[name] != live_by_name[name]:
            changed = [
                field
                for field in ("description", "input_schema", "meta")
                if shipped_by_name[name].get(field) != live_by_name[name].get(field)
            ]
            diffs.append(f"tool {name!r} changed: {', '.join(changed)}")
    return diffs


def verify_integrity() -> Dict[str, Any]:
    """Compare the live tool registration against the shipped manifest.

    Returns:
        A dict with ``match`` (``True``/``False``/``None`` -- ``None`` means
        no shipped manifest was found to compare against), ``live_digest``,
        and (when a shipped manifest exists) ``shipped_digest`` plus a
        ``diff`` list when they don't match.
    """
    live = compute_live_manifest()
    try:
        shipped = load_shipped_manifest()
    except FileNotFoundError:
        return {
            "match": None,
            "error": (
                "no shipped tool_manifest.json found -- likely a dev/editable "
                "install that never ran `pyobfus-mcp-verify --generate`, or a "
                "corrupted package"
            ),
            "live_digest": live["digest"],
        }

    match = live["digest"] == shipped["digest"]
    result: Dict[str, Any] = {
        "match": match,
        "live_digest": live["digest"],
        "shipped_digest": shipped["digest"],
    }
    if not match:
        result["diff"] = _diff_manifests(shipped["tools"], live["tools"])
    return result


def _generate(*, quiet: bool = False) -> Dict[str, Any]:
    """Regenerate ``tool_manifest.json`` from the live registration.

    Maintainer/CI action, run before tagging a release -- not something an
    end user of the installed package needs to do.
    """
    manifest = compute_live_manifest()
    path = _manifest_path()
    path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if not quiet:
        print(f"Wrote {path} ({len(manifest['tools'])} tools, digest {manifest['digest'][:12]}...)")
    return manifest


def main(argv: Optional[List[str]] = None) -> None:
    """CLI entry point: ``pyobfus-mcp-verify`` / ``pyobfus-mcp-verify --generate``."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="pyobfus-mcp-verify",
        description=(
            "Verify pyobfus-mcp's currently-registered tool descriptions "
            "against the shipped integrity manifest (P2-21, rug-pull "
            "resistance), or regenerate that manifest."
        ),
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Regenerate tool_manifest.json from the live tool registration "
        "(maintainer/CI use, before tagging a release).",
    )
    args = parser.parse_args(argv)

    if args.generate:
        _generate()
        return

    result = verify_integrity()
    if result["match"] is None:
        print(f"WARNING: {result['error']}")
        sys.exit(2)
    if result["match"]:
        print(
            f"OK: tool descriptions match the shipped manifest (digest {result['live_digest'][:12]}...)."
        )
        sys.exit(0)
    print("MISMATCH: tool descriptions differ from the shipped manifest!")
    print(f"  shipped digest: {result['shipped_digest']}")
    print(f"  live digest:    {result['live_digest']}")
    for line in result.get("diff", []):
        print(f"  - {line}")
    sys.exit(1)


__all__ = [
    "compute_live_manifest",
    "load_shipped_manifest",
    "verify_integrity",
    "main",
]
