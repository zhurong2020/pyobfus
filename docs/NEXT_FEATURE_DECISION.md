# Next Feature Decision

**Status (updated 2026-08-04): superseded for this cycle, not currently active.**
The launch wave (2026-08-01) came back with essentially flat engagement
everywhere (see `docs/POST_V0.4_TODO.md` item 2's checkpoint) — too thin for
this poll mechanism to have meant much — so the maintainer made a **direct
decision 2026-08-01** overriding the poll gate and picked **P2-17 (provenance
manifest) + P2-19 (`--preset ml`)** straight from the already-scanned ROADMAP
candidates instead. **Both shipped in pyobfus 0.5.5, 2026-08-02** (PRs #26/#27;
see `docs/POST_V0.4_TODO.md` § item 6). The poll was never actually opened —
the sections below describe the mechanism as designed, not something
currently in flight. Re-activate this process only if a future launch
generates enough real engagement to make polling meaningful again; until
then, next-feature selection is a direct maintainer call from the ROADMAP
candidate list (see `docs/ROADMAP.md`'s open P2-2/P2-6/P2-12 through P2-16/
P2-21 items).

## Decision window

Open the launch poll using
[`_drafts/launch-v0.5.4/github-poll.md`](https://github.com/zhurong2020/pyobfus/blob/main/_drafts/launch-v0.5.4/github-poll.md),
then review it after **14 days or 10 votes**, whichever comes first. Record the
opening date, closing trigger, links, and raw counts below.

| Signal | ML preset | Provenance manifest | PyInstaller guide | MCP integrity |
|---|---:|---:|---:|---:|
| Poll votes | — | — | — | — |
| Substantive comments | — | — | — | — |
| Launch-channel requests | — | — | — | — |
| Existing issue reactions | — | — | — | — |

## Selection rule

1. Prefer described workflows and reproducible pain over bare votes.
2. Require at least two independent users describing the same need before a
   large implementation; otherwise choose the smallest reversible experiment.
3. Break ties by expected user value, then implementation cost, then fit with
   pyobfus's AST + AI-debuggable scope.
4. Publish the result and rationale before implementation starts.

## Candidate experiments

- **ML/model-serving preset:** first add a failing fixture for one real serving
  framework and validate preserved reflection points.
- **Signed provenance manifest:** first define a versioned JSON schema and an
  unsigned deterministic manifest; add signing only after the contract settles.
- **PyInstaller guide:** first prove one clean obfuscate-then-bundle example in
  CI before expanding into a cookbook.
- **MCP integrity:** first threat-model which metadata can be trusted locally and
  demonstrate a changed-tool-surface detector.

## Decision record

- Poll opened: never opened — superseded by direct maintainer decision, see
  Status above
- Review trigger reached: N/A
- Selected candidate: P2-17 (provenance manifest) + P2-19 (`--preset ml`),
  chosen directly from ROADMAP, 2026-08-01
- First bounded experiment: both fully implemented and shipped as pyobfus
  0.5.5 (2026-08-02), not a bounded experiment — the maintainer judged the
  candidates low-risk/high-relevance enough to ship outright
- Rationale/link: `docs/POST_V0.4_TODO.md` § item 6; `docs/ROADMAP.md`
  "Additions from 2026-06-22 competitive + agentic-discoverability scan"
