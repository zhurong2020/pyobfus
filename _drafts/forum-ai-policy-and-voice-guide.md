---
title: Forum AI policy and human-voice guide
date: 2026-04-22
status: reference (not for publication)
---

Notes for drafting forum answers that get rewritten by a human before posting. Compiled 2026-04-22.

## Stack Overflow

Policy: https://stackoverflow.com/help/gen-ai-policy (Cloudflare blocked scrape; summary from secondary sources + https://policies.stackoverflow.co/).

- **Rule**: the 2022 ban on AI-generated answers is still live site-wide. Moderators may use AI-detection tools when reviewing. Stack Exchange's own OverflowAI experiments do not change user-posting rules.
- **AI-generated vs assisted**: fully or substantially model-written prose is the target. AI-assisted editing of a human draft is not explicitly covered, but there is no formal disclosure carve-out — if it reads generated, it gets removed.
- **Penalty**: post deletion, reputation loss, temp suspension, permanent ban for repeats. Mass-deletions happened during the 2024 OpenAI-deal revolt.
- **Self-promo / tool maintainer**: permitted if you disclose affiliation in the answer ("Disclosure: I maintain X"). Posting answers needs only 1 rep; commenting needs 50. Don't answer a question with your tool unless the question is genuinely about the problem it solves.

## Reddit /r/Python

Rules: https://www.reddit.com/r/Python/about/rules (login-gated, scrape 403).

- **Rule**: standalone "look at my project" posts are removed outside the pinned Showcase threads. Reddit-wide 90/10 self-promo guideline applies.
- **AI content**: no explicit subreddit ban yet, but mods remove low-effort AI-looking posts on sight (CHI 2025 study confirms this trend across Reddit).
- **Disclosure**: affiliation must be declared. No mandated AI tag.
- **Penalty**: removal → temp ban → permanent ban. New-account filters auto-remove low-karma posts.
- **Self-promo**: use "Showcase Saturday" / "Beginner Showcase" threads, or answer genuine questions where your tool fits. Always disclose.

## dev.to

Terms: https://dev.to/terms · CoC: https://dev.to/code-of-conduct

- **Rule**: no dedicated AI policy as of 2026-04-22. Terms require you own rights to content; CoC bans plagiarism. Community norm (unenforced) is tagging AI-assisted posts `#ai` or noting it in the intro.
- **Penalty**: moderator un-publish, account flagged for repeated low-quality posts.
- **Self-promo**: explicitly welcomed. "I built X" posts are on-brand. Include a disclosure line.

## Hacker News

Guidelines: https://news.ycombinator.com/newsguidelines.html · Show HN: https://news.ycombinator.com/showhn.html

- **Rule (direct quote)**: "Don't post generated comments or AI-edited comments. HN is for conversation between humans." Also: "Please don't use HN primarily for promotion."
- **Disclosure**: none offered. The rule is "don't post it", not "disclose it."
- **Penalty**: dang asks you to stop, then shadowban / rate-limit / green username. Detection is human pattern-matching plus user flags.
- **Show HN**: one per project, must be runnable. No upvote solicitation, no coordinated launches.

## Medium

Policy: https://help.medium.com/hc/en-us/articles/22576852947223-Artificial-Intelligence-AI-content-policy

- **Rule**: "Medium is for human storytelling." AI-assisted writing must be disclosed with a sentence in the first two paragraphs (example: "This story was written with the assistance of an AI writing program"). AI images must be captioned.
- **Not required**: spell/grammar check, outline help, fact verification.
- **Penalty**: undisclosed AI = Network-Only distribution (invisible beyond your followers). Paywalled AI content can be removed and Partner Program revoked.

## AI detectors — early 2026 reality check

- Originality.ai Turbo 3.0.1: ~98.4% detection on Claude 4 Sonnet/Opus, ~4.79% false-positive on human text. https://originality.ai/blog/is-claude-4-sonnet-opus-detectable
- GPTZero: ~97–99% on Claude Sonnet 4 with ~0.24% false positives. https://gptzero.me/
- Both score perplexity (per-token predictability) and burstiness (sentence-length variance). Claude's default style is low-perplexity and uniform-length — the exact failure mode they catch.
- Takeaway: word-for-word Claude draft WILL flag. Human rewrite cutting AI tells + adding specifics usually clears.

## Writing checklist — sound like a human at 11pm

Remove (AI tells):
- Em-dashes in prose (—). Use commas, periods, or parentheses.
- "Delve into", "furthermore", "moreover", "it's worth noting", "let's explore", "navigate the complexities."
- Perfectly parallel 3-item bullets with one-sentence items.
- Symmetric headings (Background / Implementation / Conclusion).
- Hedging stacks ("it's generally considered that it may potentially").
- Closing paragraphs that summarize what you just said.

Add (human tells):
- A specific number, version, commit hash ("on 4.7.2, not 4.7.1").
- One dated anecdote ("hit this last Tuesday debugging a celery worker").
- Contractions: don't, won't, I've.
- A named error message, stack-trace line, or filename.
- One casual aside ("this took me way too long to figure out").
- Vary paragraph length — one 1-sentence, one 4–6 sentences.
- First person: "I ran into this when I was building ..."
- Occasional uncorrected typo or small digression.

Structure:
- Short paragraphs, not markdown bullet forests. Max one list per answer.
- Lead with the answer, then explain.
- Link to a specific file/line, not a docs homepage.
- Tool author: one-line disclosure up front.
- Length targets: SO 150–300 words · HN 80–150 · dev.to 600–1,200 · Medium 800+ · Reddit match thread tone.

Final gate: paste into GPTZero. If >30% AI, rewrite — don't tweak.
