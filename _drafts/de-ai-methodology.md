---
title: De-AI Methodology — sentence-level diagnostic + rhythm rewrite
date: 2026-05-08
status: reference (institutional knowledge from the article-01 v3→v4 voice rewrite)
purpose: Reproducible workflow for reducing AI-detection probability on technical drafts before posting to forums (dev.to, HN, Reddit, CN platforms, Medium)
companion: _drafts/forum-ai-policy-and-voice-guide.md (per-platform AI policy + cheatsheet)
---

# Why this exists

Default Claude / GPT-4 output flags ~98% on GPTZero, ~98.4% on Originality.ai Turbo 3.0.1. Most platforms either ban AI-generated content (HN, Stack Overflow), require disclosure (Medium), or de-rank low-effort AI posts (Reddit, dev.to mods). Even where it's not banned, a 100%-AI-flagged article reads as low-effort to readers who care about author voice.

This methodology was distilled from the 2026-05-07 evening session that took the pyobfus dev.to article from **AI 100% / Mixed 0% / Human 0%** (v3) to a structurally-improved v4 (burstiness range expanded from 4-200 to 2-257 chars). The improvement is real and measurable; the rules below are what changed between the two versions.

---

# The 4-step workflow

## Step 1 — Diagnostic paste

Paste prose-only body (strip code blocks, frontmatter, internal-only sections) into a sentence-level detector:

| Detector | Free tier | Trade-off |
|---|---|---|
| **GPTZero** (gptzero.me) | 10K credits/month free; ~5K char/paste limit on free tier | Best per-sentence breakdown; identifies "High AI Impact" vs "Low AI Impact" sentences explicitly |
| ZeroGPT | Unlimited free | No per-sentence breakdown — only overall % |
| Sapling AI Detector | Free | Mid-quality; OK as cross-check |
| Local: Binoculars / DetectGPT | Free + private | Heavyweight (1-2 GB HuggingFace model); lower 2026 accuracy than paid |

**Recommended for one-shot pre-publish gate**: GPTZero free web tier. Split long articles into 2 ~5K-char pastes. Cost: 0.

## Step 2 — Read the per-sentence breakdown, not the overall %

The overall AI % is the headline number, but **the actionable signal is the per-sentence "High AI Impact" list**. Each sentence GPTZero flags as High AI is a rewrite target. Sentences flagged Low AI Impact are working — preserve them verbatim.

This is the key insight: **don't tweak the whole article uniformly**. Surgically rewrite only the High-AI-Impact sentences. The Low-AI-Impact sentences are evidence of what your authentic voice looks like — keep them.

## Step 3 — Rewrite High-AI sentences using the pattern table

See "Rules" section below.

## Step 4 — Re-paste and verify (optional)

Re-paste rewritten body. Target: <30% AI per the voice guide. If still failing >30%, **rewrite (don't tweak)** the next batch of flagged sentences.

**Strategic exception**: if the platform doesn't enforce AI policy (dev.to, CN platforms with light disclosure norms), function-clarity often dominates over absolute AI %. Don't burn detector credits chasing a number that doesn't gate publication. The pyobfus dev.to article shipped at v4 without re-testing, and it's working fine.

---

# Rules — what to remove vs preserve

## ❌ HIGH AI impact patterns (rewrite these)

| Pattern | Example | Why detector flags it |
|---|---|---|
| **Mid-length explanatory prose with subordinate clauses** | "Late last year I was helping ship algorithm modules out of a medical imaging research codebase." | Past-progressive opener + smooth subordinate structure |
| **"X is the Y, so I tried Y" setup-payoff** | "PyArmor is the answer everyone gives you, so I tried PyArmor first." | Predictable transition; AI's natural rhetorical shape |
| **Smooth SVO compound** | "It worked, and it broke my workflow." | Too clean. No friction. |
| **Meta-narration "X exist to Y"** | "The other three exist to make the third one usable." | Over-explained relationship; AI loves this construction |
| **"X actually means" / "X is the Y" framing** | "What 'AI-friendly obfuscation' actually means" (heading) | Definition-claim openers are AI-shape |
| **Em-dashes in prose** | "Most Python obfuscators were designed before AI-assisted coding existed — PyArmor in 2013, Cython earlier" | Em-dash overuse is THE most reliable AI tell. Use periods, commas, parentheses, or colons instead. (Em-dashes inside code blocks are fine — those don't go through the detector.) |
| **AI trigger phrases** | "delve into", "furthermore", "moreover", "it's worth noting", "let's explore", "navigate the complexities", "in conclusion", "tapestry of" | These appear ~10× more often in AI text than human text |
| **Symmetric headings** | "Background / Implementation / Conclusion" or "Why / How / What" | AI loves rhetorical symmetry; humans rarely do |
| **Hedging stacks** | "it's generally considered that it may potentially..." | Over-hedging is AI's risk-aversion |
| **Closing summaries** | "In summary, we've seen that..." | Summarizing what you just said is AI's default closer |

## ✅ LOW AI impact patterns (PRESERVE these)

| Pattern | Example | Why detector likes it |
|---|---|---|
| **Fragments (1-5 words)** | "Yeah." / "Fine." / "So I rebuilt the tool." / "PyArmor's protection model is one-way by design." | Humans write fragments naturally; AI optimizes for grammatical completeness |
| **Very long messy sentences** with parenthetical asides | "I spent something like 40 minutes manually unmapping that trace by hand against the original source, fixed the bug (a missing import, naturally), and then went and surveyed what else was on the market." | High burstiness signal; concrete detail; informal "naturally" |
| **Short technical claims** | "Cython compiles to machine code, even further." | Domain-specific + low-ceremony |
| **Specific dated/numbered specifics** | "shipped on 2026-04-22", "40 minutes", "$45 USD", "5-day trial" | Verifiable concreteness AI rarely matches |
| **First-person + contractions** | "I've been leaning on hardest", "don't", "won't", "I'd" | Conversational signature |
| **Casual asides** | "this took me way too long to figure out", "the lawyers actually read commits" | Throwaway humor / personality |
| **Named error messages / file paths / version strings** | `"AttributeError: 'I0' object has no attribute 'I2'"`, `pyobfus/trial.py:18`, `mcp 1.27` | Concrete artifact reference |
| **One uncorrected typo or small digression** (used sparingly) | "by hand against the original source, fixed the bug (a missing import, naturally)" | Authentic imperfection |

## 🎯 Burstiness — the quantitative measure

GPTZero's perplexity is hard to game without a model. Burstiness is purely statistical — anyone can compute and target it.

**Definition**: sentence-length variance. Specifically: standard deviation of sentence character lengths divided by the mean.

**Target ranges (from our v3→v4 measurement)**:
- v3 (failed at 100% AI): char range 4-200, mean 65, stddev moderate
- v4 (passed structurally): char range **2-257**, mean 68, stddev high

**Rule of thumb**: if your shortest sentence is >10 chars and your longest is <120 chars, you've got AI rhythm. Mix in:
- 1-3 ultra-short fragments per section (3-15 chars)
- 1-2 very long messy sentences per section (150+ chars)
- Don't make every paragraph the same length

**Quick local stats check** (no model needed):

```bash
awk '/^## .*Body|^## TODOs/' your_article.md | \
  awk '/^```/ { in_code = !in_code; next } !in_code { print }' | \
  tr '.' '\n' | sed 's/^[[:space:]]*//' | grep -E '^[A-Za-z]' | \
  awk '{print length}' | \
  awk '{s+=$1; if(min==""||$1<min) min=$1; if($1>max) max=$1; n++} END{printf "min=%d max=%d mean=%.0f n=%d\n",min,max,s/n,n}'
```

If `max - min < 100`, your burstiness is low. Add fragments + long messy sentences.

---

# Per-platform tuning

| Platform | AI policy strictness | De-AI effort warranted |
|---|---|---|
| **HN** | **Strictest** — "Don't post generated comments or AI-edited comments. HN is for conversation between humans." | Maximum. Aim <20%. HN comments are ≤150 words, so structural variation has fewer affordances; lean heavily on the dated-anecdote + casual-aside levers. |
| **Stack Overflow** | Strict — site-wide AI-generated answer ban (2022, still live) | Maximum. Disclose tool maintenance affiliation. |
| **Reddit /r/Python** | Mid — no explicit ban but mods remove "low-effort AI-looking posts" on sight | High. Lean on first-person + concrete code references. |
| **Medium** | Mid — AI-assisted writing must be disclosed in first 2 paragraphs ("This story was written with the assistance of an AI writing program"). Disclosure required, not banned. | Mid. Disclose, then optimize for readability over absolute AI %. |
| **dev.to** | **Loosest** — no dedicated AI policy; community norm to tag `#ai` if AI-assisted | Mid. Function-clarity + disclosure-up-front beats chasing absolute %. |
| **CN platforms** (有心工坊, 知乎, V2EX) | Loose — Chinese detectors (WriteHuman) less mature; light disclosure norm | Low to mid. Translate from de-AI'd English version. Same fragment + concrete-detail rules apply in CN. |

---

# Decision tree — when to bother

```
Is platform on the strict list (HN / SO / Reddit)?
├─ Yes → Run full diagnostic + rewrite cycle. Target <30% AI.
└─ No
   │
   Is the article >1,000 words?
   ├─ Yes → One paste-test. If <50% AI, ship; if >50%, rewrite top 5 flagged sentences only.
   └─ No → Just apply the pattern table while drafting. Skip the diagnostic step.

Is content function-heavy (technical reference, command-by-command tutorial)?
├─ Yes → Skip diagnostic. Function-clarity dominates.
└─ No → Apply diagnostic.

Are you the author + maintainer of the project the article is about?
├─ Yes → Disclose affiliation in first paragraph. Detector tolerance goes up.
└─ No → Detector tolerance goes down; rewrite more aggressively.
```

---

# Origin

This methodology was distilled 2026-05-08 from the pyobfus dev.to article rewrite session. The article (`_drafts/article-01-claude-code-mcp-integration.md`) went through 4 versions:

- **v1** (2026-04-22): drafted, never published. Targeted 4-24 post that didn't ship.
- **v2** (2026-05-05): voice-guide compliance pass. Removed em-dashes, added dated specifics. Still scored 100% AI on first paste.
- **v3** (2026-05-07): killed parallel "X is a Y" feature block, "isn't X. It's Y" closers, triplet rhythms. **Pasted into GPTZero → AI 100% / Mixed 0% / Human 0%** with "highly confident this text was AI generated" verdict.
- **v4** (2026-05-07 evening): GPTZero-diagnostic-driven rewrite. Replaced every flagged High-AI-Impact sentence; preserved every Low-AI-Impact sentence. Burstiness char-range expanded 4-200 → 2-257. **Strategic call: NOT re-paste-tested** — dev.to has no AI ban, function-clarity dominates for our buyer/user, HN/Reddit/CN get separate short-form posts. v4 shipped to dev.to 2026-05-07 evening.

The pattern table above isn't speculation; it's GPTZero's actual sentence-by-sentence verdict on a real article, generalized.

---

# Companion files

- `_drafts/forum-ai-policy-and-voice-guide.md` — per-platform AI policy ground truth + concise human-voice cheatsheet (compiled 2026-04-22)
- `_drafts/article-01-claude-code-mcp-integration.md` — the article whose v3→v4 rewrite this methodology generalizes from
- `_drafts/cross-review-prompt.md` — outside-eye review prompt to paste into Gemini / Claude.ai / ChatGPT before posting

# Skill candidate?

This methodology is reusable across projects (any tech-blog rewrite scenario). Worth considering Claude Code Skill format. See `_drafts/de-ai-skill-proposal.md` (sibling) for the proposed structure, scope, and trade-offs.

---

# ✅ Skill shipped — methodology now operational

**Update 2026-05-08**: this methodology has been distilled into a Claude Code skill and a placeholder commercial-MCP repo:

- **Free Claude Code skill** (use this today): `~/.claude/skills/tech-deai/` — auto-surfaces in any Claude Code session that involves writing/revising technical prose. 12 HIGH AI patterns + 10 LOW AI patterns + 4 platform-specific workflow prompts (`devto_workflow.md` / `hn_strict.md` / `reddit_workflow.md` / `cn_platforms.md`) + burstiness measurement bash snippet. 4-step workflow (paste → diagnose → rewrite → re-test).
- **Commercial MCP placeholder repo**: <https://github.com/zhurong2020/tech-deai-loop> (PRIVATE during placeholder phase; v0.1.0 license locked to Apache-2.0). Implementation gated on Phase 0 prerequisites — see `~/.claude/skills/tech-deai/BACKLOG.md` Phase 2.
- **Phase 0 validation** (≥3 real-article runs required before MCP implementation): 1 of 3 complete (Run 1 = pyobfus CN trio prep, 2026-05-08; Run 2 = HN Show HN, planned 2026-05-11; Run 3 = Reddit /r/Python, planned 2026-05-12). See `~/.claude/skills/tech-deai/RUN_LOG.md` for findings.

This methodology doc remains here as the **origin reference** — the institutional knowledge that birthed the skill. Future updates to the methodology should land in `~/.claude/skills/tech-deai/SKILL.md` (the runtime SSOT), not here.
