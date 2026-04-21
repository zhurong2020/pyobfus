"""pyobfus-mcp — Model Context Protocol server for pyobfus.

Exposes pyobfus's core AI-native tools (preflight check, project init,
unmap, preset listing) to MCP-capable clients: Claude Desktop, Claude
Code, Cursor, Windsurf, Zed, and anything else that speaks MCP.

See README.md in this directory for install + configuration snippets.
"""

__version__ = "0.1.0"

from pyobfus_mcp.tools import (
    check_obfuscation_risks,
    generate_pyobfus_config,
    unmap_stack_trace,
    list_presets,
    explain_preset,
)

__all__ = [
    "check_obfuscation_risks",
    "generate_pyobfus_config",
    "unmap_stack_trace",
    "list_presets",
    "explain_preset",
]
