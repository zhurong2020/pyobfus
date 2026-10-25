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
      "locals": {
        "<module>": {"<obfuscated>": "<original>", ...}
      },
      "global": {
        "<obfuscated>": {"module": "<module>", "original": "<original>"},
        ...
      }
    }

Independent directory builds use version 2 with file-scoped ``file_names``
and no global reverse table. See docs/INDEPENDENT_DIRECTORY_MAPPING_DESIGN.md.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple, Union

from pyobfus import __version__ as PYOBFUS_VERSION
from pyobfus.core.line_map import Location

MAPPING_FORMAT_VERSION = 1
INDEPENDENT_MAPPING_FORMAT_VERSION = 2


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

    # Function locals may repeat original spellings across lexical scopes.
    # Keep them separate from the module-level forward/export mapping.
    locals: Dict[str, Dict[str, str]] = field(default_factory=dict)

    files: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Independent files reuse short names; no project-wide reverse lookup is safe.
    file_names: Dict[str, Dict[str, List[str]]] = field(default_factory=dict)
    unmapped_files: Dict[str, str] = field(default_factory=dict)

    # Optional v1 extensions for exact, name-only encrypted frame restoration.
    encrypted_code: Dict[str, Dict[str, str]] = field(default_factory=dict)
    opacity_plan: Dict[str, Any] = field(default_factory=dict)

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
        for module, locals_map in getattr(global_table, "local_mappings", {}).items():
            if locals_map:
                m.locals[module] = dict(locals_map)
            for obfuscated, original in locals_map.items():
                m.global_map[obfuscated] = (module, original)
        return m

    @classmethod
    def merge(cls, mappings: Iterable["ObfuscationMapping"]) -> "ObfuscationMapping":
        """Merge multiple mappings (e.g., per-file) into one combined table."""
        merged = cls(created_at=datetime.now(timezone.utc).isoformat())
        mode_seen: set = set()
        for other in mappings:
            if other.mode == "independent_files":
                raise ValueError("File-scoped mappings cannot be merged as global name tables")
            mode_seen.add(other.mode)
            for module, module_map in other.modules.items():
                merged.modules.setdefault(module, {})
                for original, obfuscated in module_map.items():
                    merged.modules[module][original] = obfuscated
                    merged.global_map.setdefault(obfuscated, (module, original))
            for module, local_map in other.locals.items():
                merged.locals.setdefault(module, {}).update(local_map)
                for obfuscated, original in local_map.items():
                    merged.global_map.setdefault(obfuscated, (module, original))
            merged.files.update(other.files)
            if not merged.root and other.root:
                merged.root = other.root
        merged.mode = (
            "cross_file"
            if len(mode_seen) > 1
            else (mode_seen.pop() if mode_seen else "single_file")
        )
        return merged

    def add_independent_file(
        self,
        output_key: str,
        name_map: Dict[str, str],
        line_record: Dict[str, Any],
        original_source: str,
        output_code: str,
    ) -> None:
        """Collect one successful output, without collapsing names across files."""
        if self.mode != "independent_files":
            raise ValueError("Independent mapping requires an output-relative file key")
        if not _relative_path(output_key):
            self.unmapped_files[output_key] = "Output filename is not portable in a mapping"
            return
        names: Dict[str, List[str]] = {}
        for original, obfuscated in name_map.items():
            if original.isidentifier() and obfuscated.isidentifier():
                names.setdefault(unicodedata.normalize("NFKC", obfuscated), []).append(original)
        self.file_names[output_key] = {name: sorted(set(values)) for name, values in names.items()}
        self.modules[output_key] = dict(name_map)
        self.files[output_key] = {
            **line_record,
            "source_sha256": hashlib.sha256(original_source.encode("utf-8")).hexdigest(),
            "output_sha256": hashlib.sha256(output_code.encode("utf-8")).hexdigest(),
        }

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
        if self.mode == "independent_files":
            identity = {
                "file_names": self.file_names,
                "unmapped_files": self.unmapped_files,
                "files": {
                    path: {
                        key: record.get(key)
                        for key in ("source", "module", "source_sha256", "output_sha256")
                    }
                    for path, record in self.files.items()
                },
            }
            encoded = json.dumps(identity, sort_keys=True, ensure_ascii=False).encode("utf-8")
            return hashlib.sha256(encoded).hexdigest()[:8]
        items = sorted(f"{obf}:{mod}.{orig}" for obf, (mod, orig) in self.global_map.items())
        digest = hashlib.sha256("\n".join(items).encode("utf-8")).hexdigest()
        return digest[:8]

    def to_json(self, indent: int = 2) -> str:
        payload = {
            "version": (
                INDEPENDENT_MAPPING_FORMAT_VERSION
                if self.mode == "independent_files"
                else MAPPING_FORMAT_VERSION
            ),
            "pyobfus_version": self.pyobfus_version,
            "created_at": self.created_at,
            "marker_id": self.marker_id(),
            "root": self.root,
            "mode": self.mode,
            "modules": self.modules,
            "locals": self.locals,
            "global": {
                obf: {"module": mod, "original": orig}
                for obf, (mod, orig) in self.global_map.items()
            },
        }
        if self.files or self.mode == "independent_files":
            payload["files"] = {"line_map_version": 1, "entries": self.files}
        if self.mode == "independent_files":
            payload["file_names"] = self.file_names
            payload["unmapped_files"] = self.unmapped_files
        if self.encrypted_code:
            payload["encrypted_code"] = self.encrypted_code
            payload["opacity_plan"] = self.opacity_plan
        return json.dumps(payload, indent=indent, ensure_ascii=False, sort_keys=True)

    @classmethod
    def load(cls, path: Union[str, Path]) -> "ObfuscationMapping":
        """Load mapping from a JSON file written by `save()`."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Mapping file not found: {path}")

        data = json.loads(path.read_text(encoding="utf-8"))
        version = data.get("version")
        if type(version) is not int or version not in (
            MAPPING_FORMAT_VERSION,
            INDEPENDENT_MAPPING_FORMAT_VERSION,
        ):
            raise ValueError(
                f"Unsupported mapping version {version!r}. "
                "This pyobfus supports mapping versions 1 and 2."
            )
        independent = version == INDEPENDENT_MAPPING_FORMAT_VERSION
        if independent != (data.get("mode") == "independent_files"):
            raise ValueError("Mapping version 2 requires independent_files mode")

        m = cls(
            root=data.get("root", ""),
            mode=data.get("mode", "single_file"),
            pyobfus_version=data.get("pyobfus_version", ""),
            created_at=data.get("created_at", ""),
            modules=(
                {}
                if independent
                else {mod: dict(exports) for mod, exports in data.get("modules", {}).items()}
            ),
            locals=(
                {}
                if independent
                else {mod: dict(names) for mod, names in data.get("locals", {}).items()}
            ),
        )
        if not independent:
            for obf, info in data.get("global", {}).items():
                m.global_map[obf] = (info.get("module", ""), info.get("original", ""))
            encrypted = data.get("encrypted_code", {})
            plan = data.get("opacity_plan", {})
            if not isinstance(encrypted, dict) or not isinstance(plan, dict):
                raise ValueError("Invalid encrypted-code mapping extension")
            from pyobfus.core.crossfile_opacity_debug import parse_l3_co_filename

            for filename, names in encrypted.items():
                if (
                    not isinstance(filename, str)
                    or parse_l3_co_filename(filename) is None
                    or not isinstance(names, dict)
                    or not all(
                        isinstance(name, str)
                        and name.isidentifier()
                        and isinstance(original, str)
                        and original.isidentifier()
                        for name, original in names.items()
                    )
                ):
                    raise ValueError("Invalid encrypted-code name table")
            m.encrypted_code = encrypted
            m.opacity_plan = plan
        else:
            unavailable = data.get("unmapped_files", {})
            if not isinstance(unavailable, dict):
                raise ValueError("Independent unmapped_files must be an object")
            m.unmapped_files = {
                key: reason
                for key, reason in unavailable.items()
                if isinstance(key, str)
                and key
                and not key.startswith("/")
                and ".." not in key.replace("\\", "/").split("/")
                and isinstance(reason, str)
            }
            tables = data.get("file_names", {})
            if not isinstance(tables, dict):
                raise ValueError("Independent file_names must be an object")
            for file_key, names in tables.items():
                if not _relative_path(file_key) or not isinstance(names, dict):
                    continue
                validated: Dict[str, List[str]] = {}
                for name, candidates in names.items():
                    if (
                        isinstance(name, str)
                        and name.isidentifier()
                        and isinstance(candidates, list)
                        and candidates
                        and all(
                            isinstance(item, str) and item.isidentifier() for item in candidates
                        )
                    ):
                        canonical = unicodedata.normalize("NFKC", name)
                        validated.setdefault(canonical, []).extend(candidates)
                m.file_names[file_key] = {
                    name: sorted(set(values)) for name, values in validated.items()
                }

        files = data.get("files", {})
        if independent and (
            not isinstance(files, dict)
            or files.get("line_map_version") != 1
            or not isinstance(files.get("entries"), dict)
        ):
            raise ValueError("Independent mapping requires files.entries with line_map_version 1")
        if isinstance(files, dict) and files.get("line_map_version") == 1:
            entries = files.get("entries", {})
            if isinstance(entries, dict):
                if independent:
                    for key, value in entries.items():
                        if not _valid_file_identity(key, value):
                            continue
                        record = dict(value)
                        if not _valid_file(key, value):
                            record["lines"] = None
                            record["reason"] = "Invalid optional line table"
                        m.files[key] = record
                    m.file_names = {key: m.file_names.get(key, {}) for key in m.files}
                    m.modules = {
                        key: {
                            original: name
                            for name, candidates in names.items()
                            for original in candidates
                        }
                        for key, names in m.file_names.items()
                    }
                else:
                    m.files = {
                        key: value for key, value in entries.items() if _valid_file(key, value)
                    }

        # Backfill global_map if it was not present (forward-only format)
        if not independent and not m.global_map:
            for mod, exports in m.modules.items():
                for original, obfuscated in exports.items():
                    m.global_map.setdefault(obfuscated, (mod, original))

        if not independent:
            for mod, names in m.locals.items():
                for obfuscated, original in names.items():
                    m.global_map.setdefault(obfuscated, (mod, original))

        return m

    # ---- reverse lookup ---------------------------------------------

    def resolve_location(self, trace_path: str, line: int) -> Optional[Location]:
        """Resolve a complete, unique longest file-key suffix without source access.

        This query only considers the path suffix, not deployment roots. Use
        unmap_trace() for traceback-wide deployment-root inference.
        """
        if line < 1:
            return None
        path = self._match_file_path(trace_path)
        if path is None:
            return None
        return self.resolve_file_location(path, line)

    def resolve_file_location(self, path: str, line: int) -> Optional[Location]:
        """Resolve an already selected exact output key, without suffix fallback."""
        record = self.files.get(path)
        if record is None or line < 1 or path in self.unmapped_files:
            return None
        runs = record.get("lines")
        if runs is None or line > record["line_count"]:
            return None
        source_line = None
        for start, value in runs:
            if start > line:
                break
            source_line = value
        return Location(
            record["source"],
            source_line,
            record["module"],
            "generated" if source_line is None else "mapped",
        )

    def _match_file_path(self, trace_path: str) -> Optional[str]:
        """Match all file-key components, choosing the unique longest key."""
        trace = _path_parts(trace_path)
        candidates = []
        paths = set(self.files)
        if self.mode == "independent_files":
            paths.update(self.file_names)
            paths.update(self.unmapped_files)
        for path in paths:
            parts = _path_parts(path)
            if parts and len(trace) >= len(parts) and trace[-len(parts) :] == parts:
                candidates.append((len(parts), path))
        if not candidates:
            return None
        if self.mode == "independent_files" and len(candidates) > 1:
            return None
        longest = max(score for score, _ in candidates)
        matches = [path for score, path in candidates if score == longest]
        return matches[0] if len(matches) == 1 else None

    def reverse(self, obfuscated_name: str) -> Optional[str]:
        """Look up an obfuscated identifier and return the original name, or None."""
        if self.mode == "independent_files":
            return None
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
        if self.mode == "independent_files" or not self.global_map:
            return text

        names: Dict[str, List[str]] = {}
        for obfuscated, (_, original) in self.global_map.items():
            if not isinstance(original, str) or not original:
                continue
            canonical = unicodedata.normalize("NFKC", obfuscated)
            names.setdefault(canonical, []).append(original)
        return _substitute_names(text, names)

    def unmap_file_text(self, text: str, path: str) -> str:
        """Restore unique spellings in one known output file; never guess a scope."""
        return _substitute_names(text, self.file_names.get(path, {}))

    def unmap_trace(self, text: str) -> Dict[str, Any]:
        """Restore names and statement locations in standard CPython tracebacks."""
        from pyobfus.core.traceback_restore import restore_trace

        return restore_trace(self, text)

    def unmatched_names(self, text: str) -> List[str]:
        """
        Obfuscated-looking names in `text` that this mapping does not know.

        A name "looks obfuscated" when it has the same prefix-plus-digits shape
        as the names in this mapping (``I0``, ``I17``...). Any of those missing
        from the mapping usually means the trace came from a different build,
        so a reversal with this mapping would be incomplete or wrong.
        """
        known = set(self.global_map)
        if self.mode == "independent_files":
            known = {name for names in self.file_names.values() for name in names}
        known = {unicodedata.normalize("NFKC", name) for name in known}
        prefixes = {
            match.group(1)
            for name in known
            for match in [re.fullmatch(r"(.+?)[0-9]+", name)]
            if match is not None
        }
        tokens = {unicodedata.normalize("NFKC", name) for _, _, name in _unicode_identifiers(text)}
        return sorted(
            {
                name
                for name in tokens - known
                if any(
                    name.startswith(prefix)
                    and name[len(prefix) :].isascii()
                    and name[len(prefix) :].isdigit()
                    for prefix in prefixes
                )
            },
            key=lambda name: (len(name), name),
        )

    def stats(self) -> Dict[str, int]:
        return {
            "modules": len(self.modules),
            "original_names": sum(len(m) for m in self.modules.values()),
            "unique_obfuscated": (
                len({name for names in self.file_names.values() for name in names})
                if self.mode == "independent_files"
                else len(self.global_map)
            ),
        }


def _path_parts(path: str) -> List[str]:
    parts: List[str] = []
    for part in path.replace("\\", "/").split("/"):
        if part in ("", "."):
            continue
        if part == ".." and parts and parts[-1] != "..":
            parts.pop()
        else:
            parts.append(part.lower() if re.fullmatch(r"[A-Za-z]:", part) else part)
    return parts


def _substitute_names(text: str, names: Dict[str, List[str]]) -> str:
    """Use Python Unicode tokens in both mapping formats; ambiguous aliases stay."""
    output = []
    previous = 0
    for start, end, name in _unicode_identifiers(text):
        # Do not replace the identifier-shaped suffix of a larger word/number.
        if start and (text[start - 1].isalnum() or ("_" + text[start - 1]).isidentifier()):
            continue
        candidates = set(names.get(unicodedata.normalize("NFKC", name), []))
        output.append(text[previous:start])
        output.append(next(iter(candidates)) if len(candidates) == 1 else name)
        previous = end
    output.append(text[previous:])
    return "".join(output)


def _unicode_identifiers(text: str) -> Iterator[Tuple[int, int, str]]:
    """Scan Python identifier spellings, including combining continuation marks."""
    index = 0
    while index < len(text):
        if not text[index].isidentifier():
            index += 1
            continue
        end = index + 1
        while end < len(text) and ("_" + text[end]).isidentifier():
            end += 1
        yield index, end, text[index:end]
        index = end


def _relative_path(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and not value.startswith("/")
        and "\\" not in value
        and ":" not in value
        and all(p not in ("", ".", "..") for p in value.split("/"))
    )


def _valid_file(path: object, record: object) -> bool:
    """Ignore malformed optional metadata without losing legacy name tables."""
    if not _valid_file_identity(path, record):
        return False
    assert isinstance(record, dict)
    count = record["line_count"]
    runs = record.get("lines")
    if runs is None:
        return True
    if not isinstance(runs, list) or (count > 0 and not runs):
        return False
    previous = 0
    for run in runs:
        if not isinstance(run, list) or len(run) != 2:
            return False
        start, source = run
        if type(start) is not int or not previous < start <= count:
            return False
        if previous == 0 and start != 1:
            return False
        if source is not None and (type(source) is not int or source < 1):
            return False
        previous = start
    return True


def _valid_file_identity(path: object, record: object) -> bool:
    """Keep v2 path/name identity usable when only optional line runs are bad."""
    if not _relative_path(path) or not isinstance(record, dict):
        return False
    if not _relative_path(record.get("source")) or not isinstance(record.get("module"), str):
        return False
    count = record.get("line_count")
    if type(count) is not int or count < 0:
        return False
    return True
