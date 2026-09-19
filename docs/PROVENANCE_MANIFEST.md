# Obfuscation Provenance Manifest

`pyobfus --provenance-manifest PATH` writes a local JSON record for one
obfuscation run:

```bash
pyobfus src/ -o dist/ --save-mapping mapping.json --provenance-manifest provenance.json
```

The manifest is designed for offline audit and reproducibility records. It does
not call a network service, and it does not prove that the generated code is
safe or trustworthy.

For a privacy-safe operational summary that links these provenance facts to
the dry-run selection model, transformation/cache counters and verification
evidence, combine it with `--build-report`; see
[VERIFIABLE_BUILD_REPORT.md](VERIFIABLE_BUILD_REPORT.md). The provenance
manifest remains the richer supply-chain record and retains its existing v1
contract.

## Recorded Data

The top-level manifest keeps pyobfus's native provenance contract:

- `version`: pyobfus provenance-manifest format version.
- `pyobfus_version` and `tool`: pyobfus package identity used for the run.
- `created_at`: UTC creation timestamp.
- `input_root` and `output_root`: source and obfuscated output roots.
- `mode` and `preset`: obfuscation mode and selected preset, if any.
- `config_hash`: SHA-256 of the effective obfuscation config after stable JSON
  normalization.
- `source_control.git_commit`: the containing Git commit when the input path is
  inside a Git repository; otherwise `null`.
- `mapping.path` and `mapping.sha256`: mapping file location and digest when
  `--save-mapping` is used.
- `files[]`: per-file source/output paths, relative path, input SHA-256, and
  output SHA-256 when the file is present.
- `integrity`: a canonical JSON self-consistency digest for the manifest.

## CycloneDX-Compatible Section

The manifest also embeds a `cyclonedx` object:

- `bomFormat: "CycloneDX"`
- `specVersion: "1.7"` (see below for 1.6 compatibility)
- `metadata.tools.components[]`: the pyobfus tool component.
- `metadata.component`: the obfuscated output artifact, including pyobfus
  properties for config hash and mode.
- `components[]`: file components for source inputs, obfuscated outputs, and
  the debug mapping file when present.
- `dependencies[]`: relationships from each obfuscated output file to its
  source input and, when available, the mapping file.

This section intentionally lives inside the pyobfus manifest rather than
replacing it. The native fields remain the stable pyobfus contract; the
CycloneDX-compatible section gives supply-chain tools a familiar component and
relationship shape.

### Spec version: 1.7, with 1.6 compatibility

Since the release after 0.5.27, new manifests declare `specVersion: "1.7"`
(ECMA-424 2nd edition). The field subset pyobfus emits is unchanged and valid
under both 1.6 and 1.7 — the upgrade declares the current spec, it does not
start using 1.7-only fields. `--verify-provenance-manifest` accepts both
`"1.6"` and `"1.7"`, so manifests written by older releases remain valid.

That dual validity is measured, not assumed: an emitted `cyclonedx` section was
validated against the official published `bom-1.7.schema.json` and — with only
the `specVersion` string swapped — against `bom-1.6.schema.json`, and both
passed with no errors. The check is a one-time external conformance
verification, deliberately not a CI test, because it would make every run
depend on fetching a third-party schema over the network.

**Why CycloneDX 1.7's TLP distribution constraints are not used.** 1.7 adds
`metadata.distributionConstraints.tlp` (FIRST.org Traffic Light Protocol:
CLEAR / GREEN / AMBER / AMBER+STRICT / RED). It is a *sharing label* that tells
recipients how the BOM itself may be redistributed — it is not access control
and does not encrypt or restrict anything. For protected builds delivered to a
designated customer, the delivery problem that actually matters is licensing
and runtime shape (whether Pro runtime can legally ship with the output), not
how the manifest is labelled. If that delivery story is ever formalized, a
TLP marking would be a one-field addition on top, not a foundation for it.

## Integrity Digest

`integrity` is not a cryptographic signature. It confirms that the manifest's
payload still matches its own recorded digest, which helps catch accidental
corruption or partial writes.

Anyone who can edit the manifest can recompute this digest after changing the
payload. For authenticity, pair the manifest with your normal release signing or
attestation workflow.

For pyobfus's own releases, the hosted PyPI/PEP 740 attestation is the stronger
artifact-to-builder evidence; a local manifest or a successful self-dogfood run
does not replace it. See
[`RELEASE_PROVENANCE_VERIFICATION.md`](RELEASE_PROVENANCE_VERIFICATION.md) and
[`SELF_DOGFOODING_BEST_PRACTICES.md`](SELF_DOGFOODING_BEST_PRACTICES.md) for the
verification hierarchy and staged bootstrap boundary.

## Validation

Use `--verify-provenance-manifest` to validate the pyobfus manifest shape, the
embedded CycloneDX-compatible relationships, and the local integrity digest:

```bash
pyobfus --verify-provenance-manifest provenance.json
pyobfus --verify-provenance-manifest provenance.json --json
```

The JSON mode returns `valid`, `errors`, `warnings`, `summary`, `ai_hint`, and
`exit_code`, matching the project's other machine-readable CLI contracts.

## Minimal Shape

```json
{
  "version": 1,
  "pyobfus_version": "0.5.19",
  "config_hash": "sha256...",
  "source_control": {
    "git_commit": "abc123..."
  },
  "mapping": {
    "path": "mapping.json",
    "sha256": "sha256..."
  },
  "files": [
    {
      "relative_path": "app.py",
      "input": "src/app.py",
      "input_sha256": "sha256...",
      "output": "dist/app.py",
      "output_sha256": "sha256..."
    }
  ],
  "cyclonedx": {
    "bomFormat": "CycloneDX",
    "specVersion": "1.7",
    "components": [],
    "dependencies": []
  },
  "integrity": {
    "type": "sha256-canonical-json",
    "digest": "sha256..."
  }
}
```
