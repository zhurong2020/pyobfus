# Next Feature Decision

**Status:** waiting for launch feedback. Do not start a large feature merely to
fill the gap while the poll is running.

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

- Poll opened: pending external publication
- Review trigger reached: pending
- Selected candidate: pending evidence
- First bounded experiment: pending
- Rationale/link: pending
