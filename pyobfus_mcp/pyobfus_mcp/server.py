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

from typing import Any, Dict, Optional

from pyobfus_mcp.tools import (
    check_obfuscation_risks,
    explain_preset,
    generate_pyobfus_config,
    list_presets,
    protect_project,
    recommend_tier,
    start_pro_trial,
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

    # FastMCP dropped the `version=` kwarg between mcp SDK 1.0 and 1.20+.
    # The MCP protocol surfaces server version via the InitializeResult
    # capabilities object; FastMCP populates that from package metadata.
    app = FastMCP(name="pyobfus")

    # Per-tool metadata carried via the `meta` kwarg (mcp 1.27 SDK-native).
    # We use it for tool versioning ("version": "1") and tier classification
    # ("tier": "community" | "pro_funnel"), which downstream aggregators
    # (Glama, Anthropic registry filters) can read to surface "production-
    # ready" / "Pro-aware" badges. Bump version when a tool's request or
    # response schema changes — old client sessions can keep referencing
    # version "1" while new ones move to "2", per the MCP protocol's
    # forward-compatibility model.
    _META_COMMUNITY = {"version": "1", "tier": "community"}
    _META_PRO_FUNNEL = {"version": "1", "tier": "pro_funnel"}

    # Each decorated function becomes a named MCP tool. Descriptions
    # come from the docstring of the underlying tools.* function.
    @app.tool(
        name="protect_project",
        description=(
            "One call to protect a Python project end-to-end AND verify it "
            "still works: scans risks, picks a framework-aware preset, "
            "obfuscates, then byte-compiles + import-smoke-tests the output "
            "in isolated subprocesses and returns verified:true/false. Writes "
            "a private de-obfuscation mapping alongside (not inside) the "
            "output. Use this when the user wants to 'protect/obfuscate before "
            "shipping' and expects a green check, not just a transform."
        ),
        meta=dict(_META_COMMUNITY),
    )
    def _protect_project(
        path: str,
        output_dir: str = "dist",
        preset: Optional[str] = None,
        verify: bool = True,
        verify_cmd: Optional[str] = None,
        save_mapping: bool = True,
        trace_marker: bool = True,
        timeout: int = 120,
    ) -> Dict[str, Any]:
        return protect_project(
            path,
            output_dir=output_dir,
            preset=preset,
            verify=verify,
            verify_cmd=verify_cmd,
            save_mapping=save_mapping,
            trace_marker=trace_marker,
            timeout=timeout,
        )

    @app.tool(
        name="check_obfuscation_risks",
        description=(
            "Scan a Python project for patterns that may break obfuscation "
            "(eval/exec, dynamic attribute access, framework reflection, unsafe model loading). "
            "Returns severity counts, detected frameworks (FastAPI/Django/"
            "Flask/Pydantic/Click/SQLAlchemy/ML), and a suggested preset. Also "
            "locates requirements*.txt / pyproject.toml and, only if "
            "verify_dependencies_online=true, checks each declared dependency "
            "against public PyPI to flag AI-hallucinated ('slopsquatting') "
            "package names -- off by default, this tool makes no outbound "
            "network calls unless you opt in."
        ),
        meta=dict(_META_COMMUNITY),
    )
    def _check(path: str, verify_dependencies_online: bool = False) -> Dict[str, Any]:
        return check_obfuscation_risks(path, verify_dependencies_online=verify_dependencies_online)

    @app.tool(
        name="generate_pyobfus_config",
        description=(
            "Generate a pyobfus.yaml for a Python project. Auto-detects "
            "frameworks and applies the matching preset. By default returns "
            "the YAML text without writing to disk; set write=true to persist."
        ),
        meta=dict(_META_COMMUNITY),
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
        meta=dict(_META_COMMUNITY),
    )
    def _unmap(trace: str, mapping_path: str) -> Dict[str, Any]:
        return unmap_stack_trace(trace, mapping_path)

    @app.tool(
        name="list_presets",
        description=(
            "List every pyobfus preset available, grouped by tier "
            "(community / framework-aware / Pro)."
        ),
        meta=dict(_META_COMMUNITY),
    )
    def _list() -> Dict[str, Any]:
        return list_presets()

    @app.tool(
        name="explain_preset",
        description=(
            "Describe what a named preset changes: exclude names count, "
            "exclude patterns, preserve_param_names, docstring handling. "
            "For Pro presets, returns full pro_unlock metadata (trial "
            "command, checkout URL, price, money-back guarantee)."
        ),
        meta=dict(_META_COMMUNITY),
    )
    def _explain(name: str) -> Dict[str, Any]:
        return explain_preset(name)

    @app.tool(
        name="recommend_tier",
        description=(
            "Analyze a Python project and recommend pyobfus tier "
            "(community vs Pro) with reasons. Combines a preflight scan "
            "with a sensitive-string-literal heuristic. Returns "
            "free_action and pro_action with concrete next-step commands."
        ),
        meta=dict(_META_PRO_FUNNEL),
    )
    def _recommend_tier(path: str) -> Dict[str, Any]:
        return recommend_tier(path)

    @app.tool(
        name="start_pro_trial",
        description=(
            "Return structured guidance for starting the 5-day pyobfus "
            "Pro trial. Does NOT invoke the side effect — the user runs "
            "`pyobfus-trial start` in their shell. Detects whether a "
            "trial is already active and surfaces the appropriate next "
            "step plus post-trial purchase URL."
        ),
        meta=dict(_META_PRO_FUNNEL),
    )
    def _start_pro_trial() -> Dict[str, Any]:
        return start_pro_trial()

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
# Phase 3 added `recommend_tier` and `start_pro_trial` as pro_funnel tools.
tool_functions = [
    protect_project,
    check_obfuscation_risks,
    generate_pyobfus_config,
    unmap_stack_trace,
    list_presets,
    explain_preset,
    recommend_tier,
    start_pro_trial,
]
