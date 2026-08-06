"""
Configuration file validator.

Validates pyobfus YAML configuration files and reports errors/warnings.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import yaml

from pyobfus import config_schema

_JSON_TYPE_TO_LEGACY_TYPE = {
    "string": "str",
    "boolean": "bool",
    "integer": "int",
    "array": "list",
}


def _build_valid_schema() -> Dict[str, Any]:
    """
    Build the schema _validate_dict walks below, derived from
    config_schema.describe_fields()/preset_names() -- see
    pyobfus/config_schema.py's module docstring for why: this dict used to
    be hand-maintained here directly and had silently drifted stale,
    missing `preset` (the key `pyobfus --init` itself writes into every
    config it generates) and every Pro field added since v0.5.0, so
    --validate-config false-warned on --init's own output. Computed once
    at import time from ObfuscationConfig's live dataclass fields, so it
    can't drift out of sync with them again.
    """
    children: Dict[str, Any] = {}
    for entry in config_schema.describe_fields():
        key_schema: Dict[str, Any] = {
            "type": _JSON_TYPE_TO_LEGACY_TYPE.get(entry["json_type"], "str")
        }
        if entry["json_type"] == "array":
            key_schema["item_type"] = _JSON_TYPE_TO_LEGACY_TYPE.get(
                entry.get("item_type", "string"), "str"
            )
        if "valid_values" in entry:
            key_schema["valid_values"] = entry["valid_values"]
        if "min_value" in entry:
            key_schema["min_value"] = entry["min_value"]
        if entry.get("default") is not None:
            key_schema["default"] = entry["default"]
        if entry["pro_only"]:
            key_schema["requires_level"] = "pro"
        children[entry["name"]] = key_schema

    # `preset` isn't an ObfuscationConfig dataclass field -- it's popped
    # and dispatched to get_preset() before the rest of the keys are
    # applied (see ObfuscationConfig.from_file), so it's special-cased
    # here too, same as it always effectively was.
    children["preset"] = {"type": "str", "valid_values": config_schema.preset_names()}

    return {
        "obfuscation": {"type": "dict", "children": children},
        "verbose": {"type": "bool", "default": False},
    }


# Valid configuration schema
VALID_SCHEMA = _build_valid_schema()

# Common typos and their corrections
COMMON_TYPOS = {
    "exclude_pattern": "exclude_patterns",
    "exclude_name": "exclude_names",
    "string_encode": "string_encoding",
    "string_encrypt": "string_encryption",
    "import_obfuscate": "import_obfuscation",
    "remove_docstring": "remove_docstrings",
    "remove_comment": "remove_comments",
    "obfuscate": "obfuscation",
    "verbose_output": "verbose",
    "antidebug": "anti_debug",
    "anti-debug": "anti_debug",
}


class ValidationResult:
    """Result of configuration validation."""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.suggestions: List[str] = []

    @property
    def is_valid(self) -> bool:
        """Check if configuration is valid (no errors)."""
        return len(self.errors) == 0

    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.errors.append(f"[ERROR] {message}")

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(f"[WARNING] {message}")

    def add_suggestion(self, message: str) -> None:
        """Add a suggestion message."""
        self.suggestions.append(f"[HINT] {message}")

    def get_summary(self) -> str:
        """Get validation summary."""
        if self.is_valid and not self.warnings:
            return "Configuration is valid"
        elif self.is_valid:
            return f"Configuration is valid ({len(self.warnings)} warning(s))"
        else:
            return f"Configuration is invalid ({len(self.errors)} error(s))"


def validate_config_file(config_path: Path) -> ValidationResult:
    """
    Validate a configuration file.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        ValidationResult: Validation result with errors, warnings, and suggestions
    """
    result = ValidationResult()

    # Check file exists
    if not config_path.exists():
        result.add_error(f"Configuration file not found: {config_path}")
        return result

    # Check file extension
    if config_path.suffix.lower() not in [".yaml", ".yml"]:
        result.add_warning(f"Unexpected file extension: {config_path.suffix}")
        result.add_suggestion("Use .yaml or .yml extension for configuration files")

    # Try to parse YAML
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        result.add_error(f"Invalid YAML syntax: {e}")
        return result

    if config is None:
        result.add_error("Configuration file is empty")
        return result

    if not isinstance(config, dict):
        result.add_error("Configuration must be a YAML dictionary")
        return result

    # Validate structure
    _validate_dict(config, VALID_SCHEMA, "", result)

    # Check for typos
    _check_typos(config, result)

    # Check Pro feature requirements
    _check_pro_requirements(config, result)

    return result


def _validate_dict(
    config: Dict[str, Any],
    schema: Dict[str, Any],
    path: str,
    result: ValidationResult,
) -> None:
    """Recursively validate dictionary against schema."""
    for key, value in config.items():
        current_path = f"{path}.{key}" if path else key

        if key not in schema:
            # Unknown key
            result.add_warning(f"Unknown configuration key: '{current_path}'")
            continue

        key_schema = schema[key]
        expected_type = key_schema.get("type")

        # Type validation
        if expected_type == "dict":
            if not isinstance(value, dict):
                result.add_error(f"'{current_path}' must be a dictionary")
            elif "children" in key_schema:
                _validate_dict(value, key_schema["children"], current_path, result)

        elif expected_type == "list":
            if not isinstance(value, list):
                result.add_error(f"'{current_path}' must be a list")
            elif "item_type" in key_schema:
                item_type = key_schema["item_type"]
                for i, item in enumerate(value):
                    if item_type == "str" and not isinstance(item, str):
                        result.add_error(
                            f"'{current_path}[{i}]' must be a string, got {type(item).__name__}"
                        )

        elif expected_type == "str":
            if not isinstance(value, str):
                result.add_error(f"'{current_path}' must be a string")
            elif "valid_values" in key_schema:
                if value not in key_schema["valid_values"]:
                    valid = ", ".join(key_schema["valid_values"])
                    result.add_error(f"'{current_path}' must be one of: {valid} (got '{value}')")

        elif expected_type == "bool":
            if not isinstance(value, bool):
                result.add_error(f"'{current_path}' must be true or false")

        elif expected_type == "int":
            if not isinstance(value, int) or isinstance(value, bool):
                result.add_error(f"'{current_path}' must be an integer")
            elif "min_value" in key_schema and value < key_schema["min_value"]:
                result.add_error(f"'{current_path}' must be >= {key_schema['min_value']}")


def _check_typos(config: Dict[str, Any], result: ValidationResult) -> None:
    """Check for common typos in configuration keys."""

    def check_keys(d: Dict[str, Any], path: str = "") -> None:
        for key in d.keys():
            current_path = f"{path}.{key}" if path else key
            if key in COMMON_TYPOS:
                correct = COMMON_TYPOS[key]
                result.add_warning(f"'{key}' might be a typo")
                result.add_suggestion(f"Did you mean '{correct}'?")
            if isinstance(d[key], dict):
                check_keys(d[key], current_path)

    check_keys(config)


_PRO_ONLY_FIELD_NAMES = [
    entry["name"] for entry in config_schema.describe_fields() if entry["pro_only"]
]


def _check_pro_requirements(config: Dict[str, Any], result: ValidationResult) -> None:
    """
    Check if Pro features are used with correct level.

    Iterates every field config_schema flags pro_only, not a hand-picked
    subset -- the original hardcoded list here (string_encryption /
    import_obfuscation / anti_debug only) predated most of the fields it
    should have covered, same root cause as VALID_SCHEMA's staleness
    above.
    """
    obf = config.get("obfuscation", {})
    level = obf.get("level", "community")

    pro_features = [name for name in _PRO_ONLY_FIELD_NAMES if obf.get(name)]

    if pro_features and level != "pro":
        features = ", ".join(pro_features)
        result.add_warning(f"Pro features ({features}) require 'level: pro'")
        result.add_suggestion("Set 'obfuscation.level: pro' to enable Pro features")


def find_config_file(
    start_path: Optional[Path] = None,
) -> Tuple[Optional[Path], Optional[str]]:
    """
    Auto-discover configuration file.

    Searches for configuration files in this order:
    1. ./pyobfus.yaml
    2. ./pyobfus.yml
    3. ./.pyobfus.yaml
    4. ./.pyobfus.yml
    5. ./pyproject.toml (tool.pyobfus section)

    Args:
        start_path: Starting directory (default: current working directory)

    Returns:
        Tuple[Optional[Path], Optional[str]]: (config_path, config_type) or (None, None) if not found
    """
    if start_path is None:
        start_path = Path.cwd()

    # Check for YAML config files
    yaml_candidates = [
        "pyobfus.yaml",
        "pyobfus.yml",
        ".pyobfus.yaml",
        ".pyobfus.yml",
    ]

    for filename in yaml_candidates:
        config_path = start_path / filename
        if config_path.exists():
            return config_path, "yaml"

    # Check for pyproject.toml
    pyproject_path = start_path / "pyproject.toml"
    if pyproject_path.exists():
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            try:
                import tomli as tomllib
            except ImportError:
                return None, None

        try:
            with open(pyproject_path, "rb") as f:
                pyproject = tomllib.load(f)
            if "tool" in pyproject and "pyobfus" in pyproject["tool"]:
                return pyproject_path, "pyproject"
        except Exception:
            pass

    return None, None
