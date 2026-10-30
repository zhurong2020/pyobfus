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

The first standalone runtime release is `pyobfus-runtime` 0.1.0. Its release
workflow uses the same OIDC/PEP 740 path as Core and MCP, but its provenance
must be checked against the runtime project and filename rather than `pyobfus`.

## Quick Endpoint Check

Use this to confirm that PyPI has provenance JSON for a published artifact:

```bash
curl -fsS \
  -H 'Accept: application/vnd.pypi.integrity.v1+json' \
  https://pypi.org/integrity/pyobfus/0.5.27/pyobfus-0.5.27-py3-none-any.whl/provenance \
  >/tmp/pyobfus-provenance.json
```

For the runtime release:

```bash
curl -fsS \
  -H 'Accept: application/vnd.pypi.integrity.v1+json' \
  https://pypi.org/integrity/pyobfus-runtime/0.1.0/pyobfus_runtime-0.1.0-py3-none-any.whl/provenance \
  >/tmp/pyobfus-runtime-provenance.json
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
  https://files.pythonhosted.org/packages/.../pyobfus-0.5.27-py3-none-any.whl
```

Repeat for each wheel/sdist you intend to trust or mirror. Do not verify only
one file and assume the whole release is covered.

## Latest Verified Snapshot — 2026-10-30

Core 0.11.1 and MCP 0.3.17 were published from the same reviewed commit on
2026-10-30. `pypi-attestations 0.0.30 verify pypi --repository`
cryptographically verified both wheel and sdist for each project against
`https://github.com/zhurong2020/pyobfus`. PyPI JSON digests:

| Project | Version | Wheel SHA-256 | sdist SHA-256 |
|---|---:|---|---|
| `pyobfus` | `0.11.1` | `4d067b57ba55ef654094e3da4ae8e5d2947de5601a2dea6d07a80139683a4ed4` | `be3141c6c8ffdaca1e4a8a19376bb25cb44ee33b3241cc84d31d76bb8bf0357a` |
| `pyobfus-mcp` | `0.3.17` | `422f8c06b1fbf34ff170a878badf4f5f434b91261e6e1770b91af6e4fb4a9a50` | `b9a87c15fd1b8e773d3b7b453f67dd785df952246a16f558870681c11415de38` |

Both artifacts for each project passed cryptographic verification. Core and
MCP fresh installs and `pip check` passed in isolated environments; the MCP
install resolved Core 0.11.1 and runtime 0.1.1. MCP release workflow
`41020413288` succeeded. Both MCP Integrity API endpoints returned HTTP 200.
The MCP Registry versions endpoint reports 0.3.17
`active` / `isLatest=true`. See the [Core GitHub Release](https://github.com/zhurong2020/pyobfus/releases/tag/v0.11.1),
[MCP GitHub Release](https://github.com/zhurong2020/pyobfus/releases/tag/mcp-v0.3.17),
and [official MCP Registry](https://registry.modelcontextprotocol.io/v0/servers/io.github.zhurong2020%2Fpyobfus-mcp/versions).
The Zenodo archive for Core 0.11.1 was not yet discoverable in the API at
verification time; follow up and add its DOI when available.

## Previous Verified Snapshot — 2026-10-27

Core 0.10.0 was verified against both exact PyPI artifact URLs with
`pypi-attestations` 0.0.30 using `verify pypi --repository`
for `https://github.com/zhurong2020/pyobfus`. Wheel and sdist both passed
repository-bound cryptographic verification. Downloaded SHA-256 matched
PyPI JSON (`8b40bc9d71b7aa5ae31966edb35d374ec51d4f9d4f056b312b1b2125ea964d4b`
for the wheel;
`7365c9f1ede3c2484ef3ac0fb52a2a51ab1f460dcfb10ad6cb41483e1b7d2c06`
for the sdist), and both Integrity API endpoints returned HTTP 200 with the
expected content type. The tagged [OIDC release workflow](https://github.com/zhurong2020/pyobfus/actions/runs/40484190827)
succeeded. Fresh Python 3.10 and 3.15 installs resolved runtime 0.1.1,
passed `pip check` and executed generated code. The
[GitHub Release](https://github.com/zhurong2020/pyobfus/releases/tag/v0.10.0)
and [Zenodo v0.10.0 archive](https://doi.org/10.5281/zenodo.23687523)
were independently checked.

## Previous Verified Snapshot — 2026-10-26

MCP 0.3.16 was verified on 2026-10-26 with `pypi-attestations verify pypi`
against both exact PyPI URLs. Wheel and sdist both passed repository-bound
cryptographic verification. PyPI's Integrity API returned provenance for both
files, and the downloaded wheel SHA-256 matched the PyPI JSON digest
`69603cc66265910f07a32954ae45c6c18e231cd6f19734d83e944f9c4ef430b1`.
Fresh PyPI installs on Python 3.10 and 3.15 passed dependency checks, 153
MCP tests and the nine-tool stdio contract. See
[MCP release evidence](MCP_SDK_2X_RELEASE_PREP_2026-10-26.md).

## Earlier Verified Snapshot — 2026-10-14

Core 0.7.1 and MCP 0.3.13 wheel/sdist were each verified with
`pypi-attestations 0.0.30 verify pypi --repository https://github.com/zhurong2020/pyobfus`
against their exact PyPI artifact URLs. All four cryptographic verifications
passed; publisher repository/workflow were independently checked as
`zhurong2020/pyobfus` / `release.yml`. Full release-commit CI passed 27/27;
fresh Python 3.10/3.14 installations and generated-code smoke checks passed.

| Project | Version | Artifacts verified |
|---|---:|---|
| `pyobfus` | `0.7.1` | wheel and sdist |
| `pyobfus-mcp` | `0.3.13` | wheel and sdist |

## Historical endpoint snapshot — 2026-09-16

Checked on 2026-09-16 after the v0.5.27 release (pyobfus-mcp last released
`0.3.12` on 2026-09-07 and remains independently verified):

| Project | Version | Artifact | Integrity API |
|---|---:|---|---|
| `pyobfus` | `0.5.27` | `pyobfus-0.5.27-py3-none-any.whl` | `200` |
| `pyobfus` | `0.5.27` | `pyobfus-0.5.27.tar.gz` | `200` |
| `pyobfus-mcp` | `0.3.12` | `pyobfus_mcp-0.3.12-py3-none-any.whl` | `200` |
| `pyobfus-mcp` | `0.3.12` | `pyobfus_mcp-0.3.12.tar.gz` | `200` |

Commands used:

```bash
curl -fsSI -H 'Accept: application/vnd.pypi.integrity.v1+json' \
  https://pypi.org/integrity/pyobfus/0.5.27/pyobfus-0.5.27-py3-none-any.whl/provenance
curl -fsSI -H 'Accept: application/vnd.pypi.integrity.v1+json' \
  https://pypi.org/integrity/pyobfus/0.5.27/pyobfus-0.5.27.tar.gz/provenance
curl -fsSI -H 'Accept: application/vnd.pypi.integrity.v1+json' \
  https://pypi.org/integrity/pyobfus-mcp/0.3.12/pyobfus_mcp-0.3.12-py3-none-any.whl/provenance
curl -fsSI -H 'Accept: application/vnd.pypi.integrity.v1+json' \
  https://pypi.org/integrity/pyobfus-mcp/0.3.12/pyobfus_mcp-0.3.12.tar.gz/provenance
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
