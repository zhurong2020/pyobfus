# MCP Registry Publish Plan — pyobfus-mcp

**Status**: DRAFT — awaiting user go-ahead for 0.1.1 release

## Critical finding (from research agent)

The official Anthropic MCP Registry is **no longer a GitHub PR workflow**. The `modelcontextprotocol/servers` repo retired third-party listings; the canonical registry is now `registry.modelcontextprotocol.io`, managed via the `mcp-publisher` CLI tool.

**Source**: `modelcontextprotocol/servers/CONTRIBUTING.md`:
> "The README no longer contains a list of third-party MCP servers — that list has been retired in favor of the MCP Server Registry. To make your server discoverable, follow the quickstart guide to publish it there."

## Why this is actually good news

- **No human review, no CLA, no wait period.** Authentication is via GitHub device flow; publish is programmatic.
- **Namespace is automatic** — our server must be named `io.github.zhurong2020/pyobfus-mcp` (derived from our GitHub account).
- **No PR queue risk** — we're not blocked by upstream review latency.

## Required actions (~ 45 minutes)

### 1. Edit `pyobfus_mcp/README.md` to include the ownership marker

Add to line ~3 (right after the H1):

```markdown
<!-- mcp-name: io.github.zhurong2020/pyobfus-mcp -->
```

This is how the registry verifies PyPI ownership — it reads the string from the PyPI-displayed README.

### 2. Bump `pyobfus_mcp/pyproject.toml` version to `0.1.1`

We need a new PyPI release because the 0.1.0 README on PyPI lacks the marker. Since PyPI disallows re-uploading the same version, 0.1.1 is mandatory even though the code hasn't changed.

Changelog entry for pyobfus-mcp 0.1.1: "Add mcp-name ownership marker required by the MCP Server Registry."

### 3. Create `pyobfus_mcp/server.json`

Exact content (from agent research):

```json
{
  "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
  "name": "io.github.zhurong2020/pyobfus-mcp",
  "title": "pyobfus-mcp",
  "description": "The Python obfuscator for AI-assisted development workflows. Exposes pyobfus tools over MCP: risk analysis, config generation, stack-trace unmapping, and preset browsing.",
  "repository": {
    "url": "https://github.com/zhurong2020/pyobfus",
    "source": "github",
    "subfolder": "pyobfus_mcp"
  },
  "version": "0.1.1",
  "packages": [
    {
      "registryType": "pypi",
      "registryBaseUrl": "https://pypi.org",
      "identifier": "pyobfus-mcp",
      "version": "0.1.1",
      "transport": { "type": "stdio" }
    }
  ]
}
```

### 4. Rebuild + re-upload to PyPI

```bash
cd pyobfus_mcp/
rm -rf dist build pyobfus_mcp.egg-info
python -m build --sdist --wheel
twine check dist/*
twine upload dist/*
```

### 5. Install `mcp-publisher` and publish

```bash
# Linux:
curl -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_linux_amd64.tar.gz" | tar xz mcp-publisher
sudo mv mcp-publisher /usr/local/bin/

# Authenticate (opens GitHub device-flow prompt):
mcp-publisher login github

# Publish from the pyobfus_mcp/ dir where server.json lives:
cd pyobfus_mcp/
mcp-publisher publish
```

Expected result: entry live at `https://registry.modelcontextprotocol.io/` within seconds.

## Secondary distribution — awesome-mcp-servers PRs

The agent noted three high-traffic community "awesome lists" that still accept README-edit PRs:

1. `github.com/punkpeye/awesome-mcp-servers` (largest, active)
2. `github.com/wong2/awesome-mcp-servers`
3. `github.com/appcypher/awesome-mcp-servers`

These are where developers actually browse for new MCP servers. Worth doing after registry publish — 5 minutes each.

## Surprising caveats

- Only `pypi.org` is accepted by the registry. Not private mirrors. (We're fine — we're on pypi.org.)
- The registry is in "preview" — breaking changes and data resets are still possible before GA.
- A registry entry does NOT automatically surface in any client UI; clients query the registry. So discoverability still depends on each AI-tool vendor integrating the registry (which they're doing).

## Decision points for the user

1. **OK to cut pyobfus-mcp 0.1.1 just for the README marker?** (Low risk; version bump is the intended use case per registry docs.)
2. **OK to install `mcp-publisher` and run `login github` + `publish`?** (Device-flow auth; no credentials stored on disk beyond session token.)
3. **Also submit PRs to the 3 awesome-mcp-servers lists?** (Optional, recommended, ~15 min total.)
