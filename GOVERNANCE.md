# Governance

This document describes who maintains pyobfus and how decisions are made. It
exists so contributors and users know what to expect (OSPS-GV-01, OSPS-GV-03).

## Project status

pyobfus is currently a **single-maintainer** open-source project. Being honest
about that matters more than describing an aspirational committee: there is one
person with write access and release authority, and this document says so
rather than implying a larger structure.

## Roles

### Maintainer

- **GitHub:** [@zhurong2020](https://github.com/zhurong2020) — sole maintainer.
- **Holds:** write access to the repository, PyPI release authority (via GitHub
  OIDC Trusted Publishing — no long-lived tokens), the VS Code Marketplace /
  Open VSX publisher account, and the Cloudflare license Worker.
- **Responsible for:** reviewing and merging changes, cutting releases,
  triaging issues, and responding to security reports per
  [`SECURITY.md`](SECURITY.md).

Because write access equals release authority (a pushed `v*` tag triggers the
OIDC publish workflow), granting write access to anyone else is treated as
granting release authority and is not done casually. If the project gains
additional maintainers, they will be listed here, and escalated permissions
will follow a review step (OSPS-GV-04, OSPS-AC-02).

### Contributors

Anyone may contribute via pull request. The process, expectations, and
acceptance criteria are in [`CONTRIBUTING.md`](CONTRIBUTING.md). Contributions
to the Apache-2.0 core are welcome through normal PRs; Pro-edition changes are
coordinated with the maintainer directly (the Pro source is proprietary and
kept separate from the core).

## How decisions are made

- **Routine changes** (bug fixes, docs, tests): reviewed and merged by the
  maintainer. CI (tests + CodeQL, across the Python 3.9–3.14 matrix and the
  extension) must be green.
- **Feature and design decisions**: recorded in `docs/` as dated planning /
  decision documents (the current plan lives in
  [`docs/CURRENT_PLAN_ZH.md`](docs/CURRENT_PLAN_ZH.md); the ordered queue in
  [`docs/TODO.md`](docs/TODO.md)). Non-obvious product decisions get their own
  decision record, e.g. the trial strategy in
  `docs/TRIAL_STRATEGY_DECISION_2026-09-20.md`.
- **Releases**: gated behind an explicit decision, then published via the OIDC
  workflow with PEP 740 attestations. The process is documented in
  [`CONTRIBUTING.md`](CONTRIBUTING.md) / project docs.
- **Security issues**: handled privately first, per [`SECURITY.md`](SECURITY.md)
  (coordinated disclosure, 48h acknowledgement, ~90-day disclosure window).

## Public discussion

Changes are discussed in the open through
[GitHub Issues](https://github.com/zhurong2020/pyobfus/issues) and
[Discussions](https://github.com/zhurong2020/pyobfus/discussions)
(OSPS-GV-02). Design rationale is captured in `docs/` so decisions are auditable
after the fact.

## Changing this document

Because governance itself is a decision, changes to this file go through the
same PR + review path as any other change. If the maintainer set changes, update
the Roles section in the same change.
