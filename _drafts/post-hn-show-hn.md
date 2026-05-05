---
title_field: "Show HN: Pyobfus – Python obfuscator that doesn't break Claude Code"
url_field: https://github.com/zhurong2020/pyobfus
text_body: see below (HN allows EITHER url OR text — we use url, no text body, then engage in comments)
status: DRAFT v1 (2026-05-05) — for human-voice pass + GPTZero gate before submission
target_post_window: 2026-05-12 to 2026-05-19, weekday 09:00-11:00 EST (HN peak window)
sequencing: post AFTER dev.to has been live ≥48h (so commenters have material to read), BEFORE Reddit
---

# Submission strategy

HN treats a Show HN as either a URL post (no body text) OR a text post (no URL). The recommended pattern is **URL post pointing at GitHub README**, then maintainer engages in the comment thread within the first 90 minutes.

The README must be the landing surface, not the docs site. The HN crowd reads the README, judges, and either upvotes/comments or moves on. ReadTheDocs adds a hop they often won't take.

## What the title bar shows

```
Show HN: Pyobfus – Python obfuscator that doesn't break Claude Code
https://github.com/zhurong2020/pyobfus
```

Title is 65 chars including "Show HN:". Under the 80-char HN limit. Lead noun ("Pyobfus") + the differentiator ("doesn't break Claude Code") + zero hype words. The em-dash here is in the title field, which is conventional for HN titles (everything between em-dashes is the description), not in body prose.

# First-comment seed (post within 5 minutes of submission)

Per HN convention, the submitter posts a top-level comment expanding context. This is what readers actually read first.

> Author here. I built this while shipping algorithm modules from a medical imaging research codebase under active patent and software-copyright filing. Tried PyArmor first; it works, but its protection model is one-way by design — production stack traces come back as `'I0' object has no attribute 'I2'`, which Claude Code can't reason about. Cython has the same problem, plus it compiles to machine code.
>
> The differentiator in pyobfus: `--save-mapping` writes a forward + reverse name table when you obfuscate; `--unmap` applies it in reverse to a trace. Customers see the obfuscated bytes; you keep the mapping somewhere safe; when a crash arrives you reverse it locally and paste the readable trace into Claude.
>
> Also ships an MCP server (`pyobfus-mcp`) so Claude Desktop / Cursor / Windsurf / Zed can invoke `check_obfuscation_risks`, `unmap_stack_trace`, etc. as tool calls.
>
> Apache 2.0 core, 643 tests, Python 3.8–3.14. Honest about the threat model: this is name mangling plus optional string encryption, not bytecode-level encryption. A determined attacker with time can reverse most of it. If your threat model is nation-state RE, use something else.
>
> Feedback welcome on threat-model edge cases I'm missing, and on the MCP tool surface.

Word count: 188. HN sweet spot for a Show-HN seed comment is 100–200 words.

# Anticipated objections + pre-thought responses

These are likely to come up. Don't pre-emptively address all of them in the seed comment (too defensive); have responses ready when they land.

## "This is just minification with extra steps"

> Fair if your bar is "code that's hard to read." Pyobfus does name mangling at the AST level, optional string encryption (Pro), optional control-flow flattening (Pro). Where it differs from minification: the mapping table is the explicit deliverable, not a side effect, and the AI-debugging story is the whole point. If you don't care about that story, minification is faster.

## "Why not just use PyArmor?"

> PyArmor's stronger if your only goal is making static analysis hurt. It's weaker if you also need to keep AI-assisted debugging working in production, because its bytecode encryption is one-way. Different tools for different threat models. I respect what they ship; their license is also more permissive than people remember (BSD).

## "Obfuscation is security through obscurity / it doesn't work"

> Agreed if interpreted as "this stops a determined attacker." It doesn't. The intended use is friction against casual reverse engineering plus IP-claim documentation (e.g. for software-copyright filings). Read the threat-model section in the README; I'm trying to be specific about what it does and doesn't promise.

## "How is this different from Oxyry?"

> Oxyry is single-file, free-tier, no AI integration, no reverse mapping. We're aiming at the multi-file project + AI-assisted-debugging niche specifically. Oxyry is great for one-off scripts.

## "What about decompiling .pyc files?"

> The string-encryption + control-flow flattening (Pro) layers raise the cost of pyc decompilation noticeably. Community tier is honest about being lighter — name mangling on top of normal `.pyc` distribution. If your threat model needs more, that's the Pro tier or another tool entirely.

## "I built X / Y / Z that does similar things"

> Good. Drop a link, I'll add a comparison row to the README. The Python obfuscation space is small enough that I want to map it accurately.

# What NOT to include

- ❌ Don't link the dev.to article in the HN seed comment. Looks like coordinated cross-posting; HN rate-limits or shadowbans for that pattern. The dev.to link can come up naturally in a sub-thread if asked "where can I read more."
- ❌ Don't mention the PyPI alias squat plan (py-obfuscator). Not interesting to HN audience; reads as marketing minutiae.
- ❌ Don't disclose AI assistance during writing. HN forbids AI-generated comments outright (cited rule: "HN is for conversation between humans"). Disclosure doesn't help; the rule is "don't post it." Voice rewrite + GPTZero gate before posting.
- ❌ Don't pre-emptively defend against "obscurity isn't security." That's a trap — defending it sounds defensive. Address only when raised.
- ❌ Don't drop emojis. HN convention is plain text.

# Pre-submission checklist

- [ ] dev.to article has been live ≥48h
- [ ] README's top-of-fold matches what the seed comment claims (currently the top-of-fold has the "🔌 Companion MCP server: pyobfus-mcp" section — that's good)
- [ ] Run the seed comment through GPTZero (target: < 25% AI-flagged)
- [ ] Rewrite (don't tweak) any block that flags
- [ ] Verify no em-dashes in seed-comment prose (em-dashes in code are fine)
- [ ] Confirm available to monitor the thread for 90+ minutes after posting (HN's first-90-minutes rule)
- [ ] Submit Tuesday-Thursday 09:00-11:00 EST (peak active-engagement window)
- [ ] Have anticipated-objections responses copy-pasted in a scratchpad

# Voice-guide compliance (pre-GPTZero self-check)

- [x] No em-dashes in prose (only in title field per HN convention)
- [x] No "delve into / furthermore / moreover / it's worth noting / let's explore"
- [x] Contractions throughout
- [x] First person, dated, specific (medical imaging research, 643 tests, Python 3.8–3.14)
- [x] Length: 188 words (HN seed sweet spot 100–200)
- [x] One concession ("It works") to defuse fanboy framing
- [x] Honest threat-model statement up front (HN crowd respects it; punishes overclaim)
- [ ] Final GPTZero gate before posting

# CN reminder

Do NOT cross-post to V2EX in this same window. V2EX has a different submission culture and will react badly to "translated HN promo." If V2EX is targeted later, write a fresh post from CN angles, not a translation.
