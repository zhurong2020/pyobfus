# Supply-Chain Assurance

How pyobfus's existing, shipped evidence maps to the current open standards an
auditor or procurement reviewer is likely to ask about — **SLSA v1.2**,
**CycloneDX 1.7 (ECMA-424 2nd ed.)**, and **PEP 740** attestations. This page
does not add a mechanism; it names, in standard vocabulary, what the release
pipeline and the build/provenance outputs already produce, and states the
level honestly rather than over-claiming.

This is the reader-facing anchor of pyobfus's "verifiability" line. The three
underlying documents remain the source of truth for each artifact:
[Verifiable build report](VERIFIABLE_BUILD_REPORT.md),
[Provenance manifest](PROVENANCE_MANIFEST.md),
[SARIF code scanning](SARIF_CODE_SCANNING.md).

## What pyobfus produces today

| Evidence | Where it comes from | What it establishes |
|---|---|---|
| **PEP 740 attestations** | GitHub Actions release workflow → PyPI Trusted Publishing (OIDC, no long-lived token) | Binds the wheel/sdist digest to an authenticated publishing identity and its claimed publication event; verifiable against PyPI's integrity API |
| **Verifiable build report** (`--build-report`) | Core, at build time | A versioned fact model of one build: selection, effective config, transform/cache counters, syntax-verification evidence, **output SHA-256**, artifact roles |
| **Provenance manifest** (`--provenance-manifest`) | Core, at build time | Supply-chain relationships for one run (input/output roots, `config_hash`, git commit, mapping digest) with an **embedded CycloneDX section** |
| **SARIF** (`--check --sarif`) | Core preflight | Code-scanning-format projection of findings, ingestible by GitHub code scanning |
| **CodeQL** | CI on every push | Static analysis of the codebase itself |

## Mapping to SLSA v1.2 (Build track)

The release workflow's pinned PyPI publishing action produces **PyPI Publish
attestations**. A verified attestation binds an artifact digest to a Sigstore
authenticated publisher identity (including the expected repository/workflow)
and records that publisher's claim that it published the artifact to PyPI.
Consumers must verify both the digest and expected identity. See the
[PyPI Publish predicate](https://docs.pypi.org/attestations/publish/v1/) and the
[pinned action implementation](https://raw.githubusercontent.com/pypa/gh-action-pypi-publish/7245906fb61fa33a13554f9d5fb856fe61758086/attestations.py).

This establishes publication identity and artifact integrity, not how the
artifact was built, the completeness of build inputs, or isolation of the
build/signing control plane. PEP 740 is an attestation distribution mechanism;
a Publish predicate alone does not establish SLSA build provenance.
**No SLSA Build level is claimed.** L1/L2 attainment and L3 key isolation or
unforgeability require a separate assessment against the
[SLSA v1.2 build requirements](https://slsa.dev/spec/v1.2/build-requirements).
Using GitHub-hosted ephemeral runners does not by itself prove those controls.

These assurances concern publication of the pyobfus package, not the security
of code a user obfuscates; see the [threat model](THREAT_MODEL.md).

## Mapping to CycloneDX 1.7 / ECMA-424

CycloneDX 1.7 (published Oct 2025, ratified as ECMA-424 2nd ed. Dec 2025) is the
last release of the 1.x line and stays backward compatible with 1.4–1.6.

- The provenance manifest's embedded CycloneDX section now declares
  `specVersion: "1.7"`. The emitted field subset is valid under **both 1.6 and
  1.7**; `--verify-provenance-manifest` accepts either, so manifests written by
  older releases remain valid.
- pyobfus **deliberately does not yet use** 1.7's new optional structures
  (Data Provenance & Citations, TLP distribution constraints, CBOM). TLP is a
  sharing label, not access control, and the citation blocks are not needed for
  a single-run manifest. Declaring 1.7 is an honesty upgrade, not a feature
  claim. See [Provenance manifest](PROVENANCE_MANIFEST.md).

The build report's `outputs[].sha256` gives the component-level digest an SBOM
consumer expects; cross-file output is deterministic for the same input and
config (fixed in 0.5.25), so a third party can rebuild and confirm the digest.

## Mapping to PEP 740

PEP 740 attestations are published to PyPI by the OIDC release workflow. Verify
a released version without trusting this page:

```bash
# The attestation lives on PyPI's integrity endpoint, not the plain JSON API.
curl -s https://pypi.org/integrity/pyobfus/<version>/<filename>/provenance | jq .
```

(The plain `pypi.org/pypi/pyobfus/json` API reports provenance as `null`; use the
`/integrity/` endpoint.)

## What this covers in OSPS terms

This page is the "verify integrity and authenticity of releases" documentation
(OSPS-DO-03.01/03.02) and the SBOM-direction record (OSPS-QA-02.02), tying them
to the same evidence rather than duplicating it.

## Deliberately out of scope

- Any SLSA Build level claim pending a separate requirements assessment.
- Using CycloneDX 1.7's TLP/citation/CBOM blocks (not needed yet).
- Any assertion about the runtime security of obfuscated user code.
