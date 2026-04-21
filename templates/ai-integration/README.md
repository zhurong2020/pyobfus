# pyobfus AI-integration templates

Drop-in rule files that teach AI coding assistants (Claude Code, Cursor, Windsurf, Zed, GitHub Copilot) how to invoke pyobfus on *your* project. Copy the file that matches your tool into your project root.

| Tool | File to copy | Destination in your repo |
|---|---|---|
| Claude Code | `CLAUDE.md` | Project root (or merge into existing `CLAUDE.md`) |
| Cursor (new) | `cursor-rules.mdc` | `.cursor/rules/pyobfus.mdc` |
| Cursor (legacy) | `.cursorrules` | Project root |
| Windsurf | `windsurfrules.md` | Project root |
| GitHub Copilot | `copilot-instructions.md` | `.github/copilot-instructions.md` |
| Generic agent | `AGENTS.md` | Project root |

All templates are short (~50 lines). They encode the same set of facts:

- What pyobfus does (one sentence)
- When to invoke it (shipping, pre-distribution)
- The standard 3-step workflow: `--check` → `--init` → obfuscate with `--save-mapping`
- Reverse debugging: `pyobfus --unmap ...`
- Which preset to pick per framework

If you use the `pyobfus-mcp` MCP server, most of this is redundant — your agent discovers the tools automatically. Keep the template anyway; it hints to the agent *when* to reach for them.

## Contributing

Have a fix or an additional client (Zed, Continue, Aider)? PRs welcome at https://github.com/zhurong2020/pyobfus.
