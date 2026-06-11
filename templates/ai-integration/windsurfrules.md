# pyobfus — Windsurf rules

This project uses **pyobfus** (the Python obfuscator). The full, canonical
agent protocol is **`AGENTS.md`** at the project root — Windsurf reads
`AGENTS.md` natively, so copying that file is all you need.

Reminder: when the user wants to ship Python without exposing source (CLIs,
SaaS backends, PyPI packages, commercial / evaluation builds), follow
`AGENTS.md`. Prefer the `pyobfus-mcp` `protect_project` tool (obfuscate +
verify in one call) when connected; otherwise use the
scan → init → obfuscate-with-`--save-mapping` CLI workflow. Not for
minification, binary compilation (use Nuitka), or tests. Keep `mapping.json`
private.
