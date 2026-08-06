"""Tests for scripts/generate_vscode_schema.py -- the release-time tool
that emits vscode-extension/schemas/pyobfus.schema.json from
pyobfus.config_schema's introspection. Not part of the pyobfus package
(it's a dev/CI tool, see the script's own docstring), so it's imported by
file path rather than as a package module.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import jsonschema
import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "generate_vscode_schema.py"


def _load_script() -> Any:
    spec = importlib.util.spec_from_file_location("generate_vscode_schema", _SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen() -> Any:
    return _load_script()


@pytest.fixture(scope="module")
def schema(gen: Any) -> dict:
    return gen.build_schema()


def test_generated_schema_is_valid_draft7(schema: dict) -> None:
    jsonschema.Draft7Validator.check_schema(schema)


def test_preset_is_present_with_all_preset_names(gen: Any, schema: dict) -> None:
    """The exact regression this whole investigation started from:
    `preset` must be a recognized, autocompletable key."""
    from pyobfus.config import ObfuscationConfig

    preset_prop = schema["properties"]["obfuscation"]["properties"]["preset"]
    assert preset_prop["enum"] == gen.preset_names() == ObfuscationConfig.list_presets()


def test_every_dataclass_field_is_a_schema_property(schema: dict) -> None:
    from pyobfus.config_schema import describe_fields

    schema_keys = set(schema["properties"]["obfuscation"]["properties"].keys())
    field_names = {entry["name"] for entry in describe_fields()}
    assert field_names <= schema_keys


def test_pro_only_fields_are_annotated_in_their_description(schema: dict) -> None:
    props = schema["properties"]["obfuscation"]["properties"]
    assert "level: pro" in props["selective_opacity"]["description"]
    assert "level: pro" not in props["remove_docstrings"]["description"]


def test_valid_config_document_passes_validation(schema: dict) -> None:
    validator = jsonschema.Draft7Validator(schema)
    doc = {
        "obfuscation": {
            "preset": "balanced",
            "level": "pro",
            "selective_opacity": True,
            "exclude_patterns": ["**/vendor/**"],
        }
    }
    assert list(validator.iter_errors(doc)) == []


def test_typo_d_key_is_rejected(schema: dict) -> None:
    """additionalProperties: false on `obfuscation` is deliberate -- this
    is the real-time-typo-catching value proposition of doing YAML
    IntelliSense at all, matching config_validator.py's COMMON_TYPOS
    intent."""
    validator = jsonschema.Draft7Validator(schema)
    doc = {"obfuscation": {"string_encode": True}}  # real typo from COMMON_TYPOS
    errors = list(validator.iter_errors(doc))
    assert len(errors) >= 1
    assert "string_encode" in errors[0].message


def test_invalid_preset_value_is_rejected(schema: dict) -> None:
    validator = jsonschema.Draft7Validator(schema)
    doc = {"obfuscation": {"preset": "not-a-real-preset"}}
    errors = list(validator.iter_errors(doc))
    assert len(errors) >= 1


def test_wrong_type_is_rejected(schema: dict) -> None:
    validator = jsonschema.Draft7Validator(schema)
    doc = {"obfuscation": {"remove_docstrings": "yes"}}  # should be boolean
    errors = list(validator.iter_errors(doc))
    assert len(errors) >= 1


def test_checked_in_schema_file_is_not_stale(gen: Any) -> None:
    """The actual CI drift guard's logic, exercised directly. If this
    fails locally: run `python scripts/generate_vscode_schema.py`."""
    assert (
        gen.SCHEMA_PATH.exists()
    ), f"{gen.SCHEMA_PATH} doesn't exist -- run scripts/generate_vscode_schema.py"
    current = gen.SCHEMA_PATH.read_text(encoding="utf-8")
    import json

    fresh = json.dumps(gen.build_schema(), indent=2) + "\n"
    assert current == fresh, (
        "vscode-extension/schemas/pyobfus.schema.json is stale -- "
        "run: python scripts/generate_vscode_schema.py"
    )
