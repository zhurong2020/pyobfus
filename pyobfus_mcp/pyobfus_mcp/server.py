"""
MCP server entry point for pyobfus.

Uses the official Model Context Protocol Python SDK
(https://github.com/modelcontextprotocol/python-sdk). Install with:

    pip install pyobfus-mcp

Registers the pyobfus tools as MCP tool handlers and runs over stdio
(the transport used by Claude Desktop, Claude Code, Cursor, Windsurf,
and Zed). The tool implementations are pure Python in
`pyobfus_mcp.tools` and are independently testable — this module is
just a thin adapter.

Configure in Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json`
on macOS, `%APPDATA%\\Claude\\claude_desktop_config.json` on Windows):

    {
      "mcpServers": {
        "pyobfus": {
          "command": "pyobfus-mcp"
        }
      }
    }

Equivalent snippets for Cursor (`~/.cursor/mcp.json`), Windsurf, and
Zed are in `pyobfus_mcp/README.md`.
"""

from __future__ import annotations

import sys
from typing import Any, Dict, Optional

from pyobfus_mcp import __version__
from pyobfus_mcp.tools import (
    check_obfuscation_risks,
    explain_preset,
    generate_pyobfus_config,
    list_presets,
    unmap_stack_trace,
)


def _build_server() -> Any:
    """Construct and return the MCP Server instance.

    Imported lazily so callers can `from pyobfus_mcp.server import main`
    even if the `mcp` SDK isn't installed (e.g., during unit tests of
    tools.py).
    """
    try:
        from mcp.server.fastmcp import FastMCP  # type: ignore[import-not-found]
    except ImportError as e:  # pragma: no cover — runtime-only
        raise SystemExit(
            "The 'mcp' package is required to run the pyobfus-mcp server.\n"
            "Install it with: pip install mcp\n"
            f"(Original error: {e})"
        )

    app = FastMCP(name="pyobfus", version=__version__)

    # Each decorated function becomes a named MCP tool. Descriptions
    # come from the docstring of the underlying tools.* function.
    @app.tool(
        name="check_obfuscation_risks",
        description=(
            "Scan a Python project for patterns that may break obfuscation "
            "(eval/exec, dynamic attribute access, framework reflection). "
            "Returns severity counts, detected frameworks (FastAPI/Django/"
            "Flask/Pydantic/Click/SQLAlchemy), and a suggested preset."
        ),
    )
    def _check(path: str) -> Dict[str, Any]:
        return check_obfuscation_risks(path)

    @app.tool(
        name="generate_pyobfus_config",
        description=(
            "Generate a pyobfus.yaml for a Python project. Auto-detects "
            "frameworks and applies the matching preset. By default returns "
            "the YAML text without writing to disk; set write=true to persist."
        ),
    )
    def _init(
        path: str, preset_override: Optional[str] = None, write: bool = False
    ) -> Dict[str, Any]:
        return generate_pyobfus_config(path, preset_override=preset_override, write=write)

    @app.tool(
        name="unmap_stack_trace",
        description=(
            "Reverse obfuscated identifiers in a stack trace using a "
            "pyobfus mapping.json. Accepts the trace as plain text and the "
            "path to a mapping file produced by --save-mapping."
        ),
    )
    def _unmap(trace: str, mapping_path: str) -> Dict[str, Any]:
        return unmap_stack_trace(trace, mapping_path)

    @app.tool(
        name="list_presets",
        description=(
            "List every pyobfus preset available, grouped by tier "
            "(community / framework-aware / Pro)."
        ),
    )
    def _list() -> Dict[str, Any]:
        return list_presets()

    @app.tool(
        name="explain_preset",
        description=(
            "Describe what a named preset changes: exclude names count, "
            "exclude patterns, preserve_param_names, docstring handling."
        ),
    )
    def _explain(name: str) -> Dict[str, Any]:
        return explain_preset(name)

    return app


def main() -> None:
    """Entry point invoked by the `pyobfus-mcp` console script."""
    app = _build_server()
    # FastMCP.run() defaults to stdio transport, which is what Claude
    # Desktop / Cursor / Windsurf expect for locally-spawned servers.
    app.run()


if __name__ == "__main__":  # pragma: no cover
    main()


# Backwards-compat export: some test harnesses look for a `tool_functions`
# list. Provide one that enumerates the underlying callable implementations.
tool_functions = [
    check_obfuscation_risks,
    generate_pyobfus_config,
    unmap_stack_trace,
    list_presets,
    explain_preset,
]
