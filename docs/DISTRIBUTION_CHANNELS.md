# Distribution Channels State

Living reference of where `pyobfus` has a foothold, what each account looks like, and what's pending. Updated when a channel's state changes.

For the **why** behind the channel mix, see [AI_INTEGRATION_STRATEGY.md](AI_INTEGRATION_STRATEGY.md).
For **historical deltas** per session, see [V0.4_EXECUTION_LOG.md](V0.4_EXECUTION_LOG.md).

**Last updated**: 2026-08-22 (`pyobfus` 0.5.16 released 2026-08-22 — docs-only release: PyLocket comparison in `docs/COMPARISON.md` + verified/documented Python 3.14 free-threading compatibility. Previous: 0.5.15 released 2026-08-20 with the `compatibility_advisory` `--check` category + cookbooks; `pyobfus-mcp` 0.3.6 and VS Code extension 0.4.0 both shipped 2026-08-17, Marketplace upload **done** and listing re-verified at `"version":"0.4.0"`; 08-21 periodic recheck: downloads flat vs 08-20 baseline, Glama public page still lists 8 tools but version metadata stale at v0.5.13, Claude plugin submission still pending review). Earlier: 2026-06-08 (PR #5777 MERGED 2026-06-06 → punkpeye/awesome-mcp-servers now LIVE; Glama tool-count resolved 7/7).

> **Note (2026-05-09)**: most of the per-channel facts below are now current as of Session 23. Outside of the launch wave (HN 5-11 / Reddit 5-12 / CN trio 5-8/9), the live state is reflected here. Consult `docs/POST_V0.4_TODO.md` for forward TODO and `docs/V0.4_EXECUTION_LOG.md` for session-by-session deltas.

---

## 🟢 Live and owned

### PyPI — `pyobfus`
- URL: https://pypi.org/project/pyobfus/
- Current version: **0.5.16** (released 2026-08-22) · ships with PEP 740 attestations via OIDC trusted publishing
- Current headline: docs-only release — `docs/COMPARISON.md` gains a PyLocket entry, and Python 3.14 free-threading (`python3.14t`, PEP 779) compatibility is verified and documented in `docs/PYTHON314_FREETHREADING.md`. Previous 0.5.15: `--check` gains a `compatibility_advisory` category flagging real-world delivery-combo risks (import-hook/encrypted-file ecosystem, compiled packaging, model-serving), plus three new cookbooks and two runnable `examples/`.
- Pre-v0.4 baseline: ~324 downloads / month, ~30% real users (rest is mirror noise)
- Tracker: `gh api repos/zhurong2020/pyobfus` + PePy

### PyPI — `pyobfus-mcp`
- URL: https://pypi.org/project/pyobfus-mcp/
- Current version: **0.3.6** (released 2026-08-17) · ships with PEP 740 attestations via OIDC trusted publishing
- 0.3.6 contents: `server.json` now carries the GitHub repository stable ID and is re-validated against the official MCP Registry `2025-12-11` schema; a new regression test keeps `pyobfus_mcp.__version__`/`pyproject.toml`/`server.json` from drifting again. Tool surface unchanged (8 tools: 6 community + 2 pro_funnel).

### GitHub — `zhurong2020/pyobfus`
- URL: https://github.com/zhurong2020/pyobfus
- Visibility: public
- Stars: 0 (target v0.4: 100+)
- Topics (12): `python-obfuscator`, `code-obfuscator`, `ast-obfuscation`, `mcp-server`, `claude-code`, `cursor`, `llm-tools`, `ai-native`, `pyarmor-alternative`, `python-security`, `code-protection`, `source-protection`
- Wiki: disabled · Discussions: enabled · Issues: open
- Releases: latest `v0.5.16` (2026-08-22); earlier releases `v0.3.3` … `v0.5.15`, plus `mcp-v0.3.x` and `vscode-v0.x` tags (mcp releases attach wheel+sdist).

### 有心工坊 (personal blog)
- URL: https://www.arong.eu.org
- Content: CN-primary, cross-links to pyobfus in tech-empowerment (技术赋能) category
- Role in channel mix: long-form canonical CN article host; dev.to posts link here for the CN version

### Stack Overflow — Rong Zhu
- URL: https://stackoverflow.com/users/... (11 rep · 4 bronze badges)
- **Status: ⏸️ SEEDING PAUSED** (see `_drafts/stackoverflow-seeding-targets.md`)
- Rationale: SO's site-wide AI-content ban + low per-question traffic + low-rep account = bad risk/reward
- Re-evaluation trigger: pyobfus stars > 300 OR 6 months elapsed (whichever first)

### dev.to — `@zhurong2020` 🟢 FIRST POST LIVE
- URL: https://dev.to/zhurong2020
- Created: 2026-04-22
- Profile: Rong Zhu · `#f59e08` brand color · bio + 4 "Coding" fields + Work + Pronouns filled
- Current metrics (start of 2026-05-07 evening · post-publish baseline):
  - **Posts: 1** · Comments: 0 · Followers: 0
  - Following users: 28 (dev.to auto-suggestions from signup flow)
  - Following tags: 6
- Warm-up plan (executed pre-launch):
  - [x] Follow 10-15 deliberately-chosen MCP / python-obfuscation / claude-code authors
  - [x] Leave 3-5 substantive comments on related posts
  - [x] Post #1 scheduled 2026-04-24 evening → slipped to **2026-05-07 evening** (article went through v1 → v2 → v3 voice rewrite → v4 GPTZero-diagnostic-driven rewrite before final publish)
- **First post (LIVE 2026-05-07)**: *"Let Claude Code Debug Your Obfuscated Python: A Guide to the pyobfus MCP Integration"*
  - URL: <https://dev.to/zhurong2020/let-claude-code-debug-your-obfuscated-python-a-guide-to-the-pyobfus-mcp-integration-3epm>
  - Source-of-truth file: `_drafts/article-01-claude-code-mcp-integration.md` (kept post-publish for revision history)
  - Tags: `ai`, `python`, `claudecode`, `mcp`
  - Cover: `pyobfus-legal/software_copyright/screenshots/03_obfuscate_demo.png` (BEFORE/AFTER side-by-side)
  - 2 inline images: `04_json_output.png` (after Preflight check section) + `03_obfuscate_demo.png` (after Obfuscate-with-mapping section)
  - Body: 1,603 prose words · 9 fenced code blocks · disclosure line up-front

#### Auto-followed users after signup (2026-04-22)
Recording for provenance — these are dev.to's recommendations, not deliberate picks. Curated follow-ups happen during warm-up.

euromoscow · kevinmel2000 · bnlucas · hejhdiss · whoffagents · andreap · saqibjamil7866 · prashant_patil_9e62d3fa8a · luckypipewrench · shatru123 · andreas_eckhoff_7592e9859 · yaniv2809 · dev_rajput_2d46f92f8a3418 · idevusefulstuff · jon_at_backboardio · the_nortern_dev · elshadhu · bhavna_b_baa952ae51dac930 · marcosomma · syedahmershah · konark_13 · webdeveloperhyper · chocoscoding · codewithshahan · eayurt · code42cate · crd · jess

Note: `@jess` is Jess Lee, dev.to co-founder — useful to keep; `@code42cate` (Jonas Scholz) is a dev-tools creator — relevant to follow deliberately.

---

### MCP Registry — `io.github.zhurong2020/pyobfus-mcp` 🟢 LIVE
- URL: https://registry.modelcontextprotocol.io/v0/servers?search=pyobfus
- Latest published: **0.3.6** (2026-08-17) · status: `active` · `isLatest` confirmed via `mcp-publisher publish` (GitHub device-code re-auth) and the public search endpoint.
- 0.3.6 hardening: `pyobfus_mcp/server.json` validates against the official `2025-12-11` schema and includes GitHub repository stable ID `1093960892`; `fileSha256` remains omitted because the PyPI wheel/sdist multi-artifact model makes a single optional hash ambiguous.
- Implications: Claude Desktop / Claude Code / Cursor / Windsurf / Zed users querying the registry for "pyobfus" or "python obfuscator" will discover this server without manual config file edits.

### Glama — `zhurong2020/pyobfus` 🟡 LISTED / API STALE
- Public page: https://glama.ai/mcp/servers/zhurong2020/pyobfus
- 2026-08-21 recheck: the public page is reachable and still exposes 8 tool names, but its version metadata is stale (shows v0.5.13; current is 0.5.16); the older API path `/api/mcp/v1/servers/io.github.zhurong2020/pyobfus-mcp` still returns `not_found`.
- 2026-08-20: third-party maintainers independently reproduced both symptoms (build stuck on `debian:trixie-slim`, page OK but public API stale) — confirms this is Glama-side infra/sync, not a pyobfus-mcp code issue. Discord `#support` still unanswered as of 08-21; policy is passive-wait, no code change, no re-pin until Glama responds.

### Claude Plugin Marketplace 🟡 PENDING
- Console entry: `pyobfus`
- 2026-08-21 recheck: still `Submitted and pending review`, submission date Aug 2 (Console is login-gated; verified by maintainer's manual check on 08-20, no change).
- Known copy issue: submitted description says `protected_project`; correct tool name is `protect_project`. Do not resubmit only for this typo; fix opportunistically if Anthropic exposes an edit/request-changes path.

### OpenSSF Best Practices passing badge 🟢 LIVE
- URL: https://www.bestpractices.dev/projects/12788
- Project ID: 12788 · achieved: 2026-05-09 04:23:38 UTC · tier: passing (Metal series) · 67/67 criteria
- Categories met: Basics 13/13 · Change Control 9/9 · Reporting 8/8 · Quality 13/13 · Security 16/16 · Analysis 8/8
- Same tier as Kubernetes / Curl / etcd
- Badge embedded in pyobfus README header (commit `eb634ab`)
- Implications: marketable third-party project-maturity credential. Cross-referenced in awesome-mcp-servers PR #5777 description (silent edit 2026-05-09). Useful in HN/Reddit launch posts as supporting evidence; useful in 软著 / patent applications as "production use" proof (see `memory/patent_software_copyright_sync_2026-05-09.md`).

## 🟡 Pending action

### `awesome-mcp-servers` community lists — 2 LIVE / 1 dead-end (refreshed 2026-06-08)
- 🟢 **`wong2/awesome-mcp-servers` LIVE** via mcpservers.org (the list has retired direct PRs; submissions go through the form-driven `mcpservers.org/submit` channel). Listing: <https://mcpservers.org/servers/zhurong2020/pyobfus>. Approval landed same-day (2026-05-08) vs the 7-day SLA.
- 🟢 **`punkpeye/awesome-mcp-servers` PR #5777 MERGED 2026-06-06** (opened 2026-05-03 · merged by punkpeye/Frank Fiegel after ~34 days at 86K★-repo human cadence). pyobfus-mcp now listed under Developer Tools. All bot gates were green throughout (`has-emoji`/`has-glama`/`valid-name`).
- ❌ **`appcypher/awesome-mcp-servers` DEAD-END** — repo owner has disabled both PRs and Issues (`gh api repos/appcypher/awesome-mcp-servers --jq '.has_issues'` returns `false`). The CONTRIBUTING.md is stale; repo is in read-only museum mode despite still appearing active. Fork retained at `zhurong2020/awesome-mcp-servers-appcypher` for re-fork in 1 click if owner reopens.
- Implications: **2 of 3 lists now actively distribute pyobfus-mcp (≥ 90K combined stars), both LIVE** (no longer PR-gated). The launch wave's awesome-list discoverability is fully in place.

---

## 🔵 Planned, not established

### Hacker News
- No account yet (if needed, use email `zhurong0525@gmail.com`)
- Intended use: **one** Show HN after dev.to article #1 gets social proof (goal: 100+ reactions on dev.to first)
- AI policy: banned outright; post must be manually written by maintainer

### Reddit — `/r/Python`
- No pyobfus-dedicated handle planned; personal account used with disclosure
- Target: **"Showcase Saturday" pinned thread** (not a standalone post)
- AI policy: mods remove AI-looking content on sight; human voice required

### Medium
- Deferred. dev.to-first; Medium considered only if dev.to article performs (>5k views) as a reach extension with AI-disclosure header

### Zhihu (知乎) / 微信公众号 / 小红书
- Not in current plan; 有心工坊 covers the CN long-form need. Revisit Q3 2026 if CN traffic signal justifies.

---

## 📊 Metrics targets (from AI_INTEGRATION_STRATEGY.md §5)

| Metric | Baseline 2026-04-22 | v0.4 target (6 weeks) | v0.5 target |
|---|---|---|---|
| PyPI `pyobfus` monthly downloads | 324 | 1,500+ | 5,000+ |
| GitHub stars | 0 | 100+ | 300+ |
| External GitHub issues opened | 0 | 1+ | 5+ |
| MCP server installs | — | 500+ | — |
| AI-assistant recommend rate (blind test) | 0/10 | 3/10 | 7/10 |
| dev.to followers | 0 (2026-04-22) → 0 (2026-05-07 post-publish) | 50+ | 200+ |
| dev.to first-post reactions @ 24h | TBD (publish 2026-05-07 evening) | 30+ | — |
| dev.to first-post reactions @ 7d | TBD | 100+ | — |
| First pyobfus Pro license sale | — | 1 | — |

Tracking cadence: every 2 weeks append a row to V0.4_EXECUTION_LOG.md.

---

## 🔁 When to update this file

Update whenever:
- A new channel is established (account created, repo forked, etc.)
- A channel's status changes (paused ↔ active)
- A publish / post goes live (note the URL + date)
- Monthly metrics snapshot (copy current row of numbers)
