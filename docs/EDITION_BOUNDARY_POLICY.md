# Community / Pro Edition Boundary Policy

**Status:** active product and engineering policy  
**Adopted:** 2026-10-02

> Community helps users reliably obfuscate, inspect, verify, and debug;
> Pro helps commercial users protect intellectual property, constrain where and
> how artifacts execute, and trace leaks.

This document is the durable source of truth for deciding whether an existing
or future capability belongs in Community or Pro. Feature tables describe the
current product; this policy explains how those tables must evolve.

## The free floor

Community must remain useful for a real project, not merely a demo. The
following categories stay free:

- correctness, security fixes, Python/framework compatibility, and stable data
  contracts;
- the complete basic obfuscation workflow: project-wide name mangling, simple
  encoding, configuration, Community/framework presets, and file selection;
- local inspection and safe operation: risk scanning, SARIF, dry-run, syntax
  verification, mapping/unmapping, provenance, and build reports;
- reproducibility and basic local integrations through the CLI, MCP, VS Code,
  and GitHub Actions;
- documentation needed to understand limitations and ship an artifact safely.

Community has no product-imposed file or line limit. The optional `max_files`
and `max_total_loc` settings are user-selected safety rails at every tier.

### Why project size is not a paywall

This is an explicit product decision, not an accidental omission. The original
Community design considered a five-file / 1,000-line limit, partly in response
to PyArmor's free-trial restriction on “big scripts.” pyobfus does not retain
that limit or replace it with another arbitrary threshold such as 2,000 lines:

- file and line limits gate completion of the basic workflow rather than a
  commercial protection outcome;
- splitting a file trivially bypasses the limit, so it is a weak and confusing
  conversion mechanism;
- large single-file utilities, generated code, and data scripts are penalized
  even when they have no commercial protection requirement;
- the default cross-file path and named Community presets have historically
  operated without those limits, so enforcing them now would remove an
  established Community capability;
- the 2026-10-02 evidence showed a small adoption/trial funnel, not free-tier
  substitution for Pro. Adding adoption friction would address the wrong
  problem.

PyArmor remains a useful market reference, but pyobfus follows the underlying
commercial principle—charge for stronger protection and organizational value—
rather than copying its trial-size constraint. A future change to this decision
requires direct cannibalization evidence and the explicit boundary-change
process below; a round-number threshold by itself is not evidence.

We do not put correctness, compatibility, vulnerability fixes, or the ability
to evaluate output honestly behind a paywall. We also do not remove an existing
Community capability solely to manufacture conversion pressure.

## What customers buy in Pro

Pro capabilities should deliver at least one of four commercial values:

| Value group | Customer outcome | Current examples |
|---|---|---|
| Protection strength | Raises reverse-engineering cost beyond basic AST mangling | AES string encryption, control-flow flattening, dead-code injection, anti-debugging, Selective Opacity, sealing |
| Protected assets | Protects more than identifiers in source code | import strings, embedded data, Runtime String Vault, encrypted/scrubbed tracebacks |
| Distribution control | Constrains where, when, or how a shipped artifact runs | device binding, expiry, run count, platform policy, application-provided keys |
| Accountability | Attributes a build or leak to a recipient | forensic/buyer watermarking, buyer-specific builds and seals |

Paid organization services may also include managed policy, central key or
signing infrastructure, access control, audit retention, support, or an SLA.
Those are paid because the buyer and operating burden differ, not because the
local file format is artificially crippled.

## Decision rule for a new feature

Answer these questions in the feature's issue or pull request:

1. Is it necessary for correctness, security remediation, compatibility, or
   honest local verification? If yes, it is Community.
2. Is it a prerequisite for discovering, adopting, or evaluating pyobfus on a
   real project? That strongly favors Community.
3. Does it primarily increase reverse-engineering cost, protect an additional
   valuable asset, enforce a runtime/distribution policy, or identify a buyer?
   That favors Pro.
4. Is the natural buyer a team or organization needing centralized governance,
   recurring infrastructure, support, or an SLA? The managed layer may be Pro
   even when the local primitive is Community.
5. Is there external evidence for the problem and buyer—customer feedback,
   repeated user requests, a downstream integration, or observed usage? If
   not, defer the feature or keep it experimental instead of using tiering to
   invent demand.

When the answer is mixed, split the capability at a natural boundary:

- local provenance stays Community; centralized signing/KMS and team audit can
  be Pro;
- local mapping stays Community; hosted escrow, RBAC, and retention can be Pro;
- the basic Action stays Community; managed organization policy and an SLA can
  be Pro.

Do not classify by implementation difficulty, novelty, or whether a feature is
easy to gate. Classify by who receives the value and what commercial problem it
solves.

## Required change process

Any pull request that adds a capability or changes an edition boundary must:

1. state the user, buyer, problem, evidence, and decision-rule answers;
2. identify the source and license boundary (`pyobfus` may route Pro features,
   while proprietary implementations remain in the appropriate Pro package);
3. update all affected surfaces together: README, comparison tables, CLI/config
   help or schema, tests, and `[Unreleased]` changelog;
4. prove that Community correctness and existing Community workflows did not
   regress;
5. record an explicit maintainer decision before moving an existing capability
   between editions.

The Core/Pro source-separation and repository ownership rules remain defined in
[Project Structure](PROJECT_STRUCTURE.md).

## How to detect harmful over-generosity

Low sales alone are not evidence that Community is too generous. Treat free-tier
cannibalization as plausible only when evidence shows that commercial users are
solving a Pro-class problem with a Community substitute—for example, repeated
feedback that free protection is sufficient for commercial distribution, trials
that do not convert specifically because an equivalent free capability exists,
or support requests for Pro outcomes routinely satisfied by Community.

Conversely, low discovery, few trial starts, and weak downstream adoption point
to a top-of-funnel or use-case problem. The 2026-10-02 review found the latter:
small Community/extension/Action adoption and no trial registrations, with no
evidence that a free capability was replacing a Pro purchase. The response is
clearer positioning and better evidence gathering—not weakening Community.

## External reference points

This policy follows the same broad buyer-based open-core pattern used by mature
developer-tool businesses:

- [GitLab product principles](https://handbook.gitlab.com/handbook/product/product-principles/)
  describe buyer-based open-core packaging and keeping a capable open product.
- [PyArmor licensing](https://pyarmor.readthedocs.io/en/latest/licenses.html)
  separates trial/basic use from stronger protection, offline capability, and
  CI/organization needs.
- [Nuitka Commercial](https://nuitka.net/doc/commercial.html) keeps the compiler
  available while charging for commercial IP/data-protection capabilities.

These products are reference points, not templates. pyobfus keeps its own
promise: a complete, unlimited Community workflow, with payment attached to
commercial protection and control value.
