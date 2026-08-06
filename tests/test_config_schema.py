"""Tests for pyobfus/config_schema.py -- the introspection helper that
derives pyobfus.yaml's recognized keys from ObfuscationConfig's actual
dataclass fields, so config_validator.py's VALID_SCHEMA and the VS Code
extension's generated JSON Schema can't independently drift stale the way
the old hand-maintained VALID_SCHEMA did (missing `preset` and every Pro
field added since v0.5.0 -- see docs/VSCODE_EXTENSION_PLAN.md's M3
section).
"""

from __future__ import annotations

from dataclasses import fields

import pytest

from pyobfus.config import ObfuscationConfig
from pyobfus.config_schema import describe_fields, preset_names


def test_describe_fields_covers_every_dataclass_field() -> None:
    """The whole point: this can never silently omit a field again --
    every ObfuscationConfig dataclass field must appear, by construction,
    not by someone remembering to update a parallel list."""
    described_names = {entry["name"] for entry in describe_fields()}
    actual_names = {f.name for f in fields(ObfuscationConfig)}
    assert described_names == actual_names


def test_describe_fields_flags_known_pro_only_fields() -> None:
    by_name = {entry["name"]: entry for entry in describe_fields()}
    assert by_name["selective_opacity"]["pro_only"] is True
    assert by_name["scrub_traceback"]["pro_only"] is True
    assert by_name["string_encryption"]["pro_only"] is True


def test_describe_fields_does_not_flag_community_fields_pro_only() -> None:
    by_name = {entry["name"]: entry for entry in describe_fields()}
    assert by_name["remove_docstrings"]["pro_only"] is False
    assert by_name["numeric_obfuscation"]["pro_only"] is False


@pytest.mark.parametrize(
    "field_name,expected_json_type",
    [
        ("level", "string"),
        ("remove_docstrings", "boolean"),
        ("license_max_runs", "integer"),
        ("exclude_patterns", "array"),
        ("max_workers", "integer"),  # Optional[int] -- still integer, just nullable
    ],
)
def test_describe_fields_json_types(field_name: str, expected_json_type: str) -> None:
    by_name = {entry["name"]: entry for entry in describe_fields()}
    assert by_name[field_name]["json_type"] == expected_json_type


def test_describe_fields_marks_optional_fields_nullable() -> None:
    by_name = {entry["name"]: entry for entry in describe_fields()}
    assert by_name["max_workers"].get("nullable") is True
    assert by_name["requires_os"].get("nullable") is True
    # A required-with-a-real-default field should not be marked nullable.
    assert "nullable" not in by_name["remove_docstrings"]


def test_describe_fields_array_item_type() -> None:
    by_name = {entry["name"]: entry for entry in describe_fields()}
    assert by_name["exclude_patterns"]["item_type"] == "string"
    assert by_name["exclude_names"]["item_type"] == "string"


def test_describe_fields_exclude_names_default_is_json_safe_sorted_list() -> None:
    """exclude_names is a Set[str] on the dataclass -- sets aren't valid
    JSON, so the introspected default must come back as a sorted list."""
    by_name = {entry["name"]: entry for entry in describe_fields()}
    default = by_name["exclude_names"]["default"]
    assert isinstance(default, list)
    assert default == sorted(default)
    assert "print" in default


def test_describe_fields_level_has_valid_values() -> None:
    by_name = {entry["name"]: entry for entry in describe_fields()}
    assert by_name["level"]["valid_values"] == ["community", "pro"]


def test_describe_fields_min_value_for_community_limits() -> None:
    by_name = {entry["name"]: entry for entry in describe_fields()}
    assert by_name["max_files"]["min_value"] == 1
    assert by_name["max_total_loc"]["min_value"] == 1


def test_describe_fields_unknown_field_gets_generic_description_not_omitted() -> None:
    """Every field gets a description, even ones missing from the
    hand-maintained enrichment dict -- degradation, not omission, is the
    whole design point of this module."""
    for entry in describe_fields():
        assert entry["description"]
        assert isinstance(entry["description"], str)


def test_preset_names_matches_list_presets() -> None:
    assert preset_names() == ObfuscationConfig.list_presets()


def test_preset_names_is_not_empty() -> None:
    assert len(preset_names()) > 5  # sanity: community + framework + pro presets
