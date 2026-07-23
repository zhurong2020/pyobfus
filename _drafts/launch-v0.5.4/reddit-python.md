# r/Python monthly showcase entry

The 2026 r/Python rules direct project showcases to the designated showcase
thread. Do not use the old standalone-post draft without re-checking the rules.

**Facts re-verified**: 2026-07-22

- Latest Core release: `pyobfus 0.5.4` (2026-07-19).
- Latest MCP release: `pyobfus-mcp 0.3.1` (2026-06-22); unchanged because the
  0.5.4 release did not change the eight-tool MCP surface.
- Core compatibility: Python 3.9-3.14.
- Release-CI evidence: 1,046 passed, 1 skipped, 90% Core coverage; separate
  Core, MCP, and end-to-end jobs across Ubuntu, macOS, and Windows.
- Current destination:
  <https://www.reddit.com/r/Python/comments/1unctej/showcase_thread/>

## Suggested comment

**pyobfus 0.5.4 + pyobfus-mcp 0.3.1 — AST obfuscation with reversible crash traces**

Repository: <https://github.com/zhurong2020/pyobfus>

**What My Project Does**

I maintain pyobfus, an AST-based Python obfuscator. It renames identifiers, preserves
reflection-sensitive APIs through FastAPI, Django, Flask, Pydantic, Click, and
SQLAlchemy presets, and can save a private mapping that restores original names
in an obfuscated production traceback.

The separate `pyobfus-mcp` package exposes eight tools for coding agents:
project risk scanning, configuration generation, preset discovery, tier
recommendation, trial guidance, traceback unmapping, and a one-call
protect-and-verify pipeline. Tool results include structured `status`,
`ai_hint`, and `next_tool` fields instead of requiring an agent to scrape
terminal text.

**Target Audience**

Python developers and small teams distributing applications or libraries who
want to make casual source inspection harder without giving up readable crash
triage. The Community Core is Apache-2.0 and usable on its own; optional Pro
features are separately licensed and source-separated.

**Comparison**

The design trade-off is deliberate: pyobfus keeps the normal Python packaging
workflow and raises the cost of source inspection, while the developer retains
a local reverse mapping for debugging. It is not native compilation, a virtual
machine, or a hardware security boundary. An attacker who controls a running
process can still use dynamic analysis or extract material from memory.

Compared with a CLI-only workflow, the JSON contract and MCP server let an
agent scan, configure, protect, verify, and unmap through explicit schemas. The
mapping remains local and is never intended to ship with the protected output.

**What Is New**

Version 0.5.4 extends Pro device binding to every Runtime String Vault key.
Each vault receives a distinct salt, and its key is derived from the bound host
at runtime instead of shipping as a baked constant. `pyobfus-mcp` remains at
0.3.1 because this release did not change its eight-tool interface.

The release CI recorded 1,046 passing Core tests, one skip, and 90% coverage.
Core, MCP, and end-to-end suites run separately across Python 3.9-3.14 on
Ubuntu, macOS, and Windows.

**Quick Start**

```bash
pip install pyobfus
pyobfus --check src/ --json
pyobfus src/ -o dist/ --save-mapping mapping.json
```

For an MCP client, the local stdio server command is:

```bash
uvx pyobfus-mcp
```

Most useful feedback: a framework compatibility failure I can reproduce, or a
spot where the threat model above doesn't hold up. If there's an integration
missing from your actual packaging or agent workflow, say which one.
