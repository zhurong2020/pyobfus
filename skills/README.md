# pyobfus skills

Two [Claude Code](https://claude.com/claude-code) **skills**, split by whether
they change anything. Both follow the
[agentskills.io](https://agentskills.io) `SKILL.md` format, so they also work
in GitHub Copilot agent mode, Cursor, Codex CLI and other clients that read it.

| Skill | What it does | Writes? |
|---|---|---|
| [`pyobfus-protect`](pyobfus-protect/SKILL.md) | Drive the scan → preset → obfuscate → **verify** pipeline. Prefers the `pyobfus-mcp` `protect_project` tool when available; falls back to the `pyobfus` CLI. Enforces the safety invariants (keep the mapping private, never obfuscate into the source tree, never claim "ready" without a passing verification). | Yes — produces a build |
| [`pyobfus-review`](pyobfus-review/SKILL.md) | Judge whether a project is safe to obfuscate, without changing it: config-aware `--check`, then `--dry-run --json` to show exactly which artifacts a build would emit and which one must stay internal. | No — read-only |

Use `pyobfus-review` for "should we?" and `pyobfus-protect` for "do it". The
review skill refuses to build; it hands off instead.

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

Or drop a skill in directly (no plugin system needed):

```bash
mkdir -p ~/.claude/skills
cp -r skills/pyobfus-protect ~/.claude/skills/
cp -r skills/pyobfus-review ~/.claude/skills/
```

**Repository-scoped instead of user-scoped**: agents that follow the
`.github/skills/` convention (GitHub Copilot agent mode, Cursor, Codex CLI)
pick up skills committed to the repo they are working in, so every contributor
gets them without installing anything:

```bash
mkdir -p .github/skills
cp -r skills/pyobfus-review .github/skills/
```

Copy into *your* project, not into a clone of this one — these skills are for
protecting **your** code. This repository keeps the canonical copies in
`skills/` and deliberately does not duplicate them under its own
`.github/skills/`, because two copies of the same file drift.

For the richest experience, also connect the MCP server so the skill can call
`protect_project` and friends in-chat:

```bash
pip install pyobfus-mcp
# then register the `pyobfus-mcp` stdio server in your client
# (see ../pyobfus_mcp/README.md for per-client snippets)
```

## Contributing

PRs welcome at <https://github.com/zhurong2020/pyobfus>.
