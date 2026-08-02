# Doc-Sync + Positioning Audit — 2026-08-02

**Purpose**: research-and-plan handoff for a *future* session (requested explicitly —
not executed this session due to conversation length). Answers 11 questions the
maintainer raised after reviewing the post-0.5.6 README. Nothing in this doc has
been fixed yet; it's the punch list for next time.

**Context at time of writing**: pyobfus **0.5.6** live on PyPI (issue #25 fix +
CodeQL sweep), pyobfus-mcp still **0.3.1** (no MCP-side release since 0.5.4). This
follows the same pattern as [`DOC_SYNC_AUDIT_2026-07-15.md`](DOC_SYNC_AUDIT_2026-07-15.md)
(the prior doc-sync pass, done at 0.5.3) — that one only caught test-count/version
drift; this one goes deeper into structural staleness the mechanical sync missed.

---

## Q1 — README intro line missing Codex (and other tools)?

**Confirmed gap.** `README.md:7` reads:

> "...a machine-readable JSON CLI designed for [Claude Code](...), [Cursor](...), and MCP agents."

Codex is conspicuously absent, and it shouldn't be — the project already treats
Codex as a first-class client elsewhere:
- `templates/ai-integration/AGENTS.md:8-9` (the canonical agent-protocol file) explicitly says "read natively by Cursor, Windsurf, Aider, Continue, Cline, **Codex**, and more."
- `benchmarks/llm_resistance/` has a dedicated `CodexCliAttacker` class — Codex CLI is a first-class test subject for the LLM-resistance benchmark.
- The Smithery Skill listing (`docs/AGENTIC_DISCOVERABILITY_2026-06-22.md:166`) explicitly names Codex as one of the ~20 agent clients that can one-click-install `pyobfus-protect`.
- `pyobfus_mcp/pyobfus_mcp/server.json`'s `_meta.target_clients` also omits `codex` (see Q3).

**Fix**: reword the intro sentence to name Codex alongside Claude Code/Cursor, and
audit every other "supported clients" list in the repo for the same omission
(`README.md:32` MCP table intro, `pyobfus_mcp/README.md`, `server.json` `_meta.target_clients`,
`pyobfus_mcp/pyproject.toml:8` description line — currently "Claude Desktop, Claude
Code, Cursor, Windsurf, and Zed", also missing Codex). One canonical client list,
copy-pasted everywhere, would prevent this drift recurring.

---

## Q2 — PyPI badge stuck on 0.5.5?

**Investigated, not an actual bug.** Queried shields.io directly this session:

```
curl -s https://img.shields.io/pypi/v/pyobfus.json
→ {"value":"v0.5.6", ...}
curl -s https://img.shields.io/pypi/v/pyobfus.svg | grep -oE '0\.5\.[0-9]'
→ 0.5.6
```

The badge source is already correct. What the maintainer saw was almost certainly
**GitHub's camo image proxy cache or a local browser cache** — GitHub proxies all
README `<img>`/badge URLs through `camo.githubusercontent.com`, which has its own
TTL independent of shields.io's. This self-resolves within roughly an hour, or
immediately with a hard refresh / cache-busting query string.

**Action**: none needed in the repo. If it's still showing 0.5.5 by the next
session, re-check with the same `curl` commands above before assuming a repo-side
problem — the fix (if any) would be on GitHub's caching layer, not our files.

---

## Q3 — Do recent revisions (0.5.4/0.5.5/0.5.6) need syncing into pyobfus-mcp?

**Yes, in two different ways — one already fine, one genuinely stale.**

### Already fine (dynamic, no action needed)
`list_presets()` and `explain_preset()` in `pyobfus_mcp/pyobfus_mcp/tools.py`
read `ObfuscationConfig.FRAMEWORK_PRESETS` / `.list_presets()` **dynamically** —
they already return `ml` correctly today because the installed `pyobfus` dependency
resolves to 0.5.6 under the existing `pyobfus>=0.5.1` floor
(`pyobfus_mcp/pyproject.toml:40`). The issue #25 CLI-bugfix (0.5.6) required no MCP
change either — the MCP tools call the CLI's real behavior, not a cached copy of it.

### Genuinely stale (hardcoded lists that drifted)
| File:line | Current text | Problem |
|---|---|---|
| `pyobfus_mcp/pyobfus_mcp/tools.py:342-344` | `generate_pyobfus_config`'s docstring: "safe, balanced, aggressive, fastapi, django, flask, pydantic, click, sqlalchemy" | Missing `ml` (added 0.5.5). This is the parameter doc for `preset_override` — an agent reading it via introspection won't know `ml` is a valid value. |
| `pyobfus_mcp/server.json`'s `_meta.framework_presets` | `["fastapi", "django", "flask", "pydantic", "click", "sqlalchemy"]` | Missing `ml`. Static metadata array, doesn't auto-update. |
| `pyobfus_mcp/server.json`'s `_meta.target_clients` | `["claude-desktop", "claude-code", "cursor", "windsurf", "zed"]` | Missing `codex` (see Q1). |
| `pyobfus_mcp/CHANGELOG.md` `[Unreleased]` | Empty | No entry acknowledging that pyobfus 0.5.5/0.5.6 changed what the MCP tools can now do (ml preset, provenance-manifest, issue #25 fix) even though pyobfus-mcp's own code/version is unchanged. Worth at least a documentation-only note, mirroring how 0.3.1's changelog entry named the v0.5.0 Pro mechanisms. |

**Should pyobfus-mcp get a version bump (e.g. 0.3.2)?** Borderline call for the
maintainer, not mechanically obvious — the tool *surface* (8 tools, their
signatures) hasn't changed, only what one dynamic tool now *returns*. Precedent:
0.3.1's own changelog shows the project already bumped MCP for "no code change,
underlying pyobfus copy updated" once (naming the v0.5.0 Pro mechanisms in
pro-funnel copy). A docs-only patch bump to update `server.json`'s two arrays would
be consistent with that precedent and also gives Glama's admin-side Dockerfile
Build-steps field (which needs manual re-pinning per version, see `CLAUDE.md`'s
Glama note) a reason to be refreshed too — worth deciding explicitly next session
rather than defaulting either way.

---

## Q4 — Did we ever officially register the Claude Code plugin marketplace?

**`.claude-plugin/marketplace.json` exists and is valid** (`name: pyobfus`, one
plugin entry pointing at `./` with the `pyobfus-protect` skill). This is what makes
`/plugin marketplace add zhurong2020/pyobfus` work — **and that's the entire
mechanism**. Claude Code plugin marketplaces are git-repo-based and fully
self-service: there is no separate "submit for approval" or central-registry step
analogous to the MCP Registry or VS Code Marketplace. Having a valid
`marketplace.json` at the repo root *is* being "registered."

**Resolved 2026-08-02, via WebSearch**: yes, an Anthropic-curated directory exists
— the equivalent of awesome-mcp-servers/PulseMCP for MCP. Two distinct tiers:
- **`anthropics/claude-plugins-official`** — Anthropic-managed, 200+ curated
  first-party + reviewed partner plugins, auto-registered.
- **`anthropics/claude-plugins-community`** — the reviewed community
  marketplace, added manually with an `@claude-community` suffix. Its own
  GitHub description states it's a **"read-only mirror — submit plugins at
  `clau.de/plugin-directory-submission`."**

**pyobfus is confirmed absent from both** (searched "pyobfus" against all three
surfaces — official repo, community repo, and the independent
`claudepluginhub.com`/`claudemarketplaces.com` directories — zero hits). This is
the same "registry breadth" gap already documented for MCP servers in
`docs/AGENTIC_DISCOVERABILITY_2026-06-22.md` Gap 1, just for the plugin-directory
ecosystem instead.

**Submission process confirmed 2026-08-02** (fetched
`code.claude.com/docs/en/plugins#submit-your-plugin-to-the-official-marketplace`):
- The official marketplace (`claude-plugins-official`) has **no application
  process** — Anthropic decides at its discretion; the submission form does
  not add plugins there. Not a path available to us.
- The community marketplace (`claude-plugins-community`) accepts submissions
  via an **in-app web form**, not a GitHub PR: for a Team/Enterprise org,
  `claude.ai/admin-settings/directory/submissions/plugins/new`; for an
  **individual author** (pyobfus's case), the Console form at
  **`platform.claude.com/plugins/submit`**.
- Before submitting, `claude plugin validate ./your-plugin` must pass — the
  review pipeline runs the identical check. **Already run against this repo,
  passed**: `claude plugin validate ./` → `✔ Validation passed` (validates
  `.claude-plugin/marketplace.json`; the plugin manifest
  `.claude-plugin/plugin.json` — name/version/description/author/homepage/
  repository/license/keywords — is already complete and didn't need changes).
- Approved plugins get pinned to a commit SHA in the public catalog; CI
  auto-bumps the pin on new pushes. The catalog syncs **nightly**, so expect
  a delay between approval and the plugin appearing in
  `anthropics/claude-plugins-community`'s `marketplace.json`.

**Not completed this session — requires the maintainer's own authenticated
browser session.** Filling out `platform.claude.com/plugins/submit` needs a
logged-in Console account; this is not something achievable via CLI/API the
way the PyPI/MCP Registry publishes were. Local validation is the one
pre-check that *could* be automated, and it's done and passing — the
remaining step is a ~2-minute manual form submission.

`marketplace.json`'s own `metadata.version` is pinned at
`"0.1.0"` and has never moved since creation; check whether that's meant to track
anything (probably the marketplace-listing schema itself, not the pyobfus release
train, but confirm before touching it).

---

## Q5 — Do other mainstream AI tools need similar "marketplace" prep?

**Mostly already done.** `docs/AGENTIC_DISCOVERABILITY_2026-06-22.md` is the
existing research/action doc for exactly this question — re-read it before
duplicating work. State as of that doc plus what's shipped since:

| Surface | State |
|---|---|
| Official MCP Registry | ✅ done, 0.3.1 isLatest |
| Glama | ✅ done, Quality A |
| awesome-mcp-servers | ✅ merged (PR #5777) |
| Smithery | ✅ done via **Skill** channel (not MCP — local-execution tools can't use Smithery's remote-HTTP-only MCP publish) |
| mcp.so | ✅ submitted |
| PulseMCP | ⏳ submitted 2026-07-22, passive (their process is auto-ingest + manual follow-up after a week — was that follow-up ever confirmed landing? not verified this session) |
| ARD `ai-catalog.json` | ⏳ manifest implemented + CI-validated, but the **Read the Docs redirect/HTTPS/CORS verification is still an outstanding admin action** per the doc's own Gap 5 note — check whether this ever got done |
| GEO/AEO (answer-engine optimization) | Folded into the launch wave, which is now complete (2026-08-01) — but the doc's specific AEO tactics (FAQ schema, answer-first opening) were never confirmed as *applied*, only planned |
| npm `npx pyobfus-mcp` wrapper | Listed as optional/not done |

**No new tool-specific work identified for Codex specifically** beyond the
`AGENTS.md` template (already exists) and the naming-consistency fixes in Q1/Q3 —
Codex already gets pyobfus support for free through the AGENTS.md convention and
the Smithery Skill listing. The gap is purely that the *README/metadata prose*
hasn't caught up to say so, not that integration work is missing.

---

## Q6 — Do recent versions (0.5.4-0.5.6) still highlight Pro Edition's value?

**Content/judgment question — flagging for maintainer review, not something to
auto-fix.** Worth noting as context: 0.5.4 was a Pro feature (vault-key device
binding), but 0.5.5 and 0.5.6 were both Community/Free-tier-and-bugfix work
(`--preset ml`, `--provenance-manifest`, the issue #25 fix, a security hardening
commit). Three READMEs' worth of "What's new" banners in a row not mentioning Pro
at all is a real shift in what a first-time visitor sees first, even though the Pro
feature set itself hasn't shrunk. Whether that's a problem depends on current
positioning strategy (e.g., is the community-tier feature velocity itself part of
the pitch right now, per the "P2-18 benchmark, launch wave" era framing?) — this
needs the maintainer's call, not a mechanical doc fix.

---

## Q7 — Should "(Available Now)" be dropped from "Pro Edition (Available Now)"?

**Yes, recommend dropping — traced its origin, and the reason it existed no longer
applies.** `git log -S"Pro Edition (Available Now)"` shows this qualifier was added
2025-12-09 in the **v0.2.0** README rewrite — i.e., at the exact moment Pro features
first went from "planned" to "shipped," when a reader skimming the doc could
reasonably wonder if Pro was vaporware next to the Roadmap section's future
promises. **Eight months and roughly a dozen releases later**, Pro has been
continuously live and extended (String Encryption/Anti-Debug v0.1.6, Control Flow
Flattening/Dead Code/License Embedding v0.3.0, six new patent-targeted mechanisms
across v0.5.0-0.5.4) — the qualifier now reads like a defensive, launch-era
disclaimer that's outlived its purpose. Simplify the heading to `### 🔒 Pro
Edition`.

---

## Q8 — Should the old `v0.1.6+`/`v0.2.0+`/`v0.3.0+` feature-version tags be
reorganized?

**Yes — full inventory taken, genuinely cluttered.** `README.md` currently carries
**27 separate version-tag mentions** ranging from `v0.1.6` to `v0.5.6`, most
densely in the Free/Pro Edition feature lists and the Quick-Start command
examples:

```
v0.1.6+  ×4   (String Encryption/Anti-Debug intro, --preserve-param-names, Quick Start example)
v0.2.0+  ×5   (Cross-File Obfuscation, --dry-run/--no-cross-file/--verbose Quick Start examples)
v0.3.0+  ×8   (Control Flow Flattening, Dead Code Injection, License Embedding, Config Presets)
v0.5.0   ×2, v0.5.1 ×1, v0.5.3 ×1, v0.5.4 ×1, v0.5.5 ×1, v0.5.6 ×1
```

The `v0.1.6+`/`v0.2.0+`/`v0.3.0+` tags in particular are on features that have been
stable for 6+ releases and roughly 8 months — for a reader asking "what can this
tool do today," per-feature changelog trivia from 8 months ago adds noise without
adding decision-relevant information (unlike the *recent* 0.5.x tags, which are
still relevant "this is new" signals). **Recommendation**: strip the `v0.1.6+`/
`v0.2.0+`/`v0.3.0+` tags from the Free/Pro Edition feature bullet lists (the
CHANGELOG remains the authoritative place for "when did X ship"); keep version
tags only in Quick-Start *command examples* where "(v0.2.0+)" tells a reader
whether a flag will work on their installed version, and keep the still-recent
0.5.x tags since those are load-bearing "this is new" signals, not stale trivia.

---

## Q9 — "New in v0.5.0 — patent-targeted mechanisms" heading is now 6 versions
stale

**Confirmed**, `README.md:132`. The heading was accurate when v0.5.0 first shipped
the six mechanisms (2026-06-18) but hasn't been touched since, even though the
same section's body text *does* correctly track later additions inline (v0.5.1
build-flag fusion, v0.5.3 three new flags, v0.5.4 vault-key extension — this
session added that last one). **Fix**: reframe the heading to something
version-range-neutral, e.g. `#### Patent-targeted mechanisms (CN 202610712171X,
introduced v0.5.0)` — states when the *mechanism family* was introduced without
implying "v0.5.0" is still the current state.

---

## Q10 — Broader sweep: are there other "ancient" version numbers to clean up?

Covered by Q8's inventory for README specifically. Cross-file check done this
session: `llms.txt`/`docs/llms.txt`'s per-flag `(0.5.5)`-style tags were
deliberately checked in the 0.5.6 release and left alone, because they're
"introduced in" annotations for CLI flags (still historically accurate, low
clutter — one line per flag, not repeated inline prose like README's feature
list). **No further action identified there.** The Pro Edition section (Q9) and
ROADMAP.md (Q11) are the two spots with real staleness beyond README's own feature
list.

---

## Q11 — `docs/ROADMAP.md` (linked from README) hasn't been updated

**Confirmed, two distinct problems:**

1. **"Current Status" section (`docs/ROADMAP.md:10-14`) stops at 0.5.4** (2026-07-19)
   — doesn't mention 0.5.5 (2026-08-02, `--preset ml` + `--provenance-manifest`) or
   0.5.6 (2026-08-02, issue #25 fix + CodeQL sweep) at all.
2. **P2-17 and P2-19 are still checkbox-marked `[~]` (in progress)** at
   `docs/ROADMAP.md:133` and `:136`, even though both **shipped and released** as
   part of 0.5.5. The `[~]` status + "PR pending Claude Code review" phrasing
   directly contradicts `docs/POST_V0.4_TODO.md`'s own item 6, which correctly
   shows both merged and released. This is the single clearest "the roadmap and
   the actual TODO tracker have drifted apart" finding in this whole audit.

**Fix**: flip P2-17/P2-19 to `[x]` with a "_Shipped 0.5.5, 2026-08-02._" note
(matching the style already used for P2-1/P2-7/P2-8/P2-9/P2-10/P2-11 above them),
add a new "Current Status" paragraph for 0.5.5+0.5.6, and append a new "Last
Updated" trailer entry per the doc's own existing convention.

---

## Proposed priority order for next session

1. **Q11 (ROADMAP.md)** — cheapest, highest-integrity-risk fix (a public roadmap doc actively contradicting the actual TODO tracker is the kind of thing an external reader or contributor would notice and lose trust over).
2. **Q3 (MCP hardcoded lists)** — small, concrete, three files (`tools.py` docstring, `server.json` ×2 arrays), decide the version-bump question while there.
3. **Q1 (Codex everywhere)** — one wording pattern repeated across ~4-5 files, low risk.
4. **Q9 + Q7 + Q8 (README feature-section cleanup)** — bundle together since they're all edits to the same two sections (Free/Pro Edition feature lists); this is the biggest single edit, do it as one deliberate pass with a clear before/after read-through rather than piecemeal.
5. **Q4 (verify plugin-marketplace directory question)** — one `WebSearch`, resolves an open question either way.
6. **Q6 (Pro-Edition positioning)** — bring findings to the maintainer as a discussion, not a unilateral edit.
7. **Q2, Q5, Q10** — no action needed; already resolved by this audit or already tracked elsewhere.

---

## Session 2 (same day) — status update + next-session punch list

Items 1-5 above were all fixed and pushed in-session (commits `a426ab0`,
`767ba2b`, `1ab95b7`, `07ce053`, `27bfb79`). **pyobfus-mcp 0.3.2 also shipped**
(PyPI + MCP Registry both confirmed `isLatest`) — that wasn't in the original
plan but followed naturally from Q3's "decide the version-bump question."
Plugin-marketplace submission process was fully researched (see the updated
Q4 above) and local validation passes, but the actual submission needs the
maintainer's own browser session — not something Claude Code can do via
CLI/API. The Pro-Edition discussion (Q6) happened; maintainer agreed with the
proposed direction. **Everything below is written up for a cold-start session
to execute directly — no re-research needed.**

### 1. Fix a broken anchor link this session's own edit introduced

`README.md:21`'s "What's new" banner links to `[Pro Edition](#-pro-edition-available-now)`.
That anchor slug matched the *old* heading text `### 🔒 Pro Edition (Available Now)`
— but this session's Q7 fix (commit `07ce053`) renamed the heading to
`### 🔒 Pro Edition`, changing GitHub's auto-generated slug. Working out
GitHub's slug algorithm from the *old* anchor (`#-pro-edition-available-now`
for `🔒 Pro Edition (Available Now)`): the leading emoji is stripped entirely
(leaving a leading space), the rest is lowercased with spaces → hyphens and
parens dropped. Applying that to the new heading `🔒 Pro Edition` gives
**`#-pro-edition`**. Fix: change the link target at `README.md:21` from
`#-pro-edition-available-now` to `#-pro-edition`. (Verify by rendering the
README on GitHub after pushing — anchor slugs are worth a visual sanity check
since the algorithm isn't 100% guaranteed from this derivation alone.)

### 2. Add a persistent Pro-Edition anchor line (Q6 outcome, maintainer agreed)

**Agreed direction**: don't cram Pro mentions into unrelated release notes
(that reads as marketing fluff, against this project's consistently honest,
non-hyped voice — see the trial's "not a security boundary" framing and the
0.5.5 caveats about `preserve_param_names` as precedent for that voice).
Instead, add one small **structural, non-rotating** anchor near the top —
separate from the "What's new" banner (which stays honest/specific to each
release and will keep rotating through whatever actually shipped, Pro or
not) — so a reader lands on evidence Pro hasn't gone stale even during a
Community-focused release run.

**Why the underlying worry checks out as smaller than it first looked**:
this session cross-checked 0.5.4-0.5.6's actual content against two axes —
Pro's 6 patent mechanisms are all about *protection strength* (anti-piracy,
encryption, watermarking); 0.5.5's Community additions (`--preset ml`,
`--provenance-manifest`) are about *developer experience / audit tooling*.
Different axes — the new free features aren't cannibalizing what Pro sells,
so the Free/Pro differentiation logic is still coherent. The `### 🔒 Pro
Edition` section itself is also unconditionally present on every page load,
right after Free Edition — it never "disappeared." The real gap is just that
nothing near the *top* of the page reminds a skimming reader Pro exists,
since that job was being done incidentally by "What's new" banners that
happened to be about Pro in 0.5.0-0.5.4 and stopped being incidental once
three releases in a row were Community-focused.

**Concrete fix**: insert a new line in `README.md` between the intro
paragraph (currently line 19, "A Python code obfuscator built with...") and
the "What's new" banner (currently line 21), so it reads as a stable fact
about the product rather than dated news:

```markdown
> **🔒 Pro Edition available** — 6 patent-targeted protection mechanisms (Selective Opacity, forensic watermarking, Runtime String Vault, and more) layered on top of the free AST obfuscator, $45 one-time, no subscription. See [Pro Edition](#-pro-edition) below.
```

Notes on this draft, so the next session can adjust with the same reasoning
rather than re-deriving it from scratch:
- "$45 one-time, no subscription" is intentional — it's pyobfus's actual
  differentiator per `pricing_strategy.md`'s single-tier positioning (vs.
  PyArmor's $89 Pro and vs. subscription-based competitors), not filler.
  **Do not turn this into a pricing-tier discussion** — the memory is
  explicit that multi-tier pricing was already proposed and rejected once.
- "6 patent-targeted" matches the exact count and framing already used at
  `README.md:132`'s section body — consistent, not a new claim.
- Uses the anchor `#-pro-edition` (see item 1 above — fix that link first,
  then this new line's `(#-pro-edition)` target will already be correct).
- This is ONE line, not a redesign of the intro. Resist the urge to bundle
  additional Pro copy in while touching this area — that's exactly the
  "marketing fluff creep" the agreed direction was meant to avoid.

### 3. Maintainer's own actions

- **✅ Plugin-marketplace submission — done 2026-08-02.** Submitted via the
  Console form (`platform.claude.com/plugins/submit`), guided field-by-field
  in the same session's chat log. Confirmation page: "Plugin submitted for
  review." **Status is "submitted for review," not "live"** — Anthropic's
  review team evaluates it, may follow up for more info, and per the form's
  own text "submitting this form does not guarantee inclusion." One
  submission hiccup worth remembering: the `Link to plugin` field first
  rejected the pasted GitHub URL with `plugin_url: must not contain spaces
  or control characters` — a copy-paste artifact (invisible whitespace/
  control char from the chat UI), fixed by retyping the URL manually rather
  than pasting. No further action needed on this item until/unless
  Anthropic follows up; check back later for approval status at
  `github.com/anthropics/claude-plugins-community` (syncs nightly after
  approval) or via "View submissions" in the Console.
- **⏳ Glama admin Dockerfile Build-steps field** — still open. Per the
  existing `CLAUDE.md` Glama note, this needs a manual web-UI version-string
  bump after every MCP release (0.3.1 → 0.3.2 now) — not CLI-scriptable.
  Not confirmed done for 0.3.2 yet; ~1-minute admin-panel edit when picked
  up.
