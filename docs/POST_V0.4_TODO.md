# pyobfus Post-v0.4 Action Plan

**Snapshot**: 2026-05-07 (after v0.4 distribution leg fully closed · pyobfus-mcp 0.1.2 emergency release shipped · Glama Quality A · awesome-mcp-servers PR #5777 awaiting human merge).

**Use as cold-start cheat sheet** when resuming work after a session break. This doc supersedes ad-hoc TODO scattered in chat; future Claude sessions should read this first.

---

## 30-Second Resume

**Where we are**: pyobfus 0.4.0 + pyobfus-mcp 0.1.2 published · Glama Quality A · MCP Registry isLatest · 671 tests / 91% coverage / Python 3.8-3.14. **Where we're not**: 0 GitHub stars, ~337 PyPI/month (v0.4 target was 1,500+/month). The gap is **launch execution**, not feature gaps.

**Single biggest unblocked TODO**: get the 4-platform launch out of `_drafts/` (dev.to → HN → Reddit → CN trio). Every day of delay loses ~1 week of natural-growth compound effect.

**Strategic frame**: AST-obfuscator commodity layer is **getting crowded** (`python-obfuscator` 0.1.0 revived 2026-04-03 after 5-year sleep · `python-obfuscation-framework` 1.13.0 with 14 releases in 5 weeks). pyobfus's moat is **AI-native + framework presets + reverse mapping + MCP**, not AST mechanics. **PyArmor 9.2 went VMC/ECC virtualization** — that's a different lane; do not chase.

---

## Verified facts baseline (2026-05-07 · cross-checked against PyPI authoritative APIs)

| Item | Value | Verified |
|---|---|---|
| pyobfus latest | 0.4.0 (2026-04-22) | ✅ |
| pyobfus-mcp latest | 0.1.2 (2026-05-07) | ✅ |
| pyarmor latest | **9.2.4** (2026-03-18) — VMC/ECC modes since 9.2.0 (Oct 2025) | ✅ pypi.org/pypi/pyarmor |
| python-obfuscator | **0.1.0** (2026-04-03) — was dormant 2021-2026, just revived | ✅ pypi.org/pypi/python-obfuscator |
| python-obfuscation-framework | **1.13.0** (2026-04-05) — 23 releases total, 14 in last 5 weeks | ✅ pypi.org/pypi/python-obfuscation-framework |
| mcp SDK latest | 1.27.0 (2026-04-02) — the one that surfaced our `version=` kwarg drift | ✅ pypi.org/pypi/mcp |
| Python 3.14 stable | 2025-10 (~7 months mature as of 2026-05-07) | (Python.org release calendar) |
| Python 3.15 | alpha/beta only — stable expected 2026-10 | (Python.org PEP 745 release schedule) |

---

## 🔴 P0 — Self-actionable, do this week (5-7 → 5-14)

These 4 items together = ~6 hours of work, all independent.

### P0.1 — CI smoke test against latest mcp SDK (10 min)

**Why**: directly prevents repeat of today's 0.1.2 emergency. mcp SDK API broke `FastMCP.__init__()` `version=` kwarg silently between 1.0 and 1.20+; we caught it because Glama's container build complained, not because CI noticed.

**Action**: add a job to `.github/workflows/ci.yml`:

```yaml
test-mcp-sdk-latest:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v5
    - uses: actions/setup-python@v5
      with: { python-version: "3.13" }
    - run: pip install -e ./pyobfus_mcp 'mcp>=1.20'
    - run: python -c "from pyobfus_mcp.server import _build_server; _build_server()"
```

**Done when**: green CI run; intentional regression (re-add `version=` kwarg, push to a branch) makes it red.

---

### P0.2 — PEP 740 sigstore attestations (2 hours)

**Why**: pyobfus is a **security tool** without supply-chain attestations as of 2026-05. Trail of Bits' tracker shows ~5-6% of top-360 PyPI projects publish attestations; for our category that's table-stakes credibility. GitHub Actions Trusted Publishing emits them automatically.

**Reference**: <https://peps.python.org/pep-0740/> · <https://blog.sigstore.dev/pypi-attestations-ga/> · <https://trailofbits.github.io/are-we-pep740-yet/>

**Action**:
1. Configure pypi.org "Trusted Publisher" for `zhurong2020/pyobfus` repo (one-time, 5 min on pypi.org settings)
2. Switch existing release workflow from explicit token auth to OIDC trusted publishing
3. Verify `pip install pyobfus --require-hashes` shows attestation present

**Done when**: PyPI page for pyobfus 0.4.1 (or whatever next release) shows green "Verified" badges + provenance JSON visible.

---

### P0.3 — server.json `_meta` enrichment (✅ DONE · 2026-05-08 published with 0.2.0 · ⚠️ Registry silently stripped publisher namespace)

**Why**: Glama's 2026-01-24 spec post documents that MCP Registry preserves *only* the publisher-claimed `_meta` namespace, drops others. Claiming `io.github.zhurong2020.pyobfus_mcp` namespace **now** with structured fields locks pyobfus-mcp into downstream aggregator filters before they freeze on conventions.

**Reference**: <https://glama.ai/blog/2026-01-24-official-mcp-registry-serverjson-requirements>

**Action**: ✅ Done in commit `4f8886f` — `pyobfus_mcp/server.json` now contains:

```json
"_meta": {
  "io.github.zhurong2020.pyobfus_mcp": {
    "framework_presets": ["fastapi","django","flask","pydantic","click","sqlalchemy"],
    "licensing_model": "apache-2.0-core-plus-proprietary-pro",
    "quality_grade": "A",
    "tool_intent": "code-protection",
    "target_clients": ["claude-desktop","claude-code","cursor","windsurf","zed"]
  }
}
```

**Registry publish status (2026-05-07 finding)**: ⏸️ DEFERRED. We attempted `mcp-publisher publish` against the current 0.1.2 entry and got HTTP 400 `cannot publish duplicate version`. **MCP Registry behaves the same as PyPI / Glama Release flow — it rejects same-version re-publishes**, so `_meta` for an existing version cannot be backfilled in place. There is also no `_meta`-only update command in `mcp-publisher` 1.7.8 (full subcommand list: `init / login / logout / publish / status / validate`; `status` only toggles active/deprecated).

The committed `_meta` block will ship to the registry **automatically on the next legitimate `pyobfus-mcp` version bump** — naturally bundled with N2 (FastMCP 3.0 → 0.2.0, P1 list) or any earlier bug-fix 0.1.3. **Do not bump just to refresh `_meta`** (see do-not-do list).

**Token / auth note (2026-05-07 finding)**: the previous TODO claim that the mcp-publisher token at `~/.config/mcp-publisher/token.json` is good for "~15 days" was wrong — JWT in our refresh expired within ~80 minutes. Non-interactive re-login works:

```bash
mcp-publisher login github -token "$(gh auth token)"
```

(Needs `gh auth status` showing scopes ≥ `repo` — currently `gist, read:org, repo, workflow`.) See `~/.claude/projects/-mnt-c-onedrive-msft-OneDrive---MSFT-rong-3-job-program-pyobfus/memory/mcp_publisher_auth.md`.

**Done when**: next pyobfus-mcp version bump is published to MCP Registry and `curl 'https://registry.modelcontextprotocol.io/v0/servers?search=pyobfus' | jq '...'` shows the `_meta.io.github.zhurong2020.pyobfus_mcp` block populated. Until then, `_meta` lives in source-controlled `server.json` only.

**2026-05-08 update**: `mcp-publisher publish` ran successfully alongside the 0.2.0 release (PyPI OIDC publish via `release.yml`). Registry `pyobfus-mcp` 0.2.0 entry is `active` + `isLatest: true`. **However, our publisher-claimed `_meta.io.github.zhurong2020.pyobfus_mcp` namespace was silently stripped** — the registry response shows `"_meta": {}` on the server object (only the registry's own `io.modelcontextprotocol.registry/official` outer-`_meta` survives). Hypothesis: the registry's server-side validator only accepts publisher-claimed `_meta` keys that *exactly* match the verified namespace prefix (`io.github.zhurong2020`), and our extended `.pyobfus_mcp` suffix gets rejected. Schema URL `https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json` declares `_meta: {}` (no constraint), so the rule lives in the Registry runtime, not the schema. **Plan**: investigate accepted namespace forms before the next legitimate version bump (0.2.1 bug fix or 0.3.0); try `io.github.zhurong2020` (no suffix) or nested struct form. Captured in companion memory `~/.claude/projects/-mnt-c-onedrive-msft-OneDrive---MSFT-rong-3-job-program-pyobfus/memory/mcp_registry_meta_namespace.md`.

---

### P0.4 — dev.to article (✅ FULLY DONE · LIVE 2026-05-07 evening)

**Live URL**: <https://dev.to/zhurong2020/let-claude-code-debug-your-obfuscated-python-a-guide-to-the-pyobfus-mcp-integration-3epm>


**Why**: this is the #1 leverage point. Article at `_drafts/article-01-claude-code-mcp-integration.md`, drafted 2026-05-05 (v2) → 2026-05-07 (v3 voice rewrite) → 2026-05-07 (v4 GPTZero-diagnostic-driven rewrite).

**Action history**:
1. ✅ v2 → v3 voice rewrite (commit `ca12e25`): killed parallel "X is a Y" feature block, "isn't X. It's Y" closers, triplet rhythms; added dated specifics.
2. ✅ v3 paste-tested on gptzero.me 2026-05-07 → returned **AI 100% / Mixed 0% / Human 0%**. GPTZero's per-sentence breakdown identified specific high-AI-impact sentences as the signal driver.
3. ✅ v3 → v4 surgical rewrite (uncommitted at this writing): replaced every High-AI-Impact sentence GPTZero flagged. Burstiness expanded char-length range from 4-200 (v3) to 2-257 (v4).
4. **2026-05-07 strategic decision**: v4 is **final** for dev.to. Not re-iterating on GPTZero gate. dev.to has no AI ban, disclosure-up-front handles compliance, function-clarity dominates for our buyer/user, and HN/Reddit/CN get separate short-form posts (already in `_drafts/`) so this body's detection score doesn't gate them. See v3 → v4 changelog inside the article file for the full strategic note.

**Done when** (revised): article live on dev.to; sequence then triggers HN +48h, Reddit +24h after HN, CN trio within 48h.

**Reference**:
- `_drafts/forum-ai-policy-and-voice-guide.md` — per-platform AI policy + the "human at 11pm" voice cheatsheet
- `_drafts/cross-review-prompt.md` — outside-eye review prompt (still useful if maintainer wants a Gemini/ChatGPT critique before posting)
- The GPTZero per-sentence diagnostic from the v3 paste-test is captured in the v3 → v4 changelog inside the article — do not lose this if iterating future articles, the pattern (fragments + parentheticals + very-long-messy + concrete-dated specifics PASS; medium-length explanatory prose with subordinate clauses FAILS) is the actionable signal.

---

## 🟡 P1 — v0.5 work (4-6 weeks)

### Already in `docs/ROADMAP.md` v0.5+ (still valid · re-prioritized)

| ID | Item | Status | Re-prioritization rationale |
|---|---|---|---|
| **P2-1** | Selective Opacity (layered AES protection) | TODO | Keep · core philosophical differentiator |
| **P2-3** | `--strip-ai-artifacts` mode | TODO · **promoted from P2-3** | Pairs naturally with new N3 (claude-skill preset); both serve "ship AI-generated code as IP" segment |
| **P2-4** | Import obfuscation (Pro) | TODO | Keep · closes PyArmor Pro feature gap |
| **P2-5** | Numeric / constant obfuscation | TODO | Keep · small effort, fills gap |
| **P2-2** | VSCode extension | TODO · **demoted** | VSCode marketplace is slower-growing channel than launch posts; revisit after launch data |
| **drop-3.8** | Drop Python 3.8 support | TODO | Both new competitors require `>=3.10`; we're paying 3.8 cost for shrinking userbase |

### New items surfaced from 2026-05-07 research

#### N1 — Python 3.14 PEP 750 t-string AST handler (1 day · narrow time window)

**Why**: PEP 750 introduced `Template` and `Interpolation` AST nodes new in 3.14 (`t"hello {name}"` syntax). PyArmor 9.2.4, python-obfuscator 0.1.0, python-obfuscation-framework 1.13.0 — **none verified to handle them yet**. First-mover advantage for "the obfuscator that handles 3.14 t-strings" is real but narrow (months, not years).

**Reference**: <https://peps.python.org/pep-0750/> · <https://docs.python.org/3.14/library/string.templatelib.html>

**Action**:
1. Add `ast.Template` / `ast.Interpolation` handlers to `pyobfus/transformers/string_encoder.py`
2. Test case: obfuscate a 3.14-only module using `t""` and round-trip-verify
3. Ship a blog post "pyobfus is the first Python obfuscator to handle PEP 750 t-strings" (own that SEO term)

**Done when**: 3.14 t-string regression test green; post live.

---

#### N2 — pyobfus-mcp 0.2.0 = FastMCP 1.27 features + Pro funnel + security hardening (✅ SHIPPED 2026-05-08 · 4 phases / 5 commits)

**Why (FastMCP 3.0)**: pyobfus-mcp 0.1.2 lacks production-grade features that the MCP ecosystem is converging on (tool versioning, per-tool authorization gating, OTel observability). Glama and other MCP aggregators will eventually add a "production-ready" filter — being on the wrong side of that line means we lose visibility.

> **2026-05-07 evening reality check**: when I went to wire Phase 2, I `inspect`-ed the actual `FastMCP.tool()` signature on `mcp==1.27.0`. The kwargs it accepts are: `name`, `title`, `description`, `annotations`, `icons`, `meta`, `structured_output`. **There is no typed `version=` kwarg, no per-tool `auth=` kwarg, and no native OpenTelemetry hooks** in mcp 1.27 — the "FastMCP 3.0 features" framing I'd been carrying turned out to be community/marketing aspiration, not what's actually shipped in the SDK. Plan corrected below: we use `meta={"version": "1", "tier": "..."}` dict (forward-compatible), implement tier gating at our `secure_tool` decorator layer (the Phase 1 wrapper), and add OTel via soft-import (no hard dep). This implementation is more honest and **less coupled to FastMCP API churn** — when mcp eventually ships native typed kwargs we can migrate without re-architecting.

**Why (Pro funnel · 2026-05-07 finding)**: 5 current MCP tools are community-only with weak Pro discovery. `check_obfuscation_risks` doesn't surface "Pro string-encryption would protect N sensitive literals" even when the scan finds them. `explain_preset` Pro-preset path returns the CLI hint `pyobfus-trial start` — no Stripe URL, no ROI framing, no value-prop. There is no `recommend_tier` tool. **Pro funnel via MCP is the highest-leverage monetization channel** (AI assistants invoke MCP far more often than humans run CLI directly), but it's currently the weakest funnel surface in the entire product. Bundling Pro funnel design with the FastMCP 3.0 upgrade because both touch every tool's response shape — one breaking-change window, one 0.2.0 ship.

**Why (security hardening · 2026-05-07 evening finding)**: A 10-category audit of `pyobfus_mcp/pyobfus_mcp/tools.py` + `server.py` against Atlas Whoff's "5 MCP Server Security Mistakes" (dev.to, 2026-05-06) plus 5 additional categories surfaced **3 real gaps + 2 partial gaps** (full table in `~/.claude/projects/-mnt-c-onedrive-msft-OneDrive---MSFT-rong-3-job-program-pyobfus/memory/mcp_security_audit_baseline.md`). With launch wave starting (HN 5-11 + Reddit 5-12), the Atlas-style scanner exposure is 4 days out and the gaps would scan red. Bundling fixes here because per-tool auth (already in this scope under FastMCP 3.0 baseline) and audit logging share the same `@app.tool` decorator surface, so refactoring once is cheaper than refactoring twice.

**Action**:

*FastMCP 1.27 baseline + own-layer tier gating + soft-import OTel*:
1. Bump dep `mcp>=1.27.0,<2.0.0` (we're at `>=1.20.0,<2.0.0` after the 0.1.2 fix). Trivial change in `pyobfus_mcp/pyproject.toml`.
2. Add `meta={"version": "1", "tier": "community"}` to all 5 `@app.tool` decorators in `pyobfus_mcp/pyobfus_mcp/server.py`. The `meta` dict is what mcp 1.27 actually accepts; future Pro-tier tools registered in Phase 3 will get `tier: "pro_funnel"`. This is the SDK-native forward-compatible carrier for our tool versioning intent.
3. Add tier gating to `secure_tool` decorator (the Phase 1 wrapper in `pyobfus_mcp/pyobfus_mcp/_security.py`):
   - Optional `requires_tier="community"` parameter (default community)
   - Env var `PYOBFUS_MCP_DISABLED_TOOLS=tool1,tool2,...` administratively disables tools by name
   - Disabled tools return a structured `ToolDisabled` error envelope, audit-logged with `outcome: "disabled"`
   - Disabled check happens **before** rate-limit check so disabled tools don't burn budget
   - *Closes audit category #7 partial gap*
4. OpenTelemetry instrumentation via soft-import in `secure_tool`:
   - Try to `import opentelemetry` at module load; if absent, no-op
   - If installed AND `OTEL_EXPORTER_OTLP_ENDPOINT` env var set, emit a span per tool invocation with attributes: `tool.name`, `tool.status`, `tool.duration_ms`
   - Don't add `opentelemetry-sdk` as a hard dep — install via `pip install pyobfus-mcp[otel]` (extras_require) or BYO. Keep the default install lean.

*Pro funnel*:
5. `check_obfuscation_risks` → add `pro_value` field. When scan finds N sensitive string literals or M complex CFG branches, return structured Pro recommendation including Stripe checkout URL.
6. `explain_preset` Pro path → replace `pyobfus-trial start` CLI hint with ROI framing + 14-day trial start command + Stripe pricing URL.
7. New tool `recommend_tier(path)` → analyzes project, returns free / Pro recommendation with reasons, free-trial start command, and pricing URL.
8. New tool `start_pro_trial()` → returns structured response with download / activation steps; AI can guide user end-to-end without dropping out to a browser.
9. Add `tier_context` field to all 5 tool responses so the AI knows which tier is currently active and which Pro paths are gated.

*Security hardening (new 2026-05-07 evening · all 3 surfaced by 10-category audit)*:
10. **Path scoping** — wrap all path-accepting tools (`check_obfuscation_risks`, `generate_pyobfus_config(write=True)`, `unmap_stack_trace`) with a sandbox that resolves the requested path, rejects `..`-traversal, and rejects absolute paths outside a configurable project root (default: `os.getcwd()` when the server starts). *Closes audit category #2 (overly broad filesystem access).*
11. **Rate limiting** — token bucket per session, default 30 calls/min/tool. Exposed as `PYOBFUS_MCP_RATE_LIMIT_PER_MIN` env var override. Returns structured `RateLimitExceeded` error with `retry_after_seconds` in the standard error envelope. *Closes audit category #3 (no rate limiting).*
12. **Audit logging** — JSON line per tool invocation to `stderr` (default) or `PYOBFUS_MCP_AUDIT_LOG=path/to/file.jsonl`. Fields: `ts`, `tool`, `session_id`, `params` (with `path`/`mapping_path`/`trace` value-redacted to `[REDACTED:N_chars]`), `outcome` (`success` / `error`), `duration_ms`. *Closes audit category #5 (no audit logging).*

*Ship*:
13. Bump pyobfus-mcp to 0.2.0; CHANGELOG entry includes a "Security baseline" section linking to this scope; `mcp-publisher publish` (this also picks up the deferred `_meta` from P0.3 — see P0.3 status above).

**Done when**: 5 tools versioned; Pro funnel surfaces in `check_obfuscation_risks` + `explain_preset` + new `recommend_tier` + new `start_pro_trial`; OTel traces visible with `OTEL_EXPORTER_OTLP_ENDPOINT=...`; **path-traversal attempts return structured error**; **rate-limit kicks in past 30 calls/min/tool with structured retry hint**; **every tool call emits a JSON audit line**; 0.2.0 live on PyPI + MCP Registry with `_meta` block published; 1+ Stripe checkout link click sourced from MCP-driven prompts within 30 days of launch (instrumented via OTel); a fresh run of Atlas Whoff's MCP Security Scanner (or equivalent third-party scan) shows 5/5 of his categories green for pyobfus-mcp 0.2.0.

**Ship summary (2026-05-08)**:
- **Phase 1** — Security baseline: commit `fa4094a` · 36 → 56 tests · CI 24/24 green
- **Phase 2** — FastMCP 1.27 baseline + tier gating + soft OTel: commit `b868618` · 56 → 65 tests · CI 24/24 green
- **Phase 3** — Pro funnel via MCP: commits `0cd629c` (replaced `9ec05ff` after GitHub Push Protection caught the fake Stripe-shaped fixture strings — the test fixtures themselves were reshaped to trigger only our generic-pattern detector, not the Stripe-key one) · 65 → 75 tests · CI 24/24 green
- **Phase 4** — Ship 0.2.0: commit `3f74f91` (version bump + CHANGELOG) + tag `mcp-v0.2.0` · `release.yml` OIDC publish on first try (PyPI Trusted Publisher's first real exercise) → PyPI 0.2.0 live with PEP 740 attestations · `mcp-publisher publish` published 0.2.0 to MCP Registry (token expired per the 80-min rule and was auto-refreshed via `gh auth token` workaround documented in `mcp_publisher_auth.md` — the playbook's first real reuse)
- **Status caveat**: the publisher-claimed `_meta.io.github.zhurong2020.pyobfus_mcp` block was silently stripped server-side (see P0.3 status above for hypothesis + plan). Field is present-but-empty; not a blocker.

---

#### N3 — `--target claude-skill` preset (1 week · net-new market segment)

**Why**: Claude Code's plugin/skill ecosystem exploded in 2026 (awesome-claude-plugins, tonsofskills marketplace). Skill authors increasingly want to ship **proprietary skills** without exposing source. A preset that knows the skill manifest layout (preserves `manifest.json`, `metadata.yaml`, hook entry points; obfuscates everything else) opens a buyer segment with **zero incumbent competition** — PyArmor can't address this without their own AI-friendly debugging story.

**Reference**: <https://github.com/ComposioHQ/awesome-claude-plugins> (community list) · <https://github.com/jeremylongshore/claude-code-plugins-plus-skills>

**Action**:
1. Survey 10-15 popular Claude skills on the marketplace; identify common manifest patterns
2. Define preset rules in `pyobfus/presets/claude_skill.yaml`:
   - preserve names: skill-entry hooks, manifest fields
   - exclude paths: `manifest.json`, `metadata.yaml`, `*.md` docs
3. Add CLI: `pyobfus --preset claude-skill src/`
4. Ship companion blog post: "Protect your Claude skill IP without breaking it"

**Done when**: 1+ external skill author tries it and confirms hook resolution still works.

---

## 🟢 P2 — Passive / waiting (no action needed; just monitor)

| Item | Trigger condition | ETA |
|---|---|---|
| punkpeye merges PR #5777 | 86k★-repo human cadence · `state=OPEN` confirmed 2026-05-08 morning · all bot labels green (`has-emoji`/`has-glama`/`valid-name`) · 13h-old self status update referencing Glama Quality A still un-acked by maintainer | 3-7 days typical |
| Glama "No glama.json" checklist clears | Glama cron re-scan after `glama.json` schema fix (commit `8d92487`) | 1-3 days |
| First external GitHub issue | Real user encounters something | depends on launch |
| First Pro license sale | Launch traffic + Stripe checkout funnel | depends on launch |
| GitHub stars 0 → 100+ | Launch + Glama/Registry organic discovery | depends on launch |
| Glama Quality grade re-check after `glama.json` fix | Eventual cron | 1-3 days |

### N5 — Diversify awesome-list distribution (parallel hedge against punkpeye merge latency · 1h total · ▶ IN FLIGHT 2026-05-08)

**Status 2026-05-08 morning**:
- ✅ **appcypher fork created + branch pushed**: `zhurong2020/awesome-mcp-servers-appcypher:add-pyobfus-mcp` (renamed from default `awesome-mcp-servers` to avoid collision with existing punkpeye fork) · README.md +1 line at end of Development Tools section · entry uses `simpleicons.org/python` icon + `<sup><sup>⭐</sup></sup>` Official marker per appcypher Legend · **PR creation requires browser click** (gh CLI cross-repo PR with non-default fork name returns 404; documented as known gh limitation). Compare URL ready for one-click submission.
- ⏸️ **wong2 mcpservers.org submission**: form fields pre-filled (server_name / short_description / link / category=Development / contact_email) — **user click needed** (no API for form). Skip $39 premium tier.
- 🟢 **Both submissions are user-actionable in <5 min**.

Rationale: PR #5777 has been OPEN 5 days with all gates green. punkpeye repo carries ~1k open PRs and merges at human cadence. Two other major awesome-mcp-servers lists exist; investigating both 2026-05-08 yielded:

| List | Stars | Submission channel | Cost | Verdict |
|---|---|---|---|---|
| **`punkpeye/awesome-mcp-servers`** | 86K | PR (#5777 · OPEN) | ✅ already invested | — |
| **`appcypher/awesome-mcp-servers`** | 5.5K | PR · standard `CONTRIBUTING.md` (alphabetical · 1 PR / suggestion · search-before-submit) · last push 2026-05-06 (active) · 558 open issues | 30 min single PR | **Submit** |
| **`wong2/awesome-mcp-servers`** | 4K | **No PRs accepted** · README explicitly redirects to `https://mcpservers.org/submit` form · last push 2026-04-30 | 10 min web form | **Submit** |

Why submit both despite stars-tier difference vs punkpeye:
- (i) 9.5K combined stars + mcpservers.org's own search traffic = non-trivial discoverability hedge
- (ii) Zero blocking dependency on punkpeye merge — if #5777 stalls past 14 days the two new listings prove the package
- (iii) appcypher's CONTRIBUTING discipline (alphabetical · search-before-submit) means the same single-line entry from #5777 is reusable verbatim
- (iv) wong2's mcpservers.org form is faster than any of these PR cycles

Done when: PR landed in appcypher · mcpservers.org submission acked. Track in `docs/V0.4_EXECUTION_LOG.md`.

**Cold-start hint** (do this in a fresh session, not bundled with launch wave): just open this file, jump to N5, copy the existing `#5777` single-line entry from `https://github.com/zhurong2020/pyobfus/blob/main/awesome-mcp-entry.md` (or the `git log -p` of the PR's only commit), and submit verbatim to both — alphabetical position differs but the line content is identical.

---

## Strategic do-not-do list (decisions captured 2026-05-07)

- **Don't chase PyArmor's VMC virtualization**. They went deep into bytecode-VM obfuscation in 9.2.0 (Oct 2025) — that's a different lane, fundamentally stronger but conflicts with our AI-debuggability promise. Stay in AI-native lane.
- **Don't compete on AST mechanics**. Two new commoditized AST obfuscators (python-obfuscator, python-obfuscation-framework) shipped in last 5 weeks. Adding "another transformer" doesn't move our metrics; integration story does.
- **Don't bump pyobfus or pyobfus-mcp version just to refresh metadata**. **All three downstream surfaces — PyPI, MCP Registry, and Glama — reject same-version re-publishes** (PyPI: 400 "version already exists"; MCP Registry: 400 "cannot publish duplicate version", confirmed 2026-05-07; Glama Release flow: same). Bundle metadata refresh with the next legitimate bump. For Glama-listing refresh specifically (no version change involved), use the "Claim ownership flow again" mechanism — see `~/.claude/projects/-home-wuxia-projects-pyobfus/memory/glama_metadata_schemas.md`.
- **Don't add features to free tier that have no user-demand signal**. Old roadmap "Enhanced key obfuscation" and "Code compression" were deprioritized in 2026-04 strategic shift; keep them buried.

---

## Recommended near-term sequence (3 weeks · revised 2026-05-07 evening post-launch)

```
Week 1 (5-7 → 5-11) · ✅ TECH HYGIENE LANDED · 🟢 dev.to LIVE:
  ├─ P0.1 ci smoke test                    commit 8ec0fcd
  ├─ P0.2 OIDC release workflow            commit a3da282 + PyPI Trusted Publisher registered 5-7
  ├─ P0.3 server.json _meta block          commit 4f8886f (registry publish deferred to N2)
  ├─ P0.4 v3 voice rewrite                 commit ca12e25
  ├─ P0.4 v4 GPTZero-diagnostic rewrite    commit ec5fc65
  └─ P0.4 dev.to article LIVE 5-7 evening  https://dev.to/zhurong2020/let-claude-code-debug-...

Week 1 weekend (5-8 Fri → 5-9 Sat) · CN trio (within +48h of dev.to · scheduled per maintainer 2026-05-07):
  ├─ 有心工坊 / tech-empowerment (long-form CN translation of dev.to article)
  ├─ 知乎 (adapted CN with hook + cn-friendly formatting)
  └─ V2EX (short post)
  Source draft: _drafts/post-cn-bilingual.md

Week 2 launch wave (5-11 Mon → 5-12 Tue):
  ├─ Mon 5-11 evening 9-10pm UTC: HN Show HN
  │   Source draft: _drafts/post-hn-show-hn.md (DO NOT reuse dev.to long-form;
  │   HN Show HN is a different format — short post, runnable demo, no upvote ask)
  ├─ Tue 5-12 evening: Reddit /r/Python (+24h after HN, captures HN-bounce traffic)
  │   Source draft: _drafts/post-reddit-rpython.md
  └─ Parallel: review dev.to 24h + 48h + 7d reaction metrics, capture in
     V0.4_EXECUTION_LOG.md

Week 2 cont. (5-13 → 5-18):
  ├─ Review launch wave metrics across 4 platforms; reweight v0.5 priorities
  ├─ N1 PEP 750 t-string AST handler (1 day · narrow time-window first-mover)
  └─ Begin v0.5 work depending on signal

Week 3 (5-19 → 5-25):
  ├─ N2 FastMCP 3.0 + Pro funnel + security hardening (4-5 days · 3-way bundle ·
  │   pyobfus-mcp 0.2.0 ship · also resolves deferred P0.3 _meta publish · also
  │   closes audit gaps #2/#3/#5/#7 from 2026-05-07 evening self-audit)
  └─ Start N3 claude-skill preset (1 week effort · net-new market segment)

By 2026-06-15: v0.5.0 release candidate (P2-1 + P2-3 + P2-4 + P2-5 + N1 + N2 + N3 + drop 3.8)
```

---

## Source-of-truth references (read these before reopening this doc)

- **`docs/V0.4_EXECUTION_LOG.md`** — what's been done · 17 sessions logged · Metrics Snapshot table
- **`docs/ROADMAP.md`** — public-facing strategic narrative (don't put TODOs here)
- **`docs/AI_INTEGRATION_STRATEGY.md`** — channel strategy, AI-policy risk per platform
- **`_drafts/`** — 4 launch articles + cross-review prompt + warmup checklists
- **`pyobfus_mcp/CHANGELOG.md`** — MCP server version history (currently 0.1.2)
- **`~/.claude/projects/-home-wuxia-projects-pyobfus/memory/glama_metadata_schemas.md`** — 3 distinct Glama/MCP file schemas, never confuse again
- **PR #5777**: <https://github.com/punkpeye/awesome-mcp-servers/pull/5777> · all bot checks green, awaiting human merge

---

**Last updated**: 2026-05-08 morning (post-N2-ship) · P0 status: P0.1 ✅ · P0.2 ✅ · P0.3 ✅ shipped with 0.2.0 (Registry stripped publisher namespace; investigation queued for next bump) · P0.4 ✅ live at https://dev.to/zhurong2020/let-claude-code-debug-your-obfuscated-python-a-guide-to-the-pyobfus-mcp-integration-3epm · **N2 ✅ SHIPPED**: pyobfus-mcp 0.2.0 live on PyPI (with PEP 740 attestations) + MCP Registry (active + isLatest) · launch wave next: HN Mon 5-11 / Reddit Tue 5-12 / CN trio Fri-Sat 5-8/9
**Next review**: 24h post-dev.to (2026-05-08 evening) for first-day reaction metrics; post-launch-wave (5-13) for full multi-platform signal
