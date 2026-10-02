# Cross-repository documentation sync audit — 2026-10-02

Scope: the public `pyobfus` repository, the public `pyobfus-action` repository,
the private historical `pyobfus-pro-dev` repository, and cross-project routing
records in `workspace-meta`, `home`, and `pyobfus-legal`. Backups and dated
archives were inventoried but are not synchronization targets. This audit was
opened after the Pro build/runtime split and the creation of the standalone
GitHub Action repository.

## Current architecture

| Surface | Source of truth | Distribution / lifecycle |
|---|---|---|
| Core builder and CLI | `pyobfus/` in the public `pyobfus` repo | PyPI `pyobfus`; Apache-2.0 core with source-separated Pro builder |
| Pro builder | `pyobfus_pro/` in the public `pyobfus` repo | Ships with the `pyobfus` builder under the proprietary licence |
| Target runtime | `pyobfus_runtime/` in the public `pyobfus` repo | Independently published PyPI package `pyobfus-runtime`; target machines do not need the Pro builder or a build licence |
| MCP server | `pyobfus_mcp/` in the public `pyobfus` repo | Independently versioned PyPI package `pyobfus-mcp` |
| VS Code extension | `vscode-extension/` in the public `pyobfus` repo | Independently versioned Marketplace and Open VSX artifact |
| GitHub Action | separate public repo `zhurong2020/pyobfus-action` | Independently versioned moving `v1` tag plus immutable release tags |
| Original patent-gated development history | private repo `pyobfus-pro-dev` | Historical/audit source only; no longer the current implementation source and never publishable as a package |

`pyobfus-action` is separate because Marketplace requires `action.yml` at the
repository root, `uses:` fetches the action repository, and its moving `v1` tag
must not share Core's release-tag namespace. The Action installs or invokes the
builder; it does not replace the separately redistributable runtime required by
runtime-backed Pro artifacts.

## Findings at audit time

1. The public README, changelog, runtime design, agent guide, and distribution
   channel record already describe the standalone runtime and Action.
2. `docs/PROJECT_STRUCTURE.md` still described an older single-package layout
   and omitted MCP, runtime, VS Code, skills, and the external Action repo.
3. The README's local AST pipeline description was correct but did not explain
   the system/distribution topology.
4. `docs/THREAT_MODEL.md` omitted the independently published runtime wheel
   from the protected artifact set.
5. `docs/SUPPORT_MATRIX.md` still named Core 0.5.28 and had no Action or
   Action-to-runtime delivery rows.
6. `pyobfus-action` documented its wrapper behavior accurately, but not the
   runtime dependency/delivery boundary for Pro builds or its compatibility
   contract with independently released Core/runtime versions.
7. `pyobfus-pro-dev` still presented the pre-disclosure patent gate as current,
   even though the gate was cleared, the implementation was squash-integrated,
   and the public 0.5 line shipped. Several design-document status headers also
   lagged their own completed implementation ledger.

## Resolution plan

- [x] Mark `pyobfus-pro-dev` as historical/read-only and add completion notes
      to stale design status headers without rewriting the original record.
- [x] Replace `PROJECT_STRUCTURE.md` with the current multi-distribution and
      cross-repository topology; expand the README architecture section.
- [x] Add `pyobfus-runtime` to the threat model and refresh the support matrix,
      including Action CI and delivery-boundary evidence.
- [x] Add an Action maintainer guide and document runtime deployment and
      version-compatibility rules in `pyobfus-action`.
- [x] Add a workspace-level repository map, link it from `workspace-meta` and
      `home`, and update `pyobfus-legal`'s current Phase 5/repository status.
- [x] Run each repository's applicable checks and commit changes separately;
      do not publish or release as part of documentation synchronization.

Resolution commits are recorded in the repositories themselves. The legal
workspace is intentionally not a Git repository; its two routing/status files
were updated in place and remain covered by the workspace backup policy.

## Maintenance rule

A change to package boundaries, repository ownership, release independence, or
generated-artifact runtime requirements must update, in the same workstream:

1. the owning repository's README and changelog or release notes;
2. this repository's `PROJECT_STRUCTURE.md`, `SUPPORT_MATRIX.md`, and threat
   model when their claims change;
3. the consuming repository's compatibility/delivery documentation; and
4. `CURRENT_PLAN_ZH.md` only for current operational state, not as a substitute
   for durable architecture documentation.

Historical design documents may retain their original decision-time text, but
must carry a prominent superseding status note when their instructions or
completion state are no longer current.
