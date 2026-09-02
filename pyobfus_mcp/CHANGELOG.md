# Changelog — pyobfus-mcp

All notable changes to the `pyobfus-mcp` companion package are documented here. Follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The main `pyobfus` package changelog lives in the repo root at [CHANGELOG.md](../CHANGELOG.md).

## [Unreleased]

### Fixed

- Replaced the retired `modelcontextprotocol/servers` GitHub-directory URL in
  package metadata with the live official Registry search endpoint, and added
  the same direct entry link to the MCP README.

## [0.3.10] - 2026-09-01

### Changed

- Rephrased the MCP Registry description around agent search intent: protect
  Python before shipping, reverse-map reported tracebacks, and stay local with
  no phone-home behavior.
- Expanded PyPI keywords for code protection, reverse mapping, AI-native tools,
  GitHub Copilot, and CodeBuddy. Tool behavior and schemas are unchanged.

## [0.3.9] - 2026-08-28

### Added

- `check_obfuscation_risks` now accepts `use_project_config` (default `true`).
  It discovers config relative to the validated project path, returns
  `effective_config`, `files_excluded`, and `excluded_findings`, and keeps
  excluded-file risks out of editor/agent blocking counts. Set it to `false`
  for the legacy unconfigured scan. This is read-only and adds no network
  access.

### Changed

- Raised the runtime dependency floor to `pyobfus>=0.5.18`, which provides the
  shared config resolver and config-aware preflight report fields used by
  `use_project_config=true`.

## [0.3.8] - 2026-08-24

### Added

- `_pro_unlock()` (embedded in `recommend_tier`'s `pro_action`,
  `check_obfuscation_risks`/`protect_project`'s `pro_value`, and
  `explain_preset`'s `pro_unlock`) gained a `pricing_model: "one_time"`
  field, so the "not a subscription" fact travels with the price instead
  of relying on an AI agent to infer it from `price_usd` alone.
- The runtime dependency floor is now `pyobfus>=0.5.17`, ensuring the MCP
  package always has the dependency-advisory implementation its new online
  verification parameter invokes.
- `check_obfuscation_risks` gained a `verify_dependencies_online` parameter
  (default `false`): opts into the new dependency-hallucination advisory
  (see the main package's `0.5.17` entry) for this call only.
  `pyobfus-mcp` otherwise makes zero outbound network calls, and that stays
  true by default here too — the check runs, unauthenticated against public
  PyPI, only when a caller explicitly asks. `docs/MCP_SECURITY_SCAN.md`'s
  SSRF section is updated accordingly (this is the package's first outbound
  HTTP code path, reached transitively via `pyobfus.core`; it's a
  fixed-host call, not a caller-supplied-URL fetch, so it isn't the SSRF
  pattern the OWASP MCP Security Cheat Sheet describes — see that doc for
  the full reasoning).

### Fixed

- `recommend_tier`'s `pro_tier_capabilities` no longer lists "Unlimited
  files and lines of code" as a Pro-exclusive benefit — verified this
  isn't actually gated by tier in the default obfuscation path (see the
  main `pyobfus` package's `0.5.17` Fixed entry for the full
  investigation). `free_tier_capabilities` now states the accurate,
  positive fact instead: no file/line limit at any tier, contrasted with
  PyArmor's measured ~935-940 line/file trial cap.

## [0.3.7] - 2026-08-22

### Added

- Independent security scan documented: Cisco's open-source `mcp-scanner` run
  against the published PyPI package via a live stdio `initialize` →
  `tools/list` handshake, YARA + dependency-vulnerability analyzers — 8/8
  tools SAFE, 0 findings (2026-08-20, `pyobfus-mcp` 0.3.6). Full reproducible
  steps and an honest scope statement in
  [`docs/MCP_SECURITY_SCAN.md`](../docs/MCP_SECURITY_SCAN.md), summarized in
  the package README's new "Independent security scan" section.

## [0.3.6] - 2026-08-17

### Changed

- `server.json` now includes the GitHub repository stable ID
  (`repository.id`) and has been re-validated against the official MCP
  Registry `2025-12-11` schema. `fileSha256` is still intentionally omitted:
  PyPI publishes multiple artifacts, and an incorrect single-artifact hash
  would be worse than no optional hash.

### Fixed

- Runtime package metadata (`pyobfus_mcp.__version__`), `pyproject.toml`,
  and `server.json` had drifted out of sync at points in prior releases.
  A new regression test (`test_version_metadata.py`) now asserts all three
  — plus `server.json`'s `repository.id` — stay aligned on every release.

## [0.3.5] - 2026-08-04

**Feature release (P2-21): tool-description integrity, rug-pull
resistance.** New `pyobfus-mcp-verify` CLI entry point (a standalone
script, not an MCP tool — the tool count stays at 8) compares the
currently-installed package's actually-registered tool
name/description/input-schema/meta against `tool_manifest.json`, a
manifest frozen at release time via `pyobfus-mcp-verify --generate`. A
SHA-256 self-consistency digest over the canonical manifest lets a user
(or CI) detect drift between what a release documents and what it
actually ships — the realistic threat for a PyPI-distributed local-stdio
server, as opposed to a live remote server mutating mid-session.

Deliberately shipped as a standalone CLI, not an MCP tool: the real
threat model here is pre-session/external verification (a user or CI
checking before trusting an install), which a model calling a tool
mid-conversation can't meaningfully provide anyway — and it avoids any
MCP tool-surface churn (still 8 tools, no Glama/Registry re-pin needed
beyond the routine version bump this release already requires for other
reasons).

Honesty note: explicitly documented as a self-consistency digest, not a
cryptographic signature — matches the same correction the P2-17
provenance-manifest review already made (no private key or third-party
trust anchor involved). A user wanting stronger assurance is pointed to
the digest published in each GitHub Release's notes.

### Added

- `pyobfus_mcp/tool_manifest.py` — `compute_live_manifest()`,
  `verify_integrity()`, `load_shipped_manifest()`, and the
  `pyobfus-mcp-verify` CLI entry point.
- `pyobfus_mcp/tool_manifest.json` — the shipped manifest (regenerated
  before each release).
- 13 new tests, including a real regression guard: the test suite fails
  if a tool's description/schema/meta changes without regenerating the
  manifest.

## [0.3.4] - 2026-08-04

**Feature release (P2-12).** `check_obfuscation_risks` and `protect_project`
now also scan for PII-shaped string literals — emails, IPv4 addresses,
GUIDs, and home-directory paths that name a real user (`/home/<user>/`,
`/Users/<user>/`, `C:\Users\<user>\`) — a distinct signal class from the
existing credential-shaped detection (API keys, Stripe/AWS key formats,
opaque bearer tokens). The two counts are reported separately in the
`pro_value` response field (`sensitive_literal_count` vs.
`pii_literal_count`) since the remediation story differs: credentials call
for encryption, PII calls for asking whether the value belongs in source at
all. Folded into the existing `pro_value` envelope rather than shipped as a
new standalone tool, so the MCP tool count stays at 8 (the roadmap's
original "new `scan_secrets` tool" framing was reconsidered after finding
credential-shape detection already existed here — see
`docs/ROADMAP.md`'s P2-12 entry for the full reasoning). 3 new tests.

### Changed

- `pro_value.pii_literal_count` — new field alongside the existing
  `pro_value.sensitive_literal_count`.

## [0.3.3] - 2026-08-02

**Docs/content-only release** (same pattern as 0.3.2). No tool code,
signatures, or wire behavior changed — pyobfus 0.5.5's `--preset ml` and
0.5.6's preset/config-override fix required no MCP-side change (dynamic +
wire-behavior-only, respectively), but 0.5.7's `--import-obfuscation` (Pro,
P2-4) was missing from the three tools that describe Pro's mechanism set to
the calling agent as a static string/list rather than deriving it
dynamically — the same class of drift `ml` had before 0.3.2.

### Changed

- **`recommend_tier` and `start_pro_trial`'s hardcoded Pro-mechanism lists
  now include `--import-obfuscation` (pyobfus 0.5.7)** — `pro_action.
  estimated_protection` and `pro_tier_capabilities` in `recommend_tier`, and
  `trial_features` in `start_pro_trial`, previously enumerated only the four
  v0.5.0-0.5.4 mechanisms (Selective Opacity, forensic watermarking, Runtime
  String Vault, @seal_code/--scrub-traceback). An agent calling either tool
  today would get a stale answer for "what does Pro include."

## [0.3.2] — 2026-08-02

**Docs/metadata-only release.** No tool code, signatures, or wire behavior
changed — `list_presets()`/`explain_preset()` already returned pyobfus
0.5.5's `ml` preset correctly at runtime (they read
`ObfuscationConfig.FRAMEWORK_PRESETS` dynamically under the existing
`pyobfus>=0.5.1` dependency floor). This release syncs the *static*
metadata that had drifted, per `docs/DOC_SYNC_AUDIT_2026-08-02.md`.

### Changed

- **`server.json`'s `_meta` and `generate_pyobfus_config`'s docstring now
  name the `ml` framework preset** (pyobfus 0.5.5), and `_meta.target_clients`
  plus `pyproject.toml`'s keywords/description now include `codex` — already
  a first-class client via the `AGENTS.md` template and the Smithery Skill
  listing, just missing from this package's own metadata.

## [0.3.1] — 2026-06-22

_(Published to PyPI 2026-06-22 via OIDC; MCP Registry updated to 0.3.1 isLatest the same day.)_

### Changed

- **Pro-funnel copy now names the v0.5 Pro mechanisms.** With pyobfus 0.5.0
  published and the patent application past preliminary examination, the
  patent-safe-copy constraint is lifted. `recommend_tier` and `start_pro_trial`
  now surface Selective Opacity, forensic watermarking, the Runtime String
  Vault, `@seal_code`, and `--scrub-traceback` (available as `pyobfus build`
  flags in 0.5.1 and via the `pyobfus_pro` API), not just the older AES-256 /
  anti-debug set. `check_obfuscation_risks` recommends the Runtime String Vault
  alongside string encryption when sensitive literals are found.
- **Dependency floor raised to `pyobfus>=0.5.1`** (was `>=0.4.1`), since the
  copy references the 0.5.1 build-flag surface. Publish pyobfus 0.5.1 first.

No tool surface change (still 8 tools); no MCP Registry server.json change
beyond the version bump.

## [0.3.0] — 2026-06-11

### Added

- **`protect_project` tool — the one-call, self-verifying obfuscation pipeline.** Scans risks → picks a framework-aware preset → obfuscates (via the real `pyobfus` CLI) → **round-trip-verifies** the output and returns `verified: true/false` plus a `confidence` level. Verification never imports the obfuscated code into the server process: it byte-compiles the output (`compileall`) and import-smoke-tests each top-level module in isolated subprocesses, so a renamed-but-consistent codebase still passes while genuinely broken output (won't compile / won't import) comes back `verified: false` with `status: "warnings"` so an agent knows **not** to ship it. The de-obfuscation mapping is written *alongside* (never inside) the output. An optional caller-supplied `verify_cmd` (app-level end-to-end check) is gated behind `PYOBFUS_MCP_ALLOW_VERIFY_CMD=1` since it runs an arbitrary command. Brings the registered tool count to **eight**. 15 new tests.
- **`next_tool` field on tool responses.** A machine-readable `{tool, reason, args}` companion to the free-text `ai_hint`, so agents chain multi-step workflows deterministically instead of re-parsing prose each hop.
- **`protect_project` stamps the `--trace-marker` header by default** (`trace_marker=True`). Obfuscated files carry a `# pyobfus:obfuscated` header so an agent that later opens one from a traceback knows to reverse the names with `unmap_stack_trace`. The response surfaces `obfuscation.trace_marker_id`. Set `trace_marker=False` to skip.

## [0.2.0] — 2026-05-08

Production hardening release. Closes the 3 ❌ gaps + 2 ⚠️ partials surfaced
by the 2026-05-07 self-audit against Atlas Whoff's "5 MCP Server Security
Mistakes That Could Expose Your AI Stack" (dev.to, 2026-05-06), plus adds
the first Pro funnel surface to the MCP layer (the highest-volume
interaction channel — AI assistants invoke MCP far more often than humans
run the CLI directly).

### Added — Security baseline (Phase 1)

- **Path scoping** (`PYOBFUS_MCP_PROJECT_ROOT` env var) — every tool that
  accepts a filesystem path now resolves the input and rejects any path
  whose resolved form escapes the configured project root. `..`-traversal
  and absolute paths to other locations both return a structured
  `PathScopeError` envelope. Default root is the server process's cwd.
- **Sliding-window rate limiting** (`PYOBFUS_MCP_RATE_LIMIT_PER_MIN` env
  var, default 30 calls/min/tool) — protects against prompt-injected agent
  loops. Exceeding the cap returns a `RateLimitExceeded` envelope with a
  `retry_after_seconds` field. Set to 0 to disable.
- **JSON-line audit logging** (`PYOBFUS_MCP_AUDIT_LOG` env var) — every
  tool invocation emits a JSON line to stderr (default) or a configurable
  file. Fields: `ts`, `tool`, `params`, `outcome`, `duration_ms`. The
  `unmap_stack_trace` tool redacts the `trace` parameter (which can carry
  sensitive log data captured by the original crash) to a length-only
  marker.

### Added — FastMCP 1.27 baseline + tier gating (Phase 2)

- All 5 existing tools now carry `meta={"version": "1", "tier": "community"}`
  on their `@app.tool()` registration (mcp 1.27 SDK-native `meta` kwarg).
  Forward-compatible with future native typed `version=` kwargs.
- **Administrative tool gating** (`PYOBFUS_MCP_DISABLED_TOOLS` env var,
  comma-separated) — operators can restrict an exposed server to a subset
  of tools without redeploying. Disabled tools return a structured
  `ToolDisabled` envelope, audit-logged with `outcome: "disabled"`. Check
  fires *before* rate limit so disabled tools don't burn budget.
- **OpenTelemetry instrumentation** (soft-imported) — when `opentelemetry`
  is installed (e.g. via `pip install pyobfus-mcp[otel]`) and a
  `TracerProvider` is configured (typically the user sets
  `OTEL_EXPORTER_OTLP_ENDPOINT` and runs an SDK initializer), every tool
  invocation emits a span with attributes `tool.name`, `tool.status`,
  `tool.duration_ms`. Without OTel installed, the span context yields a
  no-op object — zero runtime cost.
- New `[otel]` extras in `pyproject.toml` for opt-in install of
  `opentelemetry-api` / `opentelemetry-sdk` / `opentelemetry-exporter-otlp`.

### Added — Pro funnel via MCP (Phase 3)

- **`pro_value` field on `check_obfuscation_risks`** — when the scan
  finds likely-sensitive string literals (api_key/secret/bearer/password
  assignments, Stripe keys, AWS access key IDs, generic 40+ char
  alphanumeric tokens) or high-severity findings, the response gains a
  structured Pro-upsell envelope including applicable_features, rationale,
  recommendation_strength (low/medium/high), trial_command, checkout_url,
  price_usd, money_back_guarantee_days. Omitted on clean projects (no
  noise).
- **`pro_unlock` field on `explain_preset` Pro path** — replaces the
  previous CLI-only hint with a structured dict (trial_command,
  trial_duration_days, checkout_url, price_usd, money_back_guarantee_days,
  instant_delivery) plus an ai_hint that includes price, trial duration,
  and the Stripe checkout URL inline. Community presets keep the simple
  "Apply with: pyobfus..." hint (no pro_unlock — would be noise).
- **`recommend_tier(path)` [NEW TOOL]** — analyzes a project and
  recommends `community` vs `pro` with reasoning. Decision rule: Pro when
  `sensitive_literal_count >= 4` OR `high_severity_findings >= 3`, else
  community. Returns concrete `free_action` and `pro_action` so the AI
  agent can route the user without round-trips.
- **`start_pro_trial() [NEW TOOL]** — structured guidance for the 5-day
  Pro trial. Detects whether a trial is already active and adjusts the
  ai_hint accordingly. Surfaces post-trial Stripe checkout URL + $45 USD
  price + 30-day money-back guarantee inline. Tool itself does NOT invoke
  the side effect — the user runs `pyobfus-trial start` in their shell.
- **`tier_context` field on Pro-funnel-relevant tools** —
  `check_obfuscation_risks`, `explain_preset`, `recommend_tier`,
  `start_pro_trial` all return `tier_context: {tool_tier, user_tier,
  trial_days_remaining (if active), pro_unlock_url}`. Skipped on
  `list_presets` (already structurally surfaces tier breakdown) and
  `unmap_stack_trace` (irrelevant to that operation).

### Changed

- Tightened `mcp` dependency to `>=1.27.0,<2.0.0` (was `>=1.20.0`). 1.27
  is the SDK version that ships the `meta=` kwarg on `@app.tool()` we
  rely on for tier metadata.
- `server.json` `_meta` block (committed in 4f8886f, deferred during the
  P0.3 same-version rejection) now ships to the MCP Registry as part of
  this 0.2.0 publish.

### Tests

- 55 tests pass on Python 3.12 (28 in `test_security.py` for the security
  primitives + tier gating + soft OTel; 27 in `test_tools.py` for tool
  behavior + Pro funnel surfaces + meta wiring).

### Tools registered (7 total, was 5)

| Tool | tier |
|---|---|
| `check_obfuscation_risks` | community |
| `generate_pyobfus_config` | community |
| `unmap_stack_trace` | community |
| `list_presets` | community |
| `explain_preset` | community |
| `recommend_tier` | **pro_funnel** (new) |
| `start_pro_trial` | **pro_funnel** (new) |

### Migration notes

- **Breaking**: paths supplied to `check_obfuscation_risks`,
  `generate_pyobfus_config`, `unmap_stack_trace` are now scoped to
  `PYOBFUS_MCP_PROJECT_ROOT` (default: server cwd). For Claude Desktop
  configs, set the env var to your project root explicitly:
  ```json
  {
    "mcpServers": {
      "pyobfus": {
        "command": "pyobfus-mcp",
        "env": {"PYOBFUS_MCP_PROJECT_ROOT": "/Users/me/projects/myapp"}
      }
    }
  }
  ```
- **Breaking**: `mcp` dep floor moved 1.20 → 1.27. Users on older mcp
  SDKs must upgrade with `pip install --upgrade pyobfus-mcp` (which
  pulls a compatible mcp).
- **Non-breaking**: rate limiting defaults to 30/min/tool. If your agent
  legitimately calls a tool more than that, set
  `PYOBFUS_MCP_RATE_LIMIT_PER_MIN=N` to raise (or 0 to disable).

## [0.1.2] — 2026-05-07

### Fixed

- **Crash on startup with mcp SDK ≥ 1.20** — `_build_server()` called `FastMCP(name="pyobfus", version=__version__)`, but the `version=` keyword argument was removed from `FastMCP.__init__()` between mcp SDK 1.0 (when 0.1.0 was published) and 1.20+. The result was a `TypeError: FastMCP.__init__() got an unexpected keyword argument 'version'` immediately after install on any system that pulled a recent mcp SDK. Removed the kwarg; FastMCP populates the server version from package metadata via the MCP `InitializeResult.capabilities` object.

### Changed

- Tightened `mcp` dependency to `>=1.20.0,<2.0.0` (was `>=1.0.0`). The new lower bound matches the SDK version we now test against; the upper bound prevents a future mcp 2.0 from silently re-introducing breaking changes. Users on older mcp SDKs (< 1.20) must upgrade.

### Notes

The bug affected every install since the underlying `mcp` SDK shipped 1.20 (early 2026). All users on `pyobfus-mcp 0.1.0` / `0.1.1` who pulled a recent mcp SDK hit it. Recommended action for downstream users: `pip install --upgrade pyobfus-mcp`.

## [0.1.1] — 2026-04-22

### Added

- `server.json` at the package root, conforming to MCP Registry server schema 2025-12-11. Enables programmatic publication to `registry.modelcontextprotocol.io` via the `mcp-publisher` CLI.
- Ownership-verification marker (`<!-- mcp-name: io.github.zhurong2020/pyobfus-mcp -->`) at the top of `README.md`. Required by the MCP Registry to verify that the PyPI package owner controls the `io.github.zhurong2020/` namespace.

### Changed

- Nothing. Metadata-only release — no code or API changes. The tool surface, wire protocol, and behavior are identical to 0.1.0.

### Notes

The upgrade from 0.1.0 is driven purely by MCP Registry requirements: because PyPI disallows overwriting an already-published version, a patch bump is mandatory even though the change is limited to documentation and a new static config file. Future metadata-only revisions will follow the same pattern.

## [0.1.0] — 2026-04-22

### Added

- Initial public release.
- Five MCP tools exposing the pyobfus v0.4.0 AI-native capabilities:
  - `check_obfuscation_risks(path)` — pre-flight risk scan (eval/exec, dynamic attributes, framework reflection)
  - `generate_pyobfus_config(path, preset_override?, write?)` — zero-config project init with framework detection
  - `unmap_stack_trace(trace, mapping_path)` — reverse obfuscated identifiers in production tracebacks
  - `list_presets()` — enumerate community / framework / Pro presets
  - `explain_preset(name)` — describe a preset's effects
- FastMCP adapter in `server.py` with stdio transport (compatible with Claude Desktop, Claude Code, Cursor, Windsurf, Zed).
- Pure-Python tool implementations in `tools.py` — independently testable without the `mcp` SDK installed.
- Configuration snippets for Claude Desktop, Cursor, Windsurf, Zed, and `claude mcp add` in `README.md`.
- 16 tests in `tests/test_tools.py`; all pass without the MCP SDK (the SDK import is lazy in `_build_server()`).
