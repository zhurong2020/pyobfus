# Next Core release: readiness and decision boundary

Prepared 2026-10-28. Public Core is still **0.10.0**. This is a reviewable
release plan, not authorization to tag or publish. The maintainer's standing
rule requires a separate explicit release approval. The GitHub billing limit
on private repositories is expected to clear after 2026-11-01; no private
repository workflow is needed for this Core release.

## Proposed scope

Recommend **0.11.0** because the unreleased Core changes include an additive
`--check-delivery` diagnostic surface alongside a correctness fix. The exact
version remains a maintainer decision at the release gate. No MCP, runtime,
VS Code extension or Action release is required by these changes.

| Change since Core 0.10.0 | Evidence | Release wording limit |
|---|---|---|
| P0 package-root module-attribute compatibility, optional conservative preservation | [P0 validation](P0_MODULE_ATTRIBUTE_COMPAT_2026-10-28.md), PR #154 | The default still warns and may emit an unusable artifact for unproved dynamic accesses. The opt-in preserves recognized names at an obfuscation cost; it is not a universal proof. |
| P2 bounded `.pyc` evidence and frozen outer-container warnings | [P2 validation](P2_DELIVERY_DIAGNOSTICS_2026-10-28.md), PR #156 | A frozen payload is not unpacked or declared safe. `warn` remains exit code 0; consumers must inspect JSON status/findings. |

P1 packaging validation and the Linux 3.15t smoke are **validation records**,
not additional shipped capabilities. Cross-file L3 still rejects free-threaded
builds; see [3.15t record](PYTHON315_FREETHREADING_VALIDATION_2026-10-28.md).

## Gates before publication

1. Maintainer confirms scope, version and timing. Keep the two changes in
   `[Unreleased]` until the release commit.
2. Release-prep commit updates `pyproject.toml`, both README headlines,
   `docs/index.md`, changelog version/date and `CITATION.cff` together. The
   release date and version-specific Zenodo DOI must reflect actual publication;
   do not invent them in advance.
3. Run `scripts/check.sh`, all four test roots separately, build wheel/sdist,
   inspect package contents and test fresh installs on supported interpreters.
   The public PR needs its required CI result and CodeQL, plus the existing
   packaging lane; avoid adding a new matrix for this release.
4. Only after explicit approval, merge the release commit and tag through the
   existing OIDC workflow. Verify the exact PyPI artifacts and PEP 740
   attestations, GitHub Release, fresh-install behavior and eventual Zenodo
   archive. Keep MCP/runtime versions unchanged unless a separate need appears.

The private `workspace-meta` Guard remains deferred until the account limit
clears and its workflow costs have been reviewed. Do not use this release as a
reason to trigger private CI early.
