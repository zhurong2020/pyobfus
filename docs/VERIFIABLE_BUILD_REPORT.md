# Verifiable Build Report

Status: v1 contract published in pyobfus 0.5.24.

`pyobfus INPUT -o OUTPUT --build-report report.json` writes one versioned fact
model after a successful build. It brings selection, effective configuration,
transformation counters, cache outcome, syntax-verification evidence, output
digests, artifact roles, marker state, and provenance linkage into one report.
It does not replace the dry-run plan or the provenance manifest:

- the dry-run `plan` answers what would be selected and emitted, without writes;
- the build report answers what the completed build did and observed;
- the provenance manifest carries supply-chain relationships and its local
  self-consistency digest.

## v1 ownership and compatibility

Core owns the `pyobfus-build-report` contract. The root `version` governs this
report only; it is independent of the CLI envelope, dry-run plan, provenance,
SARIF, and marker versions. Consumers must ignore unknown fields. Removing or
changing the meaning/type of a field requires a report-version bump; adding an
optional field does not.

The v1 report is deterministic for the same effective configuration and output
bytes. It intentionally contains no timestamp, random run identifier, or
absolute-path field. Reports are written atomically only after all requested
verification and provenance work has succeeded. A failed build therefore never
leaves a new report that could be mistaken for success. With `--dry-run`, the
report is listed as a planned optional artifact but is not written.

## Privacy and trust boundary

Paths are input/output-root-relative POSIX labels, cwd-relative labels, or bare
basenames. The report never contains source text, string literals, mapping
contents, license/buyer/device values, encryption material, environment
variables, or absolute home paths. Output SHA-256 values describe exact build
bytes but are not signatures. Likewise, `state=completed` means pyobfus reached
the end of the local operation; it does not assert runtime correctness,
authenticity, reproducibility across nondeterministic transforms, or trusted
builder identity.

Verification is evidence-specific. If `--verify-syntax` was not requested, v1
records `mode=none` and `requested=false`; it never upgrades that absence to an
implicit pass. Syntax verification compiles in memory and does not import or
execute generated code.

## v1 shape

The stable top-level fields are `format`, `version`, `tool`, `state`, `mode`,
`effective_config`, `selection`, `transformations`, `cache`, `verification`,
`outputs`, `artifacts`, `output_marker`, `provenance`, and `privacy`. Output
records contain only `path`, `sha256`, `size_bytes`, and `role`.
