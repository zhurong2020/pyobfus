# Feature Expansion Research — 2026-08-26

Status: research complete; no implementation committed by this document.

This note evaluates the feature candidates recorded after the first real Pro
customer support signal. It separates technical/market evidence from user
validation: one customer saying that usage is going well and requesting an
invoice is valuable commercial evidence, but it is not evidence that the
customer needs a team license server, mapping encryption, or a new build mode.

## Method

The review used:

1. A local code audit of the current CLI, mapping, provenance, MCP and license
   surfaces.
2. Current primary documentation from Python, PyArmor, Nuitka, PyInstaller,
   CycloneDX, Sigstore, GitHub, Sentry, HashiCorp and Keygen.
3. A fit test against pyobfus's strategy: local-first, AI-debuggable,
   machine-readable and framework-aware, without turning into a native compiler,
   cloud obfuscation service or enterprise license platform.

This is not a user survey. Customer feedback remains a separate gate.

## Existing substrate

- `--dry-run --json` already executes the selection/transformation path without
  writing protected files, but its JSON result is mostly aggregate statistics;
  it does not expose an explicit effective configuration, selected/excluded
  file list, planned artifacts or compatibility decisions.
- `--check --json` already provides framework/risk diagnostics and a stable
  agent-facing contract, but does not consume the effective obfuscation config.
- `--provenance-manifest` already records input/output hashes, config hash, Git
  commit when available, mapping digest and a CycloneDX 1.6-compatible section;
  `--verify-provenance-manifest` checks shape and local consistency.
- `mapping.json` already has a stable marker ID and can be kept outside the
  protected output. Its digest is recorded in provenance, but neither object is
  cryptographically signed or confidential.
- `pyobfus-license status --json` already reports the current device and masked
  local license state. The current Worker verification protocol accepts a
  license key and current device fingerprint, but exposes no customer-facing
  list/rename/deactivate device API.

## Evidence from adjacent tools and standards

- Nuitka's official `--report=compilation-report.xml` records module inclusion,
  exclusions and reasons, plugin influences, data files and timings. Nuitka
  recommends attaching the report to issue reports. This is strong evidence for
  a detailed build/plan report as a troubleshooting artifact, not evidence that
  pyobfus should copy Nuitka's XML format.
- PyInstaller emits a warnings file and import cross-reference graph during
  analysis. Its documentation also stresses that static analysis cannot see all
  dynamic imports and that runtime testing is still necessary.
- Terraform's official `plan` and JSON formats establish a useful pattern:
  preview and review before mutation, with a versioned machine-readable schema.
  Terraform also warns that plan files can contain sensitive values. A pyobfus
  plan must therefore omit literal values, keys and full secret-bearing config.
- Python's `compileall`/`py_compile` return failure for syntax compilation, but
  compilation does not execute imports or prove application behaviour.
- CycloneDX supports components, dependencies, formulation/workflow evidence and
  attestations. pyobfus already implements the useful file/digest subset; a
  separate archive format is not required to claim CycloneDX alignment.
- Sigstore can sign arbitrary blobs with `cosign sign-blob` and recommends a
  verification bundle. GitHub artifact attestations similarly sign build
  provenance. These are appropriate external signing integrations; they do not
  provide confidentiality.
- Sentry's source-map guidance treats debug mapping material as sensitive and
  supports private upload or token-restricted retrieval. This maps closely to
  pyobfus mappings: keep them out of the shipped artifact and restrict access
  before inventing built-in encryption.
- Keygen models device activation as server-side machine resources with list,
  name and deactivate operations plus scoped authentication. PyArmor separately
  documents Pro/CI/group registration flows. Both show that customer-managed
  device UX is a backend/auth product, not a small CLI-only enhancement.

## Decisions by candidate

### 1. Config-aware `--check`: GO, P1

This remains the best next code candidate. It directly addresses an already
recorded P2-29 false-positive problem and reuses the same Risk contract across
CLI, MCP and VS Code.

Research decision:

- `--check` should resolve the same config discovery/override rules as an actual
  build.
- Findings inside excluded files should be omitted from the primary risk count
  but summarized separately as `excluded_findings`, not silently lost.
- A preserved name or framework preset should annotate/downgrade the relevant
  compatibility finding only when the configuration actually mitigates it.
- Dependency declarations remain project-level and must not disappear because a
  Python source directory is excluded.
- Additive JSON fields are preferable to changing severity/exit-code semantics.

### 2. Machine-readable plan: GO, but enrich `--dry-run --json`

There is sufficient adjacent-tool evidence for a reviewable plan. There is not
enough evidence for a separate `--plan` command, because `--dry-run` already has
the correct no-write execution semantics.

Recommended MVP: extend `--dry-run --json` with a versioned `plan` object:

- effective preset, level and boolean transform names;
- selected, copied and excluded relative paths with exclusion reasons;
- cross-file/single-file mode and job count;
- planned output, mapping, trace-marker and provenance paths;
- config hash and source Git commit when available;
- compatibility warnings and `ai_hint`/`next_command`.

Do not include literal configuration values, vault contents, license keys,
device fingerprints, absolute home paths or source text. Do not make a saved
plan executable/apply-able in the first version; input/config drift would make
that a second state-management system.

Priority: P1 after config-aware `--check`.

### 3. Controlled post-build verification: GO for a syntax-only spike

There is clear value in producing a machine-readable verification result, but
the original `--verify-command` concept is rejected:

- arbitrary commands introduce command-execution and quoting risk;
- importing output executes user code and can cause side effects;
- a successful import/smoke test still cannot prove application correctness.

Recommended spike:

- verify every produced `.py` with Python's `compile()` or `py_compile` without
  executing it;
- avoid leaving `__pycache__` in the delivery directory (an in-memory
  `compile(source, filename, "exec")` pass is the cleanest default);
- return per-file results in the existing JSON envelope;
- describe the result strictly as `syntax_valid`, not `runtime_verified`;
- keep provenance verification as its existing separate operation.

An opt-in module-import verifier can be reconsidered only with explicit process
isolation, timeout, environment control and a user-supplied allowlist. It must
never become an MCP tool that accepts arbitrary commands.

Priority: P1 feasibility spike after the plan schema, because the result can be
included in the same report.

### 4. Delivery bundle: NO-GO as an archive; GO as a report/profile

The existing output directory plus provenance manifest already contains most of
the useful structure. Automatically packaging `mapping.json` with distributable
code creates a serious foot-gun: the mapping is internal debug material and can
undo much of the name-hiding value.

Recommended direction:

- do not add a zip/tar `--delivery-bundle` flag now;
- add a `delivery` section to the plan/provenance report that classifies each
  artifact as `ship`, `retain-internal`, or `optional`;
- optionally add a documented `delivery` configuration profile later;
- keep mapping outside the output directory by default;
- allow a generated `DELIVERY.md` only after a user asks for a human handoff
  document.

Revisit an archive only if repeated enterprise feedback asks for a single
handoff package with an explicit public/internal split.

### 5. Mapping security: GO for hygiene and signing recipe; defer encryption

Three distinct properties must not be conflated:

- confidentiality: prevent disclosure of original names;
- integrity: detect accidental or malicious modification;
- authenticity: prove who produced the mapping.

Current provenance provides a digest relationship but not authenticity. The
lowest-cost correct improvements are:

1. Document restrictive storage/access and keep mapping outside shipped output.
2. Add a warning if a requested mapping path is inside the output directory.
3. Document external blob signing with Sigstore/cosign for teams that require
   authenticity; do not implement another private-key system in pyobfus.
4. Consider provenance/attestation signing before mapping-specific signing,
   because one signed manifest can cover output and mapping digests together.

Built-in mapping encryption is deferred. It would require password/key input,
non-interactive CI secret handling, recovery/rotation rules and encrypted-unmap
UX. Implement it only after a user provides a concrete storage threat model.

Priority: P1 small warning/documentation; signing recipe P2; encryption no-go
without demand.

### 6. Lightweight team/license UX: docs first, backend work deferred

Local device display is already implemented. True self-service device listing,
renaming and deactivation requires Worker data modelling, authenticated customer
authorization, abuse/race handling and privacy decisions. It is not justified
by an invoice request alone.

Recommended near-term scope:

- publish a vendor/billing FAQ and a generic invoice process;
- clarify the three-device entitlement, cache removal versus server-side
  deactivation, CI usage and support path;
- keep `status --json` stable and mask keys/device identifiers in shared logs;
- record repeated activation/support requests as the trigger for a backend
  machine-resource spike.

Do not add Enterprise tiers, SSO, a license portal or a complex license server.
If self-service becomes necessary, start with list + deactivate; device aliases
are optional metadata, not the first requirement.

Priority: P2 docs; backend deferred pending repeated customer evidence.

### 7. Unified compatibility report: fold into check/plan, no new command

Nuitka and PyInstaller demonstrate that reports are useful, but also that static
analysis has hard limits around dynamic imports and target environments.
pyobfus already has `compatibility_advisory` plus cookbooks and examples.

Decision:

- do not add a separate `compatibility-report` command;
- surface compatibility advisories, detected integration signals, applied
  mitigations and cookbook links inside config-aware `--check` and the enriched
  dry-run plan;
- add new compatibility rules only from a reproducible support case or a tested
  integration;
- never label a target “compatible” based only on static scanning.

## Prioritized research outcome

1. Implement config-aware `--check` after customer/invoice follow-up permits the
   next development cycle.
2. Design an additive `plan` object for existing `--dry-run --json`.
3. Spike syntax-only post-build verification and feed its result into JSON/
   provenance.
4. Add mapping-inside-output warning and mapping-handling documentation.
5. Extend plan/provenance with ship/internal artifact classification instead of
   building an archive.
6. Keep license UX and mapping encryption behind real repeated demand.

## Primary sources

- HashiCorp Terraform plan and JSON:
  <https://developer.hashicorp.com/terraform/cli/commands/plan>,
  <https://developer.hashicorp.com/terraform/internals/json-format>
- Nuitka compilation report:
  <https://nuitka.net/user-documentation/user-manual.html#compilation-report>
- PyInstaller diagnostics:
  <https://pyinstaller.org/en/stable/when-things-go-wrong.html>
- Python compile APIs:
  <https://docs.python.org/3/library/compileall.html>,
  <https://docs.python.org/3/library/py_compile.html>
- CycloneDX specification/evidence:
  <https://cyclonedx.org/specification/overview/>,
  <https://cyclonedx.org/use-cases/evidence-management/>
- Sigstore blob signing:
  <https://docs.sigstore.dev/cosign/signing/signing_with_blobs/>
- GitHub artifact attestations:
  <https://docs.github.com/en/actions/concepts/security/artifact-attestations>
- Sentry private source-map hosting:
  <https://docs.sentry.io/platforms/javascript/guides/deno/sourcemaps/uploading/hosting-publicly/>
- Keygen machine activation and management:
  <https://keygen.sh/docs/activating-machines/>,
  <https://keygen.sh/docs/api/machines/>
- PyArmor registration/licensing and current CLI:
  <https://pyarmor.readthedocs.io/en/stable/how-to/register.html>,
  <https://pyarmor.readthedocs.io/en/latest/genindex.html>
