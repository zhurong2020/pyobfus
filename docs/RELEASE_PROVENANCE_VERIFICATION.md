# Release Provenance Verification

This runbook covers pyobfus's own PyPI release provenance. It is separate from
`--provenance-manifest`, which records provenance for a user's obfuscated output.

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
  https://pypi.org/integrity/pyobfus/0.5.14/pyobfus-0.5.14-py3-none-any.whl/provenance \
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
  https://files.pythonhosted.org/packages/.../pyobfus-0.5.14-py3-none-any.whl
```

Repeat for each wheel/sdist you intend to trust or mirror. Do not verify only
one file and assume the whole release is covered.

## Latest Verified Snapshot

Checked on 2026-08-17 (re-verified same-day, after the v0.5.14 / mcp-v0.3.6
release):

| Project | Version | Artifact | Integrity API |
|---|---:|---|---|
| `pyobfus` | `0.5.14` | `pyobfus-0.5.14-py3-none-any.whl` | `200` |
| `pyobfus` | `0.5.14` | `pyobfus-0.5.14.tar.gz` | `200` |
| `pyobfus-mcp` | `0.3.6` | `pyobfus_mcp-0.3.6-py3-none-any.whl` | `200` |
| `pyobfus-mcp` | `0.3.6` | `pyobfus_mcp-0.3.6.tar.gz` | `200` |

Commands used:

```bash
curl -fsSI -H 'Accept: application/vnd.pypi.integrity.v1+json' \
  https://pypi.org/integrity/pyobfus/0.5.14/pyobfus-0.5.14-py3-none-any.whl/provenance
curl -fsSI -H 'Accept: application/vnd.pypi.integrity.v1+json' \
  https://pypi.org/integrity/pyobfus/0.5.14/pyobfus-0.5.14.tar.gz/provenance
curl -fsSI -H 'Accept: application/vnd.pypi.integrity.v1+json' \
  https://pypi.org/integrity/pyobfus-mcp/0.3.6/pyobfus_mcp-0.3.6-py3-none-any.whl/provenance
curl -fsSI -H 'Accept: application/vnd.pypi.integrity.v1+json' \
  https://pypi.org/integrity/pyobfus-mcp/0.3.6/pyobfus_mcp-0.3.6.tar.gz/provenance
```

## Sources

- PyPI Integrity API: <https://docs.pypi.org/api/integrity/>
- PyPI consuming attestations: <https://docs.pypi.org/attestations/consuming-attestations/>
- PEP 740: <https://peps.python.org/pep-0740/>
