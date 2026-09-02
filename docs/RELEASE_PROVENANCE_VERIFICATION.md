# Release Provenance Verification

This runbook covers pyobfus's own PyPI release provenance. It is separate from
`--provenance-manifest`, which records provenance for a user's obfuscated output.
It also remains separate from self-dogfooding: a tool successfully scanning or
processing its own source is regression evidence, not release authenticity.

PyPI's Integrity API exposes PEP 740 provenance objects at:

```text
https://pypi.org/integrity/<project>/<version>/<filename>/provenance
```

PyPI's own documentation is explicit about the security boundary: attestations
bind a distribution file to the identity and digest that produced it. They do
not prove that the code is bug-free, vulnerability-free, or trustworthy.

## Quick Endpoint Check

Use this to confirm that PyPI has provenance JSON for a published artifact:

```bash
curl -fsS \
  -H 'Accept: application/vnd.pypi.integrity.v1+json' \
  https://pypi.org/integrity/pyobfus/0.5.20/pyobfus-0.5.20-py3-none-any.whl/provenance \
  >/tmp/pyobfus-provenance.json
```

Exit code `0` plus `Content-Type: application/vnd.pypi.integrity.v1+json` means
the provenance object is present. This is a presence check, not a full
cryptographic verification.

## Full Verification

For cryptographic verification, use PyPI's recommended `pypi-attestations` CLI
against the exact artifact URL from PyPI's JSON API:

```bash
python -m pip install pypi-attestations

pypi-attestations verify pypi \
  --repository https://github.com/zhurong2020/pyobfus \
  https://files.pythonhosted.org/packages/.../pyobfus-0.5.20-py3-none-any.whl
```

Repeat for each wheel/sdist you intend to trust or mirror. Do not verify only
one file and assume the whole release is covered.

## Latest Verified Snapshot

Checked on 2026-09-02 after the v0.5.20 / mcp-v0.3.10 release:

| Project | Version | Artifact | Integrity API |
|---|---:|---|---|
| `pyobfus` | `0.5.20` | `pyobfus-0.5.20-py3-none-any.whl` | `200` |
| `pyobfus` | `0.5.20` | `pyobfus-0.5.20.tar.gz` | `200` |
| `pyobfus-mcp` | `0.3.10` | `pyobfus_mcp-0.3.10-py3-none-any.whl` | `200` |
| `pyobfus-mcp` | `0.3.10` | `pyobfus_mcp-0.3.10.tar.gz` | `200` |

Commands used:

```bash
curl -fsSI -H 'Accept: application/vnd.pypi.integrity.v1+json' \
  https://pypi.org/integrity/pyobfus/0.5.20/pyobfus-0.5.20-py3-none-any.whl/provenance
curl -fsSI -H 'Accept: application/vnd.pypi.integrity.v1+json' \
  https://pypi.org/integrity/pyobfus/0.5.20/pyobfus-0.5.20.tar.gz/provenance
curl -fsSI -H 'Accept: application/vnd.pypi.integrity.v1+json' \
  https://pypi.org/integrity/pyobfus-mcp/0.3.10/pyobfus_mcp-0.3.10-py3-none-any.whl/provenance
curl -fsSI -H 'Accept: application/vnd.pypi.integrity.v1+json' \
  https://pypi.org/integrity/pyobfus-mcp/0.3.10/pyobfus_mcp-0.3.10.tar.gz/provenance
```

## Verification hierarchy

Use complementary evidence rather than treating any single check as complete:

1. tagged source and reviewed release workflow define the intended inputs;
2. the hosted OIDC build and PyPI/PEP 740 attestation bind each published file
   to its builder identity and digest;
3. full attestation verification checks that binding, not merely endpoint
   presence;
4. a fresh environment installs the exact wheel and runs version/CLI/canary
   smoke tests;
5. self-dogfooding and local `--provenance-manifest` add regression/debugging
   evidence but do not supersede the hosted attestation.

The staged two-version/canary policy is documented in
[`SELF_DOGFOODING_BEST_PRACTICES.md`](SELF_DOGFOODING_BEST_PRACTICES.md).

## Sources

- PyPI Integrity API: <https://docs.pypi.org/api/integrity/>
- PyPI consuming attestations: <https://docs.pypi.org/attestations/consuming-attestations/>
- PEP 740: <https://peps.python.org/pep-0740/>
