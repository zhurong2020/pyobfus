#!/usr/bin/env python3
"""
Generate vscode-extension/schemas/pyobfus.schema.json (JSON Schema
draft-07) from pyobfus.config_schema's introspection of ObfuscationConfig's
actual dataclass fields.

Dev-time / release-time tool, not a runtime dependency of pyobfus itself --
same "generate a frozen artifact at release time, CI-check it hasn't
drifted" pattern pyobfus_mcp/tool_manifest.py already established for
P2-21's rug-pull-resistance manifest. Exists because config_validator.py's
old hand-maintained schema silently drifted stale (missing `preset` and
every Pro field added since v0.5.0) -- see
docs/VSCODE_EXTENSION_PLAN.md's M3 section for the full investigation.
`additionalProperties: false` on the `obfuscation` object is deliberate:
catching a typo'd key with a real-time red squiggle (matching
config_validator.py's existing COMMON_TYPOS intent) is a real reason to
build YAML IntelliSense at all, not just autocomplete.

Usage:
    python scripts/generate_vscode_schema.py           # (re)write the file
    python scripts/generate_vscode_schema.py --check    # exit 1 if the
                                                         # checked-in file is
                                                         # stale (CI)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))  # importable when run standalone, e.g. `python scripts/...py`

from pyobfus.config_schema import describe_fields, preset_names  # noqa: E402

SCHEMA_PATH = _REPO_ROOT / "vscode-extension" / "schemas" / "pyobfus.schema.json"


def _property_for(entry: dict) -> dict:
    prop: dict = {
        "type": [entry["json_type"], "null"] if entry.get("nullable") else entry["json_type"]
    }
    if entry["json_type"] == "array":
        prop["items"] = {"type": entry.get("item_type", "string")}
    if "valid_values" in entry:
        prop["enum"] = entry["valid_values"]
    if "min_value" in entry:
        prop["minimum"] = entry["min_value"]
    if entry["default"] is not None:
        prop["default"] = entry["default"]
    description = entry["description"]
    if entry["pro_only"]:
        description = f"{description} Requires level: pro."
    prop["description"] = description
    return prop


def build_schema() -> dict:
    obfuscation_properties = {entry["name"]: _property_for(entry) for entry in describe_fields()}
    obfuscation_properties["preset"] = {
        "type": "string",
        "enum": preset_names(),
        "description": "Named preset to use as the base configuration; "
        "individual keys below override or extend it.",
    }

    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "pyobfus.yaml",
        "description": "Configuration file for pyobfus, the Python code "
        "obfuscator. Generated from pyobfus/config_schema.py -- do not "
        "hand-edit; run scripts/generate_vscode_schema.py to regenerate.",
        "type": "object",
        "properties": {
            "obfuscation": {
                "type": "object",
                "description": "Obfuscation behavior settings.",
                "properties": obfuscation_properties,
                # Deliberate: see the module docstring above.
                "additionalProperties": False,
            },
            "verbose": {
                "type": "boolean",
                "default": False,
                "description": "Enable verbose CLI output.",
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if the checked-in schema doesn't match what this script would generate, instead of rewriting it.",
    )
    args = parser.parse_args()

    generated = json.dumps(build_schema(), indent=2) + "\n"

    if args.check:
        if not SCHEMA_PATH.exists():
            print(f"MISSING: {SCHEMA_PATH} -- run without --check to generate it.", file=sys.stderr)
            return 1
        current = SCHEMA_PATH.read_text(encoding="utf-8")
        if current != generated:
            print(
                f"STALE: {SCHEMA_PATH} does not match what pyobfus/config_schema.py "
                "would generate right now.",
                file=sys.stderr,
            )
            print("Run: python scripts/generate_vscode_schema.py", file=sys.stderr)
            return 1
        print(f"OK: {SCHEMA_PATH} is up to date.")
        return 0

    SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCHEMA_PATH.write_text(generated, encoding="utf-8")
    print(f"Wrote {SCHEMA_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
