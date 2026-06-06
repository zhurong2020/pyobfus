---
surface: GitHub Discussions (zhurong2020/pyobfus → Discussions tab)
type: native poll (Discussions → New discussion → Polls category)
status: READY — post ~24h after the Reddit thread resolves (P0.7, captures launch-wave traffic overlap)
target_post_window: HN/Reddit launch + ~24h (placeholder 2026-06-12 to 2026-06-14)
pin: yes — pin to the Discussions sidebar after posting
cross_link: drop a one-line pointer in the dev.to comments + the HN seed sub-thread (only if "what's next" comes up) + the Reddit thread footer reply. Do NOT spam the link into post bodies.
---

# Why this post exists

The launch wave (HN + Reddit + CN) is the cheapest window I'll get to ask real users what they want next, instead of guessing. A native GitHub poll keeps it one click and keeps the signal in the repo where the roadmap lives. Target: 10+ votes before deciding the v0.5 sequencing (N7 demo vs P2-2 VSCode vs N9 team server).

Keep it honest: the three options are real directions I'm weighing, not a sales funnel. No "vote and I'll build it tomorrow" — votes inform order, not promises.

---

# Poll title

```
What should pyobfus build next?
```

# Poll body (the text above the options)

> pyobfus 0.4 is out: AST name mangling, framework presets, reverse stack-trace mapping, and an MCP server so Claude/Cursor can call it as tool calls. I've got three bigger directions queued for the next cycle and I can only do one well at a time. If you've tried it (or you're the kind of person who would), I'd like to know which one would actually matter to you.
>
> One vote each. Comments welcome if your real answer is "none of these, I want X" — that's the most useful reply I can get.

# Poll options (GitHub Discussions allows up to 8; we use 3)

1. **Online demo at pyobfus.dev** — paste code in the browser, see before/after, nothing leaves your machine (runs in WebAssembly). No `pip install` to try it.
2. **VS Code extension** — obfuscate + manage the mapping file from inside the editor, right-click a folder to protect it.
3. **Self-hosted team license server** — for teams shipping commercial Python who want device-bound Pro licensing they run themselves, no third-party check-in.

---

# Engagement plan

- Reply to every "none of these, I want X" comment within a day. Those are the roadmap gold; thank them and ask one clarifying question.
- If a 4th theme shows up 3+ times in comments (e.g. "CI/CD GitHub Action", "PyInstaller integration"), add it as a pinned comment tally rather than re-doing the poll.
- After ~2 weeks or 10+ votes (whichever first), post a short "here's what won and what I'm doing about it" comment. Closing the loop publicly is the trust signal.

# What NOT to do

- ❌ Don't cross-post the poll link into the HN/Reddit post bodies — reads as vote-farming. It only goes in a reply IF someone asks "what's on the roadmap".
- ❌ Don't promise a ship date in the poll. Votes set order, not deadlines.
- ❌ Don't include the Pro/Stripe link here. This is a roadmap-signal post, not a sales surface.
- ❌ Don't list patent-gated v0.5 Pro mechanisms (Selective Opacity / forensic watermark / etc.) as options — those are not public-roadmap items until the patent 补正 is resolved.

# Voice-guide compliance

- [x] First person, specific, no hype words
- [x] No em-dashes in prose (only in option labels as separators, GitHub-conventional)
- [x] One honest concession ("I can only do one well at a time")
- [x] Invites the "none of these" answer (signals you actually want signal, not validation)
- [ ] Quick read-through before posting — 30 seconds, no detector gate needed for a poll
