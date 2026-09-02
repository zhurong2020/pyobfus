# SARIF Code Scanning

`pyobfus --check` finds constructs that may break after obfuscation
(`eval`/`exec`, dynamic attribute access, framework reflection, unsafe
deserialization, hallucinated dependency names, …). Since **0.5.21** it can
also emit those findings as a **SARIF 2.1.0** report, so they show up in GitHub
Code Scanning, pull-request review, and any other SARIF consumer — including
AI-assisted security review.

SARIF export is a thin projection of the existing report. It does **not** change
detection, severity, config handling, JSON output, or exit codes.

## Usage

```bash
# Write a SARIF report alongside the normal text output
pyobfus --check src/ --sarif pyobfus.sarif

# Keep the machine-readable pyobfus JSON on stdout AND write SARIF to a file
pyobfus --check src/ --sarif pyobfus.sarif --json
```

- `--sarif PATH` is only valid together with `--check`.
- Normal text (or `--json`) output still goes to stdout; SARIF goes to the file.
- The scan exit code is unchanged: `0` safe, `1` a high-severity finding, `2` a
  parse error. Writing SARIF never changes it.
- `--offline`, config discovery, `--config`, `--preset` and `--no-config`
  behave exactly as they do for the normal report.
- The SARIF file is written atomically (temp file + rename), so a CI job never
  uploads a partially written result.

## Rule and severity mapping

Each stable preflight category becomes one SARIF rule, `PYOBFUS/<category>`.
Finding severity maps to the SARIF result level:

| pyobfus severity | SARIF level |
|------------------|-------------|
| `high`           | `error`     |
| `medium`         | `warning`   |
| `low`            | `note`      |
| `info`           | `note`      |

Findings excluded by your effective config are still included, but as
**suppressed** results (`suppressions[].kind = "external"`, property
`pyobfus.excluded = true`) so reviewers can see them without affecting the exit
code. Parse failures are reported as invocation notifications, not as invented
source rules.

## GitHub Actions example

Upload the SARIF to Code Scanning with least privilege:

```yaml
name: pyobfus preflight
on: [push, pull_request]

permissions:
  contents: read
  security-events: write   # required to upload SARIF to Code Scanning

jobs:
  preflight:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install pyobfus
      # `|| true` keeps a high-severity finding (exit 1) from failing the job
      # before the SARIF is uploaded; drop it if you want findings to block.
      - run: pyobfus --check src/ --sarif pyobfus.sarif --offline || true
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: pyobfus.sarif
          category: pyobfus-preflight
```

> **Private repositories**: uploading to Code Scanning requires GitHub Advanced
> Security (or a public repository). On a private repo without it, the
> `upload-sarif` step is rejected — keep the SARIF as a build artifact instead.

## Privacy

The SARIF projection is deliberately conservative. It never emits source
snippets or literals (result messages are static, category-level), absolute or
`file://` paths (artifact URIs are input-root-relative POSIX), dependency-index
credentials, license state, mappings, buyer/device IDs, or any generated
output. `partialFingerprints` (`pyobfusPreflightV1`) are deterministic hashes of
a versioned tuple of rule, safe relative path and structural location; a given
finding at a stable location keeps its fingerprint, but moving the source line
changes it.

## For AI reviewers

SARIF here is a **review artifact** — a list of pre-obfuscation risk points to
look at. It is **not** a proof that the obfuscated output is safe, secure, or
correct. Treat a clean report as "no known compatibility risks were detected by
the preflight heuristics", not as a security attestation.

## See also

- [Comparison](COMPARISON.md) — how pyobfus positions against other tools.
- [Release provenance verification](RELEASE_PROVENANCE_VERIFICATION.md) — PyPI
  Integrity API / PEP 740 runbook.
