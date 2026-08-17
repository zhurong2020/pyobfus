# Obfuscation Provenance Manifest

`pyobfus --provenance-manifest PATH` writes a local JSON record for one
obfuscation run:

```bash
pyobfus src/ -o dist/ --save-mapping mapping.json --provenance-manifest provenance.json
```

The manifest is designed for offline audit and reproducibility records. It does
not call a network service, and it does not prove that the generated code is
safe or trustworthy.

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
- `specVersion: "1.6"`
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

## Integrity Digest

`integrity` is not a cryptographic signature. It confirms that the manifest's
payload still matches its own recorded digest, which helps catch accidental
corruption or partial writes.

Anyone who can edit the manifest can recompute this digest after changing the
payload. For authenticity, pair the manifest with your normal release signing or
attestation workflow.

## Minimal Shape

```json
{
  "version": 1,
  "pyobfus_version": "0.5.13",
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
    "specVersion": "1.6",
    "components": [],
    "dependencies": []
  },
  "integrity": {
    "type": "sha256-canonical-json",
    "digest": "sha256..."
  }
}
```
