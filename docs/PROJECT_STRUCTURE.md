# Project structure

This document is the durable map of pyobfus's source, distribution, and
cross-repository boundaries. Current priorities belong in
[`CURRENT_PLAN_ZH.md`](CURRENT_PLAN_ZH.md); historical implementation detail
belongs in dated design documents.

## System topology

```text
                         developer / CI
                               |
              +----------------+----------------+
              |                                 |
      pyobfus CLI/library                 pyobfus-action
      (public repo, PyPI)               (separate public repo)
              |                                 |
       +------+---------+                 invokes pyobfus
       |                |
  Apache-2.0 Core   Pro builder
                        |
                 generated artifact
                        |
                 pyobfus-runtime
            (separate PyPI distribution)

  pyobfus-mcp and the VS Code extension are separate user interfaces over
  the same CLI/contracts; neither owns the transformation implementation.
```

The builder and target runtime are deliberately different products. Build
machines use `pyobfus` and, for Pro features, a valid licence. Runtime-backed
generated artifacts import the minimal `pyobfus-runtime` distribution on the
target; they do not require the Pro builder or a build licence there.

The GitHub Action lives in `zhurong2020/pyobfus-action`, not this repository.
GitHub Marketplace requires `action.yml` at the repository root, `uses:`
fetches that repository, and the Action's moving `v1` tag must not collide with
Core release tags. It installs or invokes pyobfus; it does not bundle a copy of
the runtime into generated output.

## Repository and distribution map

| Path / repository | Responsibility | Release identity |
|---|---|---|
| `pyobfus/` | Apache-2.0 CLI, library, AST engine, config, scan and reporting contracts | PyPI `pyobfus` (contains source-separated Pro builder too) |
| `pyobfus_pro/` | Proprietary, licence-gated build-time transforms and orchestration | Versioned with the `pyobfus` builder; never part of the Apache-2.0 core |
| `pyobfus_runtime/` | Minimal proprietary runtime imported by generated Pro artifacts | PyPI `pyobfus-runtime`, independently built and published |
| `pyobfus_mcp/` | MCP server exposing eight agent tools | PyPI `pyobfus-mcp`, independent version |
| `vscode-extension/` | VS Code UI and real CLI-contract integration | VS Code Marketplace + Open VSX, independent version |
| `skills/` | Review/protection skills plus plugin metadata | Repository-distributed agent integration assets |
| `cloudflare-worker/` | Licence/trial verification and Stripe fulfillment | Independently deployed Worker; not shipped in Python wheels |
| `landing/` | Commercial landing page | GitHub Pages |
| `zhurong2020/pyobfus-action` | Composite CI wrapper for scan/build, SARIF, JSON and step outputs | GitHub Marketplace, moving `v1` plus immutable tags |
| private `pyobfus-pro-dev` | Original patent-gated v0.5 invention/development record | Historical/read-only; never publish or use as current source |

## Source layout

```text
pyobfus/
├── pyobfus/                 # Core package
│   ├── cli.py               # CLI and stable JSON entry points
│   ├── config.py            # Effective configuration
│   ├── core/                # parser, analyzer, orchestration, reports
│   ├── transformers/        # Core AST transforms
│   └── plugins/             # Core plugin interfaces
├── pyobfus_pro/             # Proprietary build-time implementation
├── pyobfus_runtime/         # Standalone target-runtime project
├── pyobfus_mcp/             # Standalone MCP distribution and tests
├── vscode-extension/        # Standalone Node/VS Code package and tests
├── cloudflare-worker/       # Licence/commerce service
├── skills/                  # Agent skills and marketplace metadata
├── templates/               # Copy-in agent rules and baselines
├── dogfood/                 # Maintained self-dogfooding canary
├── examples/                # User-facing examples
├── integration_tests/       # End-to-end CLI/example tests
├── tests/                   # Core and Pro-builder tests
├── scripts/                 # Shared checks, release and dogfood tooling
├── docs/                    # Product, architecture and operational docs
├── landing/                 # Static product site
└── .github/workflows/       # CI, release, security and docs automation
```

## Ownership and dependency rules

- Core must not import proprietary implementation modules. The CLI may route
  explicitly requested Pro behavior into `pyobfus_pro`; implementation stays
  source-separated.
- Runtime modules must remain usable without `pyobfus_pro`, the CLI,
  transformers, licence client, or build-time state.
- `pyobfus` declares `pyobfus-runtime>=0.1,<1` so builder installations can
  test and describe the target requirement. Generated artifacts still need
  that dependency installed in their deployment environment.
- MCP, VS Code, and Action consume public CLI/JSON contracts. A consumer-side
  workaround must not silently redefine those contracts; fix the owning layer
  and add contract tests instead.
- Each independently released surface keeps its own changelog and version.
  A Core release never implies an Action, MCP, runtime, or extension release.

## Test boundaries

Run the roots separately because CI treats them as separate contracts:

```bash
scripts/check.sh
venv/bin/pytest tests/
venv/bin/pytest pyobfus_mcp/tests/
venv/bin/pytest integration_tests/
venv/bin/pytest pyobfus_runtime/tests/
```

The VS Code package has its own Node toolchain; see `AGENTS.md` for the exact
commands and interpreter requirement. The external Action repository runs its
composite action against real fixtures on Ubuntu, macOS, and Windows; follow
that repository's `AGENTS.md` and `CONTRIBUTING.md` for its checks.

## Where changes belong

| Change | Owning location |
|---|---|
| Parser, transform, config, scan, JSON or SARIF behavior | `pyobfus/` + `tests/` |
| Pro build mechanism | `pyobfus_pro/` + core routing tests |
| Code imported by a generated target artifact | `pyobfus_runtime/` + boundary tests |
| MCP tool surface | `pyobfus_mcp/` |
| Editor UX | `vscode-extension/` |
| CI wrapper inputs, outputs, summary or failure semantics | external `pyobfus-action` repo |
| Licence/trial/Stripe server behavior | `cloudflare-worker/` |

When a package or repository boundary changes, update the owning README and
changelog, this document, [`SUPPORT_MATRIX.md`](SUPPORT_MATRIX.md), and
[`THREAT_MODEL.md`](THREAT_MODEL.md) when their claims are affected. The
cross-repository audit and maintenance rule are recorded in
[`CROSS_REPO_DOC_SYNC_AUDIT_2026-10-02.md`](CROSS_REPO_DOC_SYNC_AUDIT_2026-10-02.md).
