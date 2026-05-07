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

### P0.3 — server.json `_meta` enrichment (30 min)

**Why**: Glama's 2026-01-24 spec post documents that MCP Registry preserves *only* the publisher-claimed `_meta` namespace, drops others. Claiming `io.github.zhurong2020.pyobfus_mcp` namespace **now** with structured fields locks pyobfus-mcp into downstream aggregator filters before they freeze on conventions.

**Reference**: <https://glama.ai/blog/2026-01-24-official-mcp-registry-serverjson-requirements>

**Action**: edit `pyobfus_mcp/server.json` to add (alongside existing `name` / `version` / `packages`):

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

Then re-publish via `mcp-publisher publish`. (Token at `~/.config/mcp-publisher/token.json` may need refresh — `mcp-publisher login github` if expired; ours was refreshed 2026-05-07 so should be valid for ~15 days.)

**Done when**: registry.modelcontextprotocol.io's JSON for our entry shows the `_meta` field populated.

---

### P0.4 — dev.to article voice rewrite + GPTZero gate (2 hours · BLOCKING the launch chain)

**Why**: this is the #1 leverage point currently blocked. Article #1 v2 is at `_drafts/article-01-claude-code-mcp-integration.md`, drafted 2026-05-05. Needs human-voice rewrite (per `_drafts/forum-ai-policy-and-voice-guide.md`) and must pass GPTZero detector before posting (current Claude 4 output flags ~98%).

**Action**:
1. Open `_drafts/article-01-claude-code-mcp-integration.md`
2. Rewrite per voice guide: remove em-dashes in prose, ban "delve into / furthermore / moreover", add specific numbers + anecdotes, vary paragraph length, use first-person + contractions
3. Run through gptzero.me (or detector of choice) — target <30% AI probability
4. Post Thursday/Friday evening (dev.to peak traffic)

**Done when**: article live on dev.to; sequence then triggers HN +48h, Reddit +24h after HN.

**Cross-review available**: `_drafts/cross-review-prompt.md` is a self-contained prompt to paste into Gemini / Claude.ai / ChatGPT for an outside-eye pass before posting.

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

#### N2 — pyobfus-mcp 0.2.0 = FastMCP 3.0 features (2-3 days)

**Why**: FastMCP 3.0 + mcp SDK 1.27 (April 2026) added **tool versioning** (`@tool(version="1.0")` — schema breaking changes don't orphan existing Claude Code sessions), **per-tool authorization**, and **OpenTelemetry instrumentation**. pyobfus-mcp 0.1.2 has none of these. Glama and other MCP aggregators will eventually add a "production-ready" filter — being on the wrong side of that line means we lose visibility.

**Action**:
1. Bump dep `mcp>=1.27.0,<2.0.0` (we're at `>=1.20.0,<2.0.0` after the 0.1.2 fix)
2. Add `version="1"` to all 5 `@app.tool` decorators
3. Add per-tool auth scaffold (config-driven allow-list of tools)
4. Wire OpenTelemetry stdout exporter (default off; opt-in via env var)
5. Bump pyobfus-mcp to 0.2.0; CHANGELOG entry

**Done when**: 5 MCP tools have versioned schema; OTel traces visible with `OTEL_EXPORTER_OTLP_ENDPOINT=...`; 0.2.0 on PyPI + Registry.

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
| punkpeye merges PR #5777 | 86k★-repo human cadence | 3-7 days typical |
| Glama "No glama.json" checklist clears | Glama cron re-scan after `glama.json` schema fix (commit `8d92487`) | 1-3 days |
| First external GitHub issue | Real user encounters something | depends on launch |
| First Pro license sale | Launch traffic + Stripe checkout funnel | depends on launch |
| GitHub stars 0 → 100+ | Launch + Glama/Registry organic discovery | depends on launch |
| Glama Quality grade re-check after `glama.json` fix | Eventual cron | 1-3 days |

---

## Strategic do-not-do list (decisions captured 2026-05-07)

- **Don't chase PyArmor's VMC virtualization**. They went deep into bytecode-VM obfuscation in 9.2.0 (Oct 2025) — that's a different lane, fundamentally stronger but conflicts with our AI-debuggability promise. Stay in AI-native lane.
- **Don't compete on AST mechanics**. Two new commoditized AST obfuscators (python-obfuscator, python-obfuscation-framework) shipped in last 5 weeks. Adding "another transformer" doesn't move our metrics; integration story does.
- **Don't bump pyobfus or pyobfus-mcp version just to refresh metadata**. Glama Release flow rejects same-version re-publishes; PyPI doesn't allow version overwrite. Use Glama's "Claim ownership flow again" mechanism (see `~/.claude/projects/-home-wuxia-projects-pyobfus/memory/glama_metadata_schemas.md`).
- **Don't add features to free tier that have no user-demand signal**. Old roadmap "Enhanced key obfuscation" and "Code compression" were deprioritized in 2026-04 strategic shift; keep them buried.

---

## Recommended near-term sequence (3 weeks)

```
Week 1 (5-7 → 5-14):
  └─ P0.1 + P0.2 + P0.3 (technical hygiene · 3 hours total)
  └─ P0.4 dev.to voice rewrite + GPTZero gate (2 hours)
  └─ Post dev.to Thursday/Friday evening

Week 2 (5-15 → 5-22):
  ├─ +48h after dev.to: HN Show HN
  ├─ +24h after HN: Reddit /r/Python
  ├─ Within 48h of dev.to: CN trio (有心工坊 + 知乎 + V2EX)
  └─ Parallel: ship N1 t-string handler + blog post

Week 3 (5-23 → 5-30):
  ├─ Review launch metrics; reweight v0.5 priorities accordingly
  ├─ Start N3 claude-skill preset (1-week effort)
  └─ N2 FastMCP 3.0 upgrade (2-3 day effort, can interleave)

By 2026-06-15: v0.5.0 release candidate (P2-1 + P2-3 + P2-4 + P2-5 + N1 + N2 + drop 3.8)
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

**Last updated**: 2026-05-07 (Session 17 + post-research synthesis)
**Next review**: after launch posts go live (week 2-3) OR after 3 P0 items closed
