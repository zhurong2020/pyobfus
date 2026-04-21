"""Tests for ObfuscationMapping I/O and reverse-lookup (pyobfus/core/mapping.py)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pyobfus.core.mapping import (
    MAPPING_FORMAT_VERSION,
    ObfuscationMapping,
)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_from_single_file_builds_forward_and_reverse() -> None:
    m = ObfuscationMapping.from_single_file(
        {"Calculator": "I0", "add": "I1"}, module="calc"
    )
    assert m.modules["calc"]["Calculator"] == "I0"
    assert m.reverse("I0") == "Calculator"
    assert m.reverse("I1") == "add"
    assert m.reverse("I99") is None


def test_from_global_table_duck_typed() -> None:
    class FakeTable:
        def get_all_modules(self):
            return ["mod_a", "mod_b"]

        def get_module_exports(self, mod):
            return {"mod_a": {"Foo": "I0"}, "mod_b": {"Bar": "I1"}}.get(mod, {})

    m = ObfuscationMapping.from_global_table(FakeTable(), root="/tmp/src")
    assert m.mode == "cross_file"
    assert m.root == "/tmp/src"
    assert m.reverse("I0") == "Foo"
    assert m.reverse("I1") == "Bar"


def test_from_global_table_handles_missing_method() -> None:
    class Empty:
        pass

    m = ObfuscationMapping.from_global_table(Empty())
    assert m.modules == {}
    assert m.global_map == {}


def test_merge_combines_modules() -> None:
    a = ObfuscationMapping.from_single_file({"A": "I0"}, module="one")
    b = ObfuscationMapping.from_single_file({"B": "I1"}, module="two")
    merged = ObfuscationMapping.merge([a, b])
    assert merged.reverse("I0") == "A"
    assert merged.reverse("I1") == "B"
    assert set(merged.modules) == {"one", "two"}


# ---------------------------------------------------------------------------
# I/O round-trip
# ---------------------------------------------------------------------------


def test_save_load_roundtrip(tmp_path: Path) -> None:
    m = ObfuscationMapping.from_single_file(
        {"Calculator": "I0", "add": "I1"}, module="calc", root=str(tmp_path)
    )
    p = tmp_path / "mapping.json"
    m.save(p)
    loaded = ObfuscationMapping.load(p)
    assert loaded.modules == m.modules
    assert loaded.reverse("I0") == "Calculator"
    assert loaded.reverse("I1") == "add"


def test_save_creates_parent_dirs(tmp_path: Path) -> None:
    m = ObfuscationMapping.from_single_file({"X": "I0"})
    p = tmp_path / "nested" / "subdir" / "mapping.json"
    m.save(p)
    assert p.exists()


def test_load_unknown_version_rejected(tmp_path: Path) -> None:
    p = tmp_path / "mapping.json"
    p.write_text(json.dumps({"version": 99, "modules": {}, "global": {}}))
    with pytest.raises(ValueError, match="Unsupported mapping version"):
        ObfuscationMapping.load(p)


def test_load_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        ObfuscationMapping.load(Path("/nonexistent/mapping.json"))


def test_load_backfills_global_map_when_missing(tmp_path: Path) -> None:
    """Tolerate forward-only (legacy / hand-written) mapping files."""
    p = tmp_path / "m.json"
    p.write_text(
        json.dumps(
            {
                "version": MAPPING_FORMAT_VERSION,
                "modules": {"mod": {"foo": "I0"}},
                # "global" deliberately omitted
            }
        )
    )
    m = ObfuscationMapping.load(p)
    assert m.reverse("I0") == "foo"


# ---------------------------------------------------------------------------
# Text rewriting
# ---------------------------------------------------------------------------


def test_unmap_text_identifier_boundary_only() -> None:
    m = ObfuscationMapping.from_single_file({"add": "I1"}, module="calc")
    # Must NOT replace I1 inside a longer identifier like XI1Y
    text = "def I1(): pass  # I1 is the function; XI1Y is not"
    out = m.unmap_text(text)
    assert "def add():" in out
    assert "XI1Y" in out  # untouched
    assert "# add is the function" in out


def test_unmap_text_stacktrace_rewrite() -> None:
    m = ObfuscationMapping.from_single_file(
        {"Calculator": "I0", "add": "I1", "x": "I2"}, module="calc"
    )
    trace = (
        'File "dist/calc.py", line 7, in I1\n'
        "    return I0.I2 + other\n"
        "AttributeError: 'I0' object has no attribute 'I2'\n"
    )
    out = m.unmap_text(trace)
    assert 'in add' in out
    assert 'Calculator.x + other' in out
    assert "'Calculator' object has no attribute 'x'" in out


def test_reverse_qualified_dotted_path() -> None:
    m = ObfuscationMapping.from_single_file(
        {"Calculator": "I0", "add": "I1"}, module="calc"
    )
    assert m.reverse_qualified("I0.I1") == "Calculator.add"
    # Unknown parts pass through
    assert m.reverse_qualified("I0.unknown.I1") == "Calculator.unknown.add"


def test_unmap_text_empty_mapping_returns_text_unchanged() -> None:
    m = ObfuscationMapping()
    text = "nothing to see here"
    assert m.unmap_text(text) == text


def test_stats_shape() -> None:
    m = ObfuscationMapping.from_single_file({"a": "I0", "b": "I1"}, module="m")
    s = m.stats()
    assert s == {"modules": 1, "original_names": 2, "unique_obfuscated": 2}
