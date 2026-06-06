---
target_subreddit: /r/Python
post_type: standalone showcase post (NOT a comment in Showcase Saturday)
title: "Pyobfus 0.4 – AST obfuscator with reverse stack-trace mapping for AI-assisted debugging"
status: DRAFT v2 (2026-05-08) — Disclosure paragraph honest rewrite (removes "Tried PyArmor first; ... broke ... loop I'd come to depend on" claim that was narrative texture not fact · reframes as "Looked at PyArmor first; Pro pricing + one-way structural design") · ready for human-voice pass + GPTZero gate before posting
target_post_window: 2026-06-10 to 2026-06-13, weekday 12:00-15:00 EDT (US lunch peak on /r/Python) — REVISED 2026-06-05 (post ~+24h after the HN attempt on 6-09/6-10)
sequencing: post AFTER HN attempt has resolved (HN feedback may surface revisions worth folding in)
---

# Submission strategy

/r/Python permits standalone project posts when they follow the subreddit's [showcase post template](https://www.reddit.com/r/Python/wiki/rules) (What My Project Does / Target Audience / Comparison). Without that structure, the post gets removed within hours. Mods are strict.

## Title

```
Pyobfus 0.4 – AST obfuscator with reverse stack-trace mapping for AI-assisted debugging
```

87 chars. Reddit allows 300; concise is better for /r/Python where users skim. No "Show HN" prefix on Reddit (HN-only). No emojis (most /r/Python posts are plain).

## Flair

Use `Showcase` flair on the subreddit's flair picker when submitting. Without it, the showcase template doesn't excuse you from the no-self-promo default.

# Post body (target ~280 words)

> ## What My Project Does
>
> Pyobfus is an AST-based Python obfuscator (Apache 2.0). It mangles names and has framework-aware presets for FastAPI / Django / Flask / Pydantic / Click / SQLAlchemy. It also ships an MCP server so Claude / Cursor / Windsurf can invoke it as tool calls. The part that makes it different is a forward + reverse name mapping. When you obfuscate, you save that to `mapping.json`. When a production crash arrives, you run `pyobfus --unmap --trace error.log --mapping mapping.json` and get the trace back with the original identifiers restored. Paste that into your AI assistant and your debugging loop still works.
>
> ## Target Audience
>
> Production-ready, with a threat model that's honest about what it covers. Roughly three groups:
>
> - Solo devs and small teams shipping commercial Python who just want casual reverse engineering to cost more effort
> - Researchers shipping algorithm modules under active patent or software-copyright filing
> - Anyone already on Claude Code / Cursor / Windsurf who doesn't want to give up AI-assisted debugging once they ship obfuscated code
>
> Not for nation-state-grade RE resistance. For that, don't use Python.
>
> ## Comparison
>
> | | Pyobfus | PyArmor | Cython | Oxyry |
> |---|---|---|---|---|
> | Name mangling | yes | yes | n/a | yes |
> | Bytecode encryption | no (Pro: string + control flow) | yes | n/a | no |
> | Compilation to native | no | no | yes | no |
> | Reverse stack trace from prod | yes (mapping.json) | no (one-way by design) | no | no |
> | MCP / AI-tool-call surface | yes | no | no | no |
> | License | Apache 2.0 | Free to use but restricted | Apache 2.0 | proprietary |
> | Multi-file project support | yes | yes | yes | no |
>
> Disclosure: I'm the maintainer. I built it while shipping algorithm modules from a medical-imaging research codebase that needed binaries for collaborators without exposing the internals. Looked at PyArmor first, but the real protection sits behind paid Pro, and the thing that actually stopped me was the one-way design: once class names are mangled to `I0` you can't reverse them to debug a production trace. That breaks the AI-assisted debugging loop I'd come to depend on (most of the code was written *with* Claude Code in the first place), so I built pyobfus around closing that one gap.
>
> - `pip install pyobfus pyobfus-mcp`
> - https://github.com/zhurong2020/pyobfus
> - 655 tests, Python 3.8 to 3.14

Word count target: ~280. Current ~310, slight trim possible. Showcase posts on /r/Python in 2025-2026 average 200-400 words; under 200 reads as low-effort, over 500 reads as marketing.

# Comment-thread engagement plan

Within the first 4 hours, expect 2-5 substantive comments. Reply to every one within 30 minutes if possible — Reddit's algorithm rewards engagement velocity in the first 6 hours.

## Likely comment categories

### "Why not PyArmor?" (will appear within 1 hour)

Don't be defensive. Paste a 2-3 sentence response that mirrors the comparison table:

> PyArmor is stronger on raw protection because of bytecode encryption. The trade is that bytecode encryption is one-way; you can't reverse a production trace with it, so AI tools can't help debug. Pyobfus picks the other side of that trade. If you don't care about AI-assisted debugging, PyArmor's a perfectly reasonable choice.

### "Obfuscation isn't security"

Agree. Don't argue the philosophy. Quote the README's threat-model section.

### "What's the Pro tier?"

Be direct, no deflection:

> Pro adds string encryption (AES-256), control-flow flattening, anti-debug, and dead-code injection. Same Apache 2.0 core; commercial license for the Pro modules. Pricing on the GitHub README. Honestly the community tier handles 80% of what most people need.

### "What was wrong with PyArmor's trial?" / "How big does my code need to be?" (added 2026-05-09)

(Use only if asked directly. Don't bring up first — looks like competitor-bashing.)

> Tested it 2026-05-09 in a clean venv against PyArmor 9.2.4 — per-file threshold sits around 935-940 lines for sparse Python (935 passed, 940 failed). Limit is on line count not bytes (900 lines at 67 KB still passed). Error is just `ERROR out of license` with no number and no upgrade hint. Pyobfus has no per-file line limit in either tier. Repro procedure in the repo: `docs/PYARMOR_TRIAL_LIMIT_EXPERIMENT.md`. Caveat: this is PyArmor 9.2.4 specifically — newer versions might shift.

### "I tried it and X broke"

Always: ask for a minimal repro, file the GitHub issue together, link it in the Reddit reply. Public issue handling is the strongest single trust signal on /r/Python.

# What NOT to do

- ❌ Don't post a link to dev.to or HN in the Reddit body. Cross-platform link-dropping reads as coordinated promo; the mods notice. If asked, fine.
- ❌ Don't post in /r/learnpython, /r/programming, /r/coding too. One Reddit post per launch window. /r/Python is the right venue for this audience.
- ❌ Don't include screenshots in the post. /r/Python showcase posts are text-first; screenshots optional and often skipped on mobile.
- ❌ Don't @ anyone or quote dev.to/HN traffic. Reddit cares about the project on its own merits.

# Pre-submission checklist

- [ ] HN submission has resolved (front page or dropped) — fold any HN feedback
- [ ] Post body is under 350 words
- [ ] All four sections (What / Target / Comparison / Disclosure) present in order
- [ ] `Showcase` flair selected on subreddit
- [ ] GPTZero on body: under 25% AI flagged
- [ ] Verify the GitHub README top-of-fold makes sense to a /r/Python redditor (currently it does — MCP companion section + framework presets are visible)
- [ ] Available to engage the thread for 6+ hours after posting

# Voice-guide compliance

- [x] No em-dashes in prose (table separators are fine)
- [x] No banned phrases
- [x] First person, specific, named (PyArmor / Cython / Oxyry / FastAPI / etc.)
- [x] Disclosure line up front (Reddit requires)
- [x] Comparison is fair, not damning (mentions where competitors are stronger)
- [x] Honest threat model
- [ ] GPTZero gate before posting

# CN cross-post note

V2EX has a /r/Python equivalent (`/go/python`) but the post format and tone differ enough that this Reddit draft is NOT a usable starting point for V2EX. If targeted, write fresh from the CN-bilingual draft, not from this one.
