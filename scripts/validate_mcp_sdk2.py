#!/usr/bin/env python3
"""Exercise all nine tools over real SDK 2.x legacy/auto stdio sessions.

Run using a clean environment with an installed MCP wheel, the public Core and
SDK 2.x installed through normal dependency resolution. All tool writes and
product state belong to a temporary synthetic project. No trial is activated,
no user application runs, and no tool requests network access.
"""

from __future__ import annotations

import asyncio
import importlib.metadata
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


def _payload(result: Any) -> dict[str, Any]:
    wire = result.model_dump(mode="json", by_alias=True)
    if wire.get("isError", wire.get("is_error", False)):
        raise AssertionError("MCP tool failed at the protocol boundary")
    structured = wire.get("structuredContent", wire.get("structured_content"))
    if not isinstance(structured, dict):
        for content in wire.get("content", []):
            if content.get("type") == "text":
                try:
                    structured = json.loads(content["text"])
                    break
                except ValueError:
                    continue
    if isinstance(structured, dict) and isinstance(structured.get("result"), dict):
        structured = structured["result"]
    assert isinstance(structured, dict), "Missing structured tool result"
    assert structured.get("status") not in (None, "error", "fail"), structured.get("error_type")
    assert isinstance(structured.get("ai_hint"), str) and structured["ai_hint"]
    next_tool = structured.get("next_tool")
    assert isinstance(next_tool, dict) and set(next_tool) == {"tool", "reason", "args"}
    assert next_tool["tool"] is None or isinstance(next_tool["tool"], str)
    assert isinstance(next_tool["reason"], str) and next_tool["reason"]
    assert isinstance(next_tool["args"], dict)
    return structured


async def validate() -> dict[str, Any]:
    from mcp import Client
    from mcp.client.stdio import StdioServerParameters, stdio_client

    sdk = importlib.metadata.version("mcp")
    assert sdk.split(".")[0] == "2", "This validation requires mcp SDK 2.x"
    sessions = []
    for mode in ("legacy", "auto"):
        with tempfile.TemporaryDirectory(prefix="pyobfus-mcp2-") as temporary:
            root = Path(temporary)
            source = root / "src"
            source.mkdir()
            (source / "algorithm.py").write_text(
                "def calculate(value):\n    return value * 2\n", encoding="utf-8"
            )
            mapping = root / "names.json"
            mapping.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "mode": "single_file",
                        "modules": {"algorithm": {"calculate": "I0"}},
                        "global": {"I0": {"module": "algorithm", "original": "calculate"}},
                    }
                ),
                encoding="utf-8",
            )
            output = root / "protected"
            env = dict(
                os.environ,
                HOME=str(root / "home"),
                USERPROFILE=str(root / "home"),
                PYOBFUS_MCP_PROJECT_ROOT=str(root),
            )
            parameters = StdioServerParameters(
                command=sys.executable,
                args=["-I", "-m", "pyobfus_mcp.server"],
                env=env,
            )
            async with Client(
                stdio_client(parameters), mode=mode, read_timeout_seconds=60
            ) as client:
                listed = await client.list_tools()
                tools = listed.tools if hasattr(listed, "tools") else listed
                names = {tool.name for tool in tools}
                calls = [
                    ("list_presets", {}),
                    ("explain_preset", {"name": "balanced"}),
                    ("check_obfuscation_risks", {"path": str(source)}),
                    ("generate_pyobfus_config", {"path": str(source)}),
                    ("recommend_tier", {"path": str(source)}),
                    ("start_pro_trial", {}),
                    ("unmap_stack_trace", {"trace": "in I0", "mapping_path": str(mapping)}),
                    ("protect_project", {"path": str(source), "output_dir": str(output)}),
                    ("check_delivery", {"path": str(output)}),
                ]
                assert names == {name for name, _ in calls}, "Tool manifest drift"
                statuses = {}
                for name, arguments in calls:
                    payload = _payload(await client.call_tool(name, arguments))
                    if name == "unmap_stack_trace":
                        assert "calculate" in payload["unmapped_trace"]
                    if name == "protect_project":
                        assert payload["verified"] is True, "Protected synthetic output failed"
                    statuses[name] = payload["status"]
                assert not (root / "home" / ".pyobfus" / "trial.json").exists()
                assert not (root / "home" / ".pyobfus" / "license.json").exists()
                info = client.server_info
                sessions.append(
                    {
                        "mode": mode,
                        "protocol": client.protocol_version,
                        "server": (
                            info.model_dump(mode="json")
                            if hasattr(info, "model_dump")
                            else str(info)
                        ),
                        "tool_count": len(names),
                        "tool_statuses": statuses,
                    }
                )
    return {
        "sdk": sdk,
        "python": sys.version.split()[0],
        "core": importlib.metadata.version("pyobfus"),
        "mcp_package": importlib.metadata.version("pyobfus-mcp"),
        "sessions": sessions,
    }


if __name__ == "__main__":
    print(json.dumps(asyncio.run(validate()), indent=2, sort_keys=True))
