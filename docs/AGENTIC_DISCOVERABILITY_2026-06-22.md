# pyobfus — Agentic Discoverability & Usability Research

**Date**: 2026-06-22 · **Author**: Claude (research session) · **Status**: research deliverable, not yet folded into ROADMAP.md
**Question**: Beyond traditional SEO, how do we make pyobfus easy for AI agents to **find** and **use**?

---

## 0. TL;DR — do these, in this order

| # | Action | Why | Effort | Type |
|---|---|---|---|---|
| 1 | **Claim/list on Smithery + PulseMCP + mcp.so** | pyobfus is **confirmed absent** from the 3 biggest agent-runtime registries. Agents query these natively at runtime — not being there = invisible to them. | 0.5–1 day | Distribution |
| 2 | **Punch up `server.json` description** (100-char budget) | Current line is generic; differentiators (no phone-home / reverse-map / AI-native) are the agent's selection signal. | 30 min | Copy |
| 3 | **Add `uvx pyobfus-mcp` zero-install one-liner** to README + every registry | "Single command, no API key" is the trait shared by the highest install-to-view servers. | 1–2 hr | DX |
| 4 | **Write launch-wave posts in AEO structure** (answer-first, named numbers, self-contained paras) | AI search is now 12–18% of informational queries. Same content → traditional SEO + AI citation + entity authority. | folded into launch | GEO/AEO |
| 5 | **Publish `ai-catalog.json` (ARD)** at the docs domain | New Google + Linux Foundation standard (announced late May 2026). Static JSON on a CDN qualifies. Early-bird, on-brand for an AI-native tool. | 2–3 hr | Emerging |

**The headline finding**: pyobfus is *already excellent* at the **"usable by agents"** half (structured output, `ai_hint`/`next_tool`, high-quality tool descriptions, llms.txt, IDE rule templates, a Claude Skill). The real deficit is the **"found by agents"** half — specifically **registry breadth** and **being cited by AI answer engines**. This report focuses there.

---

## 1. The two axes

The user's framing is exactly right: there are two separate games now.

1. **Traditional discovery (SEO)** — humans Googling "Python obfuscator", "PyArmor alternative". pyobfus already has a landing-page plan (`/pyarmor-alternative`) and keyword-dense PyPI metadata.
2. **Agentic discovery + usage** — an AI agent (Claude Code, Cursor, a Smithery-backed assistant) needs to (a) **find** pyobfus when a user says "obfuscate my code before shipping", and (b) **call it correctly** once found.

These two games have *different front doors*. Winning SEO does nothing for (2a), and vice-versa. The rest of this report is about game 2.

---

## 2. Current-state audit (what pyobfus already has)

Verified by reading the repo + querying live registries on 2026-06-22.

### ✅ "Usable by agents" — already strong, leave mostly alone

| Asset | State | Notes |
|---|---|---|
| `pyobfus-mcp` server | 8 tools, stdio, on PyPI 0.3.1 | Good tool count (target is 5–15; agent accuracy collapses past 30 with overlapping descriptions). |
| Tool descriptions | **High quality** | Read directly from `server.py`. Each states purpose + inputs + outputs + when-to-use. `protect_project`'s description is a model example. **Well above** the "97% of tool descriptions have quality issues" bar. |
| Structured output | `ai_hint` + `next_tool` on every tool | Exactly what the 2026 guides demand: JSON with consistent shape, not prose. |
| `llms.txt` + `llms-full.txt` | root + `docs/` | Has a "When to use / When NOT to use" section — excellent for agent decision-making. |
| IDE rule templates | `templates/ai-integration/` (7 files) | AGENTS.md, CLAUDE.md, copilot, .cursorrules, cursor-rules.mdc, windsurf, README. |
| Claude Skill | `skills/pyobfus-protect/SKILL.md` | Present, but **not yet submitted to any Skill directory** (see Gap 1). |
| Outcome-style tool names | `check_obfuscation_risks`, `unmap_stack_trace`, `protect_project` | Named for task outcomes, not resources. Correct per 2026 guidance. |
| Zero-key for community tools | `server.json`: stdio + pypi, no env/config | The Pro funnel is the only thing gated; community tools need no key. **This advantage is currently understated** (see Gap 3). |

### ✅ Discovery — present in 3 registries

| Registry | State | Evidence |
|---|---|---|
| Official MCP Registry | ✅ 0.3.1, isLatest | `io.github.zhurong2020/pyobfus-mcp` |
| Glama | ✅ Quality A | Listed, all tools graded A |
| awesome-mcp-servers (punkpeye) | ✅ merged | PR #5777, 2026-06-06 |

---

## 3. Gap analysis

### 🔴 Gap 1 — Registry breadth: absent from the 3 biggest agent-runtime registries

**Confirmed on 2026-06-22:**
- **PulseMCP** (11,840+ servers): searched `pyobfus` → **"0 of 0 servers… No servers found."**
- **Smithery** (7,000+ servers): search returned nothing; Smithery is described as the *"primary MCP search layer — agents query it natively at runtime."*
- **mcp.so** (19,700+ community servers): not found in search results.

This is the single highest-leverage gap. The Official Registry + Glama are where *IDE/governance* tools look; **Smithery/PulseMCP/mcp.so are where running agents look**. There is *"no single front door — you need to be in every room where an agent might look."*

**How to fix (each is a one-time registration):**

- **Smithery** — CLI-first. `npm install -g @smithery/cli`, then `smithery mcp publish`. Smithery also auto-crawls, so the job is *"claim and clean up"* the listing rather than create it. Provide: name, one-sentence capability, tool count (8), transport (stdio), GitHub URL, homepage, optional icon. Pre-test with a JSON-RPC 2.0 `initialize` (protocolVersion `2025-11-25`).
- **PulseMCP** — hand-reviewed daily by the founder; submit via their site form. Rewards *"reviewed servers with meaningful descriptions"* — pyobfus's descriptions already qualify.
- **mcp.so** — community submission; good for newer/experimental coverage.
- **Skill directory (ClawHub / someclaudeskills.com)** — pyobfus already ships a Claude Skill but it's discovered *separately* from MCP registries. Submit `pyobfus-protect` there.

> **Verify-first step**: before submitting, double-check Smithery/mcp.so by hand (the 403 on direct fetch means I couldn't 100% confirm Smithery; PulseMCP's 0-result is confirmed). If any already auto-crawled a stale listing, claim + update it to 0.3.1.

### 🟠 Gap 2 — `server.json` top-line description is generic

Current (73 chars, under the 100-char budget):
> `MCP tools for pyobfus — the Python obfuscator for AI-assisted development.`

This is the string an agent reads *first* when scanning a registry of thousands. It states the category but **none of the differentiators**. Agents pick on specifics. Proposed rewrite (≤100 chars), leading with what's unique:
> `Obfuscate Python + reverse-map stack traces. AST-based, no phone-home, AI-debuggable. PyArmor alt.`
> (97 chars)

Also worth surfacing in the registry blurb: **8 tools, no API key, Apache-2.0 core**. (Individual tool descriptions need **no change** — they're already strong.)

### 🟡 Gap 3 — GEO/AEO: not yet optimized to be *cited* by AI answer engines

This is the explicit "AI 查询" the user named — being the tool Claude/ChatGPT/Perplexity *names* when a user asks "how do I obfuscate Python / what's a PyArmor alternative". AI search is now **12–18% of English informational queries** (up from <2% a year ago).

**Tactics (all feed the launch wave — write once, win three games):**
1. **Answer-first opening** — README + every landing page must answer the query in the **first 1–2 sentences** with a **specific number + named source**. Example: *"pyobfus is an open-source AST-based Python obfuscator: $45 one-time (no per-build phone-home, unlike PyArmor), 1,024 tests, Python 3.9–3.14."* The first 30% of the page is what gets extracted.
2. **Self-contained, extractable paragraphs** — each paragraph standalone (an answer engine quotes one paragraph, not your whole page).
3. **FAQ structured data** — add FAQ schema to the docs/landing pages ("Is pyobfus free?", "How is it different from PyArmor?", "Does it break my framework?").
4. **Named statistics with sources** — the PyArmor trial-limit finding (935–940 lines/file, empirically measured) and "1,024 tests / Python 3.9–3.14 / $45 one-time" are exactly the citable, sourced facts answer engines prefer.
5. **Indexing lag to expect**: Perplexity 2–7 days, ChatGPT 7–21 days, Claude & Google AI Overviews 14–45 days. So **front-load the AEO rewrite before the launch wave**, not after.

### 🟡 Gap 4 — Zero-friction install not maximally frictionless

`server.json` already needs no API key (good). But the modern zero-friction pattern is **`uvx pyobfus-mcp`** (run with no prior `pip install`) and a **copy-paste `mcp.json` block**. The highest install-to-view servers all share "one line, no config." Action: confirm `uvx pyobfus-mcp` works, then put the one-liner + `mcp.json` snippet at the **top** of the README and in every registry listing.

```jsonc
// ~/.claude/mcp.json (or Cursor/Windsurf equivalent)
{ "mcpServers": { "pyobfus": { "command": "uvx", "args": ["pyobfus-mcp"] } } }
```

### ✅ Gap 5 (implemented locally 2026-07-20) — ARD `ai-catalog.json`

**Agentic Resource Discovery (ARD)** — open spec from Google + a Linux Foundation working group, **announced late May 2026** (≈4 weeks ago). A provider hosts a machine-readable **`ai-catalog.json`** at a well-known path; it lists the provider's MCP servers, A2A agents, OpenAPI tools, etc. *"A static JSON file on a CDN is a valid ARD publisher — no proprietary SDK."*

pyobfus has a docs domain (readthedocs) and a GitHub Pages-capable repo. Publishing an `ai-catalog.json` that points at `pyobfus-mcp` is a **2–3 hour, on-brand, first-mover** move: pyobfus gets to credibly say it supports the newest agent-discovery standard the same month it shipped. Spec: `agenticresourcediscovery.org/spec`, repo `github.com/ards-project/ard-spec` (Apache-2.0).

**2026-07-20 update:** the ARD 1.0 manifest now lives at
`docs/.well-known/ai-catalog.json`; `mkdocs.yml` explicitly includes the hidden
directory and CI validates the JSON. Read the Docs versions content under
`/en/latest/`, so publication is not complete until the project admin adds an
exact redirect from `/.well-known/ai-catalog.json` to
`/en/latest/.well-known/ai-catalog.json` and verifies HTTPS, JSON content type,
CORS `*`, and the final body after the docs build deploys.

**2026-08-02 verification:** the versioned path is live:
`https://pyobfus.readthedocs.io/en/latest/.well-known/ai-catalog.json` returns
HTTP 200, `content-type: application/json`, and `access-control-allow-origin: *`.
The root well-known path still returns HTTP 404, so the remaining work is only the
Read the Docs root redirect/admin step.

---

## 4. Prioritized action plan

**Wave A — this week (distribution + copy, mostly hours):**
- [ ] Verify-then-claim listings: Smithery, PulseMCP, mcp.so (Gap 1)
- [ ] Submit `pyobfus-protect` Skill to a Skill directory (Gap 1)
- [ ] Rewrite `server.json` description ≤100 chars with differentiators (Gap 2) — *next `mcp-v0.3.2` or doc-only registry edit*
- [ ] Add `uvx pyobfus-mcp` + `mcp.json` block to README top (Gap 4)

**Wave B — before/with the launch wave:**
- [ ] AEO-restructure README + landing pages (answer-first, named numbers, FAQ schema) (Gap 3)
- [ ] Reuse PyArmor trial-limit + test-count facts as citable, sourced statistics (Gap 3)

**Wave C — emerging bet (one afternoon):**
- [~] ARD manifest implemented, CI-validated, and live at the Read the Docs
  versioned path; root well-known redirect remains an admin action (Gap 5)
- [ ] (optional) `npx pyobfus-mcp` thin wrapper to also occupy the npm "room"

---

## 5. What NOT to do (lane discipline)

- **Don't add more MCP tools chasing coverage.** 8 is in the sweet spot; past ~30 with overlapping descriptions, agent selection accuracy collapses. Quality over count.
- **Don't gate community tools behind any key/OAuth.** Every credential step is a drop-off. Keep the Pro funnel as the *only* gated surface.
- **Don't let marketing copy leak into tool descriptions.** Agents penalize fluff; keep them factual (purpose/inputs/outputs/auth). They already are — protect that.

---

## 6. How this compounds with the launch wave

The launch wave (HN/Reddit/dev.to, currently in `_drafts/`) and this agentic-discoverability work are the **same content effort** viewed from two angles:
- An AEO-structured dev.to/HN post → ranks in traditional search **and** becomes an answer-engine citation source **and** builds entity authority that makes Claude/Perplexity more likely to name pyobfus.
- Registry listings (Smithery/PulseMCP) → give agents a runtime path to the tool the moment a launch reader's agent goes looking.

**Recommendation**: do **Wave A (registries + uvx + server.json)** *before* firing the launch wave, so that when launch traffic's agents go looking, pyobfus is already in every room. Then write the launch posts in AEO structure (Wave B).

---

## 6.5 Progress log

- **2026-06-22 — Smithery (via Skill channel)**: ✅ Published. Smithery's *MCP* publish flow is **remote-HTTP-only** in 2026 (asks for `https://…/mcp` gateway URL) — a structural non-fit for a local-execution obfuscator (a hosted instance can't read the user's local files). Pivoted to Smithery's **Skill** publish path (GitHub-folder import, no hosting): listed `pyobfus-protect` at **`smithery.ai/skills/zhurong2020/pyobfus-protect`**, rendering correctly with one-click install across ~20 agent clients (Claude Code, Cursor, Codex, Windsurf, Goose, …). `smithery.yaml` stays in the repo (harmless; ready if Smithery adds local-server GitHub crawl). **Lesson: for local-execution tools, Smithery = Skill channel, not MCP channel.** (Namespace note: Smithery defaults the namespace to the GitHub-account *email local-part* (`zhurong0525`), not the GitHub username — create a brand-matching namespace (`smithery namespace create zhurong2020`) and republish under it, else the URL handle won't match the repo/brand.)
- **2026-06-22 — mcp.so**: ✅ Submitted via web form (`mcp.so/submit`). Created `pyobfus — Python Obfuscator` @zhurong2020 with 5 tags, the sharpened 99-char description, and a full Overview (8 tools, `uvx` install, no API key). Note: the form's **Server Config field is read-only** (shows a github/docker placeholder) — but it does NOT surface on the public page; mcp.so populates the real config by crawling the repo (README now carries the correct `uvx` mcpServers block). Public page is high-quality.
- **2026-06-22 — server.json blurb + uvx**: ✅ Committed `826c576` — README leads with `uvx pyobfus-mcp` zero-install; server.json description rewritten to 99-char differentiator-first (ships to MCP Registry on next mcp-v0.3.2 publish).
- **Next**: PulseMCP (`pulsemcp.com/submit`, same form pattern). Then Wave A done — remaining levers (GEO/AEO, launch wave) are a separate effort.

## 7. Sources

- [Getting Found by Agents: A Builder's Guide to Tool Discovery in 2026 — icme.io](https://blog.icme.io/getting-found-by-agents-a-builders-guide-to-tool-discovery-in-2026/)
- [Where to Find MCP Servers in 2026 — Automation Switch](https://automationswitch.com/ai-workflows/where-to-find-mcp-servers-2026) · [How to list your MCP server (Registry/Smithery/Glama/PulseMCP) — Tallyfy](https://tallyfy.com/how-to-list-mcp-server-registry-smithery-glama-pulsemcp/) · [MCP Registries in 2026 — RoxyAPI](https://roxyapi.com/blogs/mcp-registries-where-to-list-your-server)
- [Smithery CLI — GitHub](https://github.com/smithery-ai/cli) · [Smithery — WorkOS](https://workos.com/blog/smithery-ai) · [PulseMCP directory](https://www.pulsemcp.com/servers)
- [MCP tool discovery for LLM agents — Portkey](https://portkey.ai/blog/mcp-tool-discovery-for-llm-agents/) · [Solving the MCP Tool Discovery Problem (MCP-Zero) — Medium](https://medium.com/@amiarora/solving-the-mcp-tool-discovery-problem-how-ai-agents-find-what-they-need-b828dbce2c30)
- [Generative Engine Optimization 2026 — AI Magicx](https://www.aimagicx.com/blog/generative-engine-optimization-chatgpt-perplexity-2026) · [AEO Checklist 2026 — authoritytech.io](https://authoritytech.io/curated/answer-engine-optimization-checklist-chatgpt-perplexity-claude-2026) · [AEO Playbook 2026 — ALM Corp](https://almcorp.com/blog/answer-engine-optimization-2026/)
- [Announcing the ARD specification — Google Developers Blog](https://developers.googleblog.com/announcing-the-agentic-resource-discovery-specification/) · [ARD spec](https://agenticresourcediscovery.org/spec/) · [ard-spec — GitHub](https://github.com/ards-project/ard-spec) · [ARD launch — Hugging Face](https://huggingface.co/blog/agentic-resource-discovery-launch)
- [llms.txt for AI Agents — Fern](https://buildwithfern.com/post/optimizing-api-docs-ai-agents-llms-txt-guide) · [Build with Agent Skills — modelcontextprotocol.io](https://modelcontextprotocol.io/docs/develop/build-with-agent-skills)
</content>
</invoke>
