# Cross-Review Prompt — for Gemini / Claude.ai / ChatGPT

> Copy everything between the two horizontal rules below into the target AI chat as a single message. The prompt is self-contained: the target AI doesn't need to read any files, just respond.
>
> If you've revised any of the four drafts since this file was last regenerated, replace the corresponding `[full content here]` block with the latest text before pasting.

---

# ROLE & CONTEXT

You are a senior technical writer specializing in developer-community launch posts. You're reviewing four drafts I'm about to ship across four different developer platforms. I need detector-resistant, voice-appropriate, factually defensible final versions. Reply in English.

## Who I am

I'm Rong Zhu, solo maintainer of pyobfus, an open-source AST-based Python obfuscator with a forward+reverse name-mapping feature designed to keep AI-assisted debugging working after code ships obfuscated. v0.4.0 released 2026-04-22 to PyPI. Apache 2.0 core. Companion `pyobfus-mcp` MCP server registered in Anthropic's official MCP Registry as `io.github.zhurong2020/pyobfus-mcp`.

## The origin story (cross-reference baseline)

I built pyobfus while helping ship algorithm modules from a medical imaging research codebase that had active patent and software-copyright filings. The team needed working binaries for collaborators without exposing the internals. I tried PyArmor first; it works, but its bytecode-encryption protection model is one-way by design, which broke AI-assisted debugging because production crash traces came back as `'I0' object has no attribute 'I2'` and Claude couldn't reason about that. Cython has the same problem plus it compiles to machine code. So I built pyobfus over about a month using AI-assisted vibe coding (Claude Code), specifically organized around a forward+reverse name mapping that lets you reverse production traces back to original identifiers. Customers see the obfuscated bytes; the maintainer keeps `mapping.json` somewhere secure; when a crash arrives the maintainer reverses it locally and pastes the readable version into the AI assistant.

Key abstractions for IP safety: do **NOT** name the medical imaging field more specifically than "medical imaging research codebase"; do **NOT** name collaborators or institutions; do **NOT** mention specific algorithms.

## The four target platforms

| # | Platform | Key constraint | Length | AI-content policy |
|---|---|---|---|---|
| 1 | dev.to | Tutorial-friendly, self-promo welcome | 600–1,400 words | None formal; community norm: disclose if asked |
| 2 | Hacker News (Show HN) | Technical, anti-marketing, anti-AI strict | Title + 100–200-word seed comment | Explicit ban: "Don't post generated comments or AI-edited comments. HN is for conversation between humans." Disclosure does NOT excuse, the rule is "don't post it." |
| 3 | Reddit /r/Python | Showcase post format mandatory (What/Target/Comparison) | 200–400 words | Mods remove low-effort AI content on sight; disclosure required |
| 4 | CN bilingual (有心工坊 + 知乎 + V2EX) | Three sub-formats, common backbone | 1,400 / 1,200 / 700 字 | CN detectors less mature, but readers recognize AI style |

## Voice guide (extracted from `_drafts/forum-ai-policy-and-voice-guide.md`)

**Remove (AI tells)**:
- Em-dashes in prose. Use commas, periods, parentheses. (Em-dashes inside code blocks or table separators are fine.)
- "Delve into", "furthermore", "moreover", "it's worth noting", "let's explore", "navigate the complexities."
- Perfectly parallel 3-item bullets with single-sentence items.
- Symmetric headings (Background / Implementation / Conclusion).
- Hedging stacks ("it's generally considered that it may potentially").
- Closing paragraphs that summarize what was just said.

**Add (human tells)**:
- Specific numbers, version strings, commit hashes (e.g. "643 tests, Python 3.8–3.14").
- One dated anecdote with a small detail.
- Contractions: don't, won't, I've.
- A named error message or filename.
- One casual aside.
- Vary paragraph length: one 1-sentence paragraph, one 4–6 sentences.
- First person: "I ran into this when I was building..."
- Occasional uncorrected small digression.

**Detector reality (early 2026)**:
- Originality.ai Turbo 3.0.1: ~98% detection on Claude 4 Sonnet/Opus output, ~5% false positive on human writing.
- GPTZero: ~97% detection rate on Claude Sonnet 4.
- Both score perplexity (per-token predictability) and burstiness (sentence-length variance). Default Claude output is uniformly low-perplexity and uniform-length, which is exactly what the detectors are tuned for.
- Goal: every block of three or more sentences should pass GPTZero at < 30% AI-flagged.

# WHAT I NEED YOU TO DO

For **each** of the four drafts:

1. **Detector risk audit**: identify specific sentences or paragraphs that read AI-generated. Quote the offending text verbatim, give a 1-line reason, and propose a 1-line replacement. Be specific; don't just say "this paragraph reads AI." Mark severity high / medium / low.

2. **Cross-platform consistency**: verify the origin story (medical imaging codebase + IP filings + PyArmor try + AI debugging gap + month of vibe coding) is told consistently across all four drafts but with platform-appropriate emphasis (dev.to expanded narrative, HN tight, Reddit comparison-table-anchored, CN narrative-rich). Flag any contradictions.

3. **Voice fit**: each platform has its own register. Flag any draft where the voice doesn't fit — e.g. dev.to-style enthusiasm sneaking into the HN seed, or HN technical density making the Reddit body too dense, or English idioms creeping into the CN draft.

4. **Factual claims sanity check**: I cite PyArmor's bytecode encryption (one-way), Cython compiling to machine code, MCP Registry presence at `io.github.zhurong2020/pyobfus-mcp`, 643 tests, Python 3.8–3.14, Apache 2.0 core, framework presets for FastAPI / Django / Flask / Pydantic / Click / SQLAlchemy, six AI-integration template formats. Flag any that look wrong, unverifiable, or where I'm overclaiming.

5. **Top 3 one-shot rewrites**: pick the three highest-risk passages across all four drafts (rank by GPTZero risk × structural impact). Provide a fully-rewritten version of each as a paste-ready replacement. Don't suggest changes — produce the new text.

6. **Sequencing critique**: my planned posting order is dev.to → wait 48h → HN → wait until HN resolves → Reddit /r/Python → CN platforms within 48h after dev.to. Each spaced ≥24h. Flag any sequencing risk (e.g. HN crowd seeing dev.to first and dismissing as marketing, or Reddit timing missing US lunch peak).

# OUTPUT FORMAT

Reply in this structure verbatim:

```
# DRAFT 1 — dev.to

## Detector risk audit
| Severity | Quoted text | Why | 1-line replacement |
|---|---|---|---|
| H | "..." | ... | "..." |
| M | "..." | ... | "..." |

## Cross-platform consistency
[notes]

## Voice fit
[notes]

# DRAFT 2 — Hacker News
[same structure]

# DRAFT 3 — Reddit /r/Python
[same structure]

# DRAFT 4 — CN bilingual (有心工坊 / 知乎 / V2EX)
[same structure, audit each sub-format separately if any of them differs significantly]

# FACTUAL CLAIMS REVIEW
[bulleted list of claims + verdict + source-suggestion if uncertain]

# TOP 3 ONE-SHOT REWRITES

## Rewrite 1 — [draft name + section]
**Original**:
> [text]

**Replacement**:
> [text]

## Rewrite 2 — ...
## Rewrite 3 — ...

# SEQUENCING CRITIQUE
[notes]

# OVERALL VERDICT
[ship-ready / blocking issues / next-revision-needed]
```

# THE FOUR DRAFTS

## DRAFT 1 — dev.to (target ~1,300-1,400 words body)

[full content of `_drafts/article-01-claude-code-mcp-integration.md` body section here, from "## Let Claude Code Debug Your Obfuscated Python" through "If you ship with pyobfus, keep your mapping.json safe..." — paste the EN body, not the frontmatter or TODO scaffolding]

## DRAFT 2 — Hacker News (Show HN)

[paste two things:
1. The HN title + URL pair
2. The 188-word first-comment seed
from `_drafts/post-hn-show-hn.md`]

## DRAFT 3 — Reddit /r/Python

[paste:
1. The post title
2. The ~310-word post body (What My Project Does / Target Audience / Comparison / Disclosure / install line)
from `_drafts/post-reddit-rpython.md`]

## DRAFT 4 — CN bilingual

Three sub-formats from `_drafts/post-cn-bilingual.md`. Paste:
1. The main 有心工坊/知乎 body (~1,400 字)
2. The V2EX standalone short version (~700 字)

If you find issues that affect both, note as [BOTH] in the audit table.

---

# END OF PROMPT

The reviewer (Gemini / Claude.ai / ChatGPT) should now produce the structured output described in the OUTPUT FORMAT section above. Reply in English even if the CN draft is in Chinese — the reviewer's commentary is for the maintainer's working notes, separate from the published artifact.
