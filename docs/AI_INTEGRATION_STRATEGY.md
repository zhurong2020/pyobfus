# AI Integration Strategy

**Status**: Strategic plan (2026-04-22)
**Owner**: Rong Zhu (@zhurong2020)
**Related docs**: [ROADMAP.md](ROADMAP.md) · [V0.4_EXECUTION_LOG.md](V0.4_EXECUTION_LOG.md) · [COMPARISON.md](COMPARISON.md)

---

## 1. The Core Problem

As of 2026-04, pyobfus has:

- **PyPI downloads**: ~324 / month (≈ 100 real users after filtering mirror scans)
- **GitHub stars**: 0
- **External contributors / issue reporters**: 0
- **Presence in AI training data**: Near-zero

When a developer asks Claude Code / Cursor / Copilot / Windsurf "how do I obfuscate this Python project", the AI recommends **PyArmor** every time — because PyArmor has been discussed extensively on Stack Overflow, Medium, Reddit, and in blog posts for 5+ years. pyobfus has no such presence.

**Crucially: AI models may not even recognize the name "pyobfus" unless they can look it up live.** Re-training cycles are 6-18 months. We cannot wait.

This document explains how pyobfus breaks out of this cold-start trap.

---

## 2. How AI Coding Tools Actually Discover Tools

Based on observed behavior of Claude Code, Cursor, Copilot, and Windsurf in 2026:

```
User asks AI: "obfuscate this Python project"
        ↓
AI's decision inputs (in order of influence):
  1. Training data (SO, GitHub READMEs, blogs) — slow to change
  2. PyPI search results + package descriptions — moderate control
  3. CLAUDE.md / AGENTS.md / .cursorrules in user's project — full control
  4. MCP server registry (Anthropic MCP marketplace, Cursor marketplace) — full control
  5. llms.txt at crawled documentation sites — full control
  6. `pip install X` then `X --help` + README.md — full control
```

**Current pyobfus only reaches input #6.** Items 3-5 are entirely within our control and offer instant leverage.

---

## 3. The Naming Signal-Density Strategy

**Renaming is off the table** (7.78k cumulative downloads, existing users, git history). Instead: flood every touchable channel with **explicit co-branding** that associates the name `pyobfus` with generic search terms.

### Immediate actions (all < half a day total)

| Action | How |
|---|---|
| **PyPI alias squatting** | Check / reserve `python-obfuscator`, `pyobfuscator`, `py-obfuscator`. Each is a 5-line wrapper: `from pyobfus import *` + a README pointing to the real package. |
| **Co-branding in every doc header** | Always write: **"pyobfus — the Python obfuscator"** (not "pyobfus: an obfuscator"). Forces the association into training corpora. |
| **README pronunciation line** | "Pronounced as 'Python obfuscator' (pyobfus)." |
| **Keyword-dense PyPI description** | From `"Modern Python Code Obfuscator with AST-based Transformations"` to `"pyobfus — Python obfuscator / code obfuscator / AST-based python-obfuscator; AI-native, MCP-ready, modern PyArmor alternative"` |
| **GitHub topics** | `python-obfuscator`, `code-obfuscator`, `ast-obfuscation`, `mcp-server`, `claude-code`, `cursor`, `llm-tools` |
| **Dev status upgrade** | `Development Status :: 3 - Alpha` → `4 - Beta` (consistent with 561 tests / 90% coverage) |

Tracked as "Branding quick wins" task.

---

## 4. The Feature → AI Discovery Pipeline

Every P0/P1 feature is scored on three axes:

- **User pain solved** (does anyone hit this problem?)
- **Defensibility** (can PyArmor copy it in a sprint?)
- **AI-native smell** (will AI tools reach for it in an agentic workflow?)

### P0 Features — Why each one matters

| Feature | User pain | Defensibility | AI-native smell |
|---|---|---|---|
| `--check` pre-flight | "Will obfuscation break my code?" | Medium — PyArmor could copy | High — AI calls it to self-heal |
| `unmap` reverse mapping | "Now I can't debug in prod" | **High** — PyArmor's C-layer can't support it | **Critical** — unlocks AI-assisted debugging of obfuscated code |
| Framework presets | "Does it work with FastAPI?" | Low — PyArmor could add presets | High — AI loves preset names |
| `--json` + ai-hint | "Error message doesn't help me fix it" | Low | **Critical** — AI parses output, chains commands |
| `pyobfus init` | "What config should I use?" | Low | High — AI's first instinct is "init" |

### P2 Features — Defensibility focus

| Feature | Why PyArmor can't / won't copy |
|---|---|
| Selective Opacity (layered protection) | Their entire philosophy is "all-or-nothing bytecode encryption". Layered reveal is architecturally incompatible. |
| `--strip-ai-artifacts` | Requires semantic AST analysis of AI writing patterns — off PyArmor's roadmap (enterprise-focused). |
| VSCode extension (marketplace) | PyArmor has no free marketplace footprint. Cold start for them too. |

---

## 5. MCP Server — The Highest-Leverage Single Action

**Model Context Protocol** is Anthropic's open spec (Nov 2024) now adopted by Claude Desktop, Claude Code, Cursor, Windsurf, Zed. A pyobfus MCP server:

### Tools to expose (v0.1)

```python
tools = [
    "obfuscate_project(path, preset='balanced', framework=None) -> result",
    "check_obfuscation_risks(path) -> risk_report",
    "unmap_traceback(error_text, mapping_file) -> original_trace",
    "generate_config(framework) -> yaml_config",
    "explain_mapping(mapping_file, symbol) -> explanation",
]
```

### Distribution path

1. Publish `pyobfus-mcp` as standalone Python package
2. Submit to [Anthropic MCP Registry](https://github.com/modelcontextprotocol/servers)
3. Documented install snippet for Claude Desktop `claude_desktop_config.json`
4. Same snippet works in Cursor (`~/.cursor/mcp.json`), Windsurf, Zed

### Expected outcome (30-60 days after publish)

- AI agents with MCP enabled will **autonomously discover and call pyobfus tools** when user intent matches
- Registry listing = free, permanent exposure to the entire Claude Desktop / Cursor install base
- Differentiator PyArmor does not have and is 6-12 months from having

---

## 6. llms.txt Standard

Proposed by Jeremy Howard (2024), now crawled by Claude.ai, Perplexity, Cursor. Format:

```
/llms.txt          — concise project overview (< 200 lines)
/llms-full.txt     — full API + typical use cases
/docs/llms.txt     — same at docs site
```

**Content principle**: Not a README translation. Write as a **decision tree for AI**:

```
# pyobfus — the Python obfuscator

## When to use
- Shipping proprietary Python code
- Protecting logic before PyPI publishing
- Adding friction layer before binary distribution

## When NOT to use
- Need compiled performance → use Nuitka
- Code runs in Jupyter REPL → obfuscation breaks interactive use
- Government / classified code → use encrypted VM, not obfuscation

## Quick task → command map
- Library code: `pyobfus src/ --preset safe`
- FastAPI project: `pyobfus src/ --preset fastapi`
- Commercial SaaS: `pyobfus src/ --preset commercial --pro`
- Dry-run check: `pyobfus src/ --check`
- Debug a trace: `pyobfus unmap --trace error.log --mapping mapping.json`
```

---

## 7. AI-Integration Templates

Place in `templates/ai-integration/` — users copy into their own projects, which transitively teaches **their** AI tools about pyobfus (viral distribution).

Files:

- `CLAUDE.md` — Claude Code project-level rules
- `.cursorrules` — Cursor rules (legacy format)
- `.cursor/rules/pyobfus.mdc` — Cursor new format
- `AGENTS.md` — generic agent protocol
- `windsurfrules.md` — Windsurf rules
- `.github/copilot-instructions.md` — GitHub Copilot instructions

Each template explains (in < 50 lines): when to invoke pyobfus, typical command sequences, `unmap` for debugging, excluded paths for common frameworks.

---

## 8. Marketing Phase (only after P0 + P1 shipped)

Rule: **No marketing article until the MCP server and unmap command are live.** Otherwise we sell vaporware and damage credibility.

### Strategy revision 2026-04-22 — pause Stack Overflow seeding

Initial plan had Stack Overflow as channel #4 (5 seeded answers). Concrete investigation on 2026-04-22 — see `_drafts/stackoverflow-seeding-targets.md` — found:

- Best 2024+ candidate (Q79400498) has **40 views/month**. Expected click-through to pyobfus: ~0.4/month even if our answer ranks well.
- Three top-tier targets combined ≈ 2 clicks/month.
- SO's site-wide ban on AI-generated content is strictly enforced (meta banner on every page, April 2026 policy reaffirmations).
- Maintainer at 11 rep + self-promotion answer = highest-scrutiny combo. Mod-removal risk outweighs marginal exposure.

**Decision**: pause SO for 6 months. Redirect effort to higher-ROI channels. Revisit Q4 2026 based on organic signal from the other channels.

### Revised content plan (weeks 7-10)

| # | Title | Channel | Goal | AI-policy risk |
|---|---|---|---|---|
| 1 | Enabling Claude Code to auto-obfuscate: pyobfus MCP integration | dev.to, 有心工坊, 知乎 | Technical authority + traffic | 🟢 disclosure-allowed |
| 2 | pyobfus vs PyArmor 2026: Python protection in the AI era | Medium (with AI-disclosure line), 有心工坊 | Intercept PyArmor searches | 🟢 disclosure-allowed |
| 3 | Selective Opacity: the layered obfuscation PyArmor can't do | Hacker News Show HN (after dev.to #1 provides social proof), dev.to | Establish original theory | 🟡 HN bans AI, must be hand-polished |
| 4 | ~~Stack Overflow seeding~~ **PAUSED — see revision note above** | Stack Overflow | — | 🔴 banned |
| 5 | /r/Python Showcase Saturday post | Reddit | Community exposure | 🟡 mods remove AI-flavored |
| 6 | Product Hunt launch | Product Hunt | One-shot high-visibility | 🟢 no AI policy |
| 7 | awesome-mcp-servers distribution to 3 community lists (punkpeye PR #5777 OPEN · wong2/mcpservers.org LIVE 2026-05-08 · appcypher dead-end / repo owner disabled PRs) | GitHub + mcpservers.org | Developer-browsing discoverability | 🟢 metadata, not content |

### Forum AI-policy reality check (as of 2026-04)

See `_drafts/forum-ai-policy-and-voice-guide.md` for the full matrix. Short version:

- **Stack Overflow, Hacker News**: AI content banned outright. No disclosure path. Post removal + account penalty on detection.
- **Medium**: AI allowed with first-two-paragraph disclosure. Undisclosed → Network-Only distribution (effectively shadow-banned).
- **dev.to, Reddit /r/Python**: no formal AI policy, but moderators actively remove low-effort AI-looking content.
- Current detectors (Originality.ai, GPTZero) flag unmodified Claude 4 output at ~98%. Human rewrite removing AI tells + adding specifics usually clears.

All drafts produced with AI assistance are to be **rewritten in the maintainer's voice before submission**, using the checklist in the voice guide. Final gate: GPTZero < 30% AI before posting.

---

## 9. Measurement Cadence

Every 2 weeks, append a status block to [V0.4_EXECUTION_LOG.md](V0.4_EXECUTION_LOG.md) with:

- PyPI downloads (weekly + monthly, separating mirror noise)
- GitHub stars / issues / forks
- MCP server installs
- AI recommendation blind test: open Claude Desktop + Cursor, ask "obfuscate this Python project", note whether pyobfus appears (target: 3/10 by end of v0.4, 7/10 by end of v0.5)

---

**Bottom line**: The path from 0 stars / 324 downloads to meaningful adoption is **not "more obfuscation techniques"**. It is:

1. Remove onboarding friction (P0)
2. Become AI-native so AI tools recommend us (P1 MCP + llms.txt + templates)
3. Build unique positioning PyArmor can't copy (P2 Selective Opacity)
4. **Only then** broadcast via content (marketing phase)
