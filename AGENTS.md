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

Use the repository-local **`venv/`** on WSL/Linux. Do **not** use `.venv/`:
that directory is a Windows-side legacy environment and WSL cannot reliably run
its executables. Either activate `venv/` first, or call tools through
`venv/bin/...` directly.

```bash
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
git config core.hooksPath .githooks   # once per clone — enables the PII pre-commit guard
```

## Build / test / lint — run before every commit

```bash
venv/bin/pytest tests/                 # core suite (run this and the two below separately)
venv/bin/pytest pyobfus_mcp/tests/     # MCP server suite
venv/bin/pytest integration_tests/     # end-to-end CLI
venv/bin/black pyobfus/                # format
venv/bin/ruff check pyobfus/           # lint
venv/bin/mypy pyobfus/                 # type check
```

Note: the core and MCP test roots are collected as **separate** pytest
invocations (CI runs them as separate jobs) — don't point one `pytest` at both
roots at once.

**4th test root — `vscode-extension/`** (Node/npm, not pytest; independent
package, see `docs/VSCODE_EXTENSION_PLAN.md`):

```bash
cd vscode-extension
npm ci
npm run lint          # eslint
npm run typecheck     # tsc --noEmit
npm run pretest       # esbuild + compile tests to out/
PYOBFUS_PYTHON_PATH="$(cd .. && pwd)/venv/bin/python3" npm test
```

`npm test` needs a **resolvable interpreter with pyobfus actually
installed** for the real-contract integration tests (`test/suite/
integration.test.ts`) — without `PYOBFUS_PYTHON_PATH` set, interpreter
resolution falls back to a bare `python3`/`python` on PATH (the
`ms-python.python` extension isn't active inside the plain
`@vscode/test-electron` test profile), which on a fresh machine likely
doesn't have pyobfus installed and fails 4 of the tests with a "no module
named pyobfus" error — not a real bug, just a missing env var. WSLg (or
any real X server) is required for `@vscode/test-electron` to launch;
`xvfb-run -a npm test` works too if there's no display available.

CI runs this as a separate, path-filtered workflow
(`.github/workflows/vscode-extension-ci.yml`, sets the same env var to
`${{ env.pythonLocation }}/bin/python`), not as part of the Python
`ci.yml` jobs above.

Targets: Python **3.9–3.14** must all pass. (Python 3.8 was dropped in 0.5.0 —
EOL 2024-10 — which removed the old `astunparse`/`@requires_py39` flakiness;
`docs/PYTHON38_COMPATIBILITY.md` is retained only as historical record.)

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

## 🟢 Patent gate — CLEARED 2026-06-17 (v0.5 Pro mechanisms now releasable)

A subset of v0.5 Pro mechanisms was held back under an active patent application
(申请号 202610712171X, priority date 2026-05-22). The gate condition — *patent
formality correction resolved and application status clean* — **was met on
2026-06-17** when CNIPA issued the 初步审查合格通知书 (preliminary examination
passed). Priority is secured, so public disclosure of these mechanisms no longer
risks the application.

These mechanisms now ship to the public repo via a **controlled Phase 5 merge**
(deliberate, one-time public disclosure) — see `docs/V0.5_RELEASE_PLAN.md`. Until
that merge lands, still don't leak unreleased mechanism detail in incidental
commits. The permanent rules remain: `pyobfus-legal/` never enters git (PII), and
Pro/Core source stays separated. See `docs/POST_V0.4_TODO.md` § P1 for status.

## Where to look next

- **Forward TODO / current state**: [`docs/POST_V0.4_TODO.md`](docs/POST_V0.4_TODO.md) (single source of truth).
- **Roadmap**: [`docs/ROADMAP.md`](docs/ROADMAP.md).
- **Contributing**: [`CONTRIBUTING.md`](CONTRIBUTING.md).
- **Security policy**: [`SECURITY.md`](SECURITY.md).
