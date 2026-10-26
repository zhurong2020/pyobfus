# MCP SDK 2.x dependency release and verification (2026-10-26)

PR #134 merged the source dependency range `mcp>=1.27.0,<3.0.0` into main
(`18b346b`). PR #135 merged the 0.3.16 release files (`04985d4`), and
`mcp-v0.3.16` published the wheel and sdist to PyPI through Trusted
Publishing. This is an MCP-only release; Core remains 0.9.1 and runtime
remains 0.1.1.

## Compatibility evidence

The existing 2026-10-25 review tested a private candidate wheel with SDK
2.3.0 on Linux/Windows and Python 3.10/3.15. See
[the review](MCP_SDK_2X_REVIEW_2026-10-25.md) for the hosted runs.

This preparation tested a wheel copied from 0.3.15 with only the SDK upper
bound changed, using clean Linux CPython 3.12.3 environments, public Core
0.9.1, normal pip resolution, and `pip check`:

| SDK | MCP tests | Real stdio contract |
|---|---:|---|
| 1.27.0 | 153 passed | Existing 1.x test suite; 1 warning from pydantic-settings |
| 2.0.0 | 153 passed | legacy/auto, all 9 tools |
| 2.0.1 | 153 passed | legacy/auto, all 9 tools |
| 2.1.0 | 153 passed | legacy/auto, all 9 tools |
| 2.1.1 | 153 passed | legacy/auto, all 9 tools |
| 2.2.0 | 153 passed | legacy/auto, all 9 tools |
| 2.3.0 | 153 passed | legacy/auto, all 9 tools, using the actual branch wheel |

The first 2.0.0 validation run exposed a test harness API assumption:
`Client(StdioServerParameters(...))` is only supported by later 2.x versions.
The harness now passes `stdio_client(parameters)`, which works across the
tested range. The server and all 153 MCP tests passed without a product code
change. In both modes, the nine real tool calls returned the expected
machine-readable fields, and protected synthetic output verified successfully.

The actual branch wheel's METADATA contains
`Requires-Dist: mcp<3.0.0,>=1.27.0`. A fresh install with no SDK pin resolved
to 2.3.0, passed `pip check`, 153 tests and both stdio sessions. The
`mcp-sdk-compat` CI matrix tests the real wheel with SDK 1.27.0 and 2.0.0
on Linux/Python 3.10, plus newest 2.x on Linux/Windows × Python 3.10/3.15.
The separate newest-1.x job remains pinned to `<2` so it continues to test
that line. PR #134 passed all six compatibility jobs, CI result and CodeQL:
41 successful checks and one configured skip. Main CI for `18b346b` passed
39/39 jobs, with CodeQL successful.

The 0.3.16 release candidate builds as wheel and sdist. Both artifacts
declare the intended version and SDK range. Clean installs of the wheel
with SDK 1.27.0 and with no SDK pin passed `pip check`; the latter resolved
SDK 2.3.0. Both clean installs passed 153 MCP tests, and the default 2.3.0
install passed both real nine-tool stdio sessions with server version 0.3.16.
PR #135 passed 41 checks with one configured skip, and its merge commit
`04985d4` passed 39/39 main CI jobs and CodeQL.

## Published artifact and channel verification

- Release workflow [40248147241](https://github.com/zhurong2020/pyobfus/actions/runs/40248147241)
  successfully built and published the MCP wheel and sdist. The Core and
  runtime publish jobs were skipped.
- PyPI JSON lists both 0.3.16 files. The downloaded wheel SHA-256 matches
  PyPI's digest: `69603cc66265910f07a32954ae45c6c18e231cd6f19734d83e944f9c4ef430b1`.
- PyPI Integrity API returned provenance for both files. Independent
  `pypi-attestations verify pypi --repository https://github.com/zhurong2020/pyobfus`
  succeeded for each exact PyPI artifact URL.
- Fresh PyPI installs on Python 3.10 and 3.15 resolved MCP 0.3.16,
  Core 0.9.1 and SDK 2.3.0. Both passed `pip check`, 153 MCP tests, and
  all nine real tools over legacy/auto stdio; the handshake reported 0.3.16.
- The official MCP Registry versions endpoint reports 0.3.16 as `active`
  and `isLatest=true`. [GitHub Release](https://github.com/zhurong2020/pyobfus/releases/tag/mcp-v0.3.16)
  is published.
- The maintainer supplied Glama admin test
  `01a17790-1545-7aef-8966-dcbb65b5c39b` (2026-10-26 17:34
  Asia/Shanghai): `success` in 1m31.6s. Build steps pin
  `pyobfus-mcp==0.3.16 pyobfus==0.9.1`; the install log confirms MCP SDK
  2.3.0, MCP 0.3.16, Core 0.9.1 and runtime 0.1.1. Instance logs show
  protocol `2025-11-25`, server version 0.3.16 and nine listed tools.
  This is startup and discovery evidence, not nine individual tool calls.
  Glama's build spec says Python 3.12, while uv installed into system Python
  3.13.5. Its checkout remained at `7cf8302` with `pinnedCommit: null`;
  the server itself came from the pinned PyPI package.

## Recovery

If the new default resolver choice causes a host regression, release a new
MCP patch version restoring `<2.0.0` while the problem is investigated.
Published PyPI metadata cannot be edited in place. Affected users can pin
0.3.15 until the patch is available.

The release changes MCP package metadata and release-facing version files.
Core, runtime, the nine tool contracts and transport support are unchanged.
