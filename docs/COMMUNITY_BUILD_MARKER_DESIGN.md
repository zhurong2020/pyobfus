# Community Build Marker Design

Status: design approved for the roadmap; implementation and release remain
separately gated.

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
