# Development Roadmap

This document outlines **future plans** for pyobfus. For released version history, see [CHANGELOG.md](../CHANGELOG.md). For the detailed AI-era positioning strategy, see [AI_INTEGRATION_STRATEGY.md](AI_INTEGRATION_STRATEGY.md). For execution tracking, see [V0.4_EXECUTION_LOG.md](V0.4_EXECUTION_LOG.md).

**Target Users**: Individual developers and small teams shipping Python code in the AI-assisted development era
**Positioning**: The AI-native Python obfuscator — MCP-ready, framework-aware, open-source alternative to PyArmor

---

## Current Status

**Latest (2026-07-19)**: **pyobfus 0.5.4 released** — `--bind-device` now derives both Selective Opacity L3 keys and every Runtime String Vault key from the bound machine, closing the remaining baked-Vault-key scope boundary. The release CI recorded **1046 passed / 1 skipped / 90% coverage** in the core suite; Core, MCP, and end-to-end roots run as separate jobs across Python 3.9-3.14 and three operating systems. Published through OIDC with PEP 740 attestations. **pyobfus-mcp stays 0.3.1** because the MCP tool surface did not change.

**Prior (2026-06-22)**: **pyobfus 0.5.2 + pyobfus-mcp 0.3.1 published to PyPI** (0.5.0 was 2026-06-18; 0.5.1 same day). 0.5.1 fused the 6 v0.5 Pro mechanisms into flags on the normal obfuscation command; **0.5.2 is a patch fixing `--seal-code`/`--vault` on Python 3.9/3.10** (seal hash pinned to marshal v2; `zip(strict=)` dropped from the vault pass; 1025 core tests). mcp 0.3.1 names the v0.5 mechanisms in pro-funnel copy (dep `pyobfus>=0.5.1`); MCP Registry 0.3.1 isLatest; all via OIDC + PEP 740 attestations. Patent gate cleared 2026-06-17 (申请号 202610712171X). Ran the **agentic-discoverability Wave A** (Smithery Skill + mcp.so + `uvx` zero-install + sharpened server.json blurb) — see `docs/AGENTIC_DISCOVERABILITY_2026-06-22.md`. **JOSS paper desk-rejected 2026-06-24** (issue `openjournals/joss-reviews#10788`; grounds = scope/significance, not quality: "private-dev-then-public" + no demonstrated third-party reuse). Pivoted to the free path: **Zenodo concept DOI `10.5281/zenodo.20846053`** now minted and propagated (CITATION.cff, README badge, ORCID, arong.eu.org). See `docs/JOSS_REJECTION_20260624.md`.

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

- [x] **P1-1: `pyobfus-mcp` server** (separate package) — Expose P0 tools as Model Context Protocol server for Claude Desktop / Claude Code / Cursor / Windsurf. _Shipped; current package 0.3.1._
- [x] **P1-2: `llms.txt` + `llms-full.txt`** — Deploy at repo root and docs site. _Shipped._
- [x] **P1-3: AI integration templates** — `templates/ai-integration/` with CLAUDE.md, .cursorrules, AGENTS.md, windsurfrules.md. _Shipped._
- [x] **P1-4: PyPI metadata overhaul** — New keyword-dense description, Project-URL additions (MCP Server, AI Guide), Development Status → Production/Stable. _Shipped._
- [x] **P1-5: Incremental obfuscation** — Project-level AST/config hash cache behind `--incremental`, reusing an unchanged successful build. _Shipped._

### Branding & Discoverability (Parallel, Week 1)

- [ ] Reserve PyPI alias packages: `python-obfuscator`, `pyobfuscator`, `py-obfuscator` (if available)
- [ ] Add GitHub topics: `python-obfuscator`, `code-obfuscator`, `ast-obfuscation`, `mcp-server`, `claude-code`, `cursor`, `llm-tools`
- [x] README: add pronunciation / alias line: "pyobfus — the Python obfuscator"
- [x] Upgrade classifier: Core is now `Development Status :: 5 - Production/Stable`; MCP remains Beta

---

## v0.5.0 - AI-Native Differentiation (Weeks 7-14)

**Goal**: Establish a defensible position PyArmor cannot easily copy.

### P2 - Differentiation Layer

- [x] **P2-1: Selective Opacity (Layered Protection)** — per-symbol layers (transparent / ai-readable / obfuscated / encrypted); L3 = AES-256-GCM with lazy `__code__` materialization. _Shipped 0.5.0 2026-06-18 (mechanism + API; combined Pro-flag fusion in 0.5.1)._
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
- [ ] **P2-12: `pyobfus-mcp` `scan_secrets` tool** — New MCP tool detecting emails / IPv4 / GUIDs / paths / API-key shapes; returns structured Pro recommendation and drives an encryption-review loop from Claude Code / Cursor. Tracks obfuscator-ai's interactive-review differentiator on the MCP surface. _Estimate: 3-5 days_
- [ ] **P2-13: PyInstaller integration cookbook** — `examples/pyinstaller/` + docs page for "obfuscate then bundle to single exe". No code change; redirects Sourcedefender / Nuitka prospects who want single-binary delivery. _Estimate: 1 day_
- [ ] **P2-14: `--embed-data <path>` (Pro)** — AES-encrypt a resource file at build time, emit it as a base85 module constant + accessor. Closes Nuitka Commercial "Protect Data Files" / PyArmor `--bind-data` gap. _Estimate: 3-5 days_
- [ ] **P2-15: Anti-debug guard (Pro, opt-in)** — TracerPid (Linux) / IsDebuggerPresent (Windows) / timing-skew check. Default OFF to protect AI-debuggability; opt-in via `--anti-debug` for users who explicitly want hardened production builds. _Estimate: 3-5 days_
- [ ] **P2-16: `@requires_runtime` policy decorator (Pro)** — Refuse to load if Python version / OS / architecture doesn't match build-time constraints (e.g., "this build licensed for Linux production only"). Generalizes PyArmor BCC platform restrictions in pure Python. _Estimate: 2-3 days_

---

## Additions from 2026-06-22 competitive + agentic-discoverability scan

Surfaced by a fresh scan against PyArmor 9.2 / Nuitka / SourceDefender / CodeEnigma plus arXiv 2025-2026 (2512.16538 LLM-vs-obfuscation, 2410.05797 CodeCipher) and the 2026 AI-agent tool-discovery landscape. All stay inside the AST + AI-native lane. Full analysis: `docs/AGENTIC_DISCOVERABILITY_2026-06-22.md`.

- [ ] **P2-17: Signed obfuscation provenance manifest (Pro/Core)** — a normal pyobfus invocation emits a signed JSON manifest (files obfuscated, config hash, tool version, mapping digest; optional sigstore). Rides the 2026 SLSA/SBOM/provenance wave, reuses the existing PEP 740 muscle, and is something PyArmor's phone-home-on-build model structurally can't offer (no local-verifiable provenance). _Estimate: 3-5 days_
- [~] **P2-18: LLM-deobfuscation-resistance mode + benchmark** — the benchmark harness, five-sample corpus, functional scorer, reproducibility metadata, locked-down real-output executor, and blocking offline CI smoke job are implemented. **First real (non-stub) pilot ran 2026-08-01** — Codex CLI / `gpt-5.6-sol`, 2 of 5 corpus samples, all 6 conditions; it also surfaced and fixed a corpus-quality bug (public-domain-algorithm samples let an attacker "recall" the answer instead of defeating the obfuscation, and a no-op transform was silently diluting an aggregate). **Second model family run the same day** — `ClaudeCodeCliAttacker` (Claude subscription CLI, no API account needed) reproduced the exact same pattern as Codex on the one non-public-knowledge sample (held at C2/C3/C5), which also surfaced and fixed two pre-existing docker-executor/schema plumbing bugs unrelated to either attacker — see `docs/POST_V0.4_TODO.md` § P2-18 for the fix and the real numbers. **Full 5-sample corpus run, same day, both model families** closed the remaining gaps: `caesar`/`roman`/`price_rules` × C0-C5 × Codex + Claude. Both models agree exactly — public-knowledge samples (`luhn`/`caesar`/`roman`) always recovered (inconclusive above C1), and both non-public-knowledge samples (`billing_auth`/`price_rules`) held at every rung C2 and up, including a first-ever *clean* C4 data point (`price_rules`, 0% SRR at C4 for both models). A `--llm-resistant` preset stays deferred until a preset is justified. Remaining before a *published, reviewed* result: write up the methodology/numbers into a versioned report (results.json/report.md are gitignored by design) and decide if a third model family is worth adding. _Estimate: writeup 1 day; mode 1-2 weeks if justified_
  - **Publication dual-track**: the JOSS paper (`paper/`) is the *software-description* paper (free, low novelty bar). This benchmark is the seed for a *separate research* paper with a novel contribution — target a software-protection / security venue (SPRO, ESORICS, ACSAC, AsiaCCS) or JSS/EMSE, with an arXiv cs.CR preprint for visibility. The two papers don't conflict (different artifacts) and the research paper drives traffic back to the tool. Do NOT submit the same software paper to both JOSS and SoftwareX (dual-publication); SoftwareX (~€2.5k APC, SCIE IF~3) is the only "indexed upgrade" alternative *instead of* JOSS for this paper.
- [ ] **P2-19: ML/model-serving preset (`--preset ml`)** — protect inference-wrapper code, route model-path / weight-file constants into the Runtime String Vault, surface pickle-safety guidance. Rides the HuggingFace pickle-RCE wave; near-zero architecture cost (the preset mechanism already exists). _Estimate: 3-5 days_
- [~] **P2-20: Agentic discoverability (Wave A, mostly shipped 2026-06-22; ARD repo work 2026-07-20)** — be findable by AI agents across every discovery surface, not just human SEO. Done: Smithery via the **Skill** channel (`zhurong2020/pyobfus-protect`; Smithery's MCP-publish is remote-HTTP-only and a non-fit for a local-execution tool — the Skill channel is the right path), mcp.so listing, `uvx pyobfus-mcp` zero-install + a sharpened ≤100-char `server.json` blurb, `smithery.yaml`, and an ARD 1.0 manifest included in the verified MkDocs build. Pending: Read the Docs root redirect/header verification, PulseMCP external follow-up, and GEO/AEO launch content.

---

## Additions from 2026-07-07 research scan

A fresh external scan (web, July 2026) re-validated the 06-22 items and surfaced two new on-brand candidates. It confirms three 06-22 items are riding real, growing waves.

**Re-validation of existing items:**

- **P2-18 (LLM-deobfuscation-resistance) — strongly validated; promote to top strategic priority.** LLM code-deobfuscation went from fringe to a 2025-26 research hotspot: fine-tuned models now unwind up to 7 chained transforms and beat compiler-based deobfuscation, with systems in production at Google ([CISPA/Springer 2025](https://link.springer.com/content/pdf/10.1007/978-3-031-97620-9_15.pdf); [arXiv 2505.19887](https://arxiv.org/pdf/2505.19887)). Critically, **[Acoda (arXiv 2606.11755, 2026-06)](https://arxiv.org/pdf/2606.11755) is direct same-lane prior art** — "Adversarial Code Obfuscation for Defending against LLM-based Analysis" — to benchmark against and cite. Reconfirms the dual-track: a benchmark-only first cut (2-3 days) is both launch content and the seed for a *separate research paper* (SPRO/ESORICS/ACSAC or JSS/EMSE + arXiv cs.CR), independent of the desk-rejected JOSS software paper.
- **P2-17 (signed provenance manifest) — validated; early-bird window open.** By 2026-03, 132K+ PyPI packages carry attestations (17% of uploads), but the **SLSA-provenance slot in PEP 740 still lacks mature tooling** ([PyPI Warehouse attestation-internals](https://warehouse.pypa.io/security/attestation-internals/)) — space to be early. Reuses our existing PEP 740 muscle; structurally impossible for PyArmor's phone-home-on-build model to match with locally-verifiable provenance.
- **P2-19 (`--preset ml`) — unchanged; still low-cost / high-relevance** (HuggingFace pickle-RCE wave).

**New candidates:**

- [ ] **P2-21: pyobfus-mcp tool-description integrity (rug-pull resistance)** — the #1 MCP threat in the 2026 security baseline is tool poisoning / rug-pulls (a server silently mutating tool descriptions post-install); the defense is verifying tool metadata at install and every update ([OWASP MCP Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html); [Practical DevSecOps 2026](https://www.practical-devsecops.com/mcp-security-vulnerabilities/)). pyobfus-mcp can ship + self-verify a signed tool-description manifest so clients detect tampering — an on-brand meta-differentiator ("a security tool that secures itself"). Note: the 2026-spec OAuth 2.1 / incremental-consent items target *remote* servers; pyobfus-mcp is local stdio, so those are mostly N/A, and `protect_project`'s arbitrary-command path is already gated (`PYOBFUS_MCP_ALLOW_VERIFY_CMD`) + path-scoped from the mcp 0.2.0 hardening. _Estimate: 3-5 days._
- [ ] **P2-22: honest-comparison content — "pure-Python AST vs statically-unpackable bytecode"** (docs / launch, not a code feature). PyArmor 8.0–9.2.x bytecode is now **statically** convertible back to disassembly / experimental source with no execution ([Lil-House/Pyarmor-Static-Unpack-1shot](https://github.com/Lil-House/Pyarmor-Static-Unpack-1shot)), and PyArmor is recurrently used to hide malware ([SANS ISC 2026-01](https://isc.sans.edu/diary/31840)). Material for `COMPARISON.md` + the launch wave + P2-18's benchmark framing, reinforcing pyobfus's defender-lane / AI-debuggable positioning. _Estimate: 1 day._

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

**Last Updated**: 2026-08-01 — P2-18 got its first real (non-stub) pilots from two model families: Codex CLI / `gpt-5.6-sol` (surfaced and fixed a corpus-quality bug — public-domain-algorithm samples + a silently-diluting no-op transform) and, same day, `ClaudeCodeCliAttacker` via saved Claude subscription auth (reproduced the same held/recovered pattern on the one clean sample, and surfaced/fixed a docker-executor permission bug + a `--json-schema` compatibility bug); see `docs/POST_V0.4_TODO.md` for the fixes and real numbers.
**Prior**: 2026-07-22 — synchronized the post-0.5.4 execution state: the blocking mypy gate and hardened P2-18 benchmark harness are prepared for remote CI; ARD discovery metadata and launch drafts are ready; next-feature work remains gated on launch feedback.
**Previous**: 2026-07-07 — added the "Additions from 2026-07-07 research scan" section: external re-validation of P2-17 (SLSA/attestation adoption + tooling gap), P2-18 (LLM-deobfuscation research explosion + Acoda prior art → promote to top strategic priority), P2-19; plus two new candidates P2-21 (pyobfus-mcp tool-description integrity / rug-pull resistance) and P2-22 (honest-comparison content vs statically-unpackable PyArmor bytecode). Refreshed download figures (~1,180/mo pyobfus + ~400/mo mcp). Fixed the Glama listing note (recurring manual Build-steps bump; bumped to 0.3.1 on 07-07).
**Earlier**: 2026-06-22 — Marked 0.5.2 published (patch: `--seal-code`/`--vault` Python 3.9/3.10 fixes, PR #18); earlier same day 0.5.1 + pyobfus-mcp 0.3.1 published; added the "Additions from 2026-06-22 scan" section: P2-17 (signed provenance manifest), P2-18 (LLM-deobfuscation-resistance mode + benchmark), P2-19 (`--preset ml`), and P2-20 (agentic discoverability, Wave A mostly shipped — Smithery Skill / mcp.so / uvx / server.json). Source: 2026-06-22 competitive + AI-agent-discoverability scan (see `docs/AGENTIC_DISCOVERABILITY_2026-06-22.md`).
**Original reshape**: 2026-04-22 — Strategic reshape after AI-era competitive analysis.
