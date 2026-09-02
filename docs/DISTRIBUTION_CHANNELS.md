# Distribution Channels State

Living reference of where `pyobfus` has a foothold, what each account looks like, and what's pending. Updated when a channel's state changes.

For the **why** behind the channel mix, see [AI_INTEGRATION_STRATEGY.md](AI_INTEGRATION_STRATEGY.md).
For **historical deltas** per session, see [V0.4_EXECUTION_LOG.md](V0.4_EXECUTION_LOG.md).
For the frozen post-release evidence and recheck checklist from 2026-08-24, see
[EXTERNAL_CHANNEL_SNAPSHOT_2026-08-24.md](EXTERNAL_CHANNEL_SNAPSHOT_2026-08-24.md).

**Last updated**: 2026-09-02 (standalone SEO releases: pyobfus 0.5.20 and
pyobfus-mcp 0.3.10 published through OIDC; all four Integrity provenance
endpoints HTTP 200, fresh wheel installation verified, GitHub Releases created.
Runtime behavior and MCP schemas are unchanged. MCP Registry 0.3.10 is published
and publicly verified `active` / `isLatest=true`. VS Code extension remains 0.4.1.)

> **Note (2026-05-09)**: most of the per-channel facts below are now current as of Session 23. Outside of the launch wave (HN 5-11 / Reddit 5-12 / CN trio 5-8/9), the live state is reflected here. Consult `docs/POST_V0.4_TODO.md` for forward TODO and `docs/V0.4_EXECUTION_LOG.md` for session-by-session deltas.

---

## 🟢 Live and owned

### PyPI — `pyobfus`
- URL: https://pypi.org/project/pyobfus/
- Current version: **0.5.20** (released 2026-09-01) · ships with PEP 740 attestations via OIDC trusted publishing
- Current headline: discovery-focused metadata and README/FAQ improvements around pre-shipping protection, reverse mapping, provenance, and AI-assisted debugging; runtime behavior unchanged.
- Prior headline (0.5.19): `--dry-run --json` emits a versioned `plan` object (effective config, selected/excluded files with reasons, artifacts tagged ship/retain-internal/optional; relative labels only, not applyable); opt-in `--verify-syntax` compiles generated output in memory post-build (no import/execute, no `__pycache__`) and reports `syntax_valid` with no runtime-correctness claim.
- Prior headline (0.5.18): config-aware `--check` reports the effective project configuration and findings already mitigated by it, while preserving high-risk findings and exit-code semantics.
- Pre-v0.4 baseline: ~324 downloads / month, ~30% real users (rest is mirror noise)
- 2026-08-24 pypistats snapshot (data through 08-23, known mirrors excluded):
  day/week/month `27 / 502 / 2,059`. Weekly growth is dominated by release-day
  spikes (08-17 `124`, 08-20 `119`, 08-22 `151`); 08-23 returned to `27`, so
  this is not yet evidence of a higher organic baseline.
- 2026-08-26 recheck (data through 08-25): 08-24 release-day downloads were
  `137`, then returned to `27` on 08-25; latest day/week/month is
  `27 / 512 / 2,178`. No organic-baseline uplift established.
- Tracker: `gh api repos/zhurong2020/pyobfus` + PePy

### PyPI — `pyobfus-mcp`
- URL: https://pypi.org/project/pyobfus-mcp/
- Current version: **0.3.10** (released 2026-09-01) · ships with PEP 740 attestations via OIDC trusted publishing
- 0.3.10 contents: intent-oriented Registry description and expanded PyPI discovery keywords; tool behavior and schemas unchanged.
- 0.3.9 contents: `check_obfuscation_risks` adds default-on `use_project_config`, returns effective-config and excluded-finding context from Core, and moves the runtime dependency floor to `pyobfus>=0.5.18`.
- 2026-08-24 pypistats snapshot (data through 08-23, known mirrors excluded):
  day/week/month `11 / 242 / 772`. Release-day spikes (08-17 `95`, 08-22 `110`)
  dominate the weekly increase; 08-23 returned to `11`. CI/CD traffic remains
  included, so do not treat the increase as organic adoption yet.
- 2026-08-26 recheck (data through 08-25): 08-24 release-day downloads were
  `99`, then returned to `8` on 08-25; latest day/week/month is
  `8 / 245 / 874`. No organic-baseline uplift established.

### GitHub — `zhurong2020/pyobfus`
- URL: https://github.com/zhurong2020/pyobfus
- Visibility: public
- Stars: 6 (2026-08-24 snapshot; historical v0.4 target was 100+)
- Topics (19, updated 2026-09-01): includes `python-obfuscator`, `ast-obfuscation`, `mcp-server`, `reverse-mapping`, `stack-trace-deobfuscation`, `debuggable-obfuscation`, `github-copilot`, `codebuddy`, `provenance`, and `apache-2-0` discovery surfaces.
- 2026-08-24 feedback snapshot: 6 stars, 2 forks, 0 open issues/PRs; six
  Discussions with no new external comment on the 0.5.x announcement or
  dependency advisory. 14-day Traffic: 155 views / 65 unique visitors and
  1,480 clones / 158 unique cloners. Release-day automation dominates clones;
  08-23 nevertheless recorded 10 unique cloners. Treat as interest, not proven
  retention or production adoption.
- 2026-08-26 feedback recheck: still 6 stars, 2 forks and no open issue/PR or
  new Discussion comment. 14-day Traffic is now 176 views / 72 unique and
  1,751 clones / 182 unique. Release day 08-24 produced 268 clones / 31 unique;
  08-25 returned to 10 / 6. README and CHANGELOG each had only 3 unique views,
  so there is still no attributable `dependency_advisory` usage signal.

### VS Code Marketplace — `zhurong2020.pyobfus`
- 2026-08-24 public Gallery API: version 0.4.1, 3 installs, 124 downloads.
- No identifiable user rating/review signal yet; the API's weighted-rating
  prior is not evidence of an actual review. Continue tracking installs and
  real reviews, not raw update/download count alone.
- Wiki: disabled · Discussions: enabled · Issues: open
- Releases: latest `v0.5.20` and `mcp-v0.3.10` (2026-09-01), plus earlier Core, MCP, and VS Code tags (MCP releases attach wheel+sdist).

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
- Latest confirmed published: **0.3.10** (2026-09-02 Registry publication;
  package released 2026-09-01) · status: `active` · `isLatest=true`. The public
  version endpoint also confirms package version 0.3.10 and the updated
  pre-shipping / reverse-traceback / no-phone-home description. The prior
  TLS/EOF outage is resolved; no rebuild, retag, or PyPI re-upload was needed.
- 0.3.10 contents: discovery metadata and Registry intent-description updates;
  runtime behavior and schemas are unchanged. Prior 0.3.9 added default-on
  project-config awareness and runtime floor `pyobfus>=0.5.18`. Previous 0.3.6
  hardening: `pyobfus_mcp/server.json` validates against the official
  `2025-12-11` schema and includes GitHub repository stable ID `1093960892`;
  `fileSha256` remains omitted because the PyPI wheel/sdist multi-artifact model
  makes a single optional hash ambiguous.
- Implications: Claude Desktop / Claude Code / Cursor / Windsurf / Zed users querying the registry for "pyobfus" or "python obfuscator" will discover this server without manual config file edits.

### Glama — `zhurong2020/pyobfus` 🟡 LISTED / API STALE
- Public page: https://glama.ai/mcp/servers/zhurong2020/pyobfus
- 2026-08-21 recheck: the public page is reachable and still exposes 8 tool names, but its version metadata is stale (shows v0.5.13; current is 0.5.16); the older API path `/api/mcp/v1/servers/io.github.zhurong2020/pyobfus-mcp` still returns `not_found`.
- 2026-08-20: third-party maintainers independently reproduced both symptoms (build stuck on `debian:trixie-slim`, page OK but public API stale) — confirms this is Glama-side infra/sync, not a pyobfus-mcp code issue. Discord `#support` still unanswered as of 08-21; policy is passive-wait, no code change, no re-pin until Glama responds.
- 2026-08-22 recheck (post 0.5.16 release, user-supplied page dump): "Recent Releases" panel now lists **`0.5.12` dated 2026-08-22** — that version number belongs to the core `pyobfus` package's last GitHub Release (tagged 2026-08-06, before this session added `v0.5.16`), not to `pyobfus-mcp`'s own 0.3.x scheme, so Glama appears to be pulling GitHub Release tags from the shared `zhurong2020/pyobfus` repo without filtering by which sub-package they belong to, and mislabeling the date on top of that. Configured "Pinned commit SHA" also still reads `cd823d1` (pre-dates the 0.5.16 release commit `f694f3a`). Same underlying Glama-side crawler defect as above — no action taken, policy unchanged.
- 2026-08-24 post-0.3.8 recheck (user-supplied admin page): Build steps has already
  updated correctly to `pyobfus-mcp==0.3.8` and triggered Recent Test
  `01a033e4-3336-7e7b-9792-0d7e056d2dba` at 21:09. The page excerpt does not
  expose that test's pass/fail result, so record it only as "triggered", not
  "successful". Glama's newly advertised API path
  `/api/mcp/v1/servers/zhurong2020/pyobfus` is reachable but still returns
  `tools: []`. "Recent Releases" now calls the same event `0.5.14`, again proving
  that panel's numbering is not the MCP package's real 0.3.x version. Pinned SHA
  is now `e44e687` while repository HEAD is `8f00fba`; this does not change the
  runtime package because the Dockerfile explicitly installs the PyPI 0.3.8
  artifact, but it does explain stale checkout/page metadata. No local code fix.
- 2026-08-24 final test evidence (user-supplied admin logs): test
  `01a033e4-3336-7e7b-9792-0d7e056d2dba` completed **success** in 12.1s.
  Install logs confirm `pyobfus-mcp==0.3.8` plus `pyobfus==0.5.17`; the live
  `ListToolsRequest` returned all 8 tools and the new
  `verify_dependencies_online` input field. This closes the build/runtime side
  completely. The public API's `tools: []` is now proven to be directory sync
  drift, not a server introspection failure. Build Spec reports
  `pinnedCommit: null` even though generated clone logs still checkout
  `e44e687`, another Glama metadata inconsistency with no runtime impact.
- 2026-08-26 programmatic recheck: the public listing still exposes all 8 tool
  names. The formerly public API path now returns HTTP 401, so it is no longer a
  usable unauthenticated health check; continue treating the listing plus the
  successful live `ListToolsRequest` as the available evidence.

### MCP Skills trust score — 🟡 ESTABLISHED / NOT VERIFIED
- 2026-08-24 official free score API scan for `zhurong2020/pyobfus`: composite
  **6.06**, tier `established`, 14 signals, `verified=false`.
- Positive evidence: `no safety findings`; the scanner detected the AI skill.
- Blocking flags: `SINGLE_AUTHOR_LOW_ADOPTION` and `low_legit`. Because Verified
  requires composite >=7.0 plus dimension floors and no disqualifiers, the repo
  cannot claim the gold badge yet.
- Decision: do not buy the $2 full report or optimize code/docs merely to game
  the score. Re-scan after genuine adoption/contributor growth; external
  contributors, stars and real usage should improve the weak dimension
  honestly.

### Canopii Trust Index — 🟡 FALSE POSITIVE / CLAIM + RESCAN PENDING
- 2026-08-24 page state: latest scanned version is stale at MCP v0.3.7, score
  39/100 (F), confidence 81%. Its sole high failure is a broad
  `marshal.loads(...)` match at `pyobfus_pro/runtime/opacity.py:147`.
- The evidence is in the sibling Pro runtime, not `pyobfus_mcp/`, and follows a
  successful authenticated AES-GCM decrypt. No MCP tool input reaches that
  bytes/key/plaintext path. The public Canopii rule is syntax-only and scans the
  whole monorepo, so this is not evidence of an exploitable MCP deserialization
  path.
- Next action: maintainer claims the listing with GitHub and requests a v0.3.8
  rescan. If unchanged, file an upstream false-positive/scope issue with the
  authenticated-data-flow and Registry subfolder evidence. Do not embed the F
  badge or change product behavior merely to silence the scanner.
- Full evidence and the exact recheck sequence:
  [EXTERNAL_CHANNEL_SNAPSHOT_2026-08-24.md](EXTERNAL_CHANNEL_SNAPSHOT_2026-08-24.md#canopii-trust-index39100f-的处理结论).

### Claude Plugin Marketplace 🟡 PENDING
- Console entry: `pyobfus`
- 2026-08-24 maintainer recheck: still `Submitted and pending review`, submission date Aug 2.
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
