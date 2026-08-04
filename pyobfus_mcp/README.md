# pyobfus-mcp — Model Context Protocol server for pyobfus

<!-- mcp-name: io.github.zhurong2020/pyobfus-mcp -->

**pyobfus-mcp** exposes [pyobfus](https://github.com/zhurong2020/pyobfus) — the Python obfuscator — to any MCP-capable AI coding agent: **Claude Desktop, Claude Code, Cursor, Windsurf, Zed, Codex**, and anything else that speaks the [Model Context Protocol](https://modelcontextprotocol.io/).

Once configured, you can say:

> "Check if this FastAPI project is safe to obfuscate, then generate a pyobfus.yaml for it."

and the agent will autonomously call `check_obfuscation_risks` and `generate_pyobfus_config` — no copy/paste of CLI commands, no manual config editing.

## Tools exposed

| Tool | What it does |
|---|---|
| `protect_project(path, output_dir?, preset?, verify?, verify_cmd?, save_mapping?)` | **One-call, self-verifying pipeline.** Scans risks, picks a framework-aware preset, obfuscates, then byte-compiles and import-smoke-tests the output in isolated subprocesses and returns `verified: true/false` (+ `confidence`). Writes a private de-obfuscation mapping *alongside* (never inside) the output. Reach for this when the user wants to "protect/obfuscate before shipping" and expects a green check, not just a transform. |
| `check_obfuscation_risks(path)` | Pre-flight scan for `eval`/`exec`, dynamic attribute access, framework reflection. Returns severity counts, detected frameworks, and a suggested preset. |
| `generate_pyobfus_config(path, preset_override?, write?)` | Auto-detect framework → generate `pyobfus.yaml`. Returns the YAML text without writing by default; `write=True` persists to disk. |
| `unmap_stack_trace(trace, mapping_path)` | Reverse obfuscated identifiers in a production stack trace using a `mapping.json`. |
| `list_presets()` | Enumerate every preset (community / framework-aware / Pro). |
| `explain_preset(name)` | Describe what a named preset changes: exclusions, docstring handling, parameter preservation. |
| `recommend_tier(path)` | Analyze a project and recommend community vs Pro, with reasoning and concrete next-step commands. |
| `start_pro_trial()` | Return structured guidance for starting the 5-day Pro trial. |

All tools return dicts with a `status` field, a free-text `ai_hint`, and a machine-readable `next_tool` field (`{tool, reason, args}`) so an agent can chain steps deterministically. `verify_cmd` in `protect_project` runs an arbitrary command and is therefore opt-in behind `PYOBFUS_MCP_ALLOW_VERIFY_CMD=1`.

## Install

### Zero-install (recommended)

If you have [`uv`](https://docs.astral.sh/uv/), no separate install step is needed — point your client at `uvx` and it fetches `pyobfus-mcp` (plus `pyobfus` and the MCP SDK) into an ephemeral environment on first run. **No API key required.**

```json
{
  "mcpServers": {
    "pyobfus": {
      "command": "uvx",
      "args": ["pyobfus-mcp"]
    }
  }
}
```

### Or install with pip

```bash
pip install pyobfus-mcp
```

This pulls `pyobfus` and the MCP Python SDK automatically. Then use `"command": "pyobfus-mcp"` in the per-client configs below.

## Configure

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "pyobfus": {
      "command": "pyobfus-mcp"
    }
  }
}
```

Restart Claude Desktop. The pyobfus tools appear in the tool list.

### Cursor

Edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "pyobfus": {
      "command": "pyobfus-mcp"
    }
  }
}
```

### Windsurf

Edit `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "pyobfus": {
      "command": "pyobfus-mcp"
    }
  }
}
```

### Zed

In `~/.config/zed/settings.json`:

```json
{
  "context_servers": {
    "pyobfus": {
      "command": {
        "path": "pyobfus-mcp",
        "args": []
      }
    }
  }
}
```

### Claude Code

```bash
claude mcp add pyobfus pyobfus-mcp
```

## Example session

```
User:  Can you check whether this Python project is safe to obfuscate?
       Path: /Users/me/code/my-api

Agent: [invokes check_obfuscation_risks("/Users/me/code/my-api")]
       I found 2 high-severity and 3 medium-severity patterns. FastAPI is
       detected, so I'd suggest the `fastapi` preset. Want me to generate
       the config?

User:  Yes please, write it.

Agent: [invokes generate_pyobfus_config("/Users/me/code/my-api",
         preset_override="fastapi", write=True)]
       Wrote pyobfus.yaml. Next: pyobfus /Users/me/code/my-api -o dist/
       -c pyobfus.yaml
```

## Debugging obfuscated code with your AI assistant

The killer feature: keep AI-assisted debugging even after you obfuscate.

```
User:  Here's a crash from prod. Can you help?
       [pastes traceback full of I0, I1, I2...]

Agent: [invokes unmap_stack_trace(trace, "path/to/mapping.json")]
       Reversed. The crash is in Calculator.add() called from
       main() — 'Calculator' object has no attribute 'add_x'. Looks like
       a typo in the method call site…
```

## Verifying tool integrity

Tool poisoning / "rug-pulls" — a server's tool descriptions silently
changing after you've reviewed and trusted them — are the #1 threat in
the 2026 MCP security baseline. `pyobfus-mcp-verify` checks the
currently-installed package's tool descriptions/schemas against a
manifest frozen at release time:

```bash
pyobfus-mcp-verify
# OK: tool descriptions match the shipped manifest (digest 5cf4c902d460...).
```

A mismatch (exit code 1) means the installed tools differ from what the
release shipped — worth investigating before trusting the server. This
is a self-consistency digest, not a cryptographic signature: it proves
the package matches its own shipped manifest, not that a specific party
signed it. For stronger assurance, compare the printed digest against
the one published in the [GitHub Release notes](https://github.com/zhurong2020/pyobfus/releases)
for the version you installed.

## License

Apache-2.0. Same as the main pyobfus package. The pyobfus Pro features remain license-gated; this MCP server only wraps the community-tier tools.

## Links

- **Main package**: https://pypi.org/project/pyobfus/
- **Source**: https://github.com/zhurong2020/pyobfus
- **AI integration strategy**: [docs/AI_INTEGRATION_STRATEGY.md](https://github.com/zhurong2020/pyobfus/blob/main/docs/AI_INTEGRATION_STRATEGY.md)
- **MCP specification**: https://modelcontextprotocol.io/
