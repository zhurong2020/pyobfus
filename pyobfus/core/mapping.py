"""
Obfuscation mapping I/O and reverse-lookup.

Persists the original→obfuscated name mapping produced by a pyobfus run
to a JSON file and loads it back to reverse obfuscated identifiers in
stack traces and error messages.

This unlocks the "AI can still debug obfuscated code" workflow that is
core to pyobfus's AI-native positioning: paste the obfuscated production
traceback + mapping.json, and the user (or their AI coding assistant)
gets the original names back — without reversing the obfuscation itself.

File format (version 1):

    {
      "version": 1,
      "pyobfus_version": "0.3.3",
      "created_at": "2026-04-22T15:00:00Z",
      "root": "/path/to/src",
      "mode": "cross_file" | "single_file",
      "modules": {
        "<module>": {"<original>": "<obfuscated>", ...}
      },
      "global": {
        "<obfuscated>": {"module": "<module>", "original": "<original>"},
        ...
      }
    }
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple, Union

from pyobfus import __version__ as PYOBFUS_VERSION

# Identifier regex: Python 3 allows Unicode, but obfuscated names are always
# ASCII-safe, so this simple pattern is enough for stack-trace rewriting.
_IDENT_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b")

MAPPING_FORMAT_VERSION = 1


@dataclass
class ObfuscationMapping:
    """Two-way mapping between original and obfuscated names."""

    root: str = ""
    mode: str = "single_file"  # or "cross_file"
    pyobfus_version: str = PYOBFUS_VERSION
    created_at: str = ""

    # Forward: module -> {original: obfuscated}
    modules: Dict[str, Dict[str, str]] = field(default_factory=dict)

    # Reverse: obfuscated -> (module, original)
    global_map: Dict[str, Tuple[str, str]] = field(default_factory=dict)

    # ---- construction ------------------------------------------------

    @classmethod
    def from_single_file(
        cls, name_map: Dict[str, str], root: str = "", module: str = "__main__"
    ) -> "ObfuscationMapping":
        """Build a mapping from a single file's NameMangler output."""
        m = cls(
            root=root,
            mode="single_file",
            created_at=datetime.now(timezone.utc).isoformat(),
            modules={module: dict(name_map)},
        )
        for original, obfuscated in name_map.items():
            if obfuscated not in m.global_map:
                m.global_map[obfuscated] = (module, original)
        return m

    @classmethod
    def from_global_table(cls, global_table: object, root: str = "") -> "ObfuscationMapping":
        """Build a mapping from a CrossFileOrchestrator's GlobalSymbolTable."""
        m = cls(
            root=root,
            mode="cross_file",
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        # Duck-typed: global_table exposes .get_all_modules() and .get_module_exports(m)
        modules: Iterable[str] = getattr(global_table, "get_all_modules", lambda: [])()
        get_exports = getattr(global_table, "get_module_exports", None)
        if get_exports is None:
            return m

        for module in modules:
            exports: Dict[str, str] = get_exports(module)
            if not exports:
                continue
            m.modules[module] = dict(exports)
            for original, obfuscated in exports.items():
                if obfuscated not in m.global_map:
                    m.global_map[obfuscated] = (module, original)
        return m

    @classmethod
    def merge(cls, mappings: Iterable["ObfuscationMapping"]) -> "ObfuscationMapping":
        """Merge multiple mappings (e.g., per-file) into one combined table."""
        merged = cls(created_at=datetime.now(timezone.utc).isoformat())
        mode_seen: set = set()
        for other in mappings:
            mode_seen.add(other.mode)
            for module, module_map in other.modules.items():
                merged.modules.setdefault(module, {})
                for original, obfuscated in module_map.items():
                    merged.modules[module][original] = obfuscated
                    merged.global_map.setdefault(obfuscated, (module, original))
            if not merged.root and other.root:
                merged.root = other.root
        merged.mode = (
            "cross_file"
            if len(mode_seen) > 1
            else (mode_seen.pop() if mode_seen else "single_file")
        )
        return merged

    # ---- I/O ---------------------------------------------------------

    def save(self, path: Union[str, Path]) -> None:
        """Write mapping to a JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")

    def marker_id(self) -> str:
        """Stable 8-char id derived from the obfuscation name map.

        Deterministic across runs with the same names (independent of the
        timestamp), so the per-file ``# pyobfus:obfuscated`` trace marker and
        this mapping file cross-reference reliably. An agent that finds the
        marker in an obfuscated traceback can confirm it matches the mapping
        it holds before trusting an `--unmap`.
        """
        items = sorted(f"{obf}:{mod}.{orig}" for obf, (mod, orig) in self.global_map.items())
        digest = hashlib.sha256("\n".join(items).encode("utf-8")).hexdigest()
        return digest[:8]

    def to_json(self, indent: int = 2) -> str:
        payload = {
            "version": MAPPING_FORMAT_VERSION,
            "pyobfus_version": self.pyobfus_version,
            "created_at": self.created_at,
            "marker_id": self.marker_id(),
            "root": self.root,
            "mode": self.mode,
            "modules": self.modules,
            "global": {
                obf: {"module": mod, "original": orig}
                for obf, (mod, orig) in self.global_map.items()
            },
        }
        return json.dumps(payload, indent=indent, ensure_ascii=False, sort_keys=True)

    @classmethod
    def load(cls, path: Union[str, Path]) -> "ObfuscationMapping":
        """Load mapping from a JSON file written by `save()`."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Mapping file not found: {path}")

        data = json.loads(path.read_text(encoding="utf-8"))
        version = data.get("version")
        if version != MAPPING_FORMAT_VERSION:
            raise ValueError(
                f"Unsupported mapping version {version!r}. "
                f"This pyobfus expects version {MAPPING_FORMAT_VERSION}."
            )

        m = cls(
            root=data.get("root", ""),
            mode=data.get("mode", "single_file"),
            pyobfus_version=data.get("pyobfus_version", ""),
            created_at=data.get("created_at", ""),
            modules={mod: dict(exports) for mod, exports in data.get("modules", {}).items()},
        )
        for obf, info in data.get("global", {}).items():
            m.global_map[obf] = (info.get("module", ""), info.get("original", ""))

        # Backfill global_map if it was not present (forward-only format)
        if not m.global_map:
            for mod, exports in m.modules.items():
                for original, obfuscated in exports.items():
                    m.global_map.setdefault(obfuscated, (mod, original))

        return m

    # ---- reverse lookup ---------------------------------------------

    def reverse(self, obfuscated_name: str) -> Optional[str]:
        """Look up an obfuscated identifier and return the original name, or None."""
        info = self.global_map.get(obfuscated_name)
        if info is None:
            return None
        return info[1] or None

    def reverse_qualified(self, qualified: str) -> str:
        """Unmap every dotted segment: `I0.I1` -> `MyClass.my_method`."""
        parts = qualified.split(".")
        out: List[str] = []
        for part in parts:
            out.append(self.reverse(part) or part)
        return ".".join(out)

    def unmap_text(self, text: str) -> str:
        """
        Replace every occurrence of a known obfuscated identifier in `text`
        with its original name. Non-obfuscated tokens pass through unchanged.

        Substitution is token-boundary aware (uses \\b identifier matches),
        so e.g. "I1" inside "MyI1Thing" is NOT replaced.
        """
        if not self.global_map:
            return text

        def _sub(match: "re.Match[str]") -> str:
            tok = match.group(1)
            original = self.reverse(tok)
            return original if original else tok

        return _IDENT_RE.sub(_sub, text)

    def stats(self) -> Dict[str, int]:
        return {
            "modules": len(self.modules),
            "original_names": sum(len(m) for m in self.modules.values()),
            "unique_obfuscated": len(self.global_map),
        }
