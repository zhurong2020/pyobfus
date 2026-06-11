# AGENTS.md — pyobfus

Canonical, tool-agnostic guide for AI coding agents (and humans) working **on**
the pyobfus codebase. Tool-specific files defer here: `CLAUDE.md` imports this
file; Cursor / Windsurf / Aider / Codex read `AGENTS.md` natively.

> Looking to *use* pyobfus to protect your own code, not develop it? See the
> [`pyobfus-protect` skill](skills/pyobfus-protect/SKILL.md) and the
> [`templates/ai-integration/`](templates/ai-integration/) rule files instead.

## What this project is

pyobfus is an **AST-based Python code obfuscator** — framework-aware presets,
reverse stack-trace mapping for AI-assisted debugging, and a machine-readable
JSON CLI. A transparent, open-source alternative to PyArmor. The repo ships
**two packages**:

- `pyobfus/` — the obfuscator (CLI + library). Published as `pyobfus`.
- `pyobfus_mcp/` — an MCP server exposing the tools to AI agents. Published as
  `pyobfus-mcp`.

Plus `pyobfus_pro/` (commercial, license-gated features) kept source-separated
from the Apache-2.0 core.

## Setup

```bash
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
git config core.hooksPath .githooks   # once per clone — enables the PII pre-commit guard
```

## Build / test / lint — run before every commit

```bash
pytest tests/                 # core suite (run this and the two below separately)
pytest pyobfus_mcp/tests/     # MCP server suite
pytest integration_tests/     # end-to-end CLI
black pyobfus/                # format
ruff check pyobfus/           # lint
mypy pyobfus/                 # type check
```

Note: the core and MCP test roots are collected as **separate** pytest
invocations (CI runs them as separate jobs) — don't point one `pytest` at both
roots at once.

Targets: Python **3.8–3.14** must all pass. New Pro-feature CLI integration
tests need `@requires_py39` — read [`docs/PYTHON38_COMPATIBILITY.md`](docs/PYTHON38_COMPATIBILITY.md)
first (astunparse output is unstable on 3.8).

## Repository layout

```
pyobfus/            # core obfuscator: cli.py, config.py, core/, transformers/
pyobfus_mcp/        # MCP server (FastMCP): pyobfus_mcp/{server,tools,_security}.py
pyobfus_pro/        # Pro edition (commercial license) — kept separate from core
skills/             # Claude Code skill (pyobfus-protect) + plugin marketplace
templates/          # copy-in AI rule files + python-baseline bootstrap
tests/ · pyobfus_mcp/tests/ · integration_tests/
docs/               # ROADMAP.md, POST_V0.4_TODO.md (forward TODO SoT), threat model
cloudflare-worker/  # Pro license verification Worker
```

## Conventions

- **Stable JSON contract.** Every CLI mode and MCP tool returns a dict with
  `status`, `ai_hint`, and (MCP) a machine-readable `next_tool` field. Don't
  break these shapes without a version bump.
- **Dual license, separated source.** Never move Pro logic into the Apache-2.0
  core or vice-versa. Never commit Pro license keys or the Stripe webhook secret
  to this public repo.
- **Public repo.** This is `zhurong2020/pyobfus`, public. The PII pre-commit
  hook blocks a fixed set of personal identifiers — keep them out of code,
  commits, and docs.

## ⚠️ Patent gate — read before implementing v0.5 Pro mechanisms

A subset of v0.5 Pro mechanisms is under an active patent application. **Do not
implement or publicly commit those mechanisms in this repo** until the patent
formality correction is resolved and the application status is clean. Naming a
feature in `docs/ROADMAP.md` is fine; revealing its algorithmic mechanism in a
public commit, branch, PR, or issue is not. See `docs/POST_V0.4_TODO.md` for the
current gate status before touching anything marked 🔒.

## Where to look next

- **Forward TODO / current state**: [`docs/POST_V0.4_TODO.md`](docs/POST_V0.4_TODO.md) (single source of truth).
- **Roadmap**: [`docs/ROADMAP.md`](docs/ROADMAP.md).
- **Contributing**: [`CONTRIBUTING.md`](CONTRIBUTING.md).
- **Security policy**: [`SECURITY.md`](SECURITY.md).
