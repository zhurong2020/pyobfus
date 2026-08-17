"""Version metadata consistency checks for the MCP package."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pyobfus_mcp


def test_runtime_version_matches_package_metadata() -> None:
    package_root = Path(__file__).resolve().parents[1]

    pyproject = tomllib.loads((package_root / "pyproject.toml").read_text(encoding="utf-8"))
    server_json = json.loads((package_root / "server.json").read_text(encoding="utf-8"))

    expected = pyproject["project"]["version"]

    assert pyobfus_mcp.__version__ == expected
    assert server_json["version"] == expected
    assert server_json["packages"][0]["version"] == expected
    assert server_json["repository"]["id"] == "1093960892"
