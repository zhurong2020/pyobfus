# Changelog — pyobfus-mcp

All notable changes to the `pyobfus-mcp` companion package are documented here. Follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The main `pyobfus` package changelog lives in the repo root at [CHANGELOG.md](../CHANGELOG.md).

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
