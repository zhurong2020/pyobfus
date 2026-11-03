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

## Final version commit and checks

- [ ] Recheck customer CI replies and any newly failed workflow before proceeding.
- [ ] Confirm the final release scope above and obtain release approval.
- [ ] In the same release commit, set `pyproject.toml` to 0.12.0, promote Core's
  `[Unreleased]` changelog with the real release date, update the README banner,
  and update `CITATION.cff` version/date. Do not invent a new Zenodo record DOI
  before the archive exists. Worker logging entries already say deployed.
- [ ] README and release notes explicitly state that Pro CI builds need
  `PYOBFUS_LICENSE_KEY` or registered runner state. Link the
  [CI licensing guide](CI_LICENSING.md). Correctly describe Fernet without
  implying that the generated artifact format changed.
- [ ] Refresh the editable package metadata after the version edit.
- [ ] Run `scripts/check.sh`, `scripts/check_unreleased_changelogs.py` and
  `scripts/check_runtime_version.py` with the repository `venv/` Python.
  A sibling's pending changelog is reviewed, not automatically a reason to
  release that package. Record the deliberate deferrals above.
- [ ] Run each Python test root separately. Include the benchmark smoke/key
  exposure commands from CI. Verify the MCP SDK and Python 3.15 jobs through
  their maintained workflows rather than assuming the four local roots cover them.
- [ ] Merge the version commit through normal checks, then run the manual
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

- [ ] Validate the prepared Action input through hosted consumer tests. After
  Core 0.12.0 is available, switch its temporary reviewed-source test pin to the
  published wheel, release the wrapper through its own approval path, and only
  then use `license-key` in `@v1` examples. Until then, pass the secret through the
  published Action step's `env: PYOBFUS_LICENSE_KEY`.
- [ ] Update Glama's installation step to `pyobfus==0.12.0`, then verify the
  build, MCP handshake and nine tools. Do not bump MCP solely for this install pin.
- [ ] Update workspace version records, verify the next natural backup includes
  the release evidence, and monitor customer CI replies. No duplicate notification
  mail is sent automatically by this checklist.

The DEV one-week review remains November 4 after 09:43 CST; the LinkedIn review
remains around November 5 evening. Neither is a Core release blocker.
