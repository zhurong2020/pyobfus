# Community Build Marker Design

Status: **implemented** (2026-09-10, held in `[Unreleased]`); release remains
separately gated.

## Correction: what the output actually did before implementation

This document was written from the assumption that Core output already began
with an attribution header, and that the work was to formalize it. Measured
against the code before implementation, that premise was wrong in both
directions, and the corrected picture is what shipped:

- **Community output carried no marker at all.** `CodeGenerator.add_header_comment`
  was effectively dead code on that path: the single-file branch built the
  header string and then wrote the file by regenerating from the AST, silently
  discarding it. Directory mode never called it.
- **Pro build-fusion output was the only path that emitted the header** — and
  it was the leaky one, writing `# Original: <absolute path>` verbatim.

So the absolute-path disclosure was a Pro-path defect, not a free-tier one, and
the "existing free-output header" being formalized did not exist in shipped
output. The implementation therefore does two things rather than one: it
removes the absolute path, and it makes the marker actually reach output on
every path.

Two other decisions follow from that correction:

- **`auto` emits on every edition**, with `edition=` reflecting the real level.
  This preserves the Pro fusion path's existing banner (minus the leak) instead
  of silently removing it, and starts honouring the Community promise. The
  "suppress for a non-Community distribution" option below is left open but not
  taken.
- **The config key stays `community_marker`** as specified here, even though
  the marker is not Community-only, rather than inventing a second vocabulary
  mid-implementation. The help text says it governs all editions.

## Decision

pyobfus should keep and formalize a transparent marker on Community-generated
Python output, but it should **not** add a covert, tamper-resistant or
buyer-identifying watermark to the free Apache-2.0 path.

This is an evolution of existing behavior, not a new restriction. Core output
already begins with:

```python
# Obfuscated with pyobfus
# https://github.com/zhurong2020/pyobfus
# Original: ...
# DO NOT EDIT - Generated code
```

The current header is useful attribution, but it is not versioned, is not
machine-readable and can expose an absolute input path. The next design should
turn it into a privacy-safe **Community build marker**.

## Three distinct marker layers

These concepts must not be merged or described under one ambiguous
"watermark" label:

| Layer | Edition | Purpose | Security claim |
|---|---|---|---|
| Community build marker | Core / free | Transparent attribution and generated-file identification | None; removable by anyone with the output |
| Trace marker | Core, opt-in | Tell humans/agents how to use a retained mapping to reverse a traceback | Stable workflow identifier, not ownership proof |
| Forensic watermark | Pro, opt-in per buyer | Produce buyer-specific evidence for leak investigation | Tamper-evident mechanism subject to its documented threat model |

The Community marker must never contain a buyer ID, license key, device ID,
mapping digest, source hash, secret, absolute path or personal information.
The trace marker must continue to require an explicitly saved mapping. The Pro
forensic implementation remains source-separated under `pyobfus_pro/`.

## Proposed Community marker v1

Illustrative shape:

```python
# pyobfus:generated format=1 edition=community
# Tool: pyobfus 0.x.y — https://github.com/zhurong2020/pyobfus
# Source: package/module.py
# DO NOT EDIT — generated output
```

Requirements:

- preserve shebang and PEP 263 encoding-cookie placement;
- use only a project-relative POSIX path when the source is under the input
  root; otherwise use the basename or omit the field;
- be deterministic for identical tool version, relative input and config;
- add no import, assignment, runtime branch, startup cost or observable Python
  object;
- remain a comment so compilation, packaging and syntax verification are
  unaffected;
- use an independent prefix from `# pyobfus:obfuscated`, so the trace-marker
  parser cannot confuse attribution with mapping availability;
- be emitted once and remain idempotent across cache/rebuild paths;
- describe `edition=community` as build provenance, not as a license
  enforcement or authenticity signal.

## Control and compatibility policy

The default remains marker-on for Community builds because that matches current
output behavior. Do not make "marker removal" a Pro security feature: Core is
open source, the marker is a comment, and such a paywall would be trivial to
bypass while weakening the project's transparent free-tier promise.

Before implementation, add an explicit policy control for environments that
forbid generated banners. Preferred additive configuration:

```yaml
output:
  community_marker: auto  # auto | on | off
```

`auto` preserves today's default for Community output and may suppress the
marketing line in a future non-Community distribution while retaining any
separately requested trace marker. A CLI override may be added only if its
naming cannot be confused with `--trace-marker`.

Changing this setting must not alter transformation semantics. It may affect
output hashes and therefore must be included in the effective config hash,
dry-run plan and provenance manifest. Existing JSON fields and exit codes stay
unchanged; any new fields are additive and versioned.

## Relationship to provenance

The marker is a human/agent hint. The provenance manifest remains the detailed
offline record, and PyPI attestations remain release-artifact evidence.

A later provenance-manifest version may add an additive object such as:

```json
{
  "output_marker": {
    "format": 1,
    "edition": "community",
    "mode": "auto",
    "emitted": true
  }
}
```

It must not claim that the marker proves authenticity. If authenticity is
needed, sign or attest the manifest/artifact outside this comment marker.

## Tests and acceptance criteria

- unit tests for single-file and project-relative paths;
- regression test proving no absolute WSL/Windows/home path reaches output;
- shebang and encoding-cookie tests shared with trace-marker insertion;
- idempotency and no-double-header tests;
- syntax verification and import-smoke compatibility;
- output-marker combinations: Community only, trace only, both, neither;
- dry-run/config/provenance tests for the additive marker state;
- PyInstaller and Nuitka cookbook smoke tests confirming that the marker does
  not change runtime behavior;
- documentation must say "transparent attribution marker", never
  "anti-piracy protection".

## Non-goals

- preventing a user from deleting a comment;
- tracking Community users or phoning home;
- embedding identifiers in constants, control flow, bytecode or runtime data;
- weakening or duplicating Pro forensic watermarking;
- treating generated user output as pyobfus-owned code;
- changing the Apache-2.0 Core / proprietary Pro boundary.

## Implementation sequence

1. Refactor header insertion into a prologue-safe, idempotent marker helper and
   remove absolute-path emission.
2. Add the config/schema/CLI policy and include it in the dry-run plan.
3. Add the provenance-manifest marker record without breaking v1 validation.
4. Synchronize README, config examples, VS Code schema and both agent skills.
5. Run all Python/MCP/integration/extension gates plus packaging smoke tests.

No version bump, tag or release is authorized by this design document.

## Implementation record (2026-09-10)

- `pyobfus/core/build_marker.py` — new module owning the marker block, the
  privacy-safe source label, mode resolution and the shared prologue-safe
  insertion helper that `pyobfus.cli`'s trace marker now imports.
- `pyobfus/constants.py` — `BUILD_MARKER_PREFIX` / `BUILD_MARKER_FORMAT`.
- `pyobfus/config.py` + `config_schema.py` — the `community_marker` key; the
  VS Code JSON schema regenerates from the dataclass, so it picked the field up
  automatically.
- `pyobfus/cli.py` — `--community-marker/--no-community-marker` (tri-state),
  and the single-file write path no longer regenerates from the tree, which is
  what dropped the marker.
- `pyobfus/core/orchestrator.py` — cross-file write path stamps the marker
  using the already-project-relative path.
- `pyobfus/core/build_plan.py` + `core/provenance.py` — additive
  `output_marker` state.
- `tests/test_build_marker.py` — 36 tests covering the acceptance criteria
  below.

Deliberately not done: the PyInstaller/Nuitka cookbook smoke tests are covered
indirectly by `--verify-syntax` on marked output plus a real import-and-execute
check of cross-file output; a full bundler matrix was judged disproportionate
for a comment block that provably adds no runtime object.
