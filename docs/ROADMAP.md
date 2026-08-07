# Development Roadmap

This document outlines **future plans** for pyobfus. For released version history, see [CHANGELOG.md](../CHANGELOG.md). For the detailed AI-era positioning strategy, see [AI_INTEGRATION_STRATEGY.md](AI_INTEGRATION_STRATEGY.md). For execution tracking, see [V0.4_EXECUTION_LOG.md](V0.4_EXECUTION_LOG.md).

**Target Users**: Individual developers and small teams shipping Python code in the AI-assisted development era
**Positioning**: The AI-native Python obfuscator — MCP-ready, framework-aware, open-source alternative to PyArmor

---

## Current Status

**Latest (2026-08-06)**: **VS Code extension P2-2 milestone chain complete (M0/M1/M2 all shipped), plus a same-day expedited bugfix patch.** `pyobfus` 0.5.12 released — pure version-bump/CHANGELOG-promotion for M0 (`pyobfus-trial status --json` / `pyobfus-license status --json`, code already merged 2026-08-04), tagged via OIDC + PEP 740, PyPI confirmed latest. Same session: `vscode-extension` 0.2.0 (M2 — status bar tier indicator, "Generate pyobfus.yaml", right-click "Obfuscate with pyobfus", guided Pro-trial/unlock commands) published to the Marketplace — 24/24 tests green locally against the real CLI, clean `.vsix` package. Along the way, empirically confirmed how to update an *already-listed* Marketplace extension (M1's runbook only covered first-ever publish): a "⋯" overflow menu next to the extension's name → "Update" → upload the new `.vsix` → a transient "verifying `<version>`" state before the public listing flips over — written up in `docs/VSCODE_MARKETPLACE_PUBLISHER_SETUP.md`. Also fixed a small pre-existing gap: the extension's own `CHANGELOG.md` had never split M1's content into a `[0.1.0]` header (M1 and M2 were both sitting under one `[Unreleased]`) — now `[Unreleased]` → `[0.2.0]` → `[0.1.0]`. **Then, hands-on testing of the freshly-shipped 0.2.0 immediately surfaced a real crash** in "Obfuscate with pyobfus": `runJsonCommand` never set an explicit `cwd` for `python -m pyobfus`, which puts cwd first on `sys.path` — an ambient cwd (or sibling) named `pyobfus` shadows the real install as a namespace package. Fixed (`runJsonCommand` now defaults `cwd` to `os.tmpdir()`; the one call site that needs a real project-rooted cwd for `pyobfus.yaml` auto-discovery, `obfuscateFile.ts`, gets a dedicated `cwdForTarget()`) and released same-day as **`vscode-extension` 0.2.1**, jumping the usual spacing gate since it fixes a genuine crash rather than shipping a routine feature. 8 new tests, 32/32 total passing, real CI green. Next PyPI release-spacing gate (per the convention below): eligible **2026-08-08** (2 days after 0.5.12). **M3** (`pyobfus.yaml` IntelliSense) is now **code-complete**, same day as its own scoping: new `pyobfus/config_schema.py` fixes a real core bug found while scoping (`--validate-config` false-warned on `preset` and every Pro field added since v0.5.0) and feeds a JSON Schema (`scripts/generate_vscode_schema.py` → `vscode-extension/schemas/pyobfus.schema.json`) wired into the extension via a declarative `contributes.yamlValidation` entry — simpler than the original design's runtime-API-registration plan, revised mid-implementation after finding `redhat.vscode-yaml`'s docs supported a purely declarative path with no activation-order risk. Held for its own Marketplace gate as v0.3.0; see `docs/VSCODE_EXTENSION_PLAN.md`'s M3 section for the full account.

**Prior (2026-08-04)**: **Six-feature release day** — pyobfus 0.5.8 (P2-13 PyInstaller cookbook) → 0.5.9 (P2-16 `@requires_runtime` policy decorator) → mcp-0.3.4 (P2-12 PII-shape detection) → 0.5.10 (P2-14 `--embed-data`) → 0.5.11 (P2-15 native anti-debug) → mcp-0.3.5 (P2-21 tool-description integrity), all via OIDC + PEP 740 attestations, MCP Registry re-published (`isLatest=0.3.5`). A one-time exception to the batch cadence — see the release-spacing gate note under P2-2 below for the going-forward rule. Same day: scoped and shipped the **VS Code extension** (P2-2) after real competitive research (see P2-2 entry) — **M1 published same-day** as `pyobfus` v0.1.0 on the VS Code Marketplace (publisher `zhurong2020`, https://marketplace.visualstudio.com/items?itemName=zhurong2020.pyobfus), while M0 (CLI `--json` prerequisite) stays code-complete-but-held on its own 2026-08-06 gate. Also caught and fixed a pre-existing CI regression (P2-15 anti-debug tests failing under `--cov`, red on `main` for 3 commits before v0.5.11, unnoticed until checked). Full detail: `CLAUDE.md` cold-start block, `docs/VSCODE_EXTENSION_PLAN.md`.

**Prior (2026-08-02)**: **pyobfus 0.5.7 prepared for release** with **P2-4** (`--import-obfuscation`, Pro) and **P2-22** (honest AST-vs-bytecode comparison content). `--import-obfuscation` rewrites top-level imports to runtime `importlib` / `__import__` calls and auto-enables AES so import strings do not remain plaintext; P2-22 updates `docs/COMPARISON.md` and the README FAQ with the honest PyArmor-alternative framing that bytecode protection is a stronger speed bump, not irreversible client-side cryptography. Full core/MCP/integration test roots passed locally before release prep. `pyobfus-mcp` stays 0.3.2 because there is no MCP tool-surface change.

**Earlier (2026-08-02)**: **pyobfus 0.5.6 released**, same day as 0.5.5. **0.5.5** shipped **P2-17** (`--provenance-manifest` — local JSON build-provenance manifest) and **P2-19** (`--preset ml` — community-tier model-serving preset), both implemented by Codex CLI and reviewed/finished by Claude Code (PRs #26/#27). Review surfaced a real bug — issue #25 — where a preset's `preserve_param_names`/`remove_docstrings`/`remove_comments` choices were silently clobbered by the CLI's own option defaults on the normal, documented invocation (no extra flags); **0.5.6 fixes it** by making those three CLI flags tri-state, closes issue #25, and also sweeps 2 open CodeQL `py/overly-permissive-file` alerts in the P2-18 benchmark's Docker-executor sandbox (one code-fixed, one dismissed with a documented rationale). Full detail: `docs/POST_V0.4_TODO.md` § items 6-7, memory-equivalent write-ups `docs/LLM_RESISTANCE_PILOT_RESULTS_2026-08-01.md` (P2-18) and the 0.5.6 release commits (`4f53c2e`, `8ec8abc`). **pyobfus-mcp released 0.3.2 the same day** — docs/metadata-only (no tool-surface change): `server.json`'s framework-preset and target-client arrays now name `ml` and `codex`, per `docs/DOC_SYNC_AUDIT_2026-08-02.md`. PyPI + MCP Registry both confirmed `isLatest`. Also submitted pyobfus to the Claude Code community plugin directory (`platform.claude.com/plugins/submit`), status "submitted and pending review."

**Earlier (2026-07-19)**: **pyobfus 0.5.4 released** — `--bind-device` now derives both Selective Opacity L3 keys and every Runtime String Vault key from the bound machine, closing the remaining baked-Vault-key scope boundary. The release CI recorded **1046 passed / 1 skipped / 90% coverage** in the core suite; Core, MCP, and end-to-end roots run as separate jobs across Python 3.9-3.14 and three operating systems. Published through OIDC with PEP 740 attestations. **pyobfus-mcp stays 0.3.1** because the MCP tool surface did not change.

**Earlier (2026-06-22)**: **pyobfus 0.5.2 + pyobfus-mcp 0.3.1 published to PyPI** (0.5.0 was 2026-06-18; 0.5.1 same day). 0.5.1 fused the 6 v0.5 Pro mechanisms into flags on the normal obfuscation command; **0.5.2 is a patch fixing `--seal-code`/`--vault` on Python 3.9/3.10** (seal hash pinned to marshal v2; `zip(strict=)` dropped from the vault pass; 1025 core tests). mcp 0.3.1 names the v0.5 mechanisms in pro-funnel copy (dep `pyobfus>=0.5.1`); MCP Registry 0.3.1 isLatest; all via OIDC + PEP 740 attestations. Patent gate cleared 2026-06-17 (申请号 202610712171X). Ran the **agentic-discoverability Wave A** (Smithery Skill + mcp.so + `uvx` zero-install + sharpened server.json blurb) — see `docs/AGENTIC_DISCOVERABILITY_2026-06-22.md`. **JOSS paper desk-rejected 2026-06-24** (issue `openjournals/joss-reviews#10788`; grounds = scope/significance, not quality: "private-dev-then-public" + no demonstrated third-party reuse). Pivoted to the free path: **Zenodo concept DOI `10.5281/zenodo.20846053`** now minted and propagated (CITATION.cff, README badge, ORCID, arong.eu.org). See `docs/JOSS_REJECTION_20260624.md`.

### Snapshot (2026-05-07, historical)

See [CHANGELOG.md](../CHANGELOG.md) for the latest release and version history.

- **pyobfus 0.4.0** released 2026-04-22 (AI-native CLI + framework presets + reverse stack-trace mapping)
- **pyobfus-mcp 0.1.2** released 2026-05-07 (emergency fix for `FastMCP.__init__()` `version=` kwarg drift in mcp SDK ≥ 1.20; see `pyobfus_mcp/CHANGELOG.md`)
- At the current 0.5.4 baseline: 1046 core tests passed, 1 skipped, 90% coverage (multi-OS CI/CD across Python 3.9-3.14)
- Full Pro feature set available
- Parallel file processing support (`-j/--jobs`)
- PyPI downloads: pyobfus ~337/month, pyobfus-mcp ~239/month (real users only, ex-mirrors)
- GitHub stars: 0 — launch posts drafted in `_drafts/` (dev.to / HN / Reddit / CN tri-platform), pending human-voice rewrite + GPTZero gate before publication
- **Glama listing live** at <https://glama.ai/mcp/servers/zhurong2020/pyobfus> with Quality grade **A**, all 7 MCP tools individually A
- **Anthropic MCP Registry**: `io.github.zhurong2020/pyobfus-mcp` v0.2.0 active and isLatest
- **awesome-mcp-servers** [#5777](https://github.com/punkpeye/awesome-mcp-servers/pull/5777) **MERGED 2026-06-06** — pyobfus-mcp now listed in `punkpeye/awesome-mcp-servers` (86K★) under Developer Tools

---

## Strategic Shift (2026-04): AI-Native Positioning

After competitive analysis and PyPI/GitHub signal review, the roadmap below has been reshaped around two insights:

1. **Feature gaps blocking adoption** are not more obfuscation techniques — they are friction points (framework incompatibility, debugging blocker, zero-config onboarding)
2. **AI coding tools** (Claude Code, Cursor, Copilot, Windsurf) are becoming the primary tool-discovery channel. pyobfus must be "AI-native" to be recommended.

The previous v0.4.0 plan (Enhanced Key Obfuscation, Code Compression) has been deprioritized in favor of the plan below.

---

## v0.4.0 - Foundation for Adoption (4-6 weeks)

**Goal**: Remove adoption friction + make pyobfus AI-discoverable.

### P0 - Must Ship (Weeks 1-3)

Core functionality that unblocks real user scenarios and becomes the foundation for AI integration.

- [x] **P0-1: `pyobfus --check` pre-flight mode** — Scan project for `eval`/`exec`/`getattr`/dynamic attribute access, framework reflection points, `__all__` exports. Output JSON risk report with `ai-hint` field suggesting next command. _Shipped 0.4.0._
- [x] **P0-2: `pyobfus unmap` reverse mapping command** — Input error stacktrace + mapping.json → output original variable-name trace. Unlocks "AI can still debug obfuscated code". _Shipped 0.4.0._
- [x] **P0-3: Framework presets** — `--preset fastapi|django|flask|pydantic|click` with built-in exclusion rules for each framework's reflection points. _Shipped 0.4.0._
- [x] **P0-4: AI-friendly CLI** — Global `--json` output mode, structured error messages with `ai_hint` field, machine-readable exit codes. _Shipped 0.4.0._
- [x] **P0-5: `pyobfus init`** — Scan project → detect framework → generate `pyobfus.yaml` with auto-exclude list. One-command onboarding. _Shipped 0.4.0._

### P1 - AI Ecosystem Integration (Weeks 4-6)

Builds on top of P0 primitives to make pyobfus appear natively in the AI-assisted workflow.

- [x] **P1-1: `pyobfus-mcp` server** (separate package) — Expose P0 tools as Model Context Protocol server for Claude Desktop / Claude Code / Cursor / Windsurf / Codex. _Shipped; current package 0.3.2._
- [x] **P1-2: `llms.txt` + `llms-full.txt`** — Deploy at repo root and docs site. _Shipped._
- [x] **P1-3: AI integration templates** — `templates/ai-integration/` with CLAUDE.md, .cursorrules, AGENTS.md, windsurfrules.md. _Shipped._
- [x] **P1-4: PyPI metadata overhaul** — New keyword-dense description, Project-URL additions (MCP Server, AI Guide), Development Status → Production/Stable. _Shipped._
- [x] **P1-5: Incremental obfuscation** — Project-level AST/config hash cache behind `--incremental`, reusing an unchanged successful build. _Shipped._

### Branding & Discoverability (Parallel, Week 1)

- [~] Reserve PyPI alias packages: `python-obfuscator`, `pyobfuscator`, `py-obfuscator` (if available). `python-obfuscator` and `pyobfuscator`/`PyObfuscator` are already occupied by third-party projects; `py-obfuscator` currently returns 404 on PyPI's JSON API and is the only remaining possible alias, requiring a maintainer-side PyPI publish/claim if still wanted.
- [x] Add GitHub topics: `python-obfuscator`, `code-obfuscator`, `ast-obfuscation`, `mcp-server`, `claude-code`, `cursor`, `llm-tools`. _Verified 2026-08-02; all listed topics are present._
- [x] README: add pronunciation / alias line: "pyobfus — the Python obfuscator"
- [x] Upgrade classifier: Core is now `Development Status :: 5 - Production/Stable`; MCP remains Beta

---

## v0.5.0 - AI-Native Differentiation (Weeks 7-14)

**Goal**: Establish a defensible position PyArmor cannot easily copy.

### P2 - Differentiation Layer

- [x] **P2-1: Selective Opacity (Layered Protection)** — per-symbol layers (transparent / ai-readable / obfuscated / encrypted); L3 = AES-256-GCM with lazy `__code__` materialization. _Shipped 0.5.0 2026-06-18 (mechanism + API; combined Pro-flag fusion in 0.5.1)._
- [~] **P2-2: VSCode Extension** — _Scoped 2026-08-04 after real market research, replacing the one-line stub._ No competitor (PyArmor/Nuitka/Sourcedefender) has a VS Code extension — first-mover. Real trust risk to design around: a malicious extension literally named "Python Obfuscator for VSCode" (300K+ installs, XMRig cryptominer campaign, April 2025) poisoned this exact category's reputation — pyobfus's listing leans on its verifiable trust infra (OpenSSF badge, PEP 740, provenance + tool-integrity manifests) explicitly. Headline v1 feature re-prioritized from the stub based on 2026 trend research: `pyobfus --check --json` → native `DiagnosticCollection` (Error-Lens-style inline diagnostics, zero core-code changes needed) ranks above "right-click obfuscate" (weakest/most-cloneable differentiator). Full design + staged milestones (M0 CLI `--json` prerequisites → M1 diagnostics+unmap, first Marketplace publish → M2 status bar/funnel → M3 yaml IntelliSense) in `docs/VSCODE_EXTENSION_PLAN.md`. **M0 shipped as pyobfus 0.5.12, 2026-08-06** (`--json` on `pyobfus-trial status`/`pyobfus-license status`, 12 tests). **M1 published 2026-08-04** as `pyobfus` v0.1.0 on the VS Code Marketplace — https://marketplace.visualstudio.com/items?itemName=zhurong2020.pyobfus. **M2 published 2026-08-06** as v0.2.0 (status bar, generate-config, right-click obfuscate, Pro funnel) — https://github.com/zhurong2020/pyobfus/releases/tag/vscode-v0.2.0. **0.2.1 shipped same day** as an expedited bugfix patch — a `cwd`-shadowing crash in "Obfuscate with pyobfus" found via hands-on testing — https://github.com/zhurong2020/pyobfus/releases/tag/vscode-v0.2.1. **M3** (`pyobfus.yaml` IntelliSense) was scoped and built 2026-08-06 (see `docs/VSCODE_EXTENSION_PLAN.md`'s dedicated M3 section for the full account). Scoping surfaced a real **pyobfus core bug** along the way, independent of the extension: `pyobfus/config_validator.py`'s hand-maintained `VALID_SCHEMA` was stale, missing `preset` (which `--init` itself writes into every config) and every Pro field added since v0.5.0, so `--validate-config` false-warned on `--init`'s own output — reproduced empirically, now fixed. New `pyobfus/config_schema.py` introspects `ObfuscationConfig`'s actual dataclass fields and feeds both `config_validator.py` (closes the bug, computed live, nothing cached to drift) and `scripts/generate_vscode_schema.py`, which emits a real JSON Schema draft-07 wired into the extension via a declarative `contributes.yamlValidation` entry in `package.json` — simpler than the original design's runtime-API-registration plan (`redhat.vscode-yaml`'s `registerContributor` API has a documented activation-order reliability gap the declarative path doesn't share), found and swapped in mid-implementation. 23 + 9 + 5 new tests across the two packages.

  **Released 2026-08-07, a day ahead of the originally-projected 2026-08-08 gate, on explicit user request** (one day after 0.5.12 still fits the "1-2 days apart" spacing rule). `pyobfus` **0.5.13** (the `config_schema.py` fix + P2-23 Nuitka-comparison content) tagged, OIDC + PEP 740 release workflow green, confirmed live on PyPI. `vscode-extension` **0.3.0** built, 37/37 tests green (lint/typecheck/pretest/real-contract tests against 0.5.13), packaged as `pyobfus-0.3.0.vsix`, tagged `vscode-v0.3.0` and pushed — **Marketplace upload is the one step that needs a human in a browser** (the "⋯" overflow menu → Update flow from `docs/VSCODE_MARKETPLACE_PUBLISHER_SETUP.md`; no CLI/PAT path exists yet, see M1's Azure DevOps org-creation blocker below), pending as of this write-up. _Estimate: 1-2 weeks total, M0-M2 slices all done in 2 days, M3 scoped+built+tagged in 2 days._

  **🔁 Release-spacing gate (established 2026-08-04)**: per explicit user direction, releases publish 1-2 days apart rather than batched, using this project's own established "wait N days, check at next cold-start" gate convention (no extra scheduling infra). M0/M2 both shipped on their **2026-08-06** gate date as planned; M3 + pyobfus 0.5.13 shipped **2026-08-07** (see above). **Cold-start check** (applies to all future releases): if today's date is on/after the eligible date and the corresponding milestone is code-complete + tests green, promote its CHANGELOG `[Unreleased]` entry to a version, bump the version field, tag, and publish — don't wait to be asked.

  **M1 shipped 2026-08-04**: `vscode-extension/` scaffold, diagnostics provider, reverse-trace command, and `.github/workflows/vscode-extension-ci.yml` all built and verified green in real CI (13/13 tests passing, including a real contract test against actually-installed pyobfus, not mocked). Three real bugs found and fixed along the way via actually running things in CI rather than assuming: non-.ts fixture files silently dropped by `tsc` (twice — `.js` cli-script fixtures, fixed by converting to `.ts`; then a `.py` fixture, fixed with a dedicated copy script since Python obviously can't become TypeScript), and the Extension Host test subprocess not reliably inheriting `actions/setup-python`'s PATH modification (fixed with a `PYOBFUS_PYTHON_PATH` env-var resolution source in `locate.ts` — a generally useful CI/testing escape hatch, not a narrow workaround). **Marketplace publisher registration blocker**: CLI/PAT-based `vsce publish` needs an Azure DevOps org; org creation hit an unresolved "no subscription found" error against two valid M365 Dev Program subscriptions (Owner role, Azure Plan) — a documented gap, not a stale-token issue (that fix, forcing re-auth via the Azure Portal directory switcher, was tried and didn't resolve it). Worked around entirely via the Marketplace web UI's manual `.vsix` upload path (`marketplace.visualstudio.com/manage/publishers/<publisher>` → "New extension" → "Visual Studio Code"), which uses the web session's own auth and never touches Azure DevOps/PAT machinery — confirmed via the "[Succeeded] Extension publish" email and live listing. Full detail + M4 CI-auto-publish consequence: `docs/VSCODE_EXTENSION_PLAN.md`'s "Marketplace publishing note."

  **M2 code-complete 2026-08-04**: status bar (tier + last-check summary, click → tier-gated QuickPick menu), "Generate pyobfus.yaml" (`--init --json`), "Obfuscate with pyobfus" (Explorer/editor context menus, real obfuscate `--json`, newly typed `ObfuscateSuccessResult`/`ObfuscateErrorResult`), and Pro trial/unlock funnel commands (copy manually synced from `pyobfus/constants.py`, which now names the TS file in its `DOCS_TO_UPDATE` comment). A new `cli/errorReporting.ts` shares the ENOENT-with-actionable-buttons handling across the four new commands rather than growing a third/fourth near-copy of what M1 already had twice. 12 new tests (8 pure-logic for `deriveTier`'s tier-precedence rules, 4 new real-contract integration tests) — 24/24 total passing locally against the actual installed pyobfus (`PYOBFUS_PYTHON_PATH=venv/bin/python3 npm test`); real CI run pending at release time.
- [x] **P2-3: `--strip-ai-artifacts` mode** — Removes AI provenance markers (`Generated by Claude`, `Co-Authored-By: Claude`, `🤖 Generated with`, ...) from docstrings + attribution dunders (`__author__` etc.). Conservative attribution-only matching; arbitrary string literals untouched; comments already dropped by the AST round-trip. Community-tier, 27 tests. _Shipped 2026-06-06 (branch `feat/strip-ai-artifacts`)._
- [x] **P2-4: Import obfuscation (Pro)** — Top-level imports → runtime `importlib` + encrypted strings. Implemented 2026-08-02 behind `--import-obfuscation`: rewrites `import ...` and absolute `from ... import ...`, skips relative / `__future__` / star imports, and auto-enables AES string encryption so module names do not remain plaintext. Full core/MCP/integration test suites plus black/ruff/mypy passed locally. _Remaining before release: human review and release packaging._
- [x] **P2-5: Numeric / Constant obfuscation** — `--numeric-obfuscation`. Opaque arithmetic expressions for number literals (int → XOR/add/sub identities, float → `float.fromhex`). Community-tier, value-preserving, 37 tests. _Shipped 2026-06-06 (branch `feat/numeric-obfuscation`)._
- [x] **P2-6: pyobfus-mcp 0.2.0 production hardening** — _Re-audited 2026-08-04: this item's own title names the version that already shipped it (0.2.0, 2026-05-08) — the checkbox was simply never flipped._ Path scoping (`validate_path`/`PYOBFUS_MCP_PROJECT_ROOT`), sliding-window rate limiting (`check_rate_limit`/`PYOBFUS_MCP_RATE_LIMIT_PER_MIN`), JSON-line audit logging with parameter redaction (`audit_log`/`PYOBFUS_MCP_AUDIT_LOG`), administrative tool gating (`PYOBFUS_MCP_DISABLED_TOOLS`), and soft-imported OpenTelemetry instrumentation are all live in `pyobfus_mcp/_security.py` and wired onto every tool via the `@secure_tool()` decorator (verified in `tools.py`); per-tool versioning ships via the `meta={"version": "1", ...}` kwarg in `server.py`. Only "per-tool authorization" from the original wishlist is unaccounted for, and it is very likely N/A here for the same reason P2-21 below already documents: the 2026-spec OAuth 2.1 / incremental-consent model targets *remote* MCP servers, and pyobfus-mcp is local stdio only. Full detail: `pyobfus_mcp/CHANGELOG.md` `[0.2.0]`.

#### Additions from 2026-05-09 competitive scan

The four items below were surfaced by a competitive feature scan against PyArmor 9.2.x, Nuitka Commercial, Sourcedefender, and vmp-protector 1.0.0. They stay inside the AST + AI-native lane and represent the highest-ROI Pro additions.

- [x] **P2-7: Forensic watermarking / `--fingerprint <buyer-id>` (Pro)** — per-buyer deterministic key derivation (`forensic_seed` / `WatermarkRNG` / `derive_layer_key`) for piracy traceback. _Shipped 0.5.0 2026-06-18 (Pro-layer key watermarking + API; Core rename-RNG single-seed integration in 0.5.1)._
- [x] **P2-8: Hardware / time / period license binding (Pro)** — device / expiry / run-count binding woven into the AES-GCM decryption path (`pyobfus_pro.license_binding`): the license gate is the GCM tag check itself, no separate patchable check. _Shipped 0.5.0 2026-06-18 (mechanism + API; `--bind-device` / `--expire-hard` / `--period` build flags in 0.5.1)._
- [x] **P2-9: `@seal_code` integrity decorator (Pro)** — build-time bytecode hash baked in; runtime detection of in-memory patching, with layer-aware sealing for L3 functions. _Shipped 0.5.0 2026-06-18 (decorator + build pass; combined-flag fusion in 0.5.1)._
- [x] **P2-10: `--scrub-traceback` production traceback encryption (Pro)** — hybrid RSA-2048-OAEP + AES-256-GCM error-ID encryption; developer reverses with the new **`pyobfus-unscrub`** CLI. _Shipped 0.5.0 2026-06-18 (`pyobfus-unscrub` CLI + build pass; `--scrub-traceback` fusion in 0.5.1)._

---

## v0.5.0 — ✅ DONE: dropped Python 3.8 support (2026-06-18)

Python 3.8 reached end-of-life in **October 2024**. The ecosystem has moved on, yet we continue to hit it with recurring CI flakes from `astunparse` (our 3.8 fallback for `ast.unparse()`). Already-documented incidents in [`docs/PYTHON38_COMPATIBILITY.md`](PYTHON38_COMPATIBILITY.md): 8 distinct problems, including the 2026-04 single-Pro-feature CLI flake that required skipping four CLI integration tests on 3.8.

**Proposed action in v0.5**:
- Bump `requires-python = ">=3.9"` in `pyobfus/pyproject.toml`
- Drop the `astunparse` dependency marker (only needed for 3.8)
- Remove `@requires_py39` decorators across the test suite
- Drop `3.8` from the CI matrix
- Remove `docs/PYTHON38_COMPATIBILITY.md` (or move to an archived-notes folder for history)

Benefits: simpler test matrix (~15% faster CI), one less dependency, and eliminates the whole class of astunparse-vs-ast.unparse divergences.

---

## v0.5.1 - Pro Commercial Hardening (4-6 weeks)

**Goal**: Round out the Pro feature surface against the 2026-05-09 competitive scan (PyArmor 9.2.x, Nuitka Commercial, Sourcedefender, vmp-protector 1.0.0, obfuscator-ai). Items here are smaller individually but together close most remaining feature-parity gaps without leaving the AST + AI-native lane.

- [x] **P2-11: Runtime String Vault (Pro)** — encrypted KV namespace for runtime secrets with lazy per-entry AES-256-GCM decryption and schema-without-key queries (`vault_secrets({...})` marker + `Vault`). _Shipped 0.5.0 2026-06-18 (mechanism + API; combined-flag fusion in 0.5.1)._
- [x] **P2-12: `pyobfus-mcp` `scan_secrets` tool** — _Shipped mcp 0.3.4, 2026-08-04, folded into an existing tool rather than standalone._ `check_obfuscation_risks` (and `protect_project`) now detect both credential shapes (API keys/Stripe/AWS/bearer, pre-existing) and PII shapes (emails/IPv4/GUIDs/home-directory paths naming a real user, new — `_PII_LITERAL_PATTERNS`), surfaced as two independent counts (`sensitive_literal_count` / `pii_literal_count`) in the `pro_value` field, since the remediation story differs (encrypt vs. reconsider whether it belongs in source). Deliberate design call: kept folded into the existing tool rather than shipped as a new standalone `scan_secrets` tool, so the MCP tool count stays at 8 and no Glama/Registry tool-surface churn is needed beyond the routine version re-pin. Home-directory-path matching is deliberately narrow (only `/home/<user>/`, `/Users/<user>/`, `C:\Users\<user>\`) to avoid false-positiving on ordinary path literals. 3 new tests, including one asserting generic paths do NOT count as PII.
- [x] **P2-13: PyInstaller integration cookbook** — _Shipped 0.5.8, 2026-08-04 (checkbox missed in that release's own re-audit)._ `examples/pyinstaller/` is a verified end-to-end reproduction (confirmed original identifier names never reach the compiled binary, and `pyobfus --unmap` still reverses a traceback from the bundled executable) + `docs/PYINSTALLER_COOKBOOK.md`, cross-linked from `docs/COMPARISON.md`'s Nuitka section and a README FAQ entry. No code change; redirects Sourcedefender / Nuitka prospects who want single-binary delivery.
- [x] **P2-14: `--embed-data <path>` (Pro)** — _Shipped 0.5.10, 2026-08-04._ AES-256-GCM encrypts a resource file at build time (same cipher construction as the Runtime String Vault) and emits it base85-encoded as a module constant plus a generated `get_embedded_data()` accessor that decrypts on call, not at import. Closes Nuitka Commercial "Protect Data Files" / PyArmor `--bind-data` gap. Not part of the patent-gated combination claims. `pyobfus_pro/runtime/embedded_data.py`, 11 new tests.
- [x] **P2-15: Anti-debug guard (Pro, opt-in)** — _Fully shipped 0.5.11, 2026-08-04._ `--anti-debug` (default OFF) now implements all four detection methods: the original `sys.gettrace()` (Python-level tracers) plus TracerPid (Linux, `/proc/self/status`), WinAPI `IsDebuggerPresent()` (Windows), and a timing-skew check (single-step detection on any platform, generous threshold to avoid false-positiving under CPU throttling). `pyobfus_pro/anti_debug.py`'s `AntiDebugInjector`, 6 new tests exercising the real injected runtime logic via mocks, not just the generated source text.
- [x] **P2-16: `@requires_runtime` policy decorator (Pro)** — _Shipped 0.5.9, 2026-08-04._ `--requires-os` / `--requires-python-min` / `--requires-arch` inject a module-top `requires_runtime(...)` guard (same shape as `--expire-hard`/`--period`) refusing import when the running OS / Python version / CPU architecture don't match build-time constraints. Generalizes PyArmor BCC platform restrictions in pure Python. Not part of the patent-gated combination claims. `pyobfus_pro/runtime_policy.py`, 15 new tests.

---

## Additions from 2026-06-22 competitive + agentic-discoverability scan

Surfaced by a fresh scan against PyArmor 9.2 / Nuitka / SourceDefender / CodeEnigma plus arXiv 2025-2026 (2512.16538 LLM-vs-obfuscation, 2410.05797 CodeCipher) and the 2026 AI-agent tool-discovery landscape. All stay inside the AST + AI-native lane. Full analysis: `docs/AGENTIC_DISCOVERABILITY_2026-06-22.md`.

- [x] **P2-17: Obfuscation provenance manifest (`--provenance-manifest`)** — _Shipped 0.5.5, 2026-08-02_ (implemented by Codex, reviewed by Claude Code, PR #27; see `docs/POST_V0.4_TODO.md` § item 6). A normal pyobfus invocation writes a local JSON manifest (files obfuscated, config hash, tool version, mapping digest, a SHA-256 self-consistency integrity digest). Review renamed an overclaimed "signature" to "integrity digest" — it's not a cryptographic signature, no private key involved; real signing via sigstore stays future work. Reuses the existing digest pattern in `pyobfus/core/mapping.py`, and is something PyArmor's phone-home-on-build model structurally can't offer (no local-verifiable provenance).
- [x] **P2-18: LLM-deobfuscation-resistance mode + benchmark — internal evidence complete 2026-08-01.** Full 5-sample corpus run against two model families (Codex CLI `gpt-5.6-sol` + Claude Code CLI `sonnet`, both via saved subscription logins, no API accounts). Public-knowledge samples (`luhn`/`caesar`/`roman`) always recovered above C1 — inconclusive, expected. Both non-public-knowledge samples (`billing_auth`/`price_rules`) held at every condition C2 and up for **both** model families, including the project's first clean C4 data point (`price_rules`, 0% SRR at C4, independently confirmed twice). Decision: two model families is sufficient (both already agree; a third only matters if a future publication reviewer asks). Reviewed writeup: `docs/LLM_RESISTANCE_PILOT_RESULTS_2026-08-01.md`. A `--llm-resistant` preset stays deferred until product demand justifies it; the separate *published research paper* track this seeds remains low-priority/no-urgency (see this doc's Roadmap-after-v0 section). _Remaining: none blocking; publication effort only if picked up later._
  - **Publication dual-track**: the JOSS paper (`paper/`) is the *software-description* paper (free, low novelty bar). This benchmark is the seed for a *separate research* paper with a novel contribution — target a software-protection / security venue (SPRO, ESORICS, ACSAC, AsiaCCS) or JSS/EMSE, with an arXiv cs.CR preprint for visibility. The two papers don't conflict (different artifacts) and the research paper drives traffic back to the tool. Do NOT submit the same software paper to both JOSS and SoftwareX (dual-publication); SoftwareX (~€2.5k APC, SCIE IF~3) is the only "indexed upgrade" alternative *instead of* JOSS for this paper.
- [x] **P2-19: ML/model-serving preset (`--preset ml`)** — _Shipped 0.5.5, 2026-08-02_ (implemented by Codex, reviewed by Claude Code, PR #26; see `docs/POST_V0.4_TODO.md` § item 6). Protects inference-wrapper code (sklearn/PyTorch/HuggingFace dispatch method names via `exclude_names`, not blanket variable-name exclusion — review narrowed an overly broad first draft), routes model-path/weight-file constants toward the Runtime String Vault, surfaces pickle-safety guidance via `--check`. Rides the HuggingFace pickle-RCE wave; follows the existing `preset_fastapi`/`preset_django`/etc. classmethod pattern in `pyobfus/config.py`. Its `preserve_param_names=True` setting didn't actually take effect end-to-end until the 0.5.6 fix for issue #25 (see the Latest entry above).
- [~] **P2-20: Agentic discoverability (Wave A, mostly shipped 2026-06-22; ARD repo work 2026-07-20)** — be findable by AI agents across every discovery surface, not just human SEO. Done: Smithery via the **Skill** channel (`zhurong2020/pyobfus-protect`; Smithery's MCP-publish is remote-HTTP-only and a non-fit for a local-execution tool — the Skill channel is the right path), mcp.so listing, `uvx pyobfus-mcp` zero-install + a sharpened ≤100-char `server.json` blurb, `smithery.yaml`, and an ARD 1.0 manifest live at Read the Docs' versioned path (`/en/latest/.well-known/ai-catalog.json`, verified 2026-08-02 with JSON content type and CORS `*`). Pending: Read the Docs root `/.well-known/ai-catalog.json` redirect still returns 404, PulseMCP still has no confirmed pyobfus listing, and GEO/AEO launch-content follow-through remains a later content task.

---

## Additions from 2026-07-07 research scan

A fresh external scan (web, July 2026) re-validated the 06-22 items and surfaced two new on-brand candidates. It confirms three 06-22 items are riding real, growing waves.

**Re-validation of existing items:**

- **P2-18 (LLM-deobfuscation-resistance) — strongly validated; promote to top strategic priority.** LLM code-deobfuscation went from fringe to a 2025-26 research hotspot: fine-tuned models now unwind up to 7 chained transforms and beat compiler-based deobfuscation, with systems in production at Google ([CISPA/Springer 2025](https://link.springer.com/content/pdf/10.1007/978-3-031-97620-9_15.pdf); [arXiv 2505.19887](https://arxiv.org/pdf/2505.19887)). Critically, **[Acoda (arXiv 2606.11755, 2026-06)](https://arxiv.org/pdf/2606.11755) is direct same-lane prior art** — "Adversarial Code Obfuscation for Defending against LLM-based Analysis" — to benchmark against and cite. Reconfirms the dual-track: a benchmark-only first cut (2-3 days) is both launch content and the seed for a *separate research paper* (SPRO/ESORICS/ACSAC or JSS/EMSE + arXiv cs.CR), independent of the desk-rejected JOSS software paper.
- **P2-17 (signed provenance manifest) — validated; early-bird window open.** By 2026-03, 132K+ PyPI packages carry attestations (17% of uploads), but the **SLSA-provenance slot in PEP 740 still lacks mature tooling** ([PyPI Warehouse attestation-internals](https://warehouse.pypa.io/security/attestation-internals/)) — space to be early. Reuses our existing PEP 740 muscle; structurally impossible for PyArmor's phone-home-on-build model to match with locally-verifiable provenance.
- **P2-19 (`--preset ml`) — unchanged; still low-cost / high-relevance** (HuggingFace pickle-RCE wave).

**New candidates:**

- [x] **P2-21: pyobfus-mcp tool-description integrity (rug-pull resistance)** — _Shipped mcp 0.3.5, 2026-08-04._ New standalone `pyobfus-mcp-verify` CLI (not an MCP tool — deliberate, keeps the tool count at 8 and avoids MCP-surface churn, and the real threat model here is pre-session/external verification anyway) compares the installed package's live tool registration against `tool_manifest.json`, a manifest frozen at release time, via a SHA-256 self-consistency digest (explicitly not a cryptographic signature — same honesty correction the P2-17 provenance manifest already made). Detects drift between what a release documents and what it actually ships. 13 new tests including a real CI regression guard (fails if a tool's description/schema changes without regenerating the manifest). Note: the 2026-spec OAuth 2.1 / incremental-consent items target *remote* servers; pyobfus-mcp is local stdio, so those are mostly N/A, and `protect_project`'s arbitrary-command path is already gated (`PYOBFUS_MCP_ALLOW_VERIFY_CMD`) + path-scoped from the mcp 0.2.0 hardening.
- [x] **P2-22: honest-comparison content — "pure-Python AST vs statically-unpackable bytecode"** — _Completed 2026-08-02 for the 0.5.7 train._ `docs/COMPARISON.md` now states the tradeoff directly: PyArmor's bytecode/native-runtime layer is a stronger speed bump than AST rewriting, but public static-unpack tooling for PyArmor 8.0-9.2.x means client-side bytecode protection should not be marketed as irreversible cryptography. The same section ties pyobfus back to the defender-lane: pure-Python output, predictable builds, and AI-debuggable reverse stack-trace mapping.

---

## Additions from 2026-08-06 competitive + market scan

Run right after the VS Code extension M0-M2 + 0.2.1 bugfix ship, to re-check the competitive landscape (PyArmor/Nuitka/Sourcedefender, new AST-obfuscator entrants, VS Code Marketplace) and two adjacent trend lines (LLM-deobfuscation research, MCP ecosystem/discovery standards) before picking what's next.

**Re-validation of existing positioning — no changes needed:**

- **PyArmor** is at 9.2.6 (June 2026), added VMC/ECC bytecode-VM obfuscation modes — stays in the lane this project already ruled out (`## What We Won't Do`'s bytecode-VM item), no new threat to the AST + AI-native positioning.
- **VS Code Marketplace** — confirmed still zero direct competitors (no other Python-obfuscator extension exists) as of this scan, ~2 days after M1 published. The April 2025 malicious "Python Obfuscator for VSCode" (publisher "Mark H") is still the only incident in this category; no new ones surfaced.
- **New small AST-obfuscator entrants** (`python-obfuscator` 0.1.0 PyPI/April 2026, `ASTObfuscate`, a few GitHub hobby projects) — all single-maintainer, no framework-awareness, no reverse-trace mapping, no AI/MCP integration, no OpenSSF/PEP 740/provenance trust infra, no VS Code presence. None compete on any of pyobfus's actual differentiators. `python-obfuscation-framework` (same package already flagged in `## What We Won't Do` as PyPI-classified `stager, payload`) reappeared in this scan too — confirms the existing avoidance call was correct, no new action.

**New findings — genuinely actionable:**

- [x] **P2-23: Nuitka Commercial traceback-encryption comparison content.** — _Content-complete 2026-08-06, held for the next release-spacing gate (2026-08-08)._ Nuitka Commercial's "Traceback Encryption" (€250/year) is **symmetric-only today** ("plans to introduce asymmetric encryption in future updates" per their own docs) — our `--scrub-traceback` (RSA-2048-OAEP + AES-256-GCM hybrid, `pyobfus-unscrub` CLI to reverse) is already the more sophisticated scheme, and pyobfus's $45 one-time price undercuts Nuitka's €250/year recurring by a wide margin. `docs/COMPARISON.md` doesn't currently name this Nuitka feature at all. _Estimate: half a day, content-only, same shape as P2-22._
- [x] **P2-24: MCP Server Card applicability — investigated 2026-08-06, correction to this scan's own first-pass framing.** The original entry (below, struck through in spirit) proposed publishing a spec-compliant `server-card.json` at `/.well-known/mcp/server-card.json`. Checking SEP-2127's actual text before building anything found that framing wrong: **`.well-known` Server Card discovery is explicitly scoped to HTTP-transport servers only** — SEP-2127 itself says local, stdio-based servers "should plan to distribute via `server.json` and the MCP Registry" instead, not a `.well-known` HTTP endpoint (which a stdio process has no way to serve from in the first place). pyobfus-mcp is stdio-only, so this mechanism doesn't apply to it today — same shape as the existing "OAuth 2.1 targets remote servers, N/A for local stdio" notes already on P2-6/P2-21. The applicable mechanism (`pyobfus_mcp/server.json` published to the official MCP Registry, confirmed `isLatest`) is already in place and looks complete against the current schema. This becomes actionable only if/when N14 (hosted MCP endpoint, unbuilt) ships a real HTTP transport — no code work today. The custom ARD `ai-catalog.json` manifest (P2-20) is a *different*, non-MCP-standard mechanism (general AI-crawler discovery, not MCP protocol discovery) and is unaffected by this finding; its own pending tail (RTD root `.well-known` redirect 404, unconfirmed PulseMCP listing) stays open separately.
  - ~~Original (2026-08-06, superseded same day): "Adopt the real MCP Server Card standard path... Publish (or redirect) a spec-compliant `server-card.json` at the standard path pyobfus-mcp actually serves from."~~
- **Context, not an action item**: a Veracode Spring-2026 threat report found obfuscated-package volume in the wild up 65.1% (500K+ packages), obfuscation increasingly used to defeat malware scanners. This raises the ambient suspicion any "code obfuscator" brand carries — reinforces (doesn't change) the existing call to lean on verifiable trust infra (OpenSSF Best Practices, PEP 740, provenance/tool-integrity manifests) explicitly in listing copy, already the design principle behind P2-2's VS Code listing and P2-17/P2-21's manifests.
- LLM-deobfuscation research volume kept climbing since the 07-07 scan (BinDeObfBench, LLM-DAS, an Android/Smali obfuscation-detection study), but all of it targets **binary/ARM/Android-Smali** deobfuscation, not Python-source-level like P2-18's own benchmark — the specific lane P2-18 measured stays under-researched by outsiders, which is good: no new prior art invalidates the existing internal-evidence-complete result, and the broader trend still supports keeping `docs/LLM_RESISTANCE_PILOT_RESULTS_2026-08-01.md`'s publication track as a live (if unforced) option.

---

## v0.6.0+ Long-term (3-6 months)

### P3 - Experimental

- [ ] AI-native plugin API — natural-language transformer descriptions, LLM-generated AST plugins
- [ ] `--output-pyc` optional bytecode-only backend
- [ ] Enhanced key obfuscation (previously P1 in old plan, now low-priority: no user demand signal)

---

## What We Won't Do

To maintain focus on core users (individual developers/small teams in the AI-assisted development era):

- **Deep Bytecode Encryption** — Too complex to maintain; conflicts with AI-debuggability goal
- **Bytecode-VM Virtualization** (vmp-protector / PyArmor BCC mode lane) — Architecturally incompatible with AI-debuggability; high maintenance burden; cyber.wtf 2025-05-30 BCC analysis shows partial reversal via symbolic execution is already feasible
- **Compile to C/Machine Code** — Nuitka/Cython already do this well
- **Anti-VM / Sandbox-Detection** — Overlaps with malware-evasion tooling and risks brand poisoning (`python-obfuscation-framework 1.13.0` is already classified `stager, payload` on PyPI). pyobfus is a defender tool; must keep clear lane separation
- **Standalone Runtime Folder Model** (PyArmor `dist/` with native `.so`) — Pure Python output is part of the cross-platform value proposition
- **Enterprise License Server** — Not our target market (a recipe / Cloudflare Worker reference is fine, a SaaS is not)
- **Obfuscation-as-a-Service cloud API** — Conflicts with privacy positioning (PyArmor Basic/Pro phones home on every build; that's our negative-space)

---

## Success Metrics

### v0.4.0 Targets (set 2026-04-22 · status as of 2026-05-07)

- [x] `pyobfus --check` / `unmap` / `init` shipping and documented (P0-1, P0-2, P0-5)
- [x] `pyobfus-mcp` server published, usable in Claude Desktop / Cursor / Claude Code (PyPI 0.1.2 + MCP Registry isLatest + Glama Quality A)
- [ ] PyPI downloads: 324/month → **1,500+/month** (2026-07-07: pyobfus ~1,180/mo, pyobfus-mcp ~400/mo — but largely CI/automated and daily rate has settled to ~25/day after the June 0.5.x release burst; still 0 GitHub stars; launch posts pending in `_drafts/`)
- [ ] GitHub stars: 0 → **100+** (current: 0; same blocker — launch not yet executed)
- [ ] First external (non-owner) GitHub issue opened
- [ ] First Pro license sale

### v0.5.0 Targets

- [ ] VSCode extension live in marketplace with 500+ installs
- [ ] Selective Opacity shipping — unique positioning secured
- [ ] PyPI downloads: **5K+/month**
- [ ] GitHub stars: **300+**
- [ ] 5+ community contributors

### AI-Era Specific Metrics (New)

| Metric | Target | Measurement |
|---|---|---|
| MCP server adoption | 500+ installs | Anthropic MCP Registry / npm stats |
| AI assistant recommendation rate | 3/10 blind tests | Manual Claude / Cursor queries |
| llms.txt crawl evidence | Cited in Perplexity / Claude.ai | Referrer logs |
| CLAUDE.md template forks | 50+ | GitHub Insights |
| Stack Overflow presence | 5+ answered questions | Manual tracking |

---

## Contributing

Feature requests: GitHub issues with `enhancement` tag.
See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

---

**Last Updated**: 2026-08-06 — fresh competitive + market scan (PyArmor/
Nuitka/VS Code Marketplace/new AST-obfuscator entrants/LLM-deobfuscation
research/MCP Server Card standard) run after the VS Code extension M0-M2 +
0.2.1 patch shipped, to inform what's next; see "Additions from 2026-08-06
competitive + market scan" above. **P2-23** (Nuitka traceback-encryption
comparison content) shipped same day, content-only, held for the
2026-08-08 gate. **P2-24** was scoped as "adopt the real MCP Server Card
standard path" but, before writing any code, checking SEP-2127's actual
text found that framing wrong for pyobfus-mcp: `.well-known` Server Card
discovery is HTTP-transport-only by the spec's own words, and stdio
servers (which is all pyobfus-mcp is) are explicitly routed to
`server.json` + the MCP Registry instead — already in place. Corrected
same day rather than building something spec-incorrect; see P2-24's own
entry above for the full finding. Also fixed a stale
checkbox found while reading the file: **P2-13 (PyInstaller cookbook) was
already shipped in 0.5.8, 2026-08-04** — missed in that release's own
re-audit below.
**Prior**: 2026-08-04 — re-audited the 7 open ROADMAP items against
actual code before starting a "Tier 1, ship each as its own patch release"
push. Found 3 of 7 were significantly out of date: **P2-6 is already fully
shipped** (0.2.0, 2026-05-08 — the checkbox just never got flipped, and the
item's own title names the version that did it); **P2-12 and P2-15 are
partially shipped** (credential-pattern detection and Python-level
anti-debug both already exist; the specific gaps the items describe —
PII-shape patterns and native TracerPid/IsDebuggerPresent checks
respectively — are real and smaller than the original estimates). P2-13/
P2-14/P2-16/P2-21 were confirmed genuinely unstarted via direct grep
against the source tree, not just doc inspection.
**Prior**: 2026-08-02 — pyobfus 0.5.7 release prep: P2-4
(`--import-obfuscation`) and P2-22 (honest AST-vs-bytecode comparison content)
are ready for the patch release; pyobfus-mcp remains 0.3.2 because there is no
tool-surface change.
**Prior**: 2026-08-01 — P2-18 internal evidence complete: full 5-sample corpus × two model families (Codex + Claude, both subscription-auth, no API accounts), clean cross-model C4 data point on `price_rules`, decision made that a third model family isn't needed. Reviewed results: `docs/LLM_RESISTANCE_PILOT_RESULTS_2026-08-01.md`.
**Previous**: 2026-07-22 — synchronized the post-0.5.4 execution state: the blocking mypy gate and hardened P2-18 benchmark harness are prepared for remote CI; ARD discovery metadata and launch drafts are ready; next-feature work remains gated on launch feedback.
**Earlier**: 2026-07-07 — added the "Additions from 2026-07-07 research scan" section: external re-validation of P2-17 (SLSA/attestation adoption + tooling gap), P2-18 (LLM-deobfuscation research explosion + Acoda prior art → promote to top strategic priority), P2-19; plus two new candidates P2-21 (pyobfus-mcp tool-description integrity / rug-pull resistance) and P2-22 (honest-comparison content vs statically-unpackable PyArmor bytecode). Refreshed download figures (~1,180/mo pyobfus + ~400/mo mcp). Fixed the Glama listing note (recurring manual Build-steps bump; bumped to 0.3.1 on 07-07).
**Even earlier**: 2026-06-22 — Marked 0.5.2 published (patch: `--seal-code`/`--vault` Python 3.9/3.10 fixes, PR #18); earlier same day 0.5.1 + pyobfus-mcp 0.3.1 published; added the "Additions from 2026-06-22 scan" section: P2-17 (signed provenance manifest), P2-18 (LLM-deobfuscation-resistance mode + benchmark), P2-19 (`--preset ml`), and P2-20 (agentic discoverability, Wave A mostly shipped — Smithery Skill / mcp.so / uvx / server.json). Source: 2026-06-22 competitive + AI-agent-discoverability scan (see `docs/AGENTIC_DISCOVERABILITY_2026-06-22.md`).
**Original reshape**: 2026-04-22 — Strategic reshape after AI-era competitive analysis.
