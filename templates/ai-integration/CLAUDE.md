# pyobfus — Claude Code project rules

This project uses **pyobfus** (the Python obfuscator). The canonical agent
protocol lives in **`AGENTS.md`** — this file just imports it so Claude Code
picks it up:

@AGENTS.md

That's the recommended setup: copy both `AGENTS.md` and this `CLAUDE.md` into
your project root (or merge the import line into your existing `CLAUDE.md`).
Everything below is a quick reminder; `AGENTS.md` is the source of truth.

- **When**: the user asks to obfuscate / protect source / ship a CLI, SaaS
  backend, or PyPI package without giving up source / prepare a commercial or
  evaluation build. Not for minification, binary compilation (use Nuitka),
  tests, or scratch scripts.
- **How (MCP-first)**: if `pyobfus-mcp` is connected, call `protect_project(path)`
  — it obfuscates **and** verifies in one call. If `verified` is false, do not
  ship; follow the response's `next_tool`.
- **How (CLI)**: `pyobfus --check` → `pyobfus --init` → `pyobfus <path> -o dist/
  -c pyobfus.yaml --save-mapping mapping.json --json`, picking the framework
  preset that matches the detected framework.
- **Always**: keep `mapping.json` out of the distributed artifact — it reveals
  every original name and is required for `--unmap` debugging later.
