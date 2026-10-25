# MCP SDK 2.x dependency release preparation (2026-10-26)

PR #134 merged the source dependency range `mcp>=1.27.0,<3.0.0` into main
(`18b346b`). The published 0.3.15 wheel still caps SDK 1.x. The release
branch prepares 0.3.16; no 0.3.16 package has been published.

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
41 successful checks and one configured skip. Main CI for `18b346b` is a
separate post-merge check.

The 0.3.16 release candidate builds as wheel and sdist. Both artifacts
declare the intended version and SDK range. Clean installs of the wheel
with SDK 1.27.0 and with no SDK pin passed `pip check`; the latter resolved
SDK 2.3.0. Both clean installs passed 153 MCP tests, and the default 2.3.0
install passed both real nine-tool stdio sessions with server version 0.3.16.
Hosted checks for this exact version must pass before publication.

## Release sequence and recovery

1. Review the 0.3.16 release PR and its hosted checks. The PR updates package
   version, changelog, README, Registry manifest and repository Dockerfile pin.
2. With maintainer release approval, merge the release PR, verify main checks,
   and tag `mcp-v0.3.16`. Verify PyPI provenance, a fresh install, nine real
   tools, and the MCP Registry and Glama pins after publication.
3. If the new default resolver choice causes a host regression, release a new
   MCP patch version restoring `<2.0.0` while the problem is investigated.
   Published PyPI metadata cannot be edited in place. Affected users can pin
   the previous MCP release until the patch is available.

The release changes MCP package metadata and release-facing version files.
Core, runtime, the nine tool contracts and transport support are unchanged.
