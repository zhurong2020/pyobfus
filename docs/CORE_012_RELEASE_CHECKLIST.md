# Core 0.12.0 release checklist

Prepared 2026-11-03 for a release on or after 2026-11-04. This is a preparation
record, not evidence that 0.12.0 has been published. Release approval is separate
from approval to prepare and test the changes.

## Scope

| Component | Planned action | Reason |
|---|---|---|
| Core | Release 0.12.0 | Consistent Pro build entitlement and device-free CI licensing |
| MCP | Keep 0.3.17 | No MCP implementation change in this release; existing CLI inheritance remains applicable |
| Runtime | Keep 0.1.1 | Artifact/runtime formats and runtime code are unchanged |
| VS Code extension | Keep 0.4.3 | Development dependency fixes do not change the shipped extension runtime |
| GitHub Action | Prepare a separate wrapper update | New `license-key` input and structured tool-error gating; validate and release separately |

Security maintenance remains available without a tier change under the
[edition-boundary policy](EDITION_BOUNDARY_POLICY.md).

## Preparation completed on November 3

- Main's Core, extension and CodeQL checks passed following the dependency fixes;
  [execution evidence](EXECUTION_PROGRESS_2026-11-03.md) includes the reviewed PRs.
- Current-source wheel and sdist built successfully and passed `twine check`.
- Fresh wheel, sdist and public-release installations pass `pip check`; the maintained
  Community canary executes with the same expected result (`25`) under both.
- The installed current-source wheel rejects an unauthorized Pro build.
- An isolated CI verification fixture covers approval, rejection, rate limiting
  and an unavailable service; no license state is written under its temporary HOME.
- A real deployed-service check with the maintainer's own license also built and
  executed the Pro canary successfully, without writing local registration state.
  Private evidence is retained in `docs/internal/release-0.12.0-prep-2026-11-03/`.
- The CI licensing Worker is already deployed. No Worker deployment is required
  solely for the Core version bump.

The rehearsal source snapshot is `e0c3bc9`. Its local distributions still say
**0.11.1**, because the release version has not been changed. They differ from
the public 0.11.1 release and must never be uploaded or represented as that
release or as 0.12.0. Rebuild from the final approved version commit.
The localhost verifier is a test fixture, not evidence of live service behavior;
the live check is recorded separately. The live check did not re-read the online
device list, so it is not a fresh device-count comparison.

## Prepared release candidates

- [Core draft PR #181](https://github.com/zhurong2020/pyobfus/pull/181), revision
  `2bd86ab`, prepares the 0.12.0 metadata, README, changelog and citation date
  together. November 4 is the planned release date, not a claim of publication.
  This candidate is separate from main and has not been merged or tagged.
- The candidate also caps development mypy below 2.0: a fresh installation of
  mypy 2.4.1 reported that the configured Python 3.9 target was unsupported.
  Fresh resolution to mypy 1.20.2 checks all 119 source files with that target.
  This is a development dependency fix, not a runtime dependency change.
- The candidate's [manual full CI run](https://github.com/zhurong2020/pyobfus/actions/runs/41562014384)
  completed successfully: all **47 jobs**, including all **21 OS/Python cells**,
  passed on `2bd86ab`. The independent Linux packaging lane also passed.
  This is candidate evidence; the final adopted main/tag revision is checked
  separately on release day.
- Actual **0.12.0** wheel and sdist builds, `twine check`, private-path inspection,
  fresh installation, `pip check` and canary execution have passed. The wheel
  also passed unauthorized rejection, isolated verifier cases and a separate
  real deployed-service owner-license build. These artifacts are candidates,
  not PyPI distributions or proof of final release provenance.
- The existing VS Code extension's 53 tests also passed with interpreter
  resolution explicitly pointing to the fresh 0.12.0 wheel installation.
  The extension itself remains at 0.4.3.
- [Action draft PR #3](https://github.com/zhurong2020/pyobfus-action/pull/3),
  revision `aa9e1b7`, passed all
  [11 hosted consumer jobs](https://github.com/zhurong2020/pyobfus-action/actions/runs/41561283062).
  Besides `license-key`, it fixes structured `status: error` / exit-1 responses
  being hidden by `fail-on: never`. The exact version and moving `v1` tags
  remain unchanged; the input is not yet in the published Action.
- The post-Core-publication Action version-pin patch has been prepared and
  `git apply --check` validated; applying it and verifying the published Core
  dependency remain post-publication steps. Release-note/support drafts and
  the Glama package-pin/acceptance plan are retained in private preparation records.

## Candidate preparation checks

- [x] Prepare one candidate commit setting `pyproject.toml` to 0.12.0, promoting
  Core's changelog with the planned November 4 date, updating the README banner
  and `CITATION.cff` version/date. No new Zenodo record DOI is invented.
- [x] Candidate README and draft release notes explicitly state that Pro CI builds need
  `PYOBFUS_LICENSE_KEY` or registered runner state. Link the
  [CI licensing guide](CI_LICENSING.md). Correctly describe Fernet without
  implying that the generated artifact format changed.
- [x] Refresh the candidate environment's editable metadata after the version edit.
- [x] Run `scripts/check.sh`, `scripts/check_unreleased_changelogs.py` and
  `scripts/check_runtime_version.py` with the repository `venv/` Python.
  A sibling's pending changelog is reviewed, not automatically a reason to
  release that package. Record the deliberate deferrals above.
- [x] Run each candidate Python test root separately. Include the benchmark smoke/key
  exposure commands from CI. Verify the MCP SDK and Python 3.15 jobs through
  their maintained workflows rather than assuming the four local roots cover them.
- [x] Build actual 0.12.0 wheel/sdist and inspect them. Fresh installs, `pip check`,
  canary semantics, unauthorized rejection and live owner CI smoke pass.
- [x] Complete the candidate's full 21-cell matrix, SDK/L3/runtime jobs and
  packaging lane. Preserve exact revision and workflow results.
- [x] Refresh customer CI-support mail and confirm the public CI licensing page
  is readable on November 3. Repeat the mail/deployment check at publication.

## November 4 adoption checks

- [ ] Recheck customer CI replies and newly failed workflows before proceeding.
- [ ] Confirm the release scope and approval; verify that the candidate's planned
  date remains correct. If the date changes, update and recheck it.
- [ ] Adopt the candidate through normal merge checks. Do not reuse an old
  rehearsal artifact or assume a draft is an already-published release.
- [ ] On the final version revision, recheck metadata and required commands as
  applicable; the candidate evidence is retained as preparation, not substituted
  for the final revision's checks.
- [ ] Run the manual
  full CI matrix on that exact main revision and verify CodeQL. November 3's
  passing 13-cell push matrix is not the final 21-cell release matrix.
- [ ] Rebuild wheel/sdist from the final version revision. Run `twine check`,
  inspect wheel contents, install in a fresh environment outside checkout import
  paths, run `pip check`, the canary and the entitlement checks, and retain hashes.

## Publish and verify

- [ ] Confirm the release tag points to the checked version revision. Push
  `v0.12.0` only as the authorized release step; `release.yml` uses PyPI Trusted
  Publishing/OIDC with PEP 740 attestations. Do not substitute a manual token
  upload, or invoke the workflow's publishing fallback as a dry run.
- [ ] Verify PyPI version and wheel/sdist hashes against the workflow artifacts.
  Cryptographically verify both distributions under the
  [provenance runbook](RELEASE_PROVENANCE_VERIFICATION.md); an HTTP 200 alone is
  only an attestation-presence check.
- [ ] Fresh-install the exact PyPI 0.12.0 wheel, check dependency resolution,
  and repeat Community, no-license rejection and live owner CI smoke cases.
- [ ] Verify GitHub Release notes, Zenodo's archive/version and concept DOI,
  then update the verified DOI evidence and citation record as needed.
- [ ] Verify Read the Docs' latest successful build revision and the public
  `CI_LICENSING` page. If a local challenge blocks access, distinguish the
  access limitation from an actual deployment failure.
- [ ] Prepare a short release verification record; keep customer and credential
  details in ignored private records.

## Channel follow-up

- [x] Validate the prepared Action input through hosted consumer tests.
- [ ] After Core 0.12.0 is available, switch its temporary reviewed-source test pin to the
  published wheel, release the wrapper through its own approval path, and only
  then use `license-key` in `@v1` examples. Until then, pass the secret through the
  published Action step's `env: PYOBFUS_LICENSE_KEY`.
- [ ] Update Glama's installation step to `pyobfus==0.12.0`, then verify the
  build, MCP handshake and nine tools. Do not bump MCP solely for this install pin.
- [ ] Update workspace version records, verify the next natural backup includes
  the release evidence, and monitor customer CI replies. No duplicate notification
  mail is sent automatically by this checklist.

Use the [post-release observation table](CORE_012_POST_RELEASE_OBSERVATION.md)
for T0, support triage and subsequent checkpoints; future results remain unfilled.

The DEV one-week review remains November 4 after 09:43 CST; the LinkedIn review
remains around November 5 evening. Neither is a Core release blocker.
