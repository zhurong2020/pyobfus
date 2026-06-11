# pyobfus skills

A [Claude Code](https://claude.com/claude-code) **skill** that teaches an agent
the full "protect Python before shipping" workflow — obfuscate **and** verify
the output still runs — using pyobfus.

| Skill | What it does |
|---|---|
| [`pyobfus-protect`](pyobfus-protect/SKILL.md) | Drive the scan → preset → obfuscate → **verify** pipeline. Prefers the `pyobfus-mcp` `protect_project` tool when available; falls back to the `pyobfus` CLI. Enforces the safety invariants (keep the mapping private, never obfuscate into the source tree, never claim "ready" without a passing verification). |

## How this differs from `templates/ai-integration/`

- `templates/ai-integration/` are **reference rule-files you copy into your own
  project** so *your* assistant knows pyobfus exists (one fact sheet per tool:
  `AGENTS.md`, `CLAUDE.md`, Cursor, Windsurf, Copilot).
- This `skills/` directory is an **installable capability** — a packaged
  workflow an agent invokes on demand, distributed as a Claude Code plugin.

## Install

This repository is a Claude Code plugin marketplace
(`.claude-plugin/marketplace.json`). From Claude Code:

```
/plugin marketplace add zhurong2020/pyobfus
/plugin install pyobfus@pyobfus
```

Or drop the skill in directly (no plugin system needed):

```bash
mkdir -p ~/.claude/skills
cp -r skills/pyobfus-protect ~/.claude/skills/
```

For the richest experience, also connect the MCP server so the skill can call
`protect_project` and friends in-chat:

```bash
pip install pyobfus-mcp
# then register the `pyobfus-mcp` stdio server in your client
# (see ../pyobfus_mcp/README.md for per-client snippets)
```

## Contributing

PRs welcome at <https://github.com/zhurong2020/pyobfus>.
