# Development Roadmap

This document outlines **future plans** for pyobfus. For released version history, see [CHANGELOG.md](../CHANGELOG.md). For the detailed AI-era positioning strategy, see [AI_INTEGRATION_STRATEGY.md](AI_INTEGRATION_STRATEGY.md). For execution tracking, see [V0.4_EXECUTION_LOG.md](V0.4_EXECUTION_LOG.md).

**Target Users**: Individual developers and small teams shipping Python code in the AI-assisted development era
**Positioning**: The AI-native Python obfuscator — MCP-ready, framework-aware, open-source alternative to PyArmor

---

## Current Status

**Latest (2026-06-22)**: **pyobfus 0.5.1 + pyobfus-mcp 0.3.1 published to PyPI** (0.5.0 was 2026-06-18). 0.5.1 fuses the 6 v0.5 Pro mechanisms into `pyobfus build` flags (1024 core tests); mcp 0.3.1 names the v0.5 mechanisms in pro-funnel copy (dep `pyobfus>=0.5.1`); MCP Registry 0.3.1 isLatest; both via OIDC + PEP 740 attestations. Patent gate cleared 2026-06-17 (申请号 202610712171X). Ran the **agentic-discoverability Wave A** (Smithery Skill + mcp.so + `uvx` zero-install + sharpened server.json blurb) — see `docs/AGENTIC_DISCOVERABILITY_2026-06-22.md`.

### Snapshot (2026-05-07, historical)

See [CHANGELOG.md](../CHANGELOG.md) for the latest release and version history.

- **pyobfus 0.4.0** released 2026-04-22 (AI-native CLI + framework presets + reverse stack-trace mapping)
- **pyobfus-mcp 0.1.2** released 2026-05-07 (emergency fix for `FastMCP.__init__()` `version=` kwarg drift in mcp SDK ≥ 1.20; see `pyobfus_mcp/CHANGELOG.md`)
- 1016+ tests with 89% coverage (multi-OS CI/CD across Python 3.9-3.14)
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

- [ ] **P0-1: `pyobfus --check` pre-flight mode** — Scan project for `eval`/`exec`/`getattr`/dynamic attribute access, framework reflection points, `__all__` exports. Output JSON risk report with `ai-hint` field suggesting next command. _Estimate: 1 week_
- [ ] **P0-2: `pyobfus unmap` reverse mapping command** — Input error stacktrace + mapping.json → output original variable-name trace. Unlocks "AI can still debug obfuscated code". _Estimate: 3-5 days_
- [ ] **P0-3: Framework presets** — `--preset fastapi|django|flask|pydantic|click` with built-in exclusion rules for each framework's reflection points. _Estimate: 1 week_
- [ ] **P0-4: AI-friendly CLI** — Global `--json` output mode, structured error messages with `ai-hint` field, machine-readable exit codes. _Estimate: 2-3 days_
- [ ] **P0-5: `pyobfus init`** — Scan project → detect framework → generate `pyobfus.yaml` with auto-exclude list. One-command onboarding. _Estimate: 3-5 days_

### P1 - AI Ecosystem Integration (Weeks 4-6)

Builds on top of P0 primitives to make pyobfus appear natively in the AI-assisted workflow.

- [ ] **P1-1: `pyobfus-mcp` server** (separate package) — Expose P0 tools as Model Context Protocol server for Claude Desktop / Claude Code / Cursor / Windsurf. _Estimate: 1 week_
- [ ] **P1-2: `llms.txt` + `llms-full.txt`** — Deploy at repo root and docs site. _Estimate: 2 hours_
- [ ] **P1-3: AI integration templates** — `templates/ai-integration/` with CLAUDE.md, .cursorrules, AGENTS.md, windsurfrules.md. _Estimate: 1 day_
- [ ] **P1-4: PyPI metadata overhaul** — New keyword-dense description, Project-URL additions (MCP Server, AI Guide), Development Status → Beta. _Estimate: 1 hour_
- [ ] **P1-5: Incremental obfuscation** — AST hash caching, only process changed files. Enables CI/CD embedding. _Estimate: 1-2 weeks_

### Branding & Discoverability (Parallel, Week 1)

- [ ] Reserve PyPI alias packages: `python-obfuscator`, `pyobfuscator`, `py-obfuscator` (if available)
- [ ] Add GitHub topics: `python-obfuscator`, `code-obfuscator`, `ast-obfuscation`, `mcp-server`, `claude-code`, `cursor`, `llm-tools`
- [ ] README: add pronunciation / alias line: "pyobfus — the Python obfuscator"
- [ ] Upgrade classifier: `Development Status :: 3 - Alpha` → `4 - Beta`

---

## v0.5.0 - AI-Native Differentiation (Weeks 7-14)

**Goal**: Establish a defensible position PyArmor cannot easily copy.

### P2 - Differentiation Layer

- [x] **P2-1: Selective Opacity (Layered Protection)** — per-symbol layers (transparent / ai-readable / obfuscated / encrypted); L3 = AES-256-GCM with lazy `__code__` materialization. _Shipped 0.5.0 2026-06-18 (mechanism + API; combined `pyobfus build` flag fusion in 0.5.1)._
- [ ] **P2-2: VSCode Extension** — Right-click obfuscate + yaml IntelliSense + status bar. Marketplace as a new distribution channel. _Estimate: 1-2 weeks_
- [x] **P2-3: `--strip-ai-artifacts` mode** — Removes AI provenance markers (`Generated by Claude`, `Co-Authored-By: Claude`, `🤖 Generated with`, ...) from docstrings + attribution dunders (`__author__` etc.). Conservative attribution-only matching; arbitrary string literals untouched; comments already dropped by the AST round-trip. Community-tier, 27 tests. _Shipped 2026-06-06 (branch `feat/strip-ai-artifacts`)._
- [ ] **P2-4: Import obfuscation (Pro)** — Top-level imports → runtime `importlib` + encrypted strings. Closes gap with PyArmor Pro. _Estimate: 1-2 weeks_
- [x] **P2-5: Numeric / Constant obfuscation** — `--numeric-obfuscation`. Opaque arithmetic expressions for number literals (int → XOR/add/sub identities, float → `float.fromhex`). Community-tier, value-preserving, 37 tests. _Shipped 2026-06-06 (branch `feat/numeric-obfuscation`)._
- [ ] **P2-6: pyobfus-mcp 0.2.0 production hardening** — FastMCP 3.0 features (per-tool versioning + per-tool authorization + OpenTelemetry instrumentation), path-scoping sandbox for file-touching tools, token-bucket rate limiting with env-var override, JSON-line audit logging with parameter redaction. Brings pyobfus-mcp to production-grade against the emerging MCP-server-security baseline (Atlas Whoff, "5 MCP Server Security Mistakes That Could Expose Your AI Stack", dev.to 2026-05-06). _Estimate: 4-5 days_

#### Additions from 2026-05-09 competitive scan

The four items below were surfaced by a competitive feature scan against PyArmor 9.2.x, Nuitka Commercial, Sourcedefender, and vmp-protector 1.0.0. They stay inside the AST + AI-native lane and represent the highest-ROI Pro additions.

- [x] **P2-7: Forensic watermarking / `--fingerprint <buyer-id>` (Pro)** — per-buyer deterministic key derivation (`forensic_seed` / `WatermarkRNG` / `derive_layer_key`) for piracy traceback. _Shipped 0.5.0 2026-06-18 (Pro-layer key watermarking + API; Core rename-RNG single-seed integration in 0.5.1)._
- [x] **P2-8: Hardware / time / period license binding (Pro)** — device / expiry / run-count binding woven into the AES-GCM decryption path (`pyobfus_pro.license_binding`): the license gate is the GCM tag check itself, no separate patchable check. _Shipped 0.5.0 2026-06-18 (mechanism + API; `--bind-device` / `--expire-hard` / `--period` build flags in 0.5.1)._
- [x] **P2-9: `@seal_code` integrity decorator (Pro)** — build-time bytecode hash baked in; runtime detection of in-memory patching, with layer-aware sealing for L3 functions. _Shipped 0.5.0 2026-06-18 (decorator + build pass; combined-flag fusion in 0.5.1)._
- [x] **P2-10: `--scrub-traceback` production traceback encryption (Pro)** — hybrid RSA-2048-OAEP + AES-256-GCM error-ID encryption; developer reverses with the new **`pyobfus-unscrub`** CLI. _Shipped 0.5.0 2026-06-18 (`pyobfus-unscrub` CLI + build pass; `pyobfus build --scrub-traceback` fusion in 0.5.1)._

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
- [ ] **P2-12: `pyobfus-mcp` `scan_secrets` tool** — New MCP tool detecting emails / IPv4 / GUIDs / paths / API-key shapes; returns structured Pro recommendation and drives an encryption-review loop from Claude Code / Cursor. Tracks obfuscator-ai's interactive-review differentiator on the MCP surface. _Estimate: 3-5 days_
- [ ] **P2-13: PyInstaller integration cookbook** — `examples/pyinstaller/` + docs page for "obfuscate then bundle to single exe". No code change; redirects Sourcedefender / Nuitka prospects who want single-binary delivery. _Estimate: 1 day_
- [ ] **P2-14: `--embed-data <path>` (Pro)** — AES-encrypt a resource file at build time, emit it as a base85 module constant + accessor. Closes Nuitka Commercial "Protect Data Files" / PyArmor `--bind-data` gap. _Estimate: 3-5 days_
- [ ] **P2-15: Anti-debug guard (Pro, opt-in)** — TracerPid (Linux) / IsDebuggerPresent (Windows) / timing-skew check. Default OFF to protect AI-debuggability; opt-in via `--anti-debug` for users who explicitly want hardened production builds. _Estimate: 3-5 days_
- [ ] **P2-16: `@requires_runtime` policy decorator (Pro)** — Refuse to load if Python version / OS / architecture doesn't match build-time constraints (e.g., "this build licensed for Linux production only"). Generalizes PyArmor BCC platform restrictions in pure Python. _Estimate: 2-3 days_

---

## Additions from 2026-06-22 competitive + agentic-discoverability scan

Surfaced by a fresh scan against PyArmor 9.2 / Nuitka / SourceDefender / CodeEnigma plus arXiv 2025-2026 (2512.16538 LLM-vs-obfuscation, 2410.05797 CodeCipher) and the 2026 AI-agent tool-discovery landscape. All stay inside the AST + AI-native lane. Full analysis: `docs/AGENTIC_DISCOVERABILITY_2026-06-22.md`.

- [ ] **P2-17: Signed obfuscation provenance manifest (Pro/Core)** — `pyobfus build` emits a signed JSON manifest (files obfuscated, config hash, tool version, mapping digest; optional sigstore). Rides the 2026 SLSA/SBOM/provenance wave, reuses the existing PEP 740 muscle, and is something PyArmor's phone-home-on-build model structurally can't offer (no local-verifiable provenance). _Estimate: 3-5 days_
- [ ] **P2-18: LLM-deobfuscation-resistance mode + benchmark** — a `--llm-resistant` preset and/or a published "LLM semantic-recovery rate X%" benchmark report. Uniquely on-brand for an AI-native obfuscator (no competitor can credibly quantify resistance *to AI*); strong launch-content story even as a benchmark-only first cut. _Estimate: benchmark 2-3 days; mode 1-2 weeks_
- [ ] **P2-19: ML/model-serving preset (`--preset ml`)** — protect inference-wrapper code, route model-path / weight-file constants into the Runtime String Vault, surface pickle-safety guidance. Rides the HuggingFace pickle-RCE wave; near-zero architecture cost (the preset mechanism already exists). _Estimate: 3-5 days_
- [~] **P2-20: Agentic discoverability (Wave A, mostly shipped 2026-06-22)** — be findable by AI agents across every discovery surface, not just human SEO. Done: Smithery via the **Skill** channel (`zhurong2020/pyobfus-protect`; Smithery's MCP-publish is remote-HTTP-only and a non-fit for a local-execution tool — the Skill channel is the right path), mcp.so listing, `uvx pyobfus-mcp` zero-install + a sharpened ≤100-char `server.json` blurb, `smithery.yaml`. Pending: PulseMCP (passive weekly ingest of the Official Registry; email fallback), ARD `ai-catalog.json` early-bird, and GEO/AEO content (answer-first openings, named-number facts, FAQ schema) folded into the launch wave.

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
- [ ] PyPI downloads: 324/month → **1,500+/month** (current: pyobfus ~337/month; launch posts pending in `_drafts/`)
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

**Last Updated**: 2026-06-22 — Marked 0.5.1 + pyobfus-mcp 0.3.1 published; added the "Additions from 2026-06-22 scan" section: P2-17 (signed provenance manifest), P2-18 (LLM-deobfuscation-resistance mode + benchmark), P2-19 (`--preset ml`), and P2-20 (agentic discoverability, Wave A mostly shipped — Smithery Skill / mcp.so / uvx / server.json). Source: 2026-06-22 competitive + AI-agent-discoverability scan (see `docs/AGENTIC_DISCOVERABILITY_2026-06-22.md`).
**Previous**: 2026-05-09 — Added P2-7..P2-10 to v0.5.0 (forensic watermarking, license binding, integrity seal, scrub-traceback) and a v0.5.1 section with P2-11..P2-16. Expanded "What We Won't Do" with bytecode-VM virtualization, anti-VM detection, standalone runtime folder model. Source: 2026-05-09 competitive scan (PyArmor 9.2.x, Nuitka Commercial, Sourcedefender, vmp-protector 1.0.0, obfuscator-ai, arXiv 2512.16538/2510.11251).
**Earlier**: 2026-04-22 — Strategic reshape after AI-era competitive analysis.
