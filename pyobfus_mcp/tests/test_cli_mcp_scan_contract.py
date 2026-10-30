"""CLI and MCP retain distinct envelopes but agree on scan exit meaning."""

import json

from click.testing import CliRunner
import pytest

from pyobfus.cli import main
from pyobfus_mcp.tools import check_obfuscation_risks


@pytest.mark.parametrize(
    "source,exit_code,status",
    [
        ("value = 1\n", 0, "success"),
        ("eval(input())\n", 1, "warnings"),
        ("def broken(:\n", 2, "error"),
    ],
)
def test_scan_contracts(tmp_path, source, exit_code, status):
    file = tmp_path / "app.py"
    file.write_text(source)
    cli = CliRunner().invoke(main, ["--check", str(file), "--offline", "--json"])
    assert cli.exit_code == exit_code, cli.output
    report = json.loads(cli.output)
    assert report["exit_code"] == exit_code
    assert "status" not in report  # Existing CLI format, not an MCP envelope.
    mcp = check_obfuscation_risks(str(file))
    assert mcp["status"] == status
    assert mcp["exit_code"] == exit_code
    assert mcp["severity_counts"] == report["severity_counts"]
    assert mcp["ai_hint"] and "next_tool" in mcp
    if exit_code == 2:
        assert mcp["next_tool"]["tool"] is None
        assert "pro_value" not in mcp


def test_missing_scan_target_is_mcp_error(tmp_path):
    result = check_obfuscation_risks(str(tmp_path / "missing.py"))
    assert result["status"] == "error"
    assert result["ai_hint"] and "next_tool" in result
