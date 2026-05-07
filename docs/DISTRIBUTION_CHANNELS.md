# Distribution Channels State

Living reference of where `pyobfus` has a foothold, what each account looks like, and what's pending. Updated when a channel's state changes.

For the **why** behind the channel mix, see [AI_INTEGRATION_STRATEGY.md](AI_INTEGRATION_STRATEGY.md).
For **historical deltas** per session, see [V0.4_EXECUTION_LOG.md](V0.4_EXECUTION_LOG.md).

**Last updated**: 2026-04-22 (evening)

---

## 🟢 Live and owned

### PyPI — `pyobfus`
- URL: https://pypi.org/project/pyobfus/
- Current version: **0.4.0** (released 2026-04-22)
- Pre-v0.4 baseline: ~324 downloads / month, ~30% real users (rest is mirror noise)
- Tracker: `gh api repos/zhurong2020/pyobfus` + PePy

### PyPI — `pyobfus-mcp`
- URL: https://pypi.org/project/pyobfus-mcp/
- Current version: **0.1.0** live; **0.1.1** staged in `pyobfus_mcp/dist/` pending publish
- 0.1.1 adds `<!-- mcp-name: io.github.zhurong2020/pyobfus-mcp -->` marker + `server.json` required by MCP Registry

### GitHub — `zhurong2020/pyobfus`
- URL: https://github.com/zhurong2020/pyobfus
- Visibility: public
- Stars: 0 (target v0.4: 100+)
- Topics (12): `python-obfuscator`, `code-obfuscator`, `ast-obfuscation`, `mcp-server`, `claude-code`, `cursor`, `llm-tools`, `ai-native`, `pyarmor-alternative`, `python-security`, `code-protection`, `source-protection`
- Wiki: disabled · Discussions: enabled · Issues: open
- Releases: v0.3.3, v0.4.0 (2 GitHub Releases with wheel+sdist attached)

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
- Published: 2026-04-22 01:48:45 UTC · status: `active` · isLatest: `true` · version: 0.1.1
- Confirmed live via `curl https://registry.modelcontextprotocol.io/v0/servers?search=pyobfus`
- Implications: Claude Desktop / Claude Code / Cursor / Windsurf / Zed users querying the registry for "pyobfus" or "python obfuscator" will discover this server without manual config file edits.

## 🟡 Pending action

### `awesome-mcp-servers` community lists — 3 PRs pending
- `punkpeye/awesome-mcp-servers` (largest, most active)
- `wong2/awesome-mcp-servers`
- `appcypher/awesome-mcp-servers`
- Plan: one-line README addition per repo under "Developer Tools" or similar category; ~15 min total
- Trigger: after MCP Registry publish settles (prevents catching a 404 link)

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
