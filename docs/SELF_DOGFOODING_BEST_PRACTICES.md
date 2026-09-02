# Self-Dogfooding and Bootstrap Best Practices

Status: research complete 2026-09-02; adoption plan proposed, no CI or release
mutation authorized by this document.

## Executive decision

pyobfus should continuously use its own **analysis, planning, reporting,
verification and provenance** capabilities, and should exercise actual
obfuscation on maintained canary projects and release-candidate wheels. It
should not replace the auditable source in its public Core/Pro distributions
with a self-obfuscated tree.

International practice supports a staged model rather than circular trust:

1. a previously released tool provides an independent-enough bootstrap lane;
2. the current checkout provides the feature-under-test lane;
3. both operate on controlled fixtures and their semantic outcomes are
   compared;
4. static-analysis findings use reviewed suppressions and a real baseline;
5. release artifacts are built in isolated hosted CI, attested and independently
   verified after installation;
6. reproducibility-sensitive inputs such as time, path, order, locale and
   randomness are either removed, normalized or recorded.

Self-use is strong regression evidence. It is not, by itself, proof that the
tool or its output is trustworthy.

## International evidence

### Staged bootstrap: GCC and Rust

GCC's normal native build uses three stages and compares the stage 2 and stage
3 compilers. A mismatch is treated as a potentially serious defect. GCC also
keeps stages in separate build directories to reduce cross-stage ABI and state
contamination. Rust similarly documents stage 0 (the prior beta compiler),
stage 1 (current source built by stage 0), stage 2 (the current compiler rebuilt
with in-tree tools), and stage 3 as a same-result test.

Applied to pyobfus, this does **not** mean byte-comparing arbitrary obfuscated
trees: some transformations may intentionally use random material and different
tool versions can legitimately change formatting. It means maintaining two
lanes and comparing explicit contracts:

- stable public `N-1` scans/builds a fixed canary;
- current checkout `N` scans/builds the same canary;
- compare selected files, reason codes, exit semantics, execution result,
  traceback recovery and verification status;
- require byte equality only for a deliberately deterministic fixture/mode.

Primary sources:

- GCC build/bootstrap documentation:
  <https://gcc.gnu.org/install/build.html>
- GCC internals, stage comparison:
  <https://gcc.gnu.org/onlinedocs/gccint/Makefile.html>
- Rust compiler bootstrap stages:
  <https://rustc-dev-guide.rust-lang.org/building/bootstrapping/what-bootstrapping-does.html>

### Trust boundary: trusting trust and diverse verification

A tool processing its own source can reproduce its own blind spots. Diverse
Double-Compiling research formalizes a stronger response for compiler
bootstraps: introduce a second trusted implementation/path and compare the
resulting chain rather than trusting self-reproduction alone.

pyobfus is not claiming DDC equivalence—Python AST obfuscation and compiled
compiler binaries have different semantics. The transferable rule is narrower:
**the current pyobfus executable must not be the only authority over current
pyobfus source or its release artifact.** The prior public wheel, normal Python
tooling, independent schema validators, GitHub-hosted build provenance and
post-install tests provide diverse checks.

Primary source:

- Wheeler, *Fully Countering Trusting Trust through Diverse
  Double-Compiling*: <https://dwheeler.com/trusting-trust/dissertation/>

### Static-analysis baseline and suppression: OASIS SARIF and GitHub

SARIF 2.1.0 defines separate concepts:

- `suppressions`: reviewed requests to exclude results from normal result lists
  or counts;
- `baselineState`: `new`, `unchanged`, `updated` or `absent` relative to a
  previous run.

The standard says that emitting `baselineState` implies a comprehensive
comparison with a baseline run. Therefore pyobfus 0.5.21 must not label all
current self-findings `unchanged` merely because a snapshot file exists.
GitHub uses fingerprints to avoid duplicate alerts and only annotates a pull
request when the alert's identified lines occur in the diff. This supports a
transition from audit-only to new-finding gating after identity is stable.

Primary sources:

- OASIS SARIF 2.1.0, suppressions and baseline state:
  <https://docs.oasis-open.org/sarif/sarif/v2.1.0/os/sarif-v2.1.0-os.html>
- GitHub third-party SARIF upload/fingerprints:
  <https://docs.github.com/en/code-security/how-tos/scan-code-for-vulnerabilities/integrate-with-existing-tools/uploading-a-sarif-file-to-github>
- GitHub code-scanning alerts in pull requests:
  <https://docs.github.com/en/code-security/concepts/code-scanning/code-scanning-alerts>

### Artifact provenance and isolation: SLSA and GitHub attestations

SLSA Build distinguishes provenance existence, hosted signed builds and
hardened isolated builds. Its model records the builder, build type, external
parameters, dependencies and artifact subjects. Higher assurance comes from
the build platform preventing cross-run influence and keeping signing material
out of user-controlled build steps—not from the package writing an unsigned
statement about itself.

pyobfus already uses hosted OIDC publication and PyPI attestations. Dogfooding
should add evidence alongside that path, not replace it:

- build wheel/sdist from the tagged source in hosted CI;
- verify the ecosystem attestation and artifact digest;
- install the produced wheel in a fresh environment;
- use that installed wheel on the canary and verify its output;
- keep local `--provenance-manifest` claims explicitly below signed build
  provenance in the trust hierarchy.

Primary sources:

- SLSA 1.2 Build levels:
  <https://slsa.dev/spec/v1.2/build-track-basics>
- SLSA Build provenance model:
  <https://slsa.dev/spec/v1.2/build-provenance>
- GitHub artifact attestations:
  <https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations>

### Reproducible outputs

The Reproducible Builds project identifies time, username/hostname, build path,
filesystem order, randomness, locale, timezone and umask as common sources of
output drift. It recommends stable inputs/outputs, minimal environmental
capture, `SOURCE_DATE_EPOCH` where timestamps are unavoidable, path
normalization and rebuilds under varied environments.

This directly reinforces two current pyobfus decisions:

- the Community marker must not emit an absolute build path or current wall
  clock;
- any deterministic self-comparison fixture must pin or remove randomized
  encryption/watermark inputs rather than pretending naturally randomized Pro
  output should be byte-identical.

Primary sources:

- Reproducible-build commandments:
  <https://reproducible-builds.org/docs/commandments/>
- Build-path guidance:
  <https://reproducible-builds.org/docs/build-path/>
- Timestamp / `SOURCE_DATE_EPOCH` guidance:
  <https://reproducible-builds.org/docs/timestamps/>
- Environmental variance and `reprotest`:
  <https://reproducible-builds.org/docs/adding-build-variance/>

## Current pyobfus self-scan evidence

On 2026-09-02, the released/current CLI was run read-only against Core:

```bash
venv/bin/pyobfus --check pyobfus --offline --no-config --json
```

It scanned 41 files with no parse errors and reported 8 high, 12 medium, 36
low and 3 info findings. Several are intentional self-hosting patterns:

- `compile()` in the parser, generator, transformer and syntax verifier;
- dynamic `getattr`/`setattr` in config, mapping and cache machinery;
- `.pt`, `.pyx` and `.pye` rule-definition literals inside the scanner itself;
- `__all__` on intentional public API surfaces.

This is useful evidence that immediate blocking would be unsound. It also shows
why broad directory exclusion is the wrong fix: doing so would hide real future
regressions. The correct sequence is triage, reasoned suppression, stable
identity and then new-finding enforcement.

## Recommended architecture

### Lane A — current-source self-analysis

Run the checkout's CLI against `pyobfus/`, `pyobfus_mcp/` and selected Pro
source in offline mode. Produce JSON and, after 0.5.21, SARIF.

- Phase A0: upload artifacts only; never block.
- Phase A1: upload SARIF to code scanning; manually triage every high finding.
- Phase A2: require reviewed suppressions with rule, safe relative path,
  location/fingerprint, reason, owner and review condition.
- Phase A3: block only new unsuppressed high findings and parse failures.
- Never reduce a general detection rule merely to make pyobfus's own dashboard
  green; first test the change against external fixtures.

### Lane B — stable/current two-lane canary

Maintain a small public fixture that covers:

- cross-file imports and `__all__`;
- Click entry points and framework reflection;
- dynamic attributes with both preserved and unsafe cases;
- mapping, trace marker and traceback reversal;
- dry-run artifact roles;
- Community marker combinations;
- syntax verification and isolated import/runtime smoke;
- provenance generation/validation;
- deterministic Community mode plus explicitly seeded Pro test cases.

Run it first with the latest public wheel (`N-1`), then the checkout (`N`).
Compare versioned semantic facts. Store results as ephemeral CI artifacts, not
committed generated output.

### Lane C — release-candidate artifact verification

After building wheel/sdist but before publication:

1. run `twine check`;
2. install the wheel—not the editable checkout—in a fresh venv;
3. run Lane B with the installed entry point;
4. inspect wheel contents for unexpected files/PII;
5. verify version/manifest/tool metadata;
6. after OIDC publication, verify PyPI attestation/digests and repeat a minimal
   install smoke from public PyPI.

Do not give analysis jobs publication credentials. Keep SARIF upload permission
and PyPI OIDC publication in separate least-privilege jobs.

### Lane D — reproducibility probe

Periodically build deterministic fixtures twice with varied temp path, locale,
timezone, file enumeration order and hash seed. Compare only outputs declared
deterministic. Classify differences rather than normalizing them blindly:

- expected cryptographic randomness;
- documented tool-version change;
- environmental leak (bug);
- unstable traversal/naming (bug);
- path/timestamp/host leakage (privacy and reproducibility bug).

## Suppression policy

A self-scan suppression is reviewable debt, not a glob-based escape hatch.
Recommended fields for a future design (not a 0.5.21 requirement):

```yaml
- rule_id: PYOBFUS/dynamic_exec
  path: pyobfus/core/syntax_verify.py
  reason: intentional in-memory compile for syntax-only verification
  owner: core
  review_when: compile call or verifier threat model changes
```

Rules:

- no wildcard that suppresses all findings in `pyobfus/`;
- no suppression without a concrete technical reason;
- suppress exact identity where practical, not only line number;
- config-excluded build files and analysis suppressions are different states;
- changing a rule/fingerprint version invalidates or explicitly migrates the
  baseline;
- SARIF `baselineState` is emitted only after a comprehensive comparison;
- dismissed GitHub alerts are not silently imported as source-controlled
  policy without review.

## What not to do

- Do not ship the public Apache-2.0 package as self-obfuscated source. The
  upstream source is already public, so protection value is negligible while
  auditability, traceback support, type checking and source/wheel comparison
  become worse.
- Do not claim self-scan success establishes tool integrity or absence of a
  supply-chain compromise.
- Do not use the current checkout as the only verifier of artifacts it created.
- Do not make all existing findings pass by weakening categories globally.
- Do not commit mappings, generated canary trees, SARIF containing source
  literals or environment-specific absolute paths.
- Do not require byte equality from randomized encryption, keys or forensic
  watermarks.
- Do not let release cadence turn an experimental dogfood job into an
  unreviewed blocking gate.

## Staged adoption for pyobfus

1. **0.5.21:** keep product scope as SARIF generation. Use pyobfus itself as a
   documented manual/audit-only upload smoke, with no baseline-state claim.
2. **Post-0.5.21 maintenance increment:** add the stable/current canary and
   artifact-only self-SARIF CI job. No failure gate yet.
3. **After two clean observation windows:** publish a reviewed suppression
   design and turn parse errors + new unsuppressed high findings into a PR gate.
4. **0.5.22 marker work:** add path/time/environment variance tests and remove
   the current absolute-path header leak.
5. **Build-report MVP:** report lane/tool version, artifact digests,
   deterministic comparison status and verification outcomes from the shared
   fact model without overstating trust.

Promotion criteria between phases: stable fingerprint/rule IDs, zero secret or
absolute-path leakage, explainable baseline changes, acceptable CI time, and at
least one real regression caught without unacceptable false-positive blocking.

No version bump, workflow mutation, tag or public release is authorized by this
research document.
