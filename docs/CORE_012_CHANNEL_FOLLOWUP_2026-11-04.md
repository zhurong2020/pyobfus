# Core 0.12.0 channel follow-up — 2026-11-04

The [Core release](CORE_0_12_0_RELEASE_2026-11-04.md) is complete. The
maintainer authorized continuation of the channel tasks on November 4.
Action v1.1.0 and Glama channel release 0.11.3 are now verified; these are
independent version schemes, not Core or MCP package versions.

## Action v1.1.0

- [PR #3](https://github.com/zhurong2020/pyobfus-action/pull/3) merged as
  `3237e1668d431e50e87150b11f81c5754ce18c71`.
- [Final candidate CI](https://github.com/zhurong2020/pyobfus-action/actions/runs/41756125212)
  and [final main CI](https://github.com/zhurong2020/pyobfus-action/actions/runs/41756251773)
  each passed all **11 jobs**. Actual `uses: ./` consumers cover all three OS
  families, clean/risky scans, tool errors, builds, an old exact-version pin,
  explicit/inherited invalid license inputs and Community builds.
- Licensing consumers now install published `pyobfus==0.12.0` and assert the
  Action's reported Core version. No development snapshot or real CI license
  is used by those hosted tests. Four local secret-boundary/error-gate
  regressions, Ruff, mypy and Marketplace metadata checks passed.
- Immutable `v1.1.0` and moving `v1` both resolve to `3237e16`. The previous
  `v1` target was `284802e`; exact `v1.0.0` and `v1.0.1` tags were preserved.
- [GitHub Release](https://github.com/zhurong2020/pyobfus-action/releases/tag/v1.1.0)
  is public, non-draft and non-prerelease. The
  [Marketplace listing](https://github.com/marketplace/actions/pyobfus-scan-and-build)
  identifies **v1.1.0** as latest and documents `license-key`.
- This is a free wrapper convenience and correctness/security fix. Core owns
  Pro activation and entitlement; no edition or generated runtime format changed.

The optional `license-key` input forwards a non-empty secret only through the
CLI child environment. Empty input retains an inherited `PYOBFUS_LICENSE_KEY`.
Structured CLI `status: error` / exit-1 responses now fail even under
`fail-on: never`; findings retain their selected gate. See [CI licensing](CI_LICENSING.md).

## Glama build and channel release

Evidence is the maintainer-provided admin pages plus build and instance logs,
not an independent login to the admin account.

| Field | Verified evidence |
|---|---|
| Test/build | `01a1a435-fda7-7745-ab9b-f6be9267c82a`, November 4 09:39 CST |
| Result | `success`, duration 2m 8.8s |
| Install command | `uv pip install --system --break-system-packages pyobfus-mcp==0.3.17 pyobfus==0.12.0` |
| Logged installed packages | Core 0.12.0 / MCP 0.3.17 / runtime 0.1.1; MCP SDK 2.3.0 |
| Initialize | Server version 0.3.17, protocol `2025-11-25` |
| Discovery | Nine tools; prompts/resources queries returned empty lists |
| Channel release | **0.11.3**, dated November 4, associated with this exact successful test |
| Checkout | `1aa011332bc2f8d5f2e096ad5be03ad4c0a25846` |

The initial test page said no release had yet been created. A later refreshed
admin page lists release 0.11.3 and associates it with the test ID above; that
later evidence resolves the pending-release state. It does not independently
prove that every already-running instance was restarted.

The Build Spec requests Python 3.12 and the setup command prints 3.12.16, but
`uv pip` explicitly installed into **Python 3.13.5 at `/usr`**. The service
interpreter path was not separately obtained, so this is not claimed as Python
3.12 service validation. The old checkout does not imply an old installed Core:
the explicit package install log records 0.12.0. No checkout synchronization or
new SHA is claimed. Discovery is not execution of all nine business tools.

## DEV one-week review

The maintainer provided the current Dashboard after the November 4 09:43 CST
checkpoint. The exact browser sampling time was not supplied; this is a
one-week-window snapshot, not an independently timed exact seven-day sample.
The public article API independently returned zero reactions and comments;
it does not expose the private view count in this response.

| Metric | Current Dashboard | Comparison with October 29 snapshot |
|---|---:|---|
| SARIF article views | **<25** | Same displayed range; exact view increment unknown |
| SARIF reactions / comments | **0 / 0** | Unchanged |
| Followers | **28** | Unchanged |
| Cloudflare article views | **64** | +10 from 54 |
| Multi-module article views | **62** | Unchanged |
| MCP integration article views | **72** | Unchanged |

Account totals: four posts, four reactions, one comment, **<500** views.
The older Cloudflare article's increase is not evidence of traffic from the
SARIF article. This sample supplies no attributable installation or qualified
usage signal. Retain the current title/cover and avoid reposting solely on these
numbers. Complete the separately scheduled LinkedIn review around November 5
evening before evaluating the already-scoped small channel experiment.

## Remaining timed checks and evidence

Session-end update: [RTD build 35630733](https://app.readthedocs.org/projects/pyobfus/builds/35630733/)
succeeded on `68bc6d7`; the public CI guide serves the Action v1.1.0 input.
The natural backup later completed with marker **November 4 09:49:59 CST**,
but its earlier snapshot still lacks the new release evidence. This resolves
the uploading state below, not the pending evidence-inclusion check. See the
[session handoff](SESSION_CLOSEOUT_2026-11-04.md).

- T+24h: **November 5 after 09:27 CST**; T+72h: **November 7 after 09:27 CST**.
  Review support, licensing monitor and reproducible build/runtime issues.
- The November 4 natural backup was still uploading when checked. Its local
  snapshot lacks this morning's release evidence directory, so eventual upload
  completion would not establish that the new evidence is backed up. Verify
  inclusion in the **next natural snapshot**; do not restart or duplicate the
  in-flight backup. No full cloud comparison is claimed in this record.
- A bounded search of local top-level project workflow files found only the
  Action's synthetic license-contract workflow, not another maintained Pro
  delivery workflow needing a secret migration. This is not an exhaustive
  audit of remote/private CI. The published Core owner's live build was already
  verified in the Core release record.
- No customer notification, paid promotion, F2/F3 implementation, MCP/runtime/
  extension release, or change to license-service configuration was performed.

Private structured evidence is retained in
`docs/internal/release-0.12.0-followup-2026-11-04/`. Future observation results
remain unfilled.
