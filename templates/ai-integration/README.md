# pyobfus AI-integration templates

Drop-in files that teach AI coding assistants how to invoke pyobfus on *your*
project.

## `AGENTS.md` is the canonical file

The agent protocol now lives in a single canonical **`AGENTS.md`** — the 2026
cross-tool standard, read natively by Cursor, Windsurf, Aider, Continue, Cline,
Codex, and more. The other files are **thin shims that point back to it**, so
there's one source of truth instead of six divergent copies.

| Tool | File to copy | Destination | Notes |
|---|---|---|---|
| **Any agent (canonical)** | `AGENTS.md` | Project root | Read natively by most 2026 agents. Start here. |
| Claude Code | `CLAUDE.md` | Project root | Just `@AGENTS.md`-imports the canonical file. |
| Cursor (new) | `cursor-rules.mdc` | `.cursor/rules/pyobfus.mdc` | Pointer; Cursor also reads `AGENTS.md` directly. |
| Cursor (legacy) | `.cursorrules` | Project root | Pointer. |
| Windsurf | `windsurfrules.md` | Project root | Pointer; Windsurf also reads `AGENTS.md` directly. |
| GitHub Copilot | `copilot-instructions.md` | `.github/copilot-instructions.md` | Self-contained (Copilot does **not** read `AGENTS.md`). |

**Simplest setup**: copy `AGENTS.md` into your project root. Add `CLAUDE.md`
(for Claude Code) and/or `copilot-instructions.md` (for Copilot) only if you use
those tools.

All shims encode the same facts as `AGENTS.md`: what pyobfus does, when to
invoke it, the `--check` → `--init` → obfuscate (`--save-mapping`) workflow,
reverse debugging via `--unmap`, per-framework preset selection, and — when the
`pyobfus-mcp` server is connected — the one-call, self-verifying
`protect_project` tool.

## Want a packaged capability instead of a fact sheet?

These templates teach an agent *about* pyobfus inside your repo. If you'd
rather install a ready-made **skill** that drives the whole protect-and-verify
workflow on demand, see [`../../skills/`](../../skills/) (Claude Code plugin).

## Contributing

Have a fix or an additional client? PRs welcome at https://github.com/zhurong2020/pyobfus.
