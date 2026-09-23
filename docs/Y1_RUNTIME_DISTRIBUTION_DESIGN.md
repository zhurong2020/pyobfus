# Redistributable Pro runtime design

Status: published `pyobfus-runtime` 0.1.0 (2026-09-24)

Local evidence: standalone boundary tests 2/2; focused runtime/fusion tests
189/189; compatibility regression tests 76/76; standalone wheel built and
installed in a clean temporary environment where `pyobfus_pro` was not
importable; wheel inspection found no Pro, transformer, licence-client, or CLI
files; Ruff and mypy pass. The first complete Core run found one module-alias
identity regression (1351 passed, 1 skipped, 1 failed); the alias was corrected
and the affected 76-test slice then passed. Final local validation passed: Core
1354/1 skipped, MCP 97, integration 12, runtime 2; Black, Ruff, mypy, MkDocs,
README links, workflow YAML, Twine, and a fresh dual-wheel install all passed.
Remote CI is green. The redistribution licence review and the project-specific
PyPI Trusted Publisher setup are complete. The licence-adjusted sdist
and wheel pass Twine, metadata/licence inspection, content-boundary inspection,
and a clean-environment install where `pyobfus_pro` is absent. The four local
test roots and all required static/documentation checks also pass. Release
workflow [`35931605485`](https://github.com/zhurong2020/pyobfus/actions/runs/35931605485)
published both artifacts through PyPI Trusted Publishing with PEP 740
attestations; PyPI metadata and a fresh PyPI install were verified on 2026-09-24.

## Problem

Some Pro transforms emit imports from `pyobfus_pro`. A customer may build an
artifact under a valid Pro licence, but the proprietary licence does not grant
permission to redistribute that package. The resulting artifact therefore
cannot be delivered legally or run on a clean target unless the recipient also
installs the complete Pro implementation.

This affects encrypted opacity, vaults, code seals, traceback scrubbing,
device binding, calendar and run-count expiry, runtime platform policy, and
embedded data. It is not limited to the three imports in the first downstream
reproduction.

## Decision

Create a separately versioned distribution named `pyobfus-runtime`, imported
as `pyobfus_runtime`.

- It contains only functions and exception types required by generated output.
- It is redistributable and does not require a pyobfus licence key at runtime.
- It contains no transformer, CLI, payment, licence-verification, or build-time
  code.
- Its public call shapes are versioned compatibility contracts. Generated code
  imports public names from the package root instead of private submodules.
- Pro remains required to create protected artifacts. Making the loader
  redistributable does not make the Pro transformers part of Core.

The runtime licence must explicitly permit customers with a valid Pro licence
to redistribute unmodified runtime wheels or bundle their unmodified contents
with artifacts produced by pyobfus. It must not depend on an implied exception
to the existing `pyobfus_pro/LICENSE` restriction.

### Licence decision (approved 2026-09-23)

Keep a custom proprietary redistribution licence; do not apply Apache-2.0,
MIT, or another open-source licence to the runtime. That preserves the product
boundary: Core is open, Pro creates protected artifacts, and the minimum code
needed to execute those artifacts may travel with them. The package metadata's
`LicenseRef-pyobfus-Runtime-1.0` is the correct PEP 639 mechanism for this
custom licence, and the full licence file is included in both distribution
archives.

The approved licence makes two narrow wording changes to the original draft:

1. Permit non-substantive packaging transformations needed to deliver an
   artifact, such as archiving, wheel vendoring, byte-compilation, or bundling
   into an executable, while continuing to prohibit functional modification.
   Otherwise an honest PyInstaller, embedded-Python, or similar delivery may
   accidentally fall outside the word "unmodified".
2. Replace the broad phrase "create or enable a competing obfuscation product"
   with a concrete restriction against using the runtime to provide a
   build-time obfuscation/protection product or service. Ordinary customers
   should not have to interpret what counts as a competitor.

It retains the other boundaries: a valid Pro holder may redistribute it only
with artifacts produced by Pro; recipients may use it only to run those
artifacts; trial use does not grant production redistribution; separate
sublicensing and misrepresentation as open source remain prohibited. This is a
product/legal recommendation, not jurisdiction-specific legal advice.

PyPI now has the ordinary project-level Trusted Publisher for `pyobfus-runtime`,
created from the pending publisher owned by `zhurong2020/pyobfus` and bound to
`.github/workflows/release.yml`. Its environment remains blank because the
publication job does not declare a GitHub environment.

## Source and compatibility layout

The standalone runtime is the single implementation. `pyobfus_pro` retains
thin re-export modules for source compatibility with:

- existing user imports;
- artifacts generated by pyobfus 0.5.x before this migration;
- the `pyobfus-unscrub` build-side command.

New artifacts import `pyobfus_runtime`. Old artifacts continue to import
`pyobfus_pro`; those shims remain for the full 0.5.x line and are not removed
without a separately announced compatibility break.

Marker-only source imports such as `from pyobfus_pro import opacity, Layer`
must be removed by the transform when their decorators have been consumed.
They must not survive merely to force installation of a build-time package.

## Package boundary

Runtime-owned capabilities:

- encrypted opacity dispatch;
- vault decryption;
- code-seal verification;
- scrubbed traceback installation and encryption primitives used in output;
- device-key derivation and machine identity;
- expiry and atomic run counters;
- OS, Python, and architecture policy checks;
- embedded-data decryption.

Build-owned capabilities that stay in `pyobfus_pro` include transformers,
configuration and layer resolution, encryption/material generation, private-key
unscrubbing workflows, licence/trial verification, and all CLI orchestration.

## Versioning

Start the runtime at `0.1.0`. Generated source depends on a stable v1 call
shape rather than checking an exact package version. Breaking call changes
require a runtime major version and a deliberate generated-code migration.

The Pro distribution depends on a compatible runtime range while it contains
the legacy re-export shims. The Core distribution must not acquire a runtime
dependency because Community-only output does not need it.

## Acceptance criteria

1. Build and publish metadata for `pyobfus-runtime` are independent from Core
   and MCP metadata.
2. A clean environment containing only the generated artifact, its ordinary
   application dependencies, and `pyobfus-runtime` executes every runtime-backed
   feature without `pyobfus_pro` being importable.
3. A pre-migration fixture importing the legacy namespace still executes when
   the Pro package and its runtime dependency are installed.
4. Wheel-content tests prove the runtime wheel excludes Pro transformers,
   licensing clients, payment code, CLIs, tests, and repository-only files.
5. Linux and Windows integration jobs exercise generated output. Python 3.9
   through 3.14 remain supported.
6. README, support matrix, Pro licence, runtime licence, changelogs, and SBOM
   output describe the delivery requirement consistently.
7. Runtime publication and the Pro/Core release that begins emitting the new
   namespace are separate release/deployment gates; runtime publication is
   complete, while the builder dependency/release gate remains.

## Rollout order

1. Add the standalone package and tests without changing emitted imports.
2. Replace Pro implementations with compatibility re-exports from the runtime.
3. Change all newly emitted imports to `pyobfus_runtime` and strip consumed
   marker imports.
4. Run unit, clean-environment, wheel-content, and Windows execution tests.
5. Update user-facing delivery and licensing documentation.
6. Publish `pyobfus-runtime` first; only then release the builder that emits its
   namespace. Never ship generated imports before their runtime is available.
