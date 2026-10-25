# Cross-file L3 preview validation

Status: 2026-10-25, unreleased development checkout. Slice D merged through
PR #126; slice E is under validation. Core 0.9.1 does not include this complete
workflow. Runtime source and version are unchanged.

## Scope and edition boundary

The user is a Pro application distributor who already controls application key
delivery and needs consistent multi-module renaming plus selected encrypted
algorithm bodies. The maintainer approved the restricted design; no new demand
survey is claimed. Encryption, key handling and runtime guard assembly stay in
`pyobfus_pro`; binding metadata, staging, recovery, delivery checks and local
mapping/unmapping remain Community. This follows
[EDITION_BOUNDARY_POLICY.md](EDITION_BOUNDARY_POLICY.md).

## Evidence so far

- Linux / CPython 3.12.3: 30 end-to-end build tests pass, including a clean
  virtual environment installed with the public `pyobfus-runtime==0.1.1` wheel.
  The target checks that Core, Pro builder and MCP imports are absent, registers
  its own provider, and executes the generated cross-module application.
- Earlier combined planner/adapter/debug/build run: 123 tests passed before
  the additional initialization, re-export and recovery cases were added.
- Real traceback saved to disk and restored via CLI with a reloaded v1 mapping:
  exact encrypted frame name restored, original line remains null.
- Wrong/missing keys, mismatched interpreter magic before provider invocation,
  fresh spawn bootstrap, relative imports and re-exports, same-named functions,
  comprehensions/lambdas, mixed delivery, extra/missing/changed files, competing
  empty output, partial metadata publication and interrupted ownership recovery
  have executable regression coverage.
- A package re-export cycle with module attribute calls exposed an existing
  Core proof limitation. New L3 mode refuses unproved module accesses; it does
  not silently publish a broken artifact or broaden Core's compatibility claim.
- Full regression: Core 4621 passed / 54 skipped, MCP 153 passed, integration
  352 passed / 10 skipped, runtime 24 passed. Final focused feature/mapping/
  delivery check: 157 passed. `scripts/check.sh` passed.

## Required platform matrix

| Platform | Python 3.10 | Python 3.12 | Python 3.15 |
|---|---|---|---|
| Linux | pending hosted job | local 30 build tests passed | pending hosted job |
| Windows | pending hosted job | pending hosted job | pending hosted job |

The new `crossfile-opacity` CI job runs all four feature test modules in these
six cells and installs public runtime 0.1.1 in an independent target venv.
No Windows result, different-minor artifact portability, free-threading or
frozen-package support is inferred from local Linux tests.

## Remaining gate

Finish full-root regression, self-review and hosted matrix; inspect the PR
checks before merging. Do not release automatically. Detailed continuing
progress is in [PROGRESS_2026-10-25.md](PROGRESS_2026-10-25.md).
