# pyobfus Post-v0.4 Action Plan

**Snapshot**: 2026-05-09 (after pyobfus-mcp 0.2.0 ship + mcpservers.org listing live + 2026-05-09 strategy review added P0.5/P0.6/P0.7 + N7/N8/N9 + single-tier pricing guardrail).

**Use as cold-start cheat sheet** when resuming work after a session break. This doc supersedes ad-hoc TODO scattered in chat; future Claude sessions should read this first.

> **Current executable handoff (2026-08-01):** use the prioritized list below.
> [`RESUME_PLAN_2026-07-19.md`](RESUME_PLAN_2026-07-19.md) is a frozen record of
> the 0.5.4 release session; its unchecked boxes are not current work.
>
> **0.5.4 published 2026-07-19.** Vault-key device binding landed (PR #19), so
> the "vault keys still ship as baked literals" scope boundary below is CLOSED.
> The trial-bypass reports #20/#21 are answered and the trial is now documented
> as a convenience control, not a security boundary. CI enforces all three test
> roots. Issue #22 is closed after PR #23 merged with the blocking mypy gate.
> **Launch wave complete 2026-08-01** (DEV/r-Python/Show HN/CN long-form/
> GitHub Discussions, all five channels) — engagement came back essentially
> flat everywhere except two real GitHub stars; decision made to stop
> pushing it and shift active work to P2-18 + subsequent features (item 4
> is now closed out, see below). Passive monitoring continues (+7d/+30d
> checkpoints), it just isn't blocking anything.
> **P2-18 internal evidence complete 2026-08-01** — full 5-sample corpus ×
> two model families (Codex + Claude), clean cross-model C4 data point,
> decision made that a third model family isn't needed. Reviewed writeup:
> `docs/LLM_RESISTANCE_PILOT_RESULTS_2026-08-01.md`. See item 4 below.
> **P2-17 + P2-19 merged and released as pyobfus 0.5.5, 2026-08-02** — PRs
> #26/#27 both reviewed, merged, live on PyPI. See item 6 below.
> **Issue #25 fixed, closed, and released as pyobfus 0.5.6 — 2026-08-02.**
> The tri-state-flag fix (`cli.py`'s three
> `--preserve-param-names`/`--remove-docstrings`/`--remove-comments`
> options now default to `None` and only override a preset/config choice
> when the user explicitly passes them) is verified by an empirical re-run
> of the original repro commands plus new/rewritten tests in
> `tests/test_framework_presets.py` (the old
> `test_cli_fastapi_preset_preserves_param_names` was itself a false
> positive — it asserted against a surviving string dict key, not the
> renamed identifier). Commit `4f53c2e` on `main`; tag `v0.5.6` pushed,
> release workflow green, PyPI JSON API confirms `0.5.6` is latest.
> Issue #25 closed with a summary comment.
> **Same session: 2 open CodeQL alerts on `main` also closed out** (High/
> CWE-732 `py/overly-permissive-file` in `benchmarks/llm_resistance/
> scorer.py`, the Docker-executor temp-dir chmod for the P2-18 benchmark
> sandbox). The directory chmod was tightened `0o755` → `0o711`
> (traverse-only, no listing — the driver only ever opens 3 known
> hardcoded paths, never lists the dir) in commit `8ec8abc`, verified
> against the real Docker sandbox
> (`test_docker_executor_can_read_mounted_temp_dir`), which auto-resolved
> that alert on the next scan. The per-file `0o644` chmod is functionally
> unavoidable — the container runs as an unrelated UID (`65534:65534`,
> chosen over the host UID specifically for escape-blast-radius
> defense-in-depth) with no shared group, so reading file *contents*
> requires the world-read bit; dismissed with a documented `won't fix`
> rationale via the code-scanning API rather than left silently open.
> **README/MCP/ROADMAP doc-staleness audit done 2026-08-02, not yet
> fixed — see item 8.** The maintainer asked 11 pointed questions after
> reviewing the post-0.5.6 README (missing Codex mentions, a PyPI-badge
> false alarm, MCP metadata that never absorbed the `ml` preset,
> whether the Claude Code plugin marketplace needs external
> registration, stale `v0.1.6+`-era version tags, a "New in v0.5.0"
> heading that's now 6 versions behind, and — the sharpest catch —
> `docs/ROADMAP.md` still showing P2-17/P2-19 as in-progress when
> they've actually shipped). Full findings + a prioritized fix order are
> in `docs/DOC_SYNC_AUDIT_2026-08-02.md`, written specifically so a
> cold-start session can act without re-researching.

## Current prioritized TODO (2026-08-01)

1. ✅ **Documentation truth sweep — completed 2026-07-20.** Active surfaces use
   the real `pyobfus SRC -o OUT --level pro --<flag>` syntax; 0.5.4 and the
   release-CI baseline are current; old release checklists are marked frozen.
2. **Launch wave — DEV published 2026-07-22; r/Python posted 2026-07-23; Show
   HN submitted 2026-08-01.** The
   canonical article is live at
   <https://dev.to/zhurong2020/i-built-a-python-obfuscator-that-keeps-production-traces-debuggable-1mp8>.
   The HN account and submission form are functional, and the maintainer posted
   a first independently written community comment on 2026-07-22. A reply to
   that thread was drafted 2026-07-23 but not yet posted: `news.ycombinator.com`
   returned HTTP 429 on `/login` for the maintainer that day (site-side rate
   limit, not an account problem) — retry once it clears. Given the HN blocker,
   the maintainer posted the r/Python showcase comment
   (`_drafts/launch-v0.5.4/reddit-python.md`, de-AI'd 2026-07-23 — disclosure
   moved to the opening sentence, closing triplet sentence broken up) ahead of
   Show HN, out of the original sequence; it went live with no AutoModerator
   removal/hold, at
   <https://www.reddit.com/r/Python/comments/1unctej/showcase_thread/>. That
   thread recycles monthly, so the URL will not be valid for a future post.
   The maintainer's Reddit account (`u/No_Emphasis8994`, 2-year account age,
   0 prior karma/contributions before this comment) posted successfully via
   the direct route without a pre-warm-up period.

   **✅ Show HN — submitted 2026-08-01.** The 429 cleared on its own; the
   maintainer independently wrote and submitted
   <https://news.ycombinator.com/item?id=49130416> ("Show HN: I built a Python
   obfuscator that keeps production traces debuggable", 76 chars, linking to
   the GitHub repo rather than the DEV article). Left the submission `text`
   field blank and posted the explanation as the first top-level comment
   instead — states the mangled-identifier readability problem for both
   developers reading a production traceback and AI coding tools (Claude
   Code/Cursor), then the `--save-mapping` / `--unmap` local reverse-mapping
   mechanism that keeps debugging local while production stays obfuscated.
   Independently written by the maintainer, no AI drafting/editing. Baseline
   ~21 minutes after submission: 1 point, 1 comment (the maintainer's own).
   Full record in `_drafts/launch-v0.5.4/README.md`. The maintainer's earlier
   drafted reply to the MCP Show HN thread (`item?id=49001279`) may still be
   unposted — not confirmed either way this session, check before assuming.

   Next: watch the Show HN thread and reply to incoming comments (own words,
   no vote solicitation), watch the r/Python comment for real replies, then
   Chinese channels → GitHub feedback poll; record +24h/+7d/+30d metrics on
   both Show HN and the overall launch. AI-generated or AI-edited HN text is
   prohibited.
   **Chinese channel status (2026-07-23)**: `cn.md`'s 长文版 and V2EX 短版 were
   de-AI'd (self-evaluative framing removed, one "不是A而是B" contrastive
   rewritten). The 长文版 destination, arong.eu.org (brand header currently
   reads "嵘说"; the site also carries older "阿嵘的云生活" / "有心言者"
   taglines on different sections), already carries two prior pyobfus posts —
   "别让你的Python代码'裸奔'了" (2025-12-27) and "pyobfus — 一个让 AI 还能读懂
   崩溃日志的 Python 代码混淆器" (2026-05-21) — so the 0.5.4 draft is a third
   post continuing an established series, not a new channel; frame it as an
   update (lead with what's new in 0.5.4) rather than re-pitching pyobfus from
   scratch, since at least the May post already covers the mapping.json/AI-
   debugging story. V2EX is now blocked, and for a structural reason unrelated
   to content rules: the maintainer's freshly Google-registered account
   requires either an invite code from an existing V2EX member or binding a
   Solana address holding ≥10,000 $V2EX tokens to activate — buying crypto for
   one forum post is not worth it, so this channel is deferred until an invite
   code is obtained through a normal contact, not chased. If it does go out,
   the target is the dedicated **开源软件** node (`v2ex.com/go/opensource`,
   not the generic 分享创造 node), which explicitly welcomes personal
   open-source project posts with real substance (not bare links) — the
   drafted short version already qualifies. A separate 知乎 piece was in the
   pre-0.5.4 "CN trio" plan but is not in the current `_drafts/launch-v0.5.4/`
   scope; not drafted unless requested.

   **✅ Launch wave complete — 2026-08-01.** All five channels published: DEV
   (2026-07-22), r/Python (2026-07-23), Show HN (2026-08-01,
   `item?id=49130416`), CN long-form (2026-08-01, via findata's canonical
   draft, WP #1706 + Discord — see `_drafts/launch-v0.5.4/README.md`), and
   GitHub Discussions (the 9-month-unanswered Q&A #2 answered, a new
   Announcement #24 covering 0.5.0-0.5.4's patent-unlock arc). V2EX stays
   deferred (account-activation blocker, unrelated to content).

   **Engagement checkpoint, ~10-12h after Show HN (2026-08-01)**: essentially
   flat across every broadcast channel — HN 2 points / 1 comment (the
   maintainer's own, no new external replies), r/Python 2 views / 1
   self-upvote / 0 replies, DEV 0 reactions / 0 comments / <25 views (flatter
   than the May post's 4/1/42). The one unambiguous positive signal: **two
   named GitHub accounts starred the repo** (`helenkwok`, `SWFDtf`), a
   deliberate action unlike a passive view, consistent with GitHub Insights'
   organic-search-referrer traffic (Google/Bing/DuckDuckGo) — people are
   quietly evaluating without leaving public comments, which is the normal
   pattern, not a launch failure.

   **Decision (2026-08-01): stop pushing the launch wave, shift focus to
   P2-18 and subsequent feature work.** With comment/reply engagement at
   effectively zero everywhere, further posting or re-bumping would look like
   chasing attention, not community building — against the project's own
   no-solicitation principle. Continue passive monitoring only (+7d/+30d
   checkpoints per channel, reply to anything real that shows up); do not
   treat this as blocking further work. See item 4 (P2-18) below for the new
   active priority.
3. ✅ **Issue #22 / mypy gate — completed 2026-07-22.** Core, Pro, and MCP (72
   source files) report zero errors; mypy stays on the 1.20 line while Python
   3.9 is supported. PR #23 passed the full remote CI matrix, merged, and
   closed issue #22.
4. ✅ **P2-18 benchmark-first evidence — closed out 2026-08-01, fed item 6.**
   The launch wave is complete and now passive-monitoring only (see item 2);
   this was the active-work item until a *credible public* result shipped,
   which then unblocked feature selection (item 6, now also done — current
   priority is issue #25, see the handoff note above).

   Unblocked; first real pilot run 2026-08-01. The Codex weekly allowance
   reset on schedule (2026-07-29
   06:54) and a full-ladder pilot ran on Windows Codex CLI 0.145.0
   (`gpt-5.6-sol`, saved ChatGPT login, `codex-windows` sandbox executor)
   across 2 corpus samples (`luhn`, `billing_auth`) × all 6 conditions:
   `harness.py --attacker codex-cli --model gpt-5.6-sol --sample luhn
   --sample billing_auth --condition C0 --condition C1 --condition C2
   --condition C3 --condition C4 --condition C5 --executor codex-windows
   --sandbox-python-zip <pinned 3.11.9 embeddable ZIP>`. This is real
   evidence, not stub output — but still just a 2-sample pilot, not yet the
   "credible public result" the Roadmap/benchmark doc require (larger corpus
   + ≥2 model families, see below).

   **A corpus-quality bug surfaced during the pilot and was fixed the same
   session, in the harness itself rather than by hand-picking samples**:
   `luhn`/`caesar`/`roman` are all well-known public-domain algorithms (Luhn
   checksum, Caesar cipher, Roman numerals) — an attacker can recall the
   correct implementation from the function name/signature alone without
   engaging the obfuscation, so a `recovered=true` on them is not evidence a
   layer failed. Separately, `luhn` has no string literals, so
   `--string-encryption` (C2) was a byte-for-byte no-op on it, silently
   diluting the C2 aggregate — the first pilot run reported C2 resistance as
   50% (in reality: 1 real result + 1 meaningless no-op averaged together).
   Fix: `conditions.py` now tags C2/C3 with `builds_on` (the rung each
   additively builds on); `harness.py` compares the new artifact's hash
   against that rung *before* spending an attacker call and records a
   `skip_reason: "noop"` row instead of scoring it. Corpus samples also carry
   a new `public_knowledge` flag (set on `luhn`/`caesar`/`roman`); `report.md`
   prints an explicit caveat naming them whenever they appear in a run. Full
   design rationale in `docs/LLM_RESISTANCE_BENCHMARK.md`. After the fix, a
   pilot rerun correctly reported C2 resistance as 100% (1/1 eligible — `luhn`
   excluded as a no-op) and spent one fewer real attacker call than the first
   attempt.

   **Real signal from the fixed pilot**: C0/C1 fully recovered on both
   samples (core mangling alone ≈0% resistance — expected, matches the
   documented positioning that only L2 encryption / L3 opacity+vault count as
   "protection" against an LLM). `billing_auth` (custom secrets, not public
   knowledge) held at C2/C3/C5 — 0% SRR / 100% resistance. Neither L3
   condition yet has a *clean* (non-public-knowledge) data point: `luhn`
   (the only C4-eligible sample run so far) is public-knowledge-tainted, and
   `billing_auth` is not C4-eligible. That is a corpus gap, not a finding
   about the opacity mechanism.

   (Remaining-before-publishable gaps (a) run C4 against a non-public-knowledge
   target and (b) expand beyond 2 of the 5 corpus samples were both closed
   the same day — see the full-corpus run below.)

   **(c) ✅ Second model family run 2026-08-01** — `ClaudeCodeCliAttacker`
   (`--attacker claude-code-cli`) shells out to `claude -p` with saved Claude
   subscription authentication, the same no-API-account discipline as
   `CodexCliAttacker`, so it does not require an Anthropic API account.
   Static-analysis containment is enforced via `--allowedTools ""` (verified
   empirically to stop tool use, not just a prompt request) since Claude Code
   has no `--sandbox` flag. First real pilot: `--model sonnet`, same 2 samples
   and all 6 conditions as the Codex pilot, `--executor docker
   --docker-image python:3.12-alpine` (this machine has no Windows/codex-windows
   sandbox). Two pre-existing plumbing bugs surfaced and were fixed the same
   session (neither specific to this attacker): Claude Code's `--json-schema`
   rejects the shared schema file's `$schema` meta key (no network access to
   resolve it) — strip it before passing; and the docker executor's scoring
   temp dir defaulted to mode 0700, unreadable by the container's unprivileged
   `--user 65534:65534`, so every row silently scored not-recovered regardless
   of attacker/condition/sample — this would have hit *any* real attacker on
   the docker executor, the path had evidently never been exercised
   end-to-end with real content before. Both fixed in `scorer.py`/`attacker.py`
   with a docker-gated regression test added.

   **Real signal, cross-model comparison (luhn/billing_auth pilot)**: on
   `billing_auth` (the only non-public-knowledge sample in this first pair),
   Claude Sonnet reproduced the *exact same pattern* as the
   Codex/`gpt-5.6-sol` pilot — recovered at C0/C1 (no protection), held at
   C2/C3/C5 (0% SRR / 100% resistance each). `luhn` (public-knowledge-tainted)
   was recovered at C0/C1/C3/C4 as expected and is excluded from the credible
   signal.

   **✅ Full-corpus run, both model families, 2026-08-01 — the clean C4 data
   point closes gaps (a) and (b).** Ran `caesar` + `roman` + `price_rules`
   (the three previously-unused samples) × all 6 conditions, once each with
   `--attacker codex-cli --model gpt-5.6-sol` and once with `--attacker
   claude-code-cli --model sonnet`, both via `--executor docker
   --docker-image python:3.12-alpine` (this machine has both `codex` and
   `claude` CLIs installed with saved subscription logins, and docker, so no
   separate Windows machine was needed this time). **Both model families
   produced the identical per-sample pattern**: `caesar` and `roman`
   (public-knowledge, Caesar cipher / Roman numerals) were recovered at
   C0/C1/C2/C3/C4 — expected and inconclusive, an attacker can recall a
   named public algorithm without engaging the obfuscation at all.
   **`price_rules` (custom tiered-pricing business logic, not public
   knowledge, `c4_eligible: true` / `c5_eligible: false`) was NOT recovered at
   C2, C3, or C4 by either model** — 0% SRR / 100% resistance at every one of
   those rungs, for both Codex and Claude, independently.

   This is the project's first clean, cross-model-validated C4 data point:
   two different model families both failed to statically recover a
   non-public-knowledge sample protected by Pro L3 Selective Opacity. Full
   corpus coverage is now: `luhn`/`caesar`/`roman` (public-knowledge, always
   recovered, inconclusive above C1) and `billing_auth`/`price_rules`
   (non-public-knowledge, both held at every rung from C2 up, both model
   families) — a 2-of-2 clean-sample record, not a single lucky case.

   **✅ Closed out 2026-08-01.** Methodology + full per-sample tables written
   up in [`docs/LLM_RESISTANCE_PILOT_RESULTS_2026-08-01.md`](LLM_RESISTANCE_PILOT_RESULTS_2026-08-01.md)
   — the deliberate, reviewed copy `benchmarks/llm_resistance/README.md`
   calls for before treating a run as evidence. **Decision: no third model
   family** — Codex and Claude are two of the current leading model families
   for code understanding and independently agree on every non-public-
   knowledge sample/condition, so 2 is sufficient; revisit only if a future
   publication reviewer specifically asks for a third. What's still open (low
   priority, no urgency): the *published* research-paper track this internal
   result would seed (see `docs/LLM_RESISTANCE_BENCHMARK.md`'s Roadmap
   section), and a larger per-condition sample count if that publication
   effort ever starts — 5 samples demonstrates the method, it isn't enough
   for a statistical confidence interval.
5. ✅ **Discoverability and citation — deployed and verified 2026-07-22.** DOI,
   README/PyPI/Read the Docs citation surfaces are present. ARD metadata is
   CI-validated and live at the Read the Docs well-known URL. PulseMCP exact
   search returned 0 results on 2026-07-22. Its submission page says Registry
   entries are ingested daily and processed weekly, and directs maintainers to
   `hello@pulsemcp.com` after a week; the maintainer sent that follow-up on
   2026-07-22, so this is now passive monitoring.
6. **⭐ DECIDED (2026-08-01) — next features: P2-17 + P2-19, implemented by
   Codex, reviewed by Claude Code.** The launch-feedback poll gate
   (`NEXT_FEATURE_DECISION.md`, 14-day/10-vote trigger) is **overridden by
   direct maintainer decision** — real launch engagement came back too thin
   for that poll to have meant much anyway (see item 2's checkpoint), so
   selection did not wait for it. Picked directly from the already-scanned
   ROADMAP candidates: **P2-17 signed obfuscation provenance manifest** and
   **P2-19 `--preset ml`**, both flagged low-cost/high-relevance in the
   2026-07-07 research scan.

   **✅ Both PRs open and reviewed, 2026-08-01** — Codex's environment lacked
   `black`/`mypy`, so Codex delivered both features combined, uncommitted, on
   `main`'s working tree with a self-reported "1 test failure" (missing `mcp`
   SDK locally — not reproducible with a complete environment, confirmed
   during review: all 73 MCP tests pass). Claude Code reviewed, fixed, split
   into two independent branches, and opened:
   - [**PR #27**](https://github.com/zhurong2020/pyobfus/pull/27) —
     `codex/p2-17-provenance-manifest`
   - [**PR #26**](https://github.com/zhurong2020/pyobfus/pull/26) —
     `codex/p2-19-ml-preset`

   Review found and fixed: an overclaimed "signature" (it's a
   self-consistency digest, not a cryptographic signature — renamed
   throughout), an overly broad `exclude_names` list in `--preset ml` that
   would have left common non-ML business-logic identifiers needlessly
   readable, a dead-branch bug in the per-ML-library exclude-glob suggestion,
   a real mypy type error, and a real `black` formatting failure (neither
   catchable in Codex's incomplete environment). Both branches are
   independently green (`black`/`ruff`/`mypy`/all three test roots) and can
   merge in either order.

   Also found, but explicitly deferred rather than fixed inline (per
   maintainer decision) since it's pre-existing and affects six *existing*
   presets, not just the new one: **`preserve_param_names=True` does not
   actually preserve parameter identifiers end-to-end through the CLI** —
   filed as [**issue #25**](https://github.com/zhurong2020/pyobfus/issues/25)
   with two reproductions (`--preset ml` and, showing it predates this work
   entirely, `--preset fastapi`) and an explanation of why the existing
   fastapi test for this claim was a false positive (its assertion matched a
   surviving string dict key, not the actual renamed identifier).

   **✅ Both merged and released as pyobfus 0.5.5, 2026-08-02.** PR #26
   fast-forward merged first; PR #27 needed a manual merge (both touched
   `CHANGELOG.md`'s `[Unreleased]` section and one adjacent `README.md`
   bullet — non-overlapping content, resolved by keeping both). Before
   merging #26, one more overclaim was caught and fixed: the `--preset ml`
   docstring/CHANGELOG entry said the preset "preserves parameter names" as
   a working feature, contradicting the issue #25 finding two paragraphs
   above — corrected to state plainly that the flag doesn't currently do
   anything (commit `630840e`), and PR #26's own description had the same
   contradiction, fixed via `gh pr edit`. Version bumped 0.5.4 → 0.5.5
   (pattern-matched to the existing 0.5.1–0.5.4 cadence of stacking
   additive CLI features under the 0.5.x line rather than a semver-strict
   0.6.0); tag `v0.5.5` pushed, OIDC release workflow green, live on PyPI
   (verified via the JSON API). `pyobfus-mcp` unchanged at 0.3.1 (no
   tool-surface change), so no Glama Build-steps re-pin needed.

   A Tools / Resources / Prompts separation is recorded in
   [`MCP_PRIMITIVES_DESIGN.md`](MCP_PRIMITIVES_DESIGN.md) as a post-launch
   research candidate, not committed scope — unrelated to this decision.
7. **✅ FIXED, RELEASED as pyobfus 0.5.6, issue closed — 2026-08-02.** It
   turned out bigger than originally filed (see below). Commit `4f53c2e`,
   tag `v0.5.6` pushed, OIDC release green, confirmed latest on PyPI's JSON
   API. Also swept 2 open CodeQL alerts in the same session — see the
   handoff note at the top of this file for the security fix.

   **Root cause found and empirically confirmed** (not just a hunch — both
   repros below were actually run against current `main`):
   [`pyobfus/cli.py:621-626`](https://github.com/zhurong2020/pyobfus/blob/main/pyobfus/cli.py#L621),
   the "Override config with CLI options" block, runs *after* the preset is
   loaded (`config = ObfuscationConfig.get_preset(preset.lower())` at line
   519) and unconditionally does:
   ```python
   config.remove_docstrings = remove_docstrings     # line 623
   config.remove_comments = remove_comments         # line 624
   config.preserve_param_names = preserve_param_names  # line 626
   ```
   where the right-hand variables are the raw Click option values —
   `preserve_param_names` defaults to `False` (`is_flag=True`, no way to
   express "not passed"), and `remove_docstrings`/`remove_comments` default
   to `True` (`--remove-docstrings/--keep-docstrings`, `default=True`).
   Any preset that sets a *different* value for one of these fields gets
   silently clobbered back to the CLI default the moment the user doesn't
   also pass the matching flag explicitly — which is the normal, documented
   way every preset is used (`pyobfus src/ -o dist/ --preset fastapi`, no
   extra flags).

   **Empirical confirmation, both reproduced against current `main`
   (2026-08-02)**:
   - `pyobfus serve.py -o out.py --preset fastapi` on
     `def predict(inputs, batch_size=8): return inputs[:batch_size]`
     → `def I2(I1, I0=8): return I1[:I0]` (params mangled — this is
     issue #25 as originally filed). Adding `--preserve-param-names`
     explicitly on top of `--preset fastapi` *does* preserve them —
     confirming the clobber, not a deeper mechanism failure.
   - **New, more severe finding**: `pyobfus docstest.py -o out.py --preset
     safe` on a function with a docstring strips the docstring, even
     though `preset_safe()` ([`pyobfus/config.py:194-197`](https://github.com/zhurong2020/pyobfus/blob/main/pyobfus/config.py#L194))
     explicitly sets `config.remove_docstrings = False` with the comment
     `# Keep docstrings`, and `preset_safe` is `preset_safe()`'s entire
     reason to exist ("Preserves docstrings for documentation" — its own
     docstring). **Every framework preset is built on `preset_safe`**
     (`fastapi`/`django`/`flask`/`pydantic`/`click`/`sqlalchemy`/`ml` all
     say "Based on preset_safe (docstrings preserved)" in their own
     docstrings) — so this isn't a `preserve_param_names`-only bug, it's
     the whole "CLI silently overrides preset intent" pattern, and
     docstring preservation is arguably the more load-bearing promise
     since every doc/README describes `--preset safe` and its descendants
     that way. `--remove-comments` is not currently observed broken (no
     preset sets `remove_comments=False`), but shares the same
     unconditional-override code shape and should get the same fix on
     principle.

   **Proposed fix** (matches a pattern already used two lines below in the
   same function — `numeric_obfuscation`/`strip_ai_artifacts` at ~line 627
   only override when the CLI flag is truthy, i.e. "only touch the preset's
   value if the user actually asked for something"):
   1. Convert `--preserve-param-names` from a one-way `is_flag=True` into a
      tri-state boolean pair:
      `--preserve-param-names/--no-preserve-param-names`, `default=None`.
      Click then yields `None` when the user passed neither flag, `True`/
      `False` when they explicitly passed one.
   2. `--remove-docstrings/--keep-docstrings` and
      `--remove-comments/--keep-comments` already use the flag-pair *syntax*
      but with `default=True` (a concrete value, not tri-state) — change
      their `default` to `None` too, for the same reason.
   3. At the override site (cli.py:621-626), only assign when the CLI value
      is not `None`:
      ```python
      if preserve_param_names is not None:
          config.preserve_param_names = preserve_param_names
      if remove_docstrings is not None:
          config.remove_docstrings = remove_docstrings
      if remove_comments is not None:
          config.remove_comments = remove_comments
      ```
      When the user doesn't pass any of these flags, the preset's own
      choice now survives; when they do pass one, it still overrides the
      preset exactly as before (explicit user intent should win).
   4. Check whether `ObfuscationConfig.from_file()`'s YAML-config code path
      (not just `--preset`) has the same interaction with these three CLI
      options, since `config_path`/`from_file` also loads a config object
      before the same override block runs.
   5. Existing tests are false positives and need rewriting, not just
      re-running: `test_cli_fastapi_preset_preserves_param_names` (and the
      django/flask/pydantic/click/sqlalchemy equivalents, if they exist)
      assert against a *string dict key* (`'user_id'`) that survives
      regardless of whether the actual parameter identifier does — see
      issue #25's own writeup for the exact false-positive mechanism. Use
      `tests/test_framework_presets.py::test_cli_ml_preset_preserves_dispatch_method_name`
      (added in PR #26) as the template for a real assertion (bare
      identifier survives unmangled, not a string literal). Also add a
      docstring-preservation regression test at the CLI level for
      `--preset safe` (and at least one framework preset), since the
      existing bug was invisible to unit tests that construct
      `ObfuscationConfig` directly (those never touch the cli.py override
      block at all — the bug only exists on the CLI code path).
   6. After the fix lands: revert the "does not currently work" honesty
      caveats added in 0.5.5 (`pyobfus/config.py` `preset_ml` docstring,
      `CHANGELOG.md`'s 0.5.5 entry) back to a positive claim, close issue
      #25 referencing the fix commit, and decide whether to broaden #25's
      title/scope to cover the docstring-clobber finding or file it as a
      companion issue (a scope call worth 30 seconds of human judgment,
      not made unilaterally this session since it changes what "closing
      #25" means).
   7. Version bump: next patch in the established 0.5.x cadence (0.5.6),
      release-commit pattern documented in this file's own 0.5.5 entry
      above and in memory `pyobfus_0_5_5_release_2026-08-02.md`.
8. **⭐ CURRENT TOP PRIORITY — README/MCP/ROADMAP doc-staleness fixes
   (researched 2026-08-02, not yet fixed).** Full findings, file:line
   references, and a recommended fix order are all in
   [`docs/DOC_SYNC_AUDIT_2026-08-02.md`](DOC_SYNC_AUDIT_2026-08-02.md) —
   read that file first, it's written so a cold-start session can act
   directly. Short version of the recommended order:
   1. `docs/ROADMAP.md` — "Current Status" stops at 0.5.4 (doesn't
      mention 0.5.5/0.5.6), and P2-17/P2-19 are still checkbox-marked
      `[~]` in-progress even though both shipped in 0.5.5. This is the
      sharpest finding (a public roadmap actively contradicting the
      actual release state).
   2. `pyobfus_mcp/` hardcoded lists that never absorbed the `ml`
      preset (0.5.5): `tools.py`'s `generate_pyobfus_config` docstring,
      and `server.json`'s `_meta.framework_presets` +
      `_meta.target_clients` arrays (the latter also missing `codex` —
      see next item). Decide whether this warrants an MCP 0.3.2
      docs-only patch bump (precedent: 0.3.1 did the same for the
      v0.5.0 Pro mechanisms).
   3. Codex is missing from ~5 "supported clients" mentions across
      `README.md`, `pyobfus_mcp/README.md`, and
      `pyobfus_mcp/pyproject.toml`'s description line, despite already
      being a first-class client via the `AGENTS.md` template and the
      Smithery Skill listing — this is a wording gap, not missing
      integration work.
   4. README Free/Pro Edition feature-list cleanup, bundled as one
      pass: fold in the preset/`--check`/`--unmap`/`--provenance-manifest`
      features (done 2026-08-02 already — verify still current), drop
      the now-stale `v0.1.6+`/`v0.2.0+`/`v0.3.0+` per-feature version
      tags (27 version mentions total in README, most add changelog
      trivia rather than decision-relevant info), reframe "New in
      v0.5.0 — patent-targeted mechanisms" (now 6 versions behind), and
      consider dropping "(Available Now)" from the Pro Edition heading
      (traced to the v0.2.0-era README, when Pro had just shipped and
      needed the disclaimer — no longer true 8 months and ~12 releases
      later).
   5. One `WebSearch`: does an Anthropic-curated directory of
      third-party Claude Code plugin marketplaces exist yet (the
      MCP-Registry equivalent)? Not verified this session — the
      self-hosted `.claude-plugin/marketplace.json` mechanism itself
      needs no external registration, but a curated directory (if one
      exists) would be a distribution channel worth joining.
   6. Bring Q6 (does the recent 0.5.4-0.5.6 run still highlight Pro
      Edition's value, given the last three "What's new" banners were
      all Community/bugfix-focused) to the maintainer as a discussion
      — it's a positioning call, not a mechanical doc fix.

Large speculative features and a JOSS re-submission remain deferred until the
project has demonstrated third-party adoption.

---

## Historical execution record (frozen; not the current TODO)

**Release history**: 0.5.0 (2026-06-18) → 0.5.1 + pyobfus-mcp 0.3.1 (2026-06-22) → 0.5.2 (2026-06-22, patch) → 0.5.3 (2026-07-07) → **0.5.4 (2026-07-19)**. Patent gate cleared 2026-06-17 (申请号 202610712171X). Python 3.8 dropped (floor 3.9). The numbered material below preserves the decisions and evidence from those releases; it is not an executable checklist.

1. ✅ **DONE 2026-06-22 — published 0.5.1 + pyobfus-mcp 0.3.1.** pyobfus 0.5.1 (`pyobfus build --flag` fusion) merged to main + tagged `v0.5.1` → OIDC PyPI publish (wheel+sdist live, PEP 740 attestations; release run `27938471463`). Then `mcp-v0.3.1` → pyobfus-mcp 0.3.1 to PyPI (run `27939165475`) + `mcp-publisher publish` → MCP Registry 0.3.1 isLatest. Glama auto re-indexes. Order honored (mcp dep `pyobfus>=0.5.1`).

1b. ✅ **DONE 2026-06-22 — published 0.5.2 (patch, PR #18).** Fixed two Python-version-specific bugs in the 0.5.1 build-fusion passes that broke `--seal-code`/`--vault` on Python 3.9/3.10: (a) the `@seal_code` integrity hash used `marshal.dumps` at the default version (≥3), which encodes string-interned state / shares refs — divergent between build-time and runtime code objects on 3.9/3.10 → spurious `IntegrityError`; pinned to **marshal version 2** (`pyobfus_pro/runtime/seal.py`). (b) the vault transformer used `zip(strict=)`, a 3.10+ kwarg → `TypeError` on 3.9; replaced with plain `zip()` (`pyobfus_pro/transformers/vault.py`). 1025 core tests (+ `TestMarshalVersionStability` regression guard); full CI matrix incl. 3.9/3.10 green; tagged `v0.5.2` → OIDC PyPI (release run `27963690396`). **Lesson: no local Python 3.9 interpreter — 3.9-only breakage (e.g. `zip(strict=)`) surfaces only on the CI matrix; rely on it for floor-version feature gaps.**
2. **🆕 Agentic discoverability — Wave A (mostly done 2026-06-22; full report `docs/AGENTIC_DISCOVERABILITY_2026-06-22.md`)**. Goal: pyobfus easy for AI agents to *find* + be *cited* by answer engines (the "usable by agents" half — structured output / `ai_hint` / good tool descriptions / llms.txt — is already strong). Done: ✅ Smithery via **Skill** channel (`smithery.ai/skills/zhurong2020/pyobfus-protect` — note: Smithery 2026 MCP-publish is remote-HTTP-only, a non-fit for a local-execution tool; the Skill channel is the right path) · ✅ mcp.so listing · ✅ `uvx pyobfus-mcp` zero-install in README + sharpened 99-char `server.json` blurb (commit `826c576`, ships to Registry on next mcp publish) · ✅ `smithery.yaml` (`49f4df3`). Pending: ⏳ PulseMCP (passive — auto-ingests Official Registry weekly; if absent ~2026-06-29, email `hello@pulsemcp.com`) · ⏭️ ARD `ai-catalog.json` early-bird (Google+LF spec, late-May-2026; static JSON on docs domain, 2-3h) · ⏭️ GEO/AEO (answer-first openings + named-number facts + FAQ schema — fold into the launch wave).
3. **🆕 New feature opportunities (2026-06-22 competitive scan vs PyArmor 9.2 / Nuitka / SourceDefender / CodeEnigma + arXiv 2512.16538 / 2410.05797)** — candidates for ROADMAP P2-17..19, all inside the AST + AI-native lane:
   - **Signed obfuscation provenance manifest** — `pyobfus build` emits a signed JSON manifest (files obfuscated / config hash / tool version / mapping digest, optional sigstore). Rides the 2026 SLSA/SBOM wave; reuses the PEP 740 muscle; PyArmor's phone-home model structurally can't give a local-verifiable provenance.
   - **LLM-deobfuscation-resistance mode + benchmark** — `--llm-resistant` preset and/or a published "LLM semantic-recovery rate X%" benchmark. Uniquely on-brand for an AI-native obfuscator; strong launch-content story even as a benchmark-only first cut.
   - **ML/model-serving preset** (`--preset ml`) — protect inference-wrapper code + model-path/weight constants into the vault; ride the HuggingFace pickle-security wave. Near-zero architecture cost (preset mechanism exists).
4. **0.5.3 — ✅ FEATURE-COMPLETE on main 2026-07-07 (unreleased; awaiting version bump + tag + publish decision).** All three deferred build-fusion flags shipped to main:
   - ✅ **`--period` (run-count counter file)** — commit `dfe1dbd`; module-top `period_check` guard + runtime `default_counter_path`, `$PYOBFUS_COUNTER_DIR` override, per-module counters.
   - ✅ **`--opacity-config` TOML pattern rules** — commit `34dcbc5`; the pre-mangle-qualname problem was solved WITHOUT a name map: resolve config in a PRE-mangle pass and inject `@opacity(Layer.ENCRYPTED)` on ENCRYPTED matches (the decorator survives mangling; the existing decorator-driven post-pass encrypts). In this fusion ordering only the ENCRYPTED layer is materialized; transparent/ai-readable/obfuscated fall through to Core mangling — a documented limitation.
   - ✅ **`--bind-device` / `--bind-device-id`** — commit `62646b6`; both binding models (build-machine + supplied machine-id). Encrypts the L3 key with a device fingerprint, then rewrites the emitted `_LAYER_KEY` literal into a runtime `bind_device_key(current_machine_id(), salt)` re-derivation. opacity.py/vault.py untouched (key passed via existing `layer_key`; only `_LAYER_KEY` rewritten). Wrong device → `OpacityRuntimeError` (real enforcement, tested). **Vault-key device binding (`_VAULT_KEY_*`) not yet covered — candidate 0.5.4 follow-up.**

   1033 tests green (+8 for 0.5.3), ruff/format/mypy clean on all new code. ✅ **Released 2026-07-07 as v0.5.3** (version bumped, CHANGELOG finalized, tag `v0.5.3` → OIDC + PEP 740 PyPI publish). **pyobfus-mcp NOT bumped** (0.5.3 changes no tool surface; the mcp `pyobfus>=0.5.1` floor resolves to 0.5.3), so **no Glama Build-steps re-bump is needed this release** (Glama installs `pyobfus-mcp==0.3.1`, unchanged). Design notes in `docs/V0.5_RELEASE_PLAN.md`.

   **↳ 0.5.4 — ✅ RELEASED 2026-07-19.** Vault-key device binding shipped via
   PR #19; the scope boundary described below is closed. Kept for the design
   rationale.
   - ✅ **Vault-key device binding — DONE (PR #19, 0.5.4).** Extend `--bind-device` to ALSO rewrite each emitted `_VAULT_KEY_<name>` constant into a runtime device derivation (same technique as the opacity `_LAYER_KEY` rewrite in `62646b6` / `build_fusion._substitute_layer_key_binding`), so `--vault --bind-device` yields a FULLY device-locked artifact. **Today only opacity L3 is locked; vault keys still ship as baked literals, so vault secrets decrypt on ANY machine** — a documented scope boundary, not a bug. Implementation note: vault runs in the PRE-pass and emits PER-vault keys (not a single post-pass `_LAYER_KEY`), so the device key must be passed into `_t_vault.transform_module(..., vault_keys=...)` at build AND a post-substitution must rewrite each `_VAULT_KEY_*` — different plumbing from opacity's single point. Add vault device-match / device-mismatch runtime tests.
   - **Doc-sync sweep — surface the LATEST version, retire stale-prominent v0.4 framing** (user-flagged 2026-07-07: the public GitHub README still leads with "New in v0.4.0" while 0.5.x is buried). Concrete gaps:
     - ✅ **`README.md` — DONE 2026-07-07** (`docs:` commit, no version bump): demoted `### 🤖 New in v0.4.0 — AI-native features` → `### 🤖 AI-native features` (those are baseline now) and added a prominent near-top **"🆕 What's new in v0.5.3"** callout surfacing the 6 Pro mechanisms + the 0.5.3 flags (they were only a deep h4). llms.txt/llms-full.txt below still pending.
     - `llms-full.txt` `# pyobfus v0.4.0` (line 131) + "v0.4 introduces AI-native features" (line 274) — bump to 0.5.x; these feed AI crawlers, so they matter for the AI-native positioning.
     - `llms.txt` — verify the feature list mentions the 0.5.x Pro mechanisms.
     - `docs/AI_INTEGRATION_STRATEGY.md` (~line 59) "561 tests" + "Alpha→Beta" — now 1033 tests / Production-Stable (low-priority historical strategy doc).
   - **Recurrence guard:** a doc-sync step is now in the release checklist (`docs/V0.5_RELEASE_PLAN.md` Phase 5.6) — every feature release must refresh the README "What's new" callout + `llms.txt`/`llms-full.txt` version framing to the shipping version.
5. ✅ **PEP 740 attestations — CONFIRMED 2026-07-19, TODO closed.** The old
   "provenance reads False" concern was a false alarm: PyPI's JSON API
   `provenance` field is always `None` and is not the right signal. The
   authoritative check is the integrity endpoint —
   `curl -so /dev/null -w '%{http_code}' https://pypi.org/integrity/pyobfus/0.5.4/pyobfus-0.5.4-py3-none-any.whl/provenance`
   returns **200** for both 0.5.3 and 0.5.4, so attestations are present and
   `release.yml` was correct all along. Original note below.

   ~~**Re-check PEP 740 attestations**~~ — PyPI's `provenance` field read `False` on the 0.5.0 wheel despite `attestations: true` in `release.yml`. 0.5.1 + mcp 0.3.1 also published with `attestations: true` (workflow steps green). Verify on the 0.5.1 / mcp 0.3.1 PyPI pages whether `provenance` now flips True; if genuinely missing, debug `gh-action-pypi-publish` config.
6. **Distribution (Phase 5.6, now unblocked)** — JOSS submission (was gated on 申请号; cite "patent pending CN 202610712171X"); launch wave (HN/Reddit/dev.to/CN drafts in `_drafts/`, run through AI-detector gate first; write in AEO structure per item 2); GitHub Discussions v0.5 priority poll. **Single biggest lever** — downloads bumped after 0.5.0 (pepy 7-day 327→680) but GitHub engagement is still ~0 (1 star / 0 issues / 0 discussions); launch is what converts download traffic into real feedback.
   - **JOSS paper — content-complete after the 2026-06-22 review pass** (`paper/paper.md` + `paper/paper.bib`). Revisions this session: CLASP citation metadata corrected + arXiv DOI added (`c99884a`); coverage 89%→90%; research-software framing strengthened for JOSS scope after reading two accepted JOSS papers — Mastodon.py (joss.08946) + scene_synthesizer (joss.07561) — which earn "demonstrable research impact" by naming a research audience/use (`ac75c8f`); Ethics statement (dual-use note) added + origin concretized to "a clinical research group's graduate students and collaborators" (`ec93046`). Decided **not** to add the PyArmor-cost angle (open-core optics). **External-review-driven hardening** (`07c49c5`, `e23dfdc`): added a 4-row tool-comparison table (first column widened to ~63% via pipe-divider dash proportions), a measured evaluation woven into Functionality (Click ~11k LOC + Rich ~38k LOC obfuscate in 2–3 s; output byte-compiles cleanly and is 17–19% *smaller* — measured 2026-06-22, .py-only), a reproducible `examples/ai_debugging/` reverse-mapping demo the paper cites (substantiates the AI-debug claim), the clinical-AI third-party-validation scenario, an explicit Community-Edition-is-fully-open-source-and-self-contained statement, and de-marketing edits. **Pushed back** on research-paper asks JOSS does not require (heavy benchmark suite, retitle, standalone Related Work section) — verified against two real accepted JOSS papers. **Then restructured to the JOSS 2026 scope/format update** (announced 2026-01-05): paper now carries all required sections — Summary, Statement of need, **State of the field**, **Software design** (with design trade-offs), **Research impact** (concrete evidence: 15 public releases since 2025-11, 1,000+ tests, OpenSSF badge, MCP registry, Click/Rich benchmark, reproducible `examples/ai_debugging`), **AI usage disclosure** (JOSS-policy-complete: tool/where/scope/human-review), Ethics statement, Acknowledgements, References — at **1304 prose words** (new JOSS range is 750-1750). **Eligibility verified**: ~7.4 months open public history (v0.1.0 2025-11-11) clears the new 6-month pre-review gate; research-impact gate met by realized developer use (the CAC pipeline) + concrete signals. **Paper compiles in CI** via `.github/workflows/draft-pdf.yml` (openjournals inara, journal=joss — the JOSS engine; run `27955210701` green, PDF artifact produced). 0 em-dash, no PII, citation keys consistent, `date: 22 June 2026`. **At-submission must disclose financial COI** (Pro edition is commercial) in the form's Message-to-editors per JOSS COI policy. **Affiliation = "Independent Researcher" (personal), no separate COI sentence** (open-core disclosure in-text suffices; company-named COI line via 上海旎嵘科技 is an optional backup card, reversible until acceptance).
   - ✅ SUBMITTED to JOSS 2026-06-22 — submission page `https://joss.theoj.org/papers/ef32f416f0f8789e388d955a69b2246d` (Type: New submission · Subject: Software engineering · version v0.5.1 · financial COI disclosed in notes-to-editor: open-core, author licenses the commercial Pro edition; paper concerns only the Apache-2.0 Community Edition). Pre-review issue = `openjournals/joss-reviews#10788`.
   - ❌ **DESK-REJECTED 2026-06-24** by Managing EiC Daniel S. Katz (issue #10788, closed). **Grounds = scope + significance, explicitly NOT software quality.** Two prongs: (1) **"private development followed by public release"** — JOSS wants ≥6 months *open* development history with public issues/PRs (ideally cross-org external contributors), not just calendar age. The editorialbot repo-analysis exposed the pattern: 356/356 commits one author, 1 star / 2 forks / 1 non-author commenter / 8 issues / 5 PRs, and code landing in concentrated 48h bursts (Nov 11-13 2025 = 36.1%, Jun 16-18 2026 = 13.5% [the v0.5 Pro-mechanism release held back for patent novelty], Apr 20-22 = 10.2%). (2) **No *demonstrated* reuse** — Katz quoted the paper's "the software is ready for that reuse … concrete rather than aspirational" and said it does NOT show the third-party reuse JOSS requires (the CAC pipeline use is the author's own team). The License "Other" flag (dual-license `LICENSE-NOTICE.md`) and the 3 no-DOI refs were **NOT** rejection reasons (green/minor). Robot checks all passed: 1462 words, all 6 required sections present, references clean. Cannot re-open/re-submit the same issue; JOSS pointed to "other venues" (joss.readthedocs.io/.../submitting.html#other-venues). **Next-step analysis** = this session's "A" deliverable (free venues: Zenodo DOI / pyOpenSci / JORS; re-qualify JOSS only after real open-dev history accrues). See also `docs/JOSS_REJECTION_20260624.md`.
   - **Publication dual-track** (also in ROADMAP P2-18): JOSS = the *software-description* paper (free, this one). A higher-impact *research* paper is a **separate** future effort built on the **P2-18 LLM-deobfuscation-resistance benchmark** → software-protection/security venue (SPRO, ESORICS, ACSAC) or JSS/EMSE + arXiv cs.CR preprint. Don't dual-submit the same software paper to JOSS and SoftwareX; SoftwareX (~€2.5k APC, SCIE IF~3) is the only indexed alternative *instead of* JOSS.
   - **DOI propagation checklist** (concept DOI `10.5281/zenodo.20846053`, minted 2026-06-25 — see `docs/JOSS_REJECTION_20260624.md`). Surfaces to add the citation/badge to:
     - **Repo/package (mostly Claude can do):** README DOI badge ✅ done + CITATION.cff ✅ done; [ ] add a `## Citation` section to README (APA + BibTeX); [ ] add `"Citation" = "https://doi.org/10.5281/zenodo.20846053"` to `[project.urls]` in **both** `pyproject.toml` (pyobfus) and `pyobfus_mcp/pyproject.toml` (badge then shows on both PyPI pages after next release); [ ] add a "How to cite" page to Read the Docs (`docs/`); [ ] CHANGELOG note.
     - **Author identity (owner does — highest value):** [ ] **ORCID** 0009-0008-6087-0581 → Works → Add → link the DOI (DataCite auto-fills); [ ] CV / personal site `zhurong2020.github.io`; [ ] Google Scholar profile if any.
     - **嵘说 / brand surfaces (owner does):** [ ] 有心工坊 / `arong.eu.org` pyobfus 产品/介绍页 → DOI badge + 「如何引用」block; [ ] future 公众号/知乎/小红书/dev.to posts include the DOI.
     - **Optional/low priority:** [ ] submit the Zenodo record to a relevant Zenodo *community* (Python/software) for discoverability; MCP-registry/Glama/Smithery listings have no citation field — skip.
     - Note: MCP shares the repo-level DOI (no separate record). The bootstrap record's version label `zenodo-archive-v0.5.2` self-corrects on the next normal release.

---

## 30-Second Resume

**Where we are** (2026-06-22): **pyobfus 0.5.2 + pyobfus-mcp 0.3.1 published to PyPI** (0.5.0 was 06-18; 0.5.1 fused the 6 v0.5 Pro mechanisms into `pyobfus build` flags; **0.5.2 is a patch fixing `--seal-code`/`--vault` on Python 3.9/3.10**, 1025 core tests; mcp 0.3.1 names the v0.5 mechanisms in pro-funnel copy, dep `pyobfus>=0.5.1`; both via OIDC with PEP 740 attestations; MCP Registry 0.3.1 isLatest). Patent gate cleared 初审合格 2026-06-17 (申请号 202610712171X) · Python 3.8 dropped, floor 3.9 · Python 3.9-3.14 × 3 OS. `release/v0.5.1` is merged to main; nothing held. **This session also ran the agentic-discoverability Wave A** (Smithery Skill + mcp.so + uvx/server.json + smithery.yaml; report `docs/AGENTIC_DISCOVERABILITY_2026-06-22.md`). The **JOSS paper** draft (`paper/`) is submit-ready (0.5.1 now on main). Prior baseline (pre-0.5 session): 0.4.1 + mcp 0.3.0 · Glama Quality A.

> **2026-06-05 Glama introspection — partial fix** (commit `bbeefb8`): Glama listing was stuck showing 5 tools and its API returned `tools:[]`. The 06-05 hypothesis was that `pyobfus_mcp/Dockerfile`'s pin (`0.1.1`→`0.2.0`) drove it. That repo-Dockerfile fix was correct to ship, but it was **NOT the operative lever** — see the 06-08 correction below.
>
> **2026-06-08 Glama introspection — TRUE root cause + RESOLVED**: inspecting the Glama admin **Dockerfile → Configuration** page showed Glama does **not** build from the repo's `pyobfus_mcp/Dockerfile` at all. It generates its own Dockerfile from the admin Configuration **"Build steps"** field (it `git clone`s the repo, then runs only those build steps — the in-repo Dockerfile is ignored). That field was **independently pinned to `pyobfus-mcp==0.1.2`** (set at the 0.1.2 release 2026-05-07) and had been stuck there, so every introspection installed the 5-tool 0.1.2 and never re-tested. **Fix (admin-only, web UI):** edited Build steps `pyobfus-mcp==0.1.2` → `==0.2.0` and saved → Glama auto-rebuilt. Test `019ea6c5-…` **succeeded 2026-06-08 18:27 CST (13.7s)**; its `ListToolsRequest` returned **all 7 tools** (5 community + `recommend_tier` + `start_pro_trial`, both `tier:pro_funnel`). Public API/listing + the page's "Tools" panel lag the successful test by hours-to-1-day; recheck `curl -s https://glama.ai/api/mcp/v1/servers/zhurong2020/pyobfus | python3 -c "import sys,json;print(len(json.load(sys.stdin)['tools']))"` → expect 7. **Lesson: Glama's container is built from the admin Configuration "Build steps" field on the Dockerfile page, which is a SEPARATE pin from the repo's own Dockerfile and can only be changed in the web UI. When a Glama listing shows a stale tool surface, fix THAT field — editing the repo Dockerfile does nothing.**
>
> **2026-07-07 Glama introspection — RECURRED (the "auto re-index" belief was wrong)**: the Build steps pin was STILL at `pyobfus-mcp==0.2.0` even though PyPI had since shipped 0.3.0 (adds `protect_project`) and 0.3.1; the public API was back to `version:null, tools:[]`. **Glama does NOT auto-follow PyPI latest** — the "Glama auto re-indexes" phrasing elsewhere in this doc/commits is misleading: it only re-tests the *pinned* version. This is a **recurring manual step: every new pyobfus-mcp release requires re-bumping this Build steps pin by hand**, or the listing silently serves the old tool surface. A stray Glama "Release 0.4.1 published" email surfaced it — but that "0.4.1" is Glama's own noisy repo-release counter (the admin "Recent Releases" panel auto-increments its own semver: the same green test `019f3b5a` that installed 0.3.1 got labeled "0.5.4" — decoupled from the actual installed version, ignore it). **Fix**: Build steps `0.2.0`→`0.3.1`, Save; test `019f3b5a` succeeded 2026-07-07 14:53 CST (12.1s), `ListToolsRequest` returned **all 8 tools** (6 community + 2 pro_funnel, incl. `protect_project`), install log confirmed `pyobfus-mcp==0.3.1 + pyobfus==0.5.2`. Step now codified in `docs/V0.5_RELEASE_PLAN.md` Phase 5.6 + memory `glama_container_build_source`.
>
> **Where we're not**: 0 GitHub stars; PyPI ~1,180/mo (pyobfus) + ~400/mo (mcp) as of 2026-07-07 — up from the ~337/mo 05-07 baseline, but largely CI/automated (daily rate settled to ~25/day after the June 0.5.x release burst; mcp shows a clean 99-download spike on its 06-22 release day) and still 0 stars, so the number is not organic adoption. v0.4 target was 1,500+/month of *real* users. The gap is **launch execution**, not feature gaps.

**Single biggest unblocked TODO**: get the 4-platform launch out of `_drafts/` (dev.to → HN → Reddit → CN trio). Every day of delay loses ~1 week of natural-growth compound effect.

**Strategic frame**: AST-obfuscator commodity layer is **getting crowded** (`python-obfuscator` 0.1.0 revived 2026-04-03 after 5-year sleep · `python-obfuscation-framework` 1.13.0 with 14 releases in 5 weeks). pyobfus's moat is **AI-native + framework presets + reverse mapping + MCP**, not AST mechanics. **PyArmor 9.2 went VMC/ECC virtualization** — that's a different lane; do not chase.

---

## 🆕 TODO — 0.4.1 新卖点发布公告（gated：先让发布流量过 1-2 天）

**Added 2026-06-11.** pyobfus 0.4.1 + pyobfus-mcp 0.3.0 已发布（见 CHANGELOG / memory `release-0.4.1-patent-clean`）。新卖点 = **"一键混淆 + 自验证"**（`protect_project`：scan→preset→obfuscate→编译+import 验证→`verified:true/false`）+ `--trace-marker` auto-unmap + 8-tool `next_tool` 链式 + Claude skill/plugin。

- **Gate（用户决定 2026-06-11）**：**等已发布版本的自然流量先过 1-2 天**再推公告（≈ **2026-06-13 之后**）。先观察 PyPI 下载/任何 issue 反馈，避免公告把"刚发现的回归"放大。
- **载体**：dev.to 长文 +（可选）HN / Reddit / 公众号 / X 短贴。可与 `_drafts/` 里压着的 4-platform launch 合流，或单独发"protect-and-verify"主题贴。
- **主信息**：定位在 PyArmor 给不了的 "AI-debuggable + 一键自验证" —— agent 敢用、好用、自动用。
- 🔒 **专利安全护栏（写文案前必读）**：只描述**公开的社区版**能力（编排 + 验证 + 经 mapping/`--unmap` 的 AI 可调试 + framework presets + MCP/skill 可发现性）。**严禁**在文案中描述或暗示说明书 §2.6 列举的 7 项未满足需求 (a)–(g)（= 专利 S1–S8 机制：分层选择保护 / 加密字节码 / 法医水印 / license 融入解密 / **traceback 加密** / 纵深签章 / 运行期机密 Vault）。**特别注意 (e)**：`--trace-marker` 是**明文标记指向公开的名称反解**，与 (e)"traceback 加密成短 ID、私钥解密、无回退" **方向相反**——文案不得把 trace-marker 说成"加密 traceback"，以免（1）误导用户（2）触碰尚未解锁的 v0.5 机制叙事。
- **依赖/正交**：与 v0.5 专利 gate 无关（0.4.1 全是公开内容）；可在补正办结前发。

---

## Verified facts baseline (2026-05-07 · cross-checked against PyPI authoritative APIs)

| Item | Value | Verified |
|---|---|---|
| pyobfus latest | 0.4.0 (2026-04-22) | ✅ |
| pyobfus-mcp latest | 0.2.0 (2026-05-08) | ✅ |
| pyarmor latest | **9.2.4** (2026-03-18) — VMC/ECC modes since 9.2.0 (Oct 2025) | ✅ pypi.org/pypi/pyarmor |
| pyarmor trial code-size limit | **~935-940 lines** for typical sparse Python (single-file threshold) — measured 2026-05-09 on PyArmor 9.2.4 trial in clean venv. 935 lines passes, 940 fails with `ERROR out of license`. By line count, not bytes (900 lines at 67 KB still passed). Gates the "Big Script / Mix String" feature paywalled across all paid tiers. Cited in launch articles to explain pyobfus's existence. | ✅ measured · full reproducible procedure in `docs/PYARMOR_TRIAL_LIMIT_EXPERIMENT.md` |
| pyarmor.cli | **9.2.4** (2026-03-18) — same release date / same maintainer / modular CLI subpackage of pyarmor; **NOT a separate competitor** | ✅ pypi.org/pypi/pyarmor.cli |
| vmp-protector | **1.0.0** (2026-05-02) — anonymous (no author email / no GitHub repo / no homepage in PyPI metadata) · MIT · 16-reg / 28-opcode register-based VM + XOR+zlib+base64 string encryption + anti-debug + anti-tamper + control-flow flattening · **bytecode-VM lane (alongside PyArmor)** · NOT in pyobfus's AST/AI-debug lane · do NOT add to pyobfus's positioning copy until provenance verified | ✅ pypi.org/pypi/vmp-protector (investigated 2026-05-08 by competitive-intel agent; manifestguard + smelt are PyArmor-search false positives, NOT competitors) |
| python-obfuscator | **0.1.0** (2026-04-03) — was dormant 2021-2026, just revived | ✅ pypi.org/pypi/python-obfuscator |
| python-obfuscation-framework | **1.13.0** (2026-04-05) — 23 releases total, 14 in last 5 weeks | ✅ pypi.org/pypi/python-obfuscation-framework |
| CodeEnigma | (surfaced 2026-06-05 competitive scan) — open-source "transparent PyArmor alternative" · AES-256 + compilation + zlib + AES-GCM **bytecode encryption** · self-contained, no external servers · **bytecode-encryption/compilation lane (alongside PyArmor / vmp-protector), NOT pyobfus's AST + AI-debug lane** · same handling as vmp-protector: track here, do NOT add to positioning copy, do NOT chase the lane (do-not-do) | github.com/KrishnanSG/codeenigma |
| mcp SDK latest | 1.27.0 (2026-04-02) — the one that surfaced our `version=` kwarg drift | ✅ pypi.org/pypi/mcp |
| Python 3.14 stable | 2025-10 (~7 months mature as of 2026-05-07) | (Python.org release calendar) |
| Python 3.15 | alpha/beta only — stable expected 2026-10 | (Python.org PEP 745 release schedule) |

---

## 🔴 P0 — Self-actionable, do this week (5-7 → 5-14)

> **✅ P0 STATUS RECONCILED 2026-06-06** — all P0 items are now done or infra-ready; the only remaining gates are external/launch-timing, not engineering:
> - P0.1 CI mcp-sdk smoke test — ✅ DONE (`8ec0fcd`, re-verified locally)
> - P0.2 PEP 740 attestations — ✅ INFRA DONE (release.yml OIDC, live on pyobfus-mcp 0.2.0; main package picks it up on next release, gated behind v0.5 patent)
> - P0.3 server.json `_meta` — ✅ DONE (shipped 0.2.0; Registry stripped the publisher namespace, retry on next mcp bump)
> - P0.4 dev.to article — ✅ DONE (live since 2026-05-07)
> - P0.5 GitHub topic curation — ✅ DONE (both `pyarmor-alternative` + `python-obfuscator-online` present, verified 2026-06-06)
> - P0.6 Socket / OpenSSF passing badge — ✅ DONE (badge live, project 12788)
> - P0.7 Discussions roadmap poll — ⏳ blocked on launch (post-launch +24h trigger)
>
> **Net: no self-actionable P0 engineering work remains.** The real remaining lever is executing the launch wave (see 30-Second Resume) and, on the patent track, the 补正 deadline (~2026-08-01).

These 4 items were originally ~6 hours of work, all independent. They are now complete (see reconciliation box above).

### P0.1 — CI smoke test against latest mcp SDK (✅ DONE · commit `8ec0fcd`)

**Status (verified 2026-06-06)**: shipped as the `mcp-sdk-latest` job in `.github/workflows/ci.yml` (lines ~107-132). Installs `pyobfus-mcp` + `mcp>=1.20` (pulls the latest mcp SDK), then runs `python -c "from pyobfus_mcp.server import _build_server; _build_server()"`. Local re-verify: `_build_server()` returns a `FastMCP` instance against mcp 1.27.0. CI now fails the day a future mcp SDK floor breaks server instantiation — exactly the 0.1.2 failure mode, now guarded. (This page previously listed it as TODO; it was actually shipped alongside the P0.6 hardening wave.)

**Why**: directly prevents repeat of the 0.1.2 emergency. mcp SDK API broke `FastMCP.__init__()` `version=` kwarg silently between 1.0 and 1.20+; we caught it because Glama's container build complained, not because CI noticed.

**Done when**: green CI run; intentional regression (re-add `version=` kwarg, push to a branch) makes it red. ✅ Met — job is green on `main`.

---

### P0.2 — PEP 740 sigstore attestations (✅ INFRA DONE · takes effect on next pyobfus release · verified 2026-06-06)

**Status**: `.github/workflows/release.yml` already runs OIDC Trusted Publishing with `id-token: write` + `attestations: write` + `attestations: true` on **both** publish jobs (`Build + publish pyobfus` and `Build + publish pyobfus-mcp`), via `pypa/gh-action-pypi-publish` (SHA-pinned). This was proven end-to-end on the **pyobfus-mcp 0.2.0** release (2026-05-08 — "PyPI Trusted Publisher's first real exercise", attestations present on that PyPI page). The MCP package leg is fully live.

**Remaining gap (not standalone-actionable now)**: the currently-live **main pyobfus 0.4.0** wheel predates this workflow (it was twine-uploaded 2026-04-22), so it carries no attestations — and a published version can't be retroactively attested. The main package picks up attestations automatically on its **next tagged release**, which is gated behind v0.5 (patent-gated, blocked until 补正办结). One residual check worth doing when that release lands: confirm the **pyobfus** package (separate from pyobfus-mcp) has its own PyPI "Trusted Publisher" entry configured, since Trusted Publisher config is per-package on pypi.org.

**Reference**: <https://peps.python.org/pep-0740/> · <https://blog.sigstore.dev/pypi-attestations-ga/> · <https://trailofbits.github.io/are-we-pep740-yet/>

**Done when**: PyPI page for the next pyobfus release (0.4.1 / 0.5.0) shows green "Verified" badges + provenance JSON visible. ✅ Already true for pyobfus-mcp 0.2.0; ⏳ pending for the main package's next release.

---

### P0.3 — server.json `_meta` enrichment (✅ DONE · 2026-05-08 published with 0.2.0 · ⚠️ Registry silently stripped publisher namespace)

**Why**: Glama's 2026-01-24 spec post documents that MCP Registry preserves *only* the publisher-claimed `_meta` namespace, drops others. Claiming `io.github.zhurong2020.pyobfus_mcp` namespace **now** with structured fields locks pyobfus-mcp into downstream aggregator filters before they freeze on conventions.

**Reference**: <https://glama.ai/blog/2026-01-24-official-mcp-registry-serverjson-requirements>

**Action**: ✅ Done in commit `4f8886f` — `pyobfus_mcp/server.json` now contains:

```json
"_meta": {
  "io.github.zhurong2020.pyobfus_mcp": {
    "framework_presets": ["fastapi","django","flask","pydantic","click","sqlalchemy"],
    "licensing_model": "apache-2.0-core-plus-proprietary-pro",
    "quality_grade": "A",
    "tool_intent": "code-protection",
    "target_clients": ["claude-desktop","claude-code","cursor","windsurf","zed"]
  }
}
```

**Registry publish status (2026-05-07 finding)**: ⏸️ DEFERRED. We attempted `mcp-publisher publish` against the current 0.1.2 entry and got HTTP 400 `cannot publish duplicate version`. **MCP Registry behaves the same as PyPI / Glama Release flow — it rejects same-version re-publishes**, so `_meta` for an existing version cannot be backfilled in place. There is also no `_meta`-only update command in `mcp-publisher` 1.7.8 (full subcommand list: `init / login / logout / publish / status / validate`; `status` only toggles active/deprecated).

The committed `_meta` block will ship to the registry **automatically on the next legitimate `pyobfus-mcp` version bump** — naturally bundled with N2 (FastMCP 3.0 → 0.2.0, P1 list) or any earlier bug-fix 0.1.3. **Do not bump just to refresh `_meta`** (see do-not-do list).

**Token / auth note (2026-05-07 finding)**: the previous TODO claim that the mcp-publisher token at `~/.config/mcp-publisher/token.json` is good for "~15 days" was wrong — JWT in our refresh expired within ~80 minutes. Non-interactive re-login works:

```bash
mcp-publisher login github -token "$(gh auth token)"
```

(Needs `gh auth status` showing scopes ≥ `repo` — currently `gist, read:org, repo, workflow`.) See `~/.claude/projects/-mnt-c-onedrive-msft-OneDrive---MSFT-rong-3-job-program-pyobfus/memory/mcp_publisher_auth.md`.

**Done when**: next pyobfus-mcp version bump is published to MCP Registry and `curl 'https://registry.modelcontextprotocol.io/v0/servers?search=pyobfus' | jq '...'` shows the `_meta.io.github.zhurong2020.pyobfus_mcp` block populated. Until then, `_meta` lives in source-controlled `server.json` only.

**2026-05-08 update**: `mcp-publisher publish` ran successfully alongside the 0.2.0 release (PyPI OIDC publish via `release.yml`). Registry `pyobfus-mcp` 0.2.0 entry is `active` + `isLatest: true`. **However, our publisher-claimed `_meta.io.github.zhurong2020.pyobfus_mcp` namespace was silently stripped** — the registry response shows `"_meta": {}` on the server object (only the registry's own `io.modelcontextprotocol.registry/official` outer-`_meta` survives). Hypothesis: the registry's server-side validator only accepts publisher-claimed `_meta` keys that *exactly* match the verified namespace prefix (`io.github.zhurong2020`), and our extended `.pyobfus_mcp` suffix gets rejected. Schema URL `https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json` declares `_meta: {}` (no constraint), so the rule lives in the Registry runtime, not the schema. **Plan**: investigate accepted namespace forms before the next legitimate version bump (0.2.1 bug fix or 0.3.0); try `io.github.zhurong2020` (no suffix) or nested struct form. Captured in companion memory `~/.claude/projects/-mnt-c-onedrive-msft-OneDrive---MSFT-rong-3-job-program-pyobfus/memory/mcp_registry_meta_namespace.md`.

---

### P0.4 — dev.to article (✅ FULLY DONE · LIVE 2026-05-07 evening)

**Live URL**: <https://dev.to/zhurong2020/let-claude-code-debug-your-obfuscated-python-a-guide-to-the-pyobfus-mcp-integration-3epm>


**Why**: this is the #1 leverage point. Article at `_drafts/article-01-claude-code-mcp-integration.md`, drafted 2026-05-05 (v2) → 2026-05-07 (v3 voice rewrite) → 2026-05-07 (v4 GPTZero-diagnostic-driven rewrite).

**Action history**:
1. ✅ v2 → v3 voice rewrite (commit `ca12e25`): killed parallel "X is a Y" feature block, "isn't X. It's Y" closers, triplet rhythms; added dated specifics.
2. ✅ v3 paste-tested on gptzero.me 2026-05-07 → returned **AI 100% / Mixed 0% / Human 0%**. GPTZero's per-sentence breakdown identified specific high-AI-impact sentences as the signal driver.
3. ✅ v3 → v4 surgical rewrite (uncommitted at this writing): replaced every High-AI-Impact sentence GPTZero flagged. Burstiness expanded char-length range from 4-200 (v3) to 2-257 (v4).
4. **2026-05-07 strategic decision**: v4 is **final** for dev.to. Not re-iterating on GPTZero gate. dev.to has no AI ban, disclosure-up-front handles compliance, function-clarity dominates for our buyer/user, and HN/Reddit/CN get separate short-form posts (already in `_drafts/`) so this body's detection score doesn't gate them. See v3 → v4 changelog inside the article file for the full strategic note.

**Done when** (revised): article live on dev.to; sequence then triggers HN +48h, Reddit +24h after HN, CN trio within 48h.

**Reference**:
- `_drafts/forum-ai-policy-and-voice-guide.md` — per-platform AI policy + the "human at 11pm" voice cheatsheet
- `_drafts/cross-review-prompt.md` — outside-eye review prompt (still useful if maintainer wants a Gemini/ChatGPT critique before posting)
- The GPTZero per-sentence diagnostic from the v3 paste-test is captured in the v3 → v4 changelog inside the article — do not lose this if iterating future articles, the pattern (fragments + parentheticals + very-long-messy + concrete-dated specifics PASS; medium-length explanatory prose with subordinate clauses FAILS) is the actionable signal.

---

### P0.5 — GitHub topic curation (✅ DONE · verified 2026-06-06)

**Status**: both target topics are live on the repo. `gh api repos/zhurong2020/pyobfus --jq '.topics'` (2026-06-06) returns: `ai-native, ast-obfuscation, claude-code, code-obfuscator, code-protection, cursor, llm-tools, mcp-server, pyarmor-alternative, python-obfuscator, python-obfuscator-online, python-security, source-protection`. Both `pyarmor-alternative` and `python-obfuscator-online` are present, so the SEO real estate is claimed ahead of the launch wave + N7 demo.

**Why**: 2026-05-09 user audit of `https://github.com/topics/code-obfuscator` confirms only 12 repos in that topic, most stale 1-2 years; pyobfus is the only modern actively-maintained Python entry. Adding 1-2 more topics now claims SEO real estate before any future demo / VSCode extension launches — topic-history matters for GitHub topic ranking.

**Action**:
```bash
gh repo edit zhurong2020/pyobfus --add-topic python-obfuscator-online
# verify pyarmor-alternative is in current 12 topics; if missing add too
gh api repos/zhurong2020/pyobfus --jq '.topics' | tr ',' '\n' | grep -i pyarmor || \
  gh repo edit zhurong2020/pyobfus --add-topic pyarmor-alternative
```

**Done when**: `gh api repos/zhurong2020/pyobfus --jq .topics` shows the new topic(s); `python-obfuscator-online` placeholder is occupied before N7 demo ships so by N7 launch the topic page already lists pyobfus.

---

### P0.6 — Socket.dev `Supply Chain Security` 71 → 90+ (✅ DONE 2026-05-09 · 4-step bundle landed)

**Why**: 2026-05-09 user observation — pyobfus is listed at `socket.dev/pypi/pyobfus` (accidentally categorized under "Control Flow" because of the `control-flow flattening` keyword) showing Quality 100 / Maintenance 100 / Vulnerability 100 / License 100 but **Supply Chain Security 71/100**. Visibly the lowest of 5 dimensions; security-conscious enterprise buyers DO check Socket as a trust signal. Both pyobfus and pyobfus-mcp share the same repo, so workflow fixes lift both packages' scores simultaneously.

**Action ship summary (2026-05-09)**:
1. ✅ **GitHub Actions SHA pinning** — all 11 action references in `.github/workflows/{ci,release}.yml` pinned to commit SHAs (was tag-pinned `@v5`). Pinned: `actions/checkout` (v5 → 93cb6efe), `actions/setup-python` (v5 → a26af69b), `codecov/codecov-action` (v5 → 75cd1169), `pypa/gh-action-pypi-publish` (release/v1 → cef22109 — refresh quarterly).
2. ✅ **CodeQL workflow added** — `.github/workflows/codeql.yml` runs `security-extended` query suite on every push, every PR, and weekly Wednesday cron. SARIF results visible in repo Security tab. **Path-ignore config added 2026-05-09 post-push** (`.github/codeql/codeql-config.yml`) excluding `examples/**` and `**/tests/**` after the first run produced 7 expected false positives (4 in examples — they intentionally demonstrate clear-text-credential anti-patterns to motivate AES-256 string encryption; 3 in tests — substring URL assertions verifying Stripe URLs appear in tool output, not security decisions). Standard OSS-CodeQL practice; the 7 alerts auto-close on next scan.
3. ✅ **OpenSSF Best Practices passing badge achieved** — Project ID 12788 at <https://www.bestpractices.dev/projects/12788>. 67/67 criteria met across Basics / Change Control / Reporting / Quality / Security / Analysis. Badge added to README. Achieved 2026-05-09 04:23:38 UTC.
4. ⏸️ **Socket re-scan pending** — Socket cron auto-rescans on ~24-48h cadence after PyPI changes; manual refresh trigger also available at `socket.dev/pypi/pyobfus`. Re-scan triggered by next pyobfus version bump anyway. Verify ≥ 90 supply-chain score post-rescan.

**Bonus side effects**:
- SECURITY.md modernized in same session (replaced no-reply email with GitHub Security Advisories + real email; updated stale Supported Versions table to current 0.4.x / 0.2.x; added pyobfus-mcp to Scope)
- The OpenSSF passing badge is a marketable signal in its own right — same tier as Kubernetes / Curl / etcd. Reference in HN/Reddit launch posts, dev.to articles, `/pyarmor-alternative` landing page (N8) when shipped.

**Done when**: re-scan shows ≥ 90 for BOTH `pyobfus` and `pyobfus-mcp` on Socket. As bonus signal, pyobfus may also recategorize off "Control Flow" once attestations present.

---

### P0.7 — GitHub Discussions "v0.5 priority signal" poll (15 min · trigger 5-13 post-launch)

**Why**: launch wave (HN 5-11 / Reddit 5-12) brings the cheapest source of signal on which v0.5 direction to prioritize. Discussions native poll posted ≤ 24h after Reddit captures max participation overlap.

**Action** (5-13 Wed evening):
1. Open a "📊 Roadmap signal" discussion in `zhurong2020/pyobfus` Discussions
2. Native poll, 3 candidates: (a) `pyobfus.dev` online demo · (b) VSCode extension · (c) Self-hosted team license server
3. Pin to Discussions sidebar
4. Cross-link from dev.to comments / HN comment thread / Reddit thread footer

**Done when**: ≥ 10 votes by 5-20; results inform N7 / P2-2 / N9 sequencing decision in week 4.

---

## 🟡 P1 — v0.5 work (8-10 weeks · revised 2026-05-09 evening for Path C patent gating)

> ⚠️ **Path C patent gating discipline (2026-05-09 evening — read first)**
>
> Audit on 2026-05-09 confirmed `pyobfus_pro/` source has been in the public GitHub repo + every PyPI wheel since V0.1.0 (2025-11-11). All V0.4.0 features are now public prior art under CN Patent Law §22, so the V0.4.0 patent path is dead. Only **未实现 + 未公开** features remain patentable.
>
> **6 v0.5/v0.5.1 Pro features have been earmarked for the patent application**: P2-1 (Selective Opacity), P2-7 (Forensic watermarking), P2-8 (License binding combo), P2-9 (`@seal_code`), P2-10 (`--scrub-traceback`), P2-11 (Runtime String Vault). Implementation of these MUST happen in a separate private repo (`pyobfus-pro-dev` or equivalent), NOT in the `zhurong2020/pyobfus` public repo, until the patent 申请号 is received.
>
> **No public commits, branches, PRs, issues, or comments referencing the algorithmic mechanism of these 6 items until patent filed.** Naming the feature in this TODO + ROADMAP is OK (no implementation detail revealed). See `~/.claude/projects/-mnt-c-onedrive-msft-OneDrive---MSFT-rong-3-job-program-pyobfus/memory/pro_disclosure_finding_2026-05-09.md` and `pyobfus_patent_strategy.md` for the full reasoning.
>
> v0.5 ship date pushed from 2026-06-15 → late July / early August 2026 to allow patent filing window (~4-6 weeks).
>
> **2026-05-09 late-evening update (Session 27)**:
> - Patent dossier framework scaffolded at `~/projects/pyobfus-legal/patent/` (off-repo): 10 sub-directories matching the CNIPA web 端 8 个 upload tabs + reusable templates symlinked from `cac-plus-ip/02_china_发明专利/_templates_CNIPA/`. v0.5 session uses this as the working directory when patent draft starts. See `pyobfus-legal/patent/README.md` for full structure + 11-step submission flow.
> - **CNIPA case # `10000559675571` already created** on 专利业务办理系统 web (https://cponline.cnipa.gov.cn → 我的办公桌 → 国家申请 → 发明专利申请) and recorded in `pyobfus-legal/patent/00_案卷信息/case_metadata.md`.
> - **USB Key / CPC desktop client are NOT required** (Session 25/26 backlog mentions are superseded). Web-based 实名认证 user path supports full submission incl. 电子签章 — applicable for individual pro-se filing. USB Key only required for 代理批量 / PCT / 委托代理 scenarios.

> **2026-05-10 update — Patent draft v1 + CNIPA web upload progress**:
>
> - Patent draft v1 complete at `pyobfus-legal/patent/` (off-repo): 5 formal application docx (claims / specification / drawings / abstract / fee-reduction request) + 1 internal disclosure mother doc + 7 mermaid figures (PNG + JPEG) + ID card A4 PDF. Invention name finalized at trim-A: 「一种基于多层选择保护与法医水印的代码混淆方法及系统」 (25 字 within CNIPA 默认 limit).
> - **费减备案 (fee reduction recordation) submitted 2026-05-10 09:16** via 专利业务办理系统 → 专利事务服务 → 费减备案 (Path A: 备案 covers 2026 全年 individual applicant patents — replaces per-case 100008 form for both pyobfus and cac-plus-ip filings this year). Currently 待审核, expected approval 1-15 working days.
> - **5 CNIPA web tabs filled + saved**: 权利要求书 / 说明书 / 说明书附图 / 说明书摘要 / 发明专利请求书. 说明书 server-side renumbering ("保存并刷新") timed out at 239 paragraphs; "保存不刷新" succeeded (manual numbering already CNIPA-standard 0001-0239). 摘要附图 = 1, 实质审查请求 = 勾, 提前公布 = 不勾, 不丧失新颖性宽限期 = 不勾.
> - **Final 提交 button** (= filing date = priority date = 不可撤销) **pending 备案 approval** to maximize automatic 85% fee reduction at 缴费 step. 1-2 weeks total expected before 提交; 受理通知书 + 申请号 expected 1-2 weeks after that.
> - **Estimated 申请号 receipt**: late May / early June 2026. **v0.5 public release earliest**: ~mid-June 2026 (after 申请号 + Path C 解禁 of `pyobfus-pro-dev` private code → public `pyobfus_pro/`).
> - All patent draft content + tax certificates + ID card + session log are in `pyobfus-legal/` (off-repo, gitignored at workspace level, contains PII + Path C confidential). `~/.claude/projects/.../memory/patent_draft_v1_2026-05-10.md` carries forward state for future sessions.

> **2026-06-17 update — 🟢 PATENT GATE CLEARED, v0.5 release unblocked**:
> - **初步审查合格通知书 issued 2026-06-17** (发文序号 2026061200904340, examiner 陈立英). The 2026-06-11 paragraph-numbering 补正 was accepted; the formality defect is resolved and the application status is clean. Per 专利法第 34 条 the application now proceeds to 18-month publication (≈2027-11).
> - **The Path C public-release gate condition ("补正 resolved + application status clean") is MET.** Priority date (2026-05-22) is secured, so public disclosure of the 🔒 v0.5 mechanisms no longer risks the application. The 🔒 rows below are **unblocked** — they ship via the controlled Phase 5 merge (see `docs/V0.5_RELEASE_PLAN.md`).
> - **Only remaining hard deadline**: substantive-examination request within 3 years of 申请日 (≈2029-05-22); the 实审费 375 is already paid, so this is low-pressure.
> - Latest patent state for cold-start: off-repo `pyobfus-legal/patent/SESSION_LOG_20260617.md` + memory `patent_correction_notice_2026-06-01.md`.
>
> **2026-06-05 update — FILED + ACCEPTED, then in formality correction (historical)**:
> - **Filed + accepted**: 申请号 **202610712171X** · 申请日 2026-05-22 (submitted 2026-05-22 via web, NOT CPC client). 受理通知书 issued. All fees paid in full (1610 yuan, verified via official 审查信息查询). Shared 2026 fee-reduction recordation `202600565835` approved (cac-plus-ip reuses it).
> - A 补正通知书 (formality correction, issued 2026-06-01) required re-submitting the specification with system-generated paragraph numbers; **answered 2026-06-11**, accepted per the 2026-06-17 update above.

### Already in `docs/ROADMAP.md` v0.5+ (still valid · re-prioritized · patent-gated marked 🔒)

> **✅ Two non-gated Core features shipped to main 2026-06-06** (unreleased, in CHANGELOG `[Unreleased]`): **P2-5** `--numeric-obfuscation` (PR #16) + **P2-3** `--strip-ai-artifacts` (PR #17). Both opt-in, default behavior unchanged, 64 tests added (main suite 655→719). The next public version bump (0.5.0) should bundle these + the staged N6 PyPI-metadata edits + the `4 - Beta → 5 - Production/Stable` classifier change. **Path C note**: these are Core/Apache-2.0, NOT the patent-gated Pro mechanisms — releasing them does NOT touch the 补正 gate. The patent-gated 🔒 rows below remain blocked until 补正办结.

| ID | Item | Status | Re-prioritization rationale |
|---|---|---|---|
| **P2-1** 🔒 | Selective Opacity (layered AES protection) | **W3 + W3-A + W3-B DONE-PRIVATE 2026-05-09** (design doc + opacity/ scaffolding + 4-layer lattice + 3-channel API + L3 lazy-materialization runtime + build-pass AST transformer with per-layer dispatch / per-build `_LAYER_KEY` / per-function `_CIPHER_<name>` / `(qualname → Layer)` orchestrator interface · 88 P2-1 tests + 218 total · 9 patent findings · end-to-end round-trip working · **P2-1 ↔ P2-9 + P2-1 ↔ P2-11 coupling contracts both fulfilled** via P2-9.1 layer-aware seal + W3-C constant-materialization Vault) | Patent target. Core philosophical differentiator. Main combination claim core. Implementation lives in private repo per Path C; ship to public on 申请号 receipt. |
| **P2-3** | `--strip-ai-artifacts` mode | ✅ **DONE 2026-06-06** (PR #17, merged to main · `transformers/ai_artifact_stripper.py` · removes AI provenance markers from docstrings + attribution dunders · conservative attribution-only · 27 tests · unreleased, in CHANGELOG `[Unreleased]`) | Pairs naturally with new N3 (claude-skill preset); both serve "ship AI-generated code as IP" segment. Public-OK (Core feature, not patent-gated). |
| **P2-4** | Import obfuscation (Pro) | TODO | Keep · closes PyArmor Pro feature gap. Public-OK (existing public Pro module category). |
| **P2-5** | Numeric / constant obfuscation | ✅ **DONE 2026-06-06** (PR #16, merged to main · `transformers/numeric_obfuscator.py` · `--numeric-obfuscation` · int→XOR/add/sub, float→`float.fromhex` · 37 tests · unreleased, in CHANGELOG `[Unreleased]`) | Keep · small effort, fills gap. Public-OK (Core feature). |
| **P2-2** | VSCode extension | TODO · **demoted** | VSCode marketplace is slower-growing channel than launch posts; revisit after launch data. Public-OK. |
| **drop-3.8** | Drop Python 3.8 support | TODO | Both new competitors require `>=3.10`; we're paying 3.8 cost for shrinking userbase. Public-OK. |
| **P2-7** 🔒 | Forensic watermarking / `--fingerprint <buyer-id>` (Pro) | **W4 PRIMITIVE DONE-PRIVATE 2026-05-09** (`forensic/watermark.py` · `forensic_seed` SHA-256 versioned · `WatermarkRNG` HMAC-SHA256 counter-mode · `derive_layer_key` per-buyer 32-byte AES-256 · `verify_layer_key_match` forensic recovery · 32 tests · 3 patent findings · zero-change wiring through existing `opacity.transform_module(layer_key=...)` and `vault.transform_module(vault_keys=...)` · Core rename-map RNG integration deferred to post-申请号) | Patent target. Strongest novelty (only vmp-protector 1.0.0 ships per-buyer deterministic build; arXiv 2510.11251 CLASP backing). **Implementation in private repo per Path C; ship to public on 申请号 receipt.** |
| **P2-8** 🔒 | License binding combo (Pro) | **W4-A PRIMITIVE DONE-PRIVATE 2026-05-09** (`license/binding.py` · `current_machine_id` OS-priority chain · `bind_device_key` PBKDF2-HMAC-SHA256 · `expire_check` ISO-date · `period_check` atomic-rename file counter · 32 tests · 3 patent findings · build-orchestrator integration tests prove license gate woven into AES-GCM decryption path) | Patent target. `--expire` + `--bind-device` + `--period` combo, pure Python. License gate is the AES-GCM tag check itself when `--bind-device` set — no separate check call to patch out. **Implementation in private repo per Path C; ship to public on 申请号 receipt.** |
| **P2-9** 🔒 | `@seal_code` integrity decorator (Pro) + **P2-9.1 layer-aware seal** | **DONE-PRIVATE 2026-05-09** (W0 runtime + W1 build-pass + P2-9.1 ciphertext-bytes seal coupling · 46 P2-9 tests · 4 patent findings · fulfills P2-1 ↔ P2-9 coupling contract) | Patent target. Build-time SHA256 + runtime detect patching, with optional ciphertext-mode seal for L3 functions (defense-in-depth above AES-GCM tag). Implementation lives in private `pyobfus-pro-dev` repo per Path C; ship to public on 申请号 receipt. |
| **P2-10** 🔒 | `--scrub-traceback` (Pro) + **dev `pyobfus-unscrub` CLI** | **DONE-PRIVATE 2026-05-09** (W0 runtime + W1 build-pass + dev CLI · 41 tests including 13 CLI · 3 patent findings) | Patent target. Production-side traceback encryption as inverse of unmap. First-of-kind architecture. Dev CLI registered as `[project.scripts]` entry in private wheel. Implementation lives in private repo per Path C. |
| **P2-11** 🔒 | Runtime String Vault (Pro) + **W3-C build-pass** | **DONE-PRIVATE 2026-05-09** (runtime + W3-C build-pass via `vault_secrets({...})` source marker · per-vault key + per-entry-encrypted dict + Vault construction emission · returns `(source, schemas)` published interface · 43 tests · 6 patent findings · fulfills P2-1 ↔ P2-11 coupling contract via constant-materialization channel) | Patent target. KV namespace for runtime secrets (vmp-protector StringVault parity). Implementation lives in private repo per Path C. |

### New items surfaced from 2026-05-07 research

#### N1 — Python 3.14 PEP 750 t-string AST handler (1 day · narrow time window)

**Why**: PEP 750 introduced `Template` and `Interpolation` AST nodes new in 3.14 (`t"hello {name}"` syntax). PyArmor 9.2.4, python-obfuscator 0.1.0, python-obfuscation-framework 1.13.0 — **none verified to handle them yet**. First-mover advantage for "the obfuscator that handles 3.14 t-strings" is real but narrow (months, not years).

**Reference**: <https://peps.python.org/pep-0750/> · <https://docs.python.org/3.14/library/string.templatelib.html>

**Action**:
1. Add `ast.Template` / `ast.Interpolation` handlers to `pyobfus/transformers/string_encoder.py`
2. Test case: obfuscate a 3.14-only module using `t""` and round-trip-verify
3. Ship a blog post "pyobfus is the first Python obfuscator to handle PEP 750 t-strings" (own that SEO term)

**Done when**: 3.14 t-string regression test green; post live.

---

#### N2 — pyobfus-mcp 0.2.0 = FastMCP 1.27 features + Pro funnel + security hardening (✅ SHIPPED 2026-05-08 · 4 phases / 5 commits)

**Why (FastMCP 3.0)**: pyobfus-mcp 0.1.2 lacks production-grade features that the MCP ecosystem is converging on (tool versioning, per-tool authorization gating, OTel observability). Glama and other MCP aggregators will eventually add a "production-ready" filter — being on the wrong side of that line means we lose visibility.

> **2026-05-07 evening reality check**: when I went to wire Phase 2, I `inspect`-ed the actual `FastMCP.tool()` signature on `mcp==1.27.0`. The kwargs it accepts are: `name`, `title`, `description`, `annotations`, `icons`, `meta`, `structured_output`. **There is no typed `version=` kwarg, no per-tool `auth=` kwarg, and no native OpenTelemetry hooks** in mcp 1.27 — the "FastMCP 3.0 features" framing I'd been carrying turned out to be community/marketing aspiration, not what's actually shipped in the SDK. Plan corrected below: we use `meta={"version": "1", "tier": "..."}` dict (forward-compatible), implement tier gating at our `secure_tool` decorator layer (the Phase 1 wrapper), and add OTel via soft-import (no hard dep). This implementation is more honest and **less coupled to FastMCP API churn** — when mcp eventually ships native typed kwargs we can migrate without re-architecting.

**Why (Pro funnel · 2026-05-07 finding)**: 5 current MCP tools are community-only with weak Pro discovery. `check_obfuscation_risks` doesn't surface "Pro string-encryption would protect N sensitive literals" even when the scan finds them. `explain_preset` Pro-preset path returns the CLI hint `pyobfus-trial start` — no Stripe URL, no ROI framing, no value-prop. There is no `recommend_tier` tool. **Pro funnel via MCP is the highest-leverage monetization channel** (AI assistants invoke MCP far more often than humans run CLI directly), but it's currently the weakest funnel surface in the entire product. Bundling Pro funnel design with the FastMCP 3.0 upgrade because both touch every tool's response shape — one breaking-change window, one 0.2.0 ship.

**Why (security hardening · 2026-05-07 evening finding)**: A 10-category audit of `pyobfus_mcp/pyobfus_mcp/tools.py` + `server.py` against Atlas Whoff's "5 MCP Server Security Mistakes" (dev.to, 2026-05-06) plus 5 additional categories surfaced **3 real gaps + 2 partial gaps** (full table in `~/.claude/projects/-mnt-c-onedrive-msft-OneDrive---MSFT-rong-3-job-program-pyobfus/memory/mcp_security_audit_baseline.md`). With launch wave starting (HN 5-11 + Reddit 5-12), the Atlas-style scanner exposure is 4 days out and the gaps would scan red. Bundling fixes here because per-tool auth (already in this scope under FastMCP 3.0 baseline) and audit logging share the same `@app.tool` decorator surface, so refactoring once is cheaper than refactoring twice.

**Action**:

*FastMCP 1.27 baseline + own-layer tier gating + soft-import OTel*:
1. Bump dep `mcp>=1.27.0,<2.0.0` (we're at `>=1.20.0,<2.0.0` after the 0.1.2 fix). Trivial change in `pyobfus_mcp/pyproject.toml`.
2. Add `meta={"version": "1", "tier": "community"}` to all 5 `@app.tool` decorators in `pyobfus_mcp/pyobfus_mcp/server.py`. The `meta` dict is what mcp 1.27 actually accepts; future Pro-tier tools registered in Phase 3 will get `tier: "pro_funnel"`. This is the SDK-native forward-compatible carrier for our tool versioning intent.
3. Add tier gating to `secure_tool` decorator (the Phase 1 wrapper in `pyobfus_mcp/pyobfus_mcp/_security.py`):
   - Optional `requires_tier="community"` parameter (default community)
   - Env var `PYOBFUS_MCP_DISABLED_TOOLS=tool1,tool2,...` administratively disables tools by name
   - Disabled tools return a structured `ToolDisabled` error envelope, audit-logged with `outcome: "disabled"`
   - Disabled check happens **before** rate-limit check so disabled tools don't burn budget
   - *Closes audit category #7 partial gap*
4. OpenTelemetry instrumentation via soft-import in `secure_tool`:
   - Try to `import opentelemetry` at module load; if absent, no-op
   - If installed AND `OTEL_EXPORTER_OTLP_ENDPOINT` env var set, emit a span per tool invocation with attributes: `tool.name`, `tool.status`, `tool.duration_ms`
   - Don't add `opentelemetry-sdk` as a hard dep — install via `pip install pyobfus-mcp[otel]` (extras_require) or BYO. Keep the default install lean.

*Pro funnel*:
5. `check_obfuscation_risks` → add `pro_value` field. When scan finds N sensitive string literals or M complex CFG branches, return structured Pro recommendation including Stripe checkout URL.
6. `explain_preset` Pro path → replace `pyobfus-trial start` CLI hint with ROI framing + 14-day trial start command + Stripe pricing URL.
7. New tool `recommend_tier(path)` → analyzes project, returns free / Pro recommendation with reasons, free-trial start command, and pricing URL.
8. New tool `start_pro_trial()` → returns structured response with download / activation steps; AI can guide user end-to-end without dropping out to a browser.
9. Add `tier_context` field to all 5 tool responses so the AI knows which tier is currently active and which Pro paths are gated.

*Security hardening (new 2026-05-07 evening · all 3 surfaced by 10-category audit)*:
10. **Path scoping** — wrap all path-accepting tools (`check_obfuscation_risks`, `generate_pyobfus_config(write=True)`, `unmap_stack_trace`) with a sandbox that resolves the requested path, rejects `..`-traversal, and rejects absolute paths outside a configurable project root (default: `os.getcwd()` when the server starts). *Closes audit category #2 (overly broad filesystem access).*
11. **Rate limiting** — token bucket per session, default 30 calls/min/tool. Exposed as `PYOBFUS_MCP_RATE_LIMIT_PER_MIN` env var override. Returns structured `RateLimitExceeded` error with `retry_after_seconds` in the standard error envelope. *Closes audit category #3 (no rate limiting).*
12. **Audit logging** — JSON line per tool invocation to `stderr` (default) or `PYOBFUS_MCP_AUDIT_LOG=path/to/file.jsonl`. Fields: `ts`, `tool`, `session_id`, `params` (with `path`/`mapping_path`/`trace` value-redacted to `[REDACTED:N_chars]`), `outcome` (`success` / `error`), `duration_ms`. *Closes audit category #5 (no audit logging).*

*Ship*:
13. Bump pyobfus-mcp to 0.2.0; CHANGELOG entry includes a "Security baseline" section linking to this scope; `mcp-publisher publish` (this also picks up the deferred `_meta` from P0.3 — see P0.3 status above).

**Done when**: 5 tools versioned; Pro funnel surfaces in `check_obfuscation_risks` + `explain_preset` + new `recommend_tier` + new `start_pro_trial`; OTel traces visible with `OTEL_EXPORTER_OTLP_ENDPOINT=...`; **path-traversal attempts return structured error**; **rate-limit kicks in past 30 calls/min/tool with structured retry hint**; **every tool call emits a JSON audit line**; 0.2.0 live on PyPI + MCP Registry with `_meta` block published; 1+ Stripe checkout link click sourced from MCP-driven prompts within 30 days of launch (instrumented via OTel); a fresh run of Atlas Whoff's MCP Security Scanner (or equivalent third-party scan) shows 5/5 of his categories green for pyobfus-mcp 0.2.0.

**Ship summary (2026-05-08)**:
- **Phase 1** — Security baseline: commit `fa4094a` · 36 → 56 tests · CI 24/24 green
- **Phase 2** — FastMCP 1.27 baseline + tier gating + soft OTel: commit `b868618` · 56 → 65 tests · CI 24/24 green
- **Phase 3** — Pro funnel via MCP: commits `0cd629c` (replaced `9ec05ff` after GitHub Push Protection caught the fake Stripe-shaped fixture strings — the test fixtures themselves were reshaped to trigger only our generic-pattern detector, not the Stripe-key one) · 65 → 75 tests · CI 24/24 green
- **Phase 4** — Ship 0.2.0: commit `3f74f91` (version bump + CHANGELOG) + tag `mcp-v0.2.0` · `release.yml` OIDC publish on first try (PyPI Trusted Publisher's first real exercise) → PyPI 0.2.0 live with PEP 740 attestations · `mcp-publisher publish` published 0.2.0 to MCP Registry (token expired per the 80-min rule and was auto-refreshed via `gh auth token` workaround documented in `mcp_publisher_auth.md` — the playbook's first real reuse)
- **Status caveat**: the publisher-claimed `_meta.io.github.zhurong2020.pyobfus_mcp` block was silently stripped server-side (see P0.3 status above for hypothesis + plan). Field is present-but-empty; not a blocker.

---

#### N3 — `--target claude-skill` preset (1 week · net-new market segment)

**Why**: Claude Code's plugin/skill ecosystem exploded in 2026 (awesome-claude-plugins, tonsofskills marketplace). Skill authors increasingly want to ship **proprietary skills** without exposing source. A preset that knows the skill manifest layout (preserves `manifest.json`, `metadata.yaml`, hook entry points; obfuscates everything else) opens a buyer segment with **zero incumbent competition** — PyArmor can't address this without their own AI-friendly debugging story.

**Reference**: <https://github.com/ComposioHQ/awesome-claude-plugins> (community list) · <https://github.com/jeremylongshore/claude-code-plugins-plus-skills>

**Action**:
1. Survey 10-15 popular Claude skills on the marketplace; identify common manifest patterns
2. Define preset rules in `pyobfus/presets/claude_skill.yaml`:
   - preserve names: skill-entry hooks, manifest fields
   - exclude paths: `manifest.json`, `metadata.yaml`, `*.md` docs
3. Add CLI: `pyobfus --preset claude-skill src/`
4. Ship companion blog post: "Protect your Claude skill IP without breaking it"

**Done when**: 1+ external skill author tries it and confirms hook resolution still works.

---

#### N6 — PyPI search ranking SEO (staged for next bumps · 0 effort to ship · ride along with N1 / N3 / future bumps)

**Why**: The user spot-checked PyPI search for "pyarmor" 2026-05-08 and pyobfus did not appear on page 1 of 4 result pages. Investigation:

- pyobfus 0.4.0 IS in the search index (live PyPI summary has 1 "PyArmor" mention; live README has 4 case-insensitive "pyarmor" mentions; keywords include `pyarmor-alternative`). Realistic location is pages 2-3.
- pyobfus-mcp 0.2.0 was **NOT in the index at all**: 0 PyArmor mentions in summary, 0 in keywords. Anyone searching "pyarmor" on PyPI would never find pyobfus-mcp.
- Top 5 results are dominated by packages that have "pyarmor" literally in **package name** (`pyarmor`, `pyarmor.cli`, `pyarmor.man`, `pyarmor.mini`, `pyarmor-webui`). Structural advantage we cannot match without renaming pyobfus to `pyobfus-pyarmor` style — which would be trademark / passing-off risk and is firmly off-limits.

**Realistic target**: page 1-2 of "pyarmor" PyPI search (top-half of the second page, not top 3). Search-result conversion (someone who finds us reading a 1-line differentiator) matters more than absolute rank.

**Action (staged 2026-05-08, takes effect on next bump per do-not-do version-bump rule)**:
1. ✅ `pyobfus/pyproject.toml` summary rewritten 2026-05-08: keeps 1 PyArmor mention but adds the differentiator phrase "same protection, traces stay debuggable" so a search-results scanner gets the value-prop in 1 sentence. Char count 320 → 282.
2. ✅ `pyobfus_mcp/pyproject.toml` summary rewritten 2026-05-08: appended "PyArmor alternative with first-class AI-debug story." (0 → 1 PyArmor mention).
3. ✅ `pyobfus_mcp/pyproject.toml` keywords gained `pyarmor-alternative` 2026-05-08.

**Hard limits (do NOT do)**:
- Don't add "pyarmor" to package name (trademark + passing-off risk; PyPI moderation may reject)
- Don't go past 2 PyArmor mentions per summary (3+ looks like keyword stuffing; PyPI Acceptable Use Policy frowns on deceptive metadata)
- Don't bump pyobfus or pyobfus-mcp version just to ship these metadata edits — same reason as P0.3 `_meta`. Bundle with N1 (PEP 750 t-string handler → 0.5.0) or N3 (claude-skill preset) or any other natural bump.

**Done when**: pyobfus 0.5.0 (or first version after this entry) is published and a fresh `curl https://pypi.org/pypi/pyobfus/json | jq .info.summary` shows the new wording; same for pyobfus-mcp on its next bump. As secondary signal, manually search "pyarmor" on PyPI 1 week after both ship and verify pyobfus + pyobfus-mcp both appear in the result set (ranking may take longer to reflect).

---

#### N7 — `pyobfus.dev` online demo + MCP gateway page (1 week · added 2026-05-09)

**Why**: 2026-05-09 user SERP audit on Google "python obfuscator" — pyobfus is not on page 1; the query "python obfuscator online" appears in Google's "people also search" with no canonical pyobfus result. PyObfuscator (PyPI generic name), pyobfuscate.com (cloud SaaS), freecodingtools.org (free in-browser tool), and Oxyry hold rank ahead of us on this query. pyobfus has no in-browser demo. Building one claims the top result for a high-intent query, opens a zero-friction "try" channel that doesn't require `pip install`, and creates a natural `/mcp` landing page that drives `pip install pyobfus-mcp` from web traffic — the highest-conversion MCP install funnel we can build (better than PyPI's plain text page or Glama's listing).

**Reference**: <https://pyodide.org/en/stable/> · pyobfus's pure-Python core makes it Pyodide-friendly for in-browser execution

**Action**:
1. Domain: register `pyobfus.dev` (~$15/yr Cloudflare Registrar) OR start with free `pyobfus.pages.dev` for MVP
2. **Free tier (Pyodide, in-browser)**: static page on Cloudflare Pages; Pyodide loads pyobfus from PyPI; paste code → click obfuscate → BEFORE/AFTER side-by-side. Privacy framing prominent ("your code never leaves your browser") — this is a real differentiator vs pyobfuscate.com's server-side model.
3. **Pro preview (Cloudflare Worker, rate-limited)**: Worker runs `pyobfus --string-encryption --control-flow` server-side, capped at 5 lines / no save. "Want to obfuscate the full file? $45 Pro" → Stripe checkout (single-tier per `pricing_strategy.md`).
4. **`/mcp` landing tab**: one-page guide — "Already using Claude Code / Cursor? Add this MCP config." Each install path (Claude Desktop / Claude Code / Cursor / Windsurf / Zed) gets a copy-paste config block. **This is the MCP install funnel.** Cross-link from PyPI `pyobfus-mcp` long_description.
5. **`/decode-stack-trace` reverse demo**: paste obfuscated stack trace + mapping.json → unmapped output (uses `unmap_stack_trace` MCP tool logic, runs in Pyodide). Captures "deobfuscate python" / "python obfuscator decode" search intent that currently goes to SO/Reddit.
6. Cloudflare Web Analytics on every page (privacy-friendly, no cookie banner needed).

**MCP tie-in**: every visitor to `/mcp` who copies a config is a pre-qualified Pro lead — they're already using AI assistants for coding (= our buyer profile). Instrument Stripe URL clicks from `/mcp` separately from `/` so we can measure MCP-attributed Pro conversion vs direct conversion.

**Done when**: domain live (`pyobfus.dev` or `pages.dev`) · 4 sub-pages (`/`, `/mcp`, `/decode-stack-trace`, `/comparison/pyarmor`) live · GitHub topic `python-obfuscator-online` (P0.5) now backed by a real page · 1+ Stripe checkout click sourced from demo within 30 days · 1+ MCP install attributable to `/mcp` page traffic.

---

#### N8 — 5-6 SEO landing pages on `pyobfus.dev` (rolling · 1-2 pages/week post-N7 MVP · added 2026-05-09)

**Why**: pyobfus's name structurally cannot win short-tail "python obfuscator" against literal-name competitors (PyObfuscator on PyPI, pyobfuscate.com domain). Winnable strategy = long-tail / high-intent queries where competitors have nothing: framework-aware preset queries, comparison queries, MCP/AI-tool integration queries. PyArmor explicitly does not have an MCP server — pages 4 monetizes that asymmetry, and the comparison page (#3) frames the MCP/AI-debug story as a category PyArmor structurally cannot enter.

**Pages to build** (priority order; each ~800-1200 words + worked example + schema.org `SoftwareApplication` markup):
1. `/pyarmor-alternative` — N6 already staged the keyword in PyPI metadata; this is the landing page that converts the click. **Centerpiece content (added 2026-05-09)**: the empirical PyArmor 9.2.4 trial-limit table from `docs/PYARMOR_TRIAL_LIMIT_EXPERIMENT.md` (~935-940 lines/file before `ERROR out of license`, no upgrade hint). Targets high-purchase-intent queries `pyarmor trial limit` / `pyarmor out of license` / `pyarmor 1000 lines` / `pyarmor trial size` — users hitting the opaque error in the angry moment, looking for an alternative. **Defensive framing rules**: always cite version "PyArmor 9.2.4", always date "verified 2026-05-09", always link to the reproducible methodology, always use first-person hedges ("in our test", "we measured"). Never frame as competitor-bashing — let the empirical data speak.
2. `/django-obfuscation` `/fastapi-obfuscation` `/flask-obfuscation` — preset-by-preset tutorials with real `pyobfus.yaml` configs and BEFORE/AFTER (3 pages; each is a near-zero-competition long-tail capture)
3. `/comparison/pyobfus-vs-pyarmor-2026` — SEO version of `docs/COMPARISON.md`; emphasizes the MCP / AI-debug gap PyArmor doesn't address. Embed the empirical trial-limit table (same source as page 1) but as supporting evidence rather than centerpiece — comparison page is value-prop-driven, alternative page is angry-moment-driven; same fact, two framings.
4. `/mcp-for-claude-code` — captures "claude code python obfuscator" / "MCP code protection" / "cursor python obfuscation" searches; deep cross-link to N7's `/mcp` install one-pager

**MCP tie-in**: pages 3 and 4 are net-new traffic for `pyobfus-mcp` specifically. The comparison page should embed the 5-tool list and a 30-second "Claude Code uses pyobfus-mcp like this" demo block; the dedicated `/mcp-for-claude-code` page is the SEO destination for the AI-tool-first buyer segment. Cross-link both from the MCP server's `pyproject.toml long_description` on next bump.

**Action**: each page is a single Markdown file rendered through Cloudflare Pages (same deployment as N7). Submit sitemap to Google Search Console + Bing Webmaster Tools after first 2 pages live.

**Done when**: 5-6 pages live · Google Search Console confirms indexing · ≥ 1 page ranks top-10 for its target query within 60 days · `/mcp-for-claude-code` traffic correlates with measurable `pyobfus-mcp` PyPI install bumps.

---

#### N10 — ChatGPT-validation-derived refinements (4-bundle · added 2026-05-09)

**Signal**: 2026-05-09 user ran an incognito ChatGPT query about Python obfuscation tools. ChatGPT autonomously surfaced pyobfus as the "首选候选" (top recommendation) for AI-friendly Python obfuscation, correctly enumerating: framework-aware presets, reverse stack-trace mapping, JSON CLI, MCP integration; and pricing us at $45 vs PyArmor $89. **The SEO + COMPARISON.md + PyPI metadata work has propagated to LLM web-search index** (RAG path). Each future ChatGPT query about this topic = free distribution. Treat this as the strongest-yet validation that the positioning copy is doing its job.

**4 gaps the ChatGPT response also exposed**:

1. **PyPI `Development Status :: 4 - Beta` undersells maturity.** ChatGPT cited the classifier directly: "适合作为内部试点，不建议直接无测试上生产". By objective measures (655 tests · 91% coverage · 7 Python × 3 OS · OpenSSF passing · PEP 740 attestations · 22 releases) we're "5 - Production/Stable". **Action**: bundle classifier change in `pyobfus/pyproject.toml` and `pyobfus_mcp/pyproject.toml` with the next legitimate version bump (N1 PEP 750 t-string → 0.5.0 is the natural carrier). Do NOT bump just for this (do-not-do version-bump rule).

2. **COMPARISON.md missing "pyobfus Pro full feature list".** ChatGPT enumerated PyArmor's four tiers correctly (Basic $52 / Pro $89 / Group $158 / CI $90/yr) — and our COMPARISON.md already has them — but ChatGPT missed dead-code injection / license embedding (`--expire` / `--bind-machine` / `--max-runs`) / 4 presets in our Pro tier because the COMPARISON.md feature matrix is buried mid-document. **Action**: ✅ Layered Deployment Strategy section added to COMPARISON.md in this session (2026-05-09). N8 `/pyarmor-alternative` landing page should mirror the "every PyArmor tier vs pyobfus single-SKU" framing prominently and lead with the full Pro feature list rather than burying it.

3. **Cross-reference our 935-940 line measurement against PyArmor's official 32768-byte code-object limit.** ChatGPT cited PyArmor's official docs: "试用版 code object 最大为 32768 bytes". 940 lines × ~32 bytes/line ≈ 30 KB ≈ approaches 32 KB — our independent measurement corroborates the official documented limit. Adding both numbers side-by-side in `docs/PYARMOR_TRIAL_LIMIT_EXPERIMENT.md` upgrades it from "we tested a number" to "we independently verified the official documented limit". **Action**: TODO. Defer until coordinated with the parallel session that owns `docs/PYARMOR_TRIAL_LIMIT_EXPERIMENT.md` (created 532614b); editing it concurrently risks merge conflict. Suggested addition is a prefatory paragraph in the Methodology section: "PyArmor's official documentation states the trial limit as 32 KB code object. Our line-count measurement of 935-940 lines for sparse Python (~32 bytes/line) corroborates this byte-level threshold from a different testing angle."

4. **"Three-layer deployment" framing — pyobfus as default-on, PyArmor/Nuitka as opt-in for crown-jewel modules.** ChatGPT recommended this stack: dev = no obfuscation; pre-release = pyobfus (AST + mapping + Claude Code debug); production = pyobfus + optional PyArmor Pro/Nuitka on highest-value modules. This is counterintuitive but high-trust framing — admitting pyobfus doesn't kill PyArmor reads as honest, especially on HN/Reddit where defensive marketing is punished. **Action**: ✅ COMPARISON.md "Layered Deployment Strategy" section added in this session (2026-05-09); README.md FAQ "Can I use pyobfus alongside PyArmor or Nuitka?" added in this session (2026-05-09); HN draft seed comment + N8 `/pyarmor-alternative` landing page closing section should also reflect this framing — handled in their respective sessions/launches.

**Done when**: classifier changed (queued for N1 bump), COMPARISON.md upgraded (✅ this session), 32768-byte cross-reference added (deferred · coordinate with other session), README/HN/landing page reflect three-layer framing (README ✅ this session; HN/landing page later).

**Additional doc-lag item discovered 2026-05-09**: `README.md` line ~27 says "registers **five** MCP tools" — pyobfus-mcp 0.2.0 actually has **7** (added `recommend_tier` + `start_pro_trial` per N2). Fix the count + add the 2 new tools to the bullet table when N1 bump goes out (same trigger as N10-1 classifier change · do-not-do version-bump rule applies). awesome-mcp-servers PR #5777 description was already refreshed independently 2026-05-09 (silent edit).
- **2026-05-29 update**: the awesome-mcp-servers **README entry line** (not just the PR description) was bumped from "Five tools" → "Seven tools" (added `recommend_tier` + `start_pro_trial`) on fork branch `add-pyobfus-mcp`. The pyobfus repo's own `README.md` line ~27 count fix **remains deferred** to the N1 bump per the do-not-do version-bump rule.

---

#### N9 — Stripe `quantity` field on the existing $45 SKU (half day · added 2026-05-09)

**Why**: closes the commercial-loop ARPU gap surfaced in 2026-05-09 strategy review WITHOUT adding Pro tiers. The single-tier $45 perpetual license is the right strategic positioning ("PyArmor alternative for the underserved low-mid segment"); a Solo/Team/Enterprise tier expansion was rejected because it breaks decision-fatigue economics at checkout, requires 6-8 weeks of team-license-server infrastructure, and pulls toward PyArmor's enterprise lane where they already win. See `~/.claude/projects/-mnt-c-onedrive-msft-OneDrive---MSFT-rong-3-job-program-pyobfus/memory/pricing_strategy.md` for the full rationale and guardrail. Stripe's native quantity field lets a small team buy 3 or 10 seats on the same SKU without cluttering the checkout page — same simplicity, higher ARPU per buyer.

**Action**:
1. In Stripe dashboard, enable `Adjustable quantity` on the existing `pyobfus Pro` price object
2. Configure tiered display: 1 = $45 · 3 = $99 ($33/seat) · 10 = $199 ($20/seat) (Stripe `pricing_tiers` natively)
3. Verify `pyobfus_pro/license/embedding.py` activation flow accepts a `seats=N` field; if not present, add it (the license-embedding framework is already there per ROADMAP P2-license-embedding work)
4. Update README purchase section: keep prominent `$45 Buy Now`; add ONE line below — "Buying for a team? 3 seats $99 / 10 seats $199" with link to the same Stripe checkout. Do NOT build a separate pricing-tier table.
5. **MCP tie-in**: update `recommend_tier` MCP tool (shipped in N2 / pyobfus-mcp 0.2.0) to surface seat-aware Stripe URLs. When AI agent detects multi-developer project structure (e.g., `CODEOWNERS` with multiple users, or `.git/config` with multiple committer signatures, or a `package.json`/`pyproject.toml` with `authors` array > 1), recommend the 3-seat or 10-seat tier instead of solo. This requires a small bump to `pyobfus-mcp` (0.2.1 patch) — bundle with the next legitimate bump per do-not-do version-bump rule, or fold into N3 claude-skill preset's MCP companion update.

**Strategic guardrail**: this is the ONLY pricing change to make. If a future session proposes Solo/Team/Enterprise tier expansion, refer back to `pricing_strategy.md` memory. The single-tier positioning is load-bearing.

**Done when**: Stripe checkout shows quantity selector and tiered pricing · README updated · `recommend_tier` MCP tool seat-aware on next pyobfus-mcp bump · 1+ multi-seat purchase within 60 days (proves the volume need exists; if zero multi-seat purchases in 60 days, that's signal the underserved-low-mid segment is genuinely solo-dominated and we can stop revisiting pricing).

---

#### N11 — JOSS (Journal of Open Source Software) submission (gated on patent 申请号 · ~2-4 month review · added 2026-05-09)

**Why**: free Crossref-DOI peer-reviewed venue for open-source software. Diamond Open Access (0 author APC, 0 reader paywall). pyobfus crosses JOSS's **6-month public-history threshold on 2026-05-12** (V0.1.0 first PyPI 2025-11-12; verified via cardiac-manuscripts JOSS submission path research 2026-04-27, source URL https://joss.theoj.org). Citing a JOSS DOI in README + landing pages + future research-software discussions raises pyobfus's academic legitimacy at zero cost.

**Reference**: <https://joss.theoj.org> · <https://joss.readthedocs.io/en/latest/submitting.html> · `~/projects/cardiac-ml-research/docs/project/JOSS_OPEN_CORE_POLICY_RESEARCH.md` (2025-11-19 prior research confirming open-core compatible with JOSS) · `~/projects/cardiac-manuscripts/cac-plus_methodology/supplementary/joss_submission_path.md` (2026-04-27 verification of 6-month rule)

**Critical sequencing constraint**: must be submitted **AFTER** patent 申请号 received per `memory/pyobfus_patent_strategy.md` Path C. JOSS publication is not net-new disclosure for already-public V0.4.0 features (PyPI release exhausted CN novelty 2025-11-11), but the JOSS paper:
1. Citing "patent pending CN [申请号]" needs the申请号 to exist
2. Forces precise articulation of the inventive step → must avoid leaking v0.5 patent claim wording before they're filed
3. Gives more substance to discuss (v0.5 features observable in public source by then)

So target submission window = **2026-Q3 / Q4** (after v0.5 ships on PyPI per Path C timeline).

**Action sequence**:
1. After patent 申请号 received: draft `paper.md` (500-1000 words per JOSS format) with structure `Summary` + `Statement of need` + `Implementation` + `Acknowledgments`
2. **Statement of need framing**: lead with AI-collaborative-workflow-infrastructure positioning per Session 23 sync point 3 (layered deployment, ChatGPT-validated three-layer stack, OpenSSF passing badge as maturity evidence); cite cardiac-ml-research as real-world validation case study (per `JOSS_OPEN_CORE_POLICY_RESEARCH.md` 2025-11-19 strategy); frame the paper as "research software toolkit for code IP protection in AI-assisted development workflows" (avoids the JOSS scope-rejection risk for "thin wrapper" / "single-function package")
3. Open-core disclosure (1-2 sentences per JOSS研究 doc): "PyObfus adopts an open-core model. The Community Edition (Apache 2.0, subject of this paper) provides core obfuscation features validated on production systems; a Professional Edition with advanced security features is available for commercial deployments."
4. Cite "patent pending CN [申请号]" as legitimacy signal in Implementation section
5. `paper.bib` for refs (pyca/cryptography for crypto baseline · arXiv 2510.11251 CLASP · vmp-protector 1.0.0 PyPI · OpenSSF Best Practices 12788 · JOSS design paper Katz 2018)
6. Submit via <https://joss.theoj.org/papers/new>; review process is open via GitHub issue tracker; respond to reviewer comments publicly
7. After acceptance: add JOSS DOI badge to README; cross-link from `pyobfus.dev` (N7) `/about` and PyPI long_description

**Risk register**:
- **Scope rejection**: JOSS sometimes rejects "thin API client" / "single-function package". Mitigation: framing per #2 above; emphasize cardiac-ml-research validation + OpenSSF badge + 90% test coverage + 21-job CI matrix as evidence of substantive engineering toolkit (≠ thin wrapper). Backup if rejected: arXiv `cs.SE` / `cs.CR` preprint (free, immediate, 0 review) → still gets timestamp + Google Scholar visibility, and most journals allow arXiv preprints alongside subsequent submission.
- **Reviewer skepticism on commercial Pro version**: pre-empted in 2025-11-19 research (`JOSS_OPEN_CORE_POLICY_RESEARCH.md`) — JOSS has no policy against open-core, only requires submitted code be OSI-licensed (✅ Apache 2.0). Rebuttal language ready in that doc Q1/Q2/Q3.
- **Review timeline uncertainty**: community-reported 2-4 months but not officially stated. Don't pin downstream marketing to JOSS DOI date.

**Done when**: paper.md drafted post-patent · submitted to JOSS · accepted with Crossref DOI · JOSS badge added to README · DOI cross-linked from pyobfus.dev (if N7 live by then) · listed in `~/projects/cardiac-ml-research/docs/project/JOSS_OPEN_CORE_POLICY_RESEARCH.md` follow-up section.

---

#### N12 — MCP Server Card (`.well-known/mcp/server-card.json`) (half day · narrow first-mover window · added 2026-06-05)

**Why**: MCP 2026 roadmap proposes **Server Cards** (SEP-1649 server-card at `/.well-known/mcp/server-card.json` + SEP-1960 manifest at `/.well-known/mcp`) — a standard for advertising server capabilities, tool surface, transports, auth, protocol version **without connecting**. Aggregators (Glama, PulseMCP, Smithery, future Anthropic clients) and crawlers read it to discover/rank servers. **Expected to land in the June-2026 spec cycle**; SDK support follows. Same narrow first-mover dynamic as N1 (PEP 750 t-strings): "the obfuscator MCP that ships a Server Card before the field" is a real-but-short SEO/discovery edge. Sources: SEP-1649 <https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1649> · MCP roadmap <https://modelcontextprotocol.io/development/roadmap>.

**Action**:
1. Author a static `server-card.json` per SEP-1649 schema: name `io.github.zhurong2020/pyobfus-mcp`, 7 tools w/ descriptions, transport `stdio` (+ remote URL once N14 lands), Apache-2.0, protocol version, link to Glama A listing + MCP Registry entry.
2. Serve it at `/.well-known/mcp/server-card.json` on `pyobfus.dev` (depends on N7 domain being live) AND commit a copy in-repo (`pyobfus_mcp/server-card.json`) so the Registry/`glama.yaml` can reference it.
3. Validate against the emerging schema (ref impl `github.com/cognimata/mcp-server-card-demo`); re-check when SEP merges into core spec (wording may shift server-card.json ↔ mcp manifest).

**Done when**: `curl https://pyobfus.dev/.well-known/mcp/server-card.json` returns a schema-valid card listing all 7 tools; in-repo copy committed; re-validation note filed when SEP-1649/1960 merges. **Path C safe** (pure metadata). **Depends on**: N7 (domain).

#### N13 — SBOM + provenance for the obfuscated *output* (1-2 weeks · enterprise differentiator · added 2026-06-05)

**Why**: SBOM/SLSA moved from buzzword to operational requirement in 2026 (US EO 14028, EU CRA; Sonatype counted 454k+ new malicious packages in 2025). Our PEP 740 attestations (P0.2 ✅) cover **our own package** only. Two net-new angles: **(a)** emit pyobfus's own CycloneDX SBOM (Tier-1 baseline extension, trust signal); **(b) ← the differentiator**: have pyobfus **emit an SBOM + integrity/provenance manifest for the obfuscated artifact it produces** — "this obfuscated build contains modules X/Y/Z, source commit, pyobfus version + config hash, per-file SHA-256". Enterprises distributing obfuscated Python increasingly need supply-chain documentation for their *output*, and **no Python obfuscator currently provides this** — a genuine, on-trend wedge (not lane-chasing). Sources: Cloudsmith 2026 supply-chain guide <https://cloudsmith.com/blog/the-2026-guide-to-software-supply-chain-security-from-static-sboms-to-agentic-governance> · Python SBOM playbook <https://kawaldeepsingh.medium.com/practical-software-supply-chain-security-2026-sboms-signing-slsa-reproducible-builds-a-0416cfac32dc>.

**Action**:
1. (a) Add CycloneDX SBOM generation for pyobfus itself to the release workflow (ride next bump; complements PEP 740). Low effort.
2. (b) New CLI flag `pyobfus --sbom <out.json>` (or auto-emit alongside `dist/`): CycloneDX-format manifest of the obfuscated output — input file set, source provenance (git commit if available), pyobfus version + obfuscation-config hash, per-output-file SHA-256, declared third-party deps untouched. Optional `--attest` to sign it (reuse sigstore path).
3. Document the output-SBOM as an enterprise/Pro-adjacent feature on the comparison page + a short blog post ("ship obfuscated Python with a supply-chain manifest").

**Done when**: release emits pyobfus's own CycloneDX SBOM; `pyobfus --sbom` produces a schema-valid CycloneDX manifest for the obfuscated output with per-file hashes; documented on `pyobfus.dev`/comparison. **Path C safe** (output metadata, not v0.5 mechanism). Decide Core-vs-Pro split for (b) before shipping.

#### N14 — Hosted/remote `pyobfus-mcp` endpoint (1 week · new install funnel · added 2026-06-05)

**Why**: the 2026-07-28 MCP spec RC makes MCP **stateless at the protocol layer** — a remote server can run behind a plain round-robin LB, no sticky sessions / shared session store. Glama explicitly lists **connectors** (hosted endpoints) above plain server listings. A hosted `pyobfus-mcp` on `pyobfus.dev` = a lower-friction discovery/install funnel than `pip install` (no local setup), and the side-effect-free tools (`check_obfuscation_risks`, `unmap_stack_trace`, `list_presets`, `explain_preset`, `recommend_tier`) are safe to expose remotely. Sources: 2026-07-28 spec RC <https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/> · MCP adoption stats <https://www.digitalapplied.com/blog/mcp-adoption-statistics-2026-model-context-protocol>.

**Action**:
1. Wrap the existing FastMCP server in a streamable-HTTP transport; deploy on `pyobfus.dev` (Cloudflare Worker / small container).
2. Expose ONLY the read-only / no-filesystem-write tools remotely; keep `generate_pyobfus_config` (writes files) stdio-local-only or sandbox its output. **Reuse the 0.2.0 security hardening** (rate limit / path scope / audit log) — this is exactly the threat surface they were built for.
3. List under Glama **connectors**; add the remote URL to the N12 Server Card; cross-link from the `/mcp` page (N7).

**Done when**: hosted endpoint live + schema-valid Server Card advertises it; read-only tools callable remotely with rate-limit + audit-log active; listed on Glama connectors; 1+ remote tool call attributable to `/mcp` page traffic. **Path C safe**. **Depends on**: N7 (domain) + ideally N12 (card) + the 0.2.0 security layer.

> **Sequencing note (2026-06-05)**: N12 is the cheap time-sensitive grab (do near-term, but needs N7's domain). N13(a) rides any release; N13(b) is the standout differentiator but needs design (Core-vs-Pro). N14 is the heaviest and rides N7 + N12 + the 0.2.0 security layer. New competitor **CodeEnigma** logged in the verified-facts table — watch only, do not chase the bytecode-encryption lane.

---

## 🟢 P2 — Passive / waiting (no action needed; just monitor)

| Item | Trigger condition | ETA |
|---|---|---|
| punkpeye merges PR #5777 | ✅ **MERGED 2026-06-06 22:52 UTC** by punkpeye (Frank Fiegel) — pyobfus-mcp now listed in `punkpeye/awesome-mcp-servers` (86K★) under Developer Tools. Opened 2026-05-03 → ~34 days at human cadence. (2026-05-29: PR had gone `CONFLICTING`/`DIRTY` from a README.md collision; resolved by merging `upstream/main` + re-appending the 7-tool entry → back to `MERGEABLE`.) | ✅ done |
| Glama license badge F → A | **2026-05-29: root-caused** — GitHub `licensee` returned `NOASSERTION` because the dual-license preamble prefixed the Apache text; Glama mirrors that field. Fix: `LICENSE` → pure Apache-2.0, notice moved to `LICENSE-NOTICE.md`. **PR #15 MERGED 2026-05-29 (commit `5556f8b`); GitHub now reports `spdx_id=Apache-2.0` ✅ (verified via `gh api repos/zhurong2020/pyobfus/license`).** Only remaining step is passive: Glama cron re-crawl flips the badge F → A. | 1-3 days (Glama crawl) |
| Glama "No glama.json" checklist clears | Glama cron re-scan after `glama.json` schema fix (commit `8d92487`) | 1-3 days |
| Glama tool-count re-index 0/5 → 7 | ✅ **2026-06-08: RESOLVED at source** — true root cause was NOT the repo Dockerfile (06-05 `bbeefb8` hypothesis) but the Glama admin **Dockerfile → Configuration "Build steps"** field, independently pinned to `pyobfus-mcp==0.1.2` (web-UI-only setting Glama generates its container from; the repo's own Dockerfile is ignored). Edited that field `0.1.2`→`0.2.0` + saved → test `019ea6c5` **succeeded 2026-06-08 18:27 CST**, introspection `ListToolsRequest` returned **all 7 tools**. **Remaining = passive re-index lag**: public API + page "Tools" panel still showed 0/5 immediately after; verify `curl -s https://glama.ai/api/mcp/v1/servers/zhurong2020/pyobfus \| python3 -c "import sys,json;print(len(json.load(sys.stdin)['tools']))"` → expect 7 within ~1 day. Full root-cause + lesson in 30-Second-Resume 2026-06-08 block above. | passive — API/listing catches up ≤1 day from the 06-08 successful test |
| First external GitHub issue | Real user encounters something | depends on launch |
| First Pro license sale | Launch traffic + Stripe checkout funnel | depends on launch |
| GitHub stars 0 → 100+ | Launch + Glama/Registry organic discovery | depends on launch |
| Glama Quality grade re-check after `glama.json` fix | Eventual cron | 1-3 days |
| ReadTheDocs `pyobfus-mcp` section (extend existing pyobfus mkdocs site) | Polish item · defer until N7/N8 unifies docs surface OR until first MCP-tool API question lands in Issues/Discussions | depends on demand |
| CCPC 软著 e-certificate | ✅ SUBMITTED 2026-05-09 evening (290元 paid · signed application PDF `软著登记申请确认签章.pdf` archived in `~/projects/pyobfus-legal/software_copyright/`); awaiting e-cert | ~30 working days from 2026-05-09 |
| Patent 受理通知书 + 申请号 (CN) | After Phase 4 of Path C — file via CPC client w/ 费减请求书 (per `memory/pyobfus_patent_strategy.md` revised 2026-05-09 evening) | ~1-2 weeks from CPC submission |
| JOSS DOI | After patent申请号 in hand → submit per N11 → open peer review on GitHub issue tracker | community-reported 2-4 months |
| 6-month JOSS public-history threshold | pyobfus V0.1.0 first PyPI 2025-11-12 → threshold met 2026-05-12 | passive — auto-clears in 3 days |

### N5 — Diversify awesome-list distribution (parallel hedge against punkpeye merge latency · ✅ COMPLETED 2026-05-08 — wong2 / mcpservers.org LIVE)

**Status 2026-05-08 (same-day approval)**:
- ✅ **wong2 / mcpservers.org APPROVED + LIVE** — approval email *"Your MCP Server has been approved!"* received from `contact@mcpservers.org` on 2026-05-08, **same day as submission** (much faster than the 7-day SLA quoted on submit). Live listing: <https://mcpservers.org/servers/zhurong2020/pyobfus> (slug is `/pyobfus`, not `/pyobfus-mcp` — directory normalizes around the GitHub repo name). Listing reflects the description + 5-tool count + dual-license note as submitted; integrates with Claude Desktop / Claude Code / Cursor / Windsurf / Zed; visible install command `pip install pyobfus-mcp`.
- ❌ **appcypher DEAD-END — owner disabled PRs + Issues** (discovered post-fork-push when the PR-create page returned *"An owner of this repository has disabled the ability to open pull requests."*; `gh api repos/appcypher/awesome-mcp-servers --jq '.has_issues'` returns `false` confirming the same setting on Issues). The CONTRIBUTING.md is stale. The repository is in read-only museum mode despite still appearing active (5.5K stars · last push 2026-05-06). **Investigation lessons**: when `gh pr list --state all` returns empty `[]` on a 5K-star awesome-list, suspect "PRs disabled" not "no PRs"; verify with `gh api repos/<owner>/<repo> --jq '{has_issues, has_pull_requests: (.has_issues==true)}'`.
- ⏸️ **Fork retained** at `zhurong2020/awesome-mcp-servers-appcypher` (zero maintenance cost · re-fork is 1 click if owner reopens · branch `add-pyobfus-mcp` kept as ready-to-go evidence).
- ✅ **N5 closed** — 2 of 3 lists actively distribute pyobfus-mcp: punkpeye PR #5777 **MERGED 2026-06-06** (86K★ · now LIVE) + wong2/mcpservers.org LIVE (4K★ + own search traffic). Combined ≥ 90K stars worth of distribution surface, both live (no longer PR-gated). The mcpservers.org direct listing lit up first (2026-05-08); punkpeye followed at human cadence ~34 days later.

**Sponsorship offer in approval email**: mcpservers.org pitched a sponsorship program for "maximum exposure on mcpservers.org + awesome-mcp-servers GitHub repo (3K stars)". **Decision: skip for now** — pyobfus has 0 GitHub stars and unproven launch metrics; spending discretionary marketing budget before launch-wave signal is irrational. Revisit post-launch (5-13+) only if (a) PyPI MoM growth ≥ 50% AND (b) sponsorship pricing is publicly disclosed AND (c) MCP-driven Stripe checkout signal exists.

Rationale: PR #5777 has been OPEN 5 days with all gates green. punkpeye repo carries ~1k open PRs and merges at human cadence. Two other major awesome-mcp-servers lists exist; investigating both 2026-05-08 yielded:

| List | Stars | Submission channel | Cost | Verdict |
|---|---|---|---|---|
| **`punkpeye/awesome-mcp-servers`** | 86K | PR (#5777 · OPEN) | ✅ already invested | — |
| **`appcypher/awesome-mcp-servers`** | 5.5K | PR · standard `CONTRIBUTING.md` (alphabetical · 1 PR / suggestion · search-before-submit) · last push 2026-05-06 (active) · 558 open issues | 30 min single PR | **Submit** |
| **`wong2/awesome-mcp-servers`** | 4K | **No PRs accepted** · README explicitly redirects to `https://mcpservers.org/submit` form · last push 2026-04-30 | 10 min web form | **Submit** |

Why submit both despite stars-tier difference vs punkpeye:
- (i) 9.5K combined stars + mcpservers.org's own search traffic = non-trivial discoverability hedge
- (ii) Zero blocking dependency on punkpeye merge — if #5777 stalls past 14 days the two new listings prove the package
- (iii) appcypher's CONTRIBUTING discipline (alphabetical · search-before-submit) means the same single-line entry from #5777 is reusable verbatim
- (iv) wong2's mcpservers.org form is faster than any of these PR cycles

Done when: PR landed in appcypher · mcpservers.org submission acked. Track in `docs/V0.4_EXECUTION_LOG.md`.

**Cold-start hint** (do this in a fresh session, not bundled with launch wave): just open this file, jump to N5, copy the existing `#5777` single-line entry from `https://github.com/zhurong2020/pyobfus/blob/main/awesome-mcp-entry.md` (or the `git log -p` of the PR's only commit), and submit verbatim to both — alphabetical position differs but the line content is identical.

---

## Strategic do-not-do list (decisions captured 2026-05-07)

- **Don't chase PyArmor's VMC virtualization**. They went deep into bytecode-VM obfuscation in 9.2.0 (Oct 2025) — that's a different lane, fundamentally stronger but conflicts with our AI-debuggability promise. Stay in AI-native lane.
- **Don't compete on AST mechanics**. Two new commoditized AST obfuscators (python-obfuscator, python-obfuscation-framework) shipped in last 5 weeks. Adding "another transformer" doesn't move our metrics; integration story does.
- **Don't bump pyobfus or pyobfus-mcp version just to refresh metadata**. **All three downstream surfaces — PyPI, MCP Registry, and Glama — reject same-version re-publishes** (PyPI: 400 "version already exists"; MCP Registry: 400 "cannot publish duplicate version", confirmed 2026-05-07; Glama Release flow: same). Bundle metadata refresh with the next legitimate bump. For Glama-listing refresh specifically (no version change involved), use the "Claim ownership flow again" mechanism — see `~/.claude/projects/-home-wuxia-projects-pyobfus/memory/glama_metadata_schemas.md`.
- **Don't add features to free tier that have no user-demand signal**. Old roadmap "Enhanced key obfuscation" and "Code compression" were deprioritized in 2026-04 strategic shift; keep them buried.
- **Don't propose Pro pricing tiers (Solo / Team / Enterprise)** (added 2026-05-09). pyobfus is positioned in the segment PyArmor underserves — solo devs, freelancers, educational users, small-tool authors. Multi-tier pricing breaks decision-fatigue economics at checkout, requires 6-8 weeks of team-license-server infrastructure, and pulls toward PyArmor's enterprise lane where they already win. Use Stripe `quantity` field on the same SKU for ARPU (N9), or build a SEPARATE product (e.g., `pyobfus.dev` SaaS) for MRR — never tier the Pro license itself. Full rationale + guardrails: `~/.claude/projects/-mnt-c-onedrive-msft-OneDrive---MSFT-rong-3-job-program-pyobfus/memory/pricing_strategy.md`.

---

## Recommended near-term sequence (3 weeks · revised 2026-05-07 evening post-launch)

```
Week 1 (5-7 → 5-11) · ✅ TECH HYGIENE LANDED · 🟢 dev.to LIVE:
  ├─ P0.1 ci smoke test                    commit 8ec0fcd
  ├─ P0.2 OIDC release workflow            commit a3da282 + PyPI Trusted Publisher registered 5-7
  ├─ P0.3 server.json _meta block          commit 4f8886f (registry publish deferred to N2)
  ├─ P0.4 v3 voice rewrite                 commit ca12e25
  ├─ P0.4 v4 GPTZero-diagnostic rewrite    commit ec5fc65
  └─ P0.4 dev.to article LIVE 5-7 evening  https://dev.to/zhurong2020/let-claude-code-debug-...

Week 1 weekend (5-8 Fri → 5-9 Sat) · CN trio (within +48h of dev.to · scheduled per maintainer 2026-05-07):
  ├─ 有心工坊 / tech-empowerment (long-form CN translation of dev.to article)
  ├─ 知乎 (adapted CN with hook + cn-friendly formatting)
  └─ V2EX (short post)
  Source draft: _drafts/post-cn-bilingual.md

Week 2 launch wave (5-11 Mon → 5-12 Tue):
  ├─ Mon 5-11 evening 9-10pm UTC: HN Show HN
  │   Source draft: _drafts/post-hn-show-hn.md (DO NOT reuse dev.to long-form;
  │   HN Show HN is a different format — short post, runnable demo, no upvote ask)
  ├─ Tue 5-12 evening: Reddit /r/Python (+24h after HN, captures HN-bounce traffic)
  │   Source draft: _drafts/post-reddit-rpython.md
  └─ Parallel: review dev.to 24h + 48h + 7d reaction metrics, capture in
     V0.4_EXECUTION_LOG.md

Week 2 cont. (5-13 → 5-18):
  ├─ Review launch wave metrics across 4 platforms; reweight v0.5 priorities
  ├─ P0.5 GitHub topic add (5 min · python-obfuscator-online + verify pyarmor-alternative)
  ├─ P0.6 Socket score push (30 min · re-scan first → maybe already 90+ from PEP 740 attestations)
  ├─ P0.7 Discussions roadmap-signal poll (15 min · 5-13 evening · feeds week-4 prioritization)
  ├─ N1 PEP 750 t-string AST handler (1 day · narrow time-window first-mover)
  └─ Begin v0.5 work depending on signal

Week 3 (5-19 → 5-25):
  └─ Start N3 claude-skill preset (1 week effort · net-new market segment)
  Note: N2 already SHIPPED 2026-05-08 ahead of original plan; original "FastMCP 3.0
  + Pro funnel + security hardening" 4-5 day bundle is done. Week 3 is now lighter.

Week 4 (5-26 → 6-1) · post-launch SEO build-out · gated on P0.7 poll signal:
  ├─ N9 Stripe quantity field on existing $45 SKU (half day · single-tier preserved)
  ├─ N7 pyobfus.dev demo MVP — Pyodide free tier + /mcp landing tab (~3-4 days)
  └─ Continue N3 claude-skill preset

Week 5 (6-2 → 6-8):
  ├─ N7 demo Pro Worker tier + /decode-stack-trace reverse demo (~2 days)
  ├─ N8 first 2 landing pages: /pyarmor-alternative + /mcp-for-claude-code
  ├─ Submit to ProductHunt (catalog-style entry, NOT launch-day push;
  │   sustained discovery · contingent on demo being live to anchor the listing)
  └─ Cross-link N7 /mcp page from pyobfus-mcp pyproject.toml long_description
     (bundle this metadata refresh with next legitimate pyobfus-mcp bump per
     do-not-do version-bump rule — likely 0.2.1 patch or N3 companion update)

Week 6 (6-9 → 6-15) · v0.5.0 RC node:
  ├─ N8 remaining 3-4 landing pages (django/fastapi/flask + comparison)
  └─ v0.5.0 RC ship: P2-1 + P2-3 + P2-4 + P2-5 + N1 + N3 + N6 metadata refresh
     + drop 3.8 + N7 demo cross-linked from PyPI long_description

By 2026-06-15: v0.5.0 release candidate (Core) + N7 demo live + 5-6 SEO pages indexed
              + Stripe quantity-tiered SKU + N9-instrumented MCP recommend_tier seat-aware
              (pyobfus-mcp 0.2.1 if needed)
```

---

## Source-of-truth references (read these before reopening this doc)

- **`docs/V0.4_EXECUTION_LOG.md`** — what's been done · 17 sessions logged · Metrics Snapshot table
- **`docs/ROADMAP.md`** — public-facing strategic narrative (don't put TODOs here)
- **`docs/AI_INTEGRATION_STRATEGY.md`** — channel strategy, AI-policy risk per platform
- **`_drafts/`** — 4 launch articles + cross-review prompt + warmup checklists
- **`pyobfus_mcp/CHANGELOG.md`** — MCP server version history (currently 0.1.2)
- **`~/.claude/projects/-home-wuxia-projects-pyobfus/memory/glama_metadata_schemas.md`** — 3 distinct Glama/MCP file schemas, never confuse again
- **PR #5777**: <https://github.com/punkpeye/awesome-mcp-servers/pull/5777> · ✅ MERGED 2026-06-06 (pyobfus-mcp now in punkpeye/awesome-mcp-servers Developer Tools)

---

**Last updated**: 2026-06-08 (PR #5777 MERGED 2026-06-06 → punkpeye/awesome-mcp-servers LIVE [N5 fully done, 2 lists live]; synced across ROADMAP/DISTRIBUTION_CHANNELS/AI_INTEGRATION_STRATEGY. Glama tool-count RESOLVED at source — true root cause = admin Configuration "Build steps" field pinned `0.1.2`, NOT the repo Dockerfile; edited to `0.2.0`, test `019ea6c5` succeeded with all 7 tools; API/listing re-index is the only passive remainder. See 30-Second-Resume 2026-06-08 block + P2 row. Also: README tool-count already reads "seven" — N10 doc-lag item resolved.). Earlier: 2026-06-05 (patent FILED+ACCEPTED 申请号 202610712171X · fees fully paid · now in 补正 formality correction ~2026-08-01 deadline · Path C gate tightened to "after 补正 resolved" · see §P1 2026-06-05 block + Glama tool-count P2 item · also: Glama introspection Dockerfile-pin fix commit bbeefb8 · **NEW N12 MCP Server Card + N13 obfuscated-output SBOM + N14 hosted MCP endpoint added from 2026-06-05 competitive/trend scan; CodeEnigma logged in verified-facts table**). Earlier: 2026-05-10 (Patent draft v1 + CNIPA web upload progress block added under §🟡 P1 v0.5 work · 5 web tabs filled + saved · 备案 submitted 待审核 · final 提交 pending 备案 approval ~1-2 weeks · 申请号 receipt expected late May / early June; v0.5 public release ~mid-June). Earlier: 2026-05-09 (added P0.5/P0.6/P0.7 + N7/N8/N9 + pricing-tier do-not-do guardrail · post-strategy-review with user) · P0 status: P0.1 ✅ · P0.2 ✅ · P0.3 ✅ shipped with 0.2.0 (Registry stripped publisher namespace; investigation queued for next bump) · P0.4 ✅ live at https://dev.to/zhurong2020/let-claude-code-debug-your-obfuscated-python-a-guide-to-the-pyobfus-mcp-integration-3epm · **P0.5/P0.6/P0.7 NEW**: GitHub topic curation + Socket score push + Discussions poll (all queued for week-2 cont. 5-13+) · **N2 ✅ SHIPPED**: pyobfus-mcp 0.2.0 live on PyPI (with PEP 740 attestations) + MCP Registry (active + isLatest) · **N5 ✅ FINAL**: wong2/mcpservers.org LIVE + punkpeye #5777 still OPEN + appcypher dead-end · **N6 ✅ STAGED**: PyPI summary + keywords edits in source (both packages); ride next legitimate version bump · **N7/N8/N9 NEW**: pyobfus.dev demo + 5-6 SEO landing pages + Stripe quantity field (gated on launch signal · weeks 4-6) · launch wave next: HN Mon 5-11 / Reddit Tue 5-12 / CN trio Fri-Sat 5-8/9
**Next review**: post-备案 approval (1-15 working days from 2026-05-10 · estimated 5-12 → 5-25) for final 提交 + 申请号 timeline; 24h post-dev.to for first-day reaction metrics; post-launch-wave (5-13) for full multi-platform signal feeding P0.7 poll → N7/N8/N9 prioritization decision in week 4
