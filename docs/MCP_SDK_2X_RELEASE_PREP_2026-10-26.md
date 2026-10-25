# MCP SDK 2.x dependency release preparation (2026-10-26)

This branch prepares `pyobfus-mcp` to declare `mcp>=1.27.0,<3.0.0`. The
published 0.3.15 metadata still caps SDK 1.x. No package has been published
from this branch.

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
to 2.3.0, passed `pip check`, 153 tests and both stdio sessions. The current
`mcp-sdk-compat` CI matrix tests the real wheel with SDK 1.27.0 and 2.0.0
on Linux/Python 3.10, plus newest 2.x on Linux/Windows × Python 3.10/3.15.
The separate newest-1.x job remains pinned to `<2` so it continues to test
that line. Hosted results for this branch must be checked before merge.

## Release sequence and recovery

1. Review the metadata and CI change, then merge only after required hosted
   checks pass. The merged source range is not a published package change.
2. With maintainer release approval, bump the MCP package version, update the
   changelog and registry manifest, build both wheel and sdist, inspect their
   metadata, and tag the MCP release. Verify PyPI provenance, a fresh install,
   nine real tools, and the MCP Registry and Glama pins after publication.
3. If the new default resolver choice causes a host regression, release a new
   MCP patch version restoring `<2.0.0` while the problem is investigated.
   Published PyPI metadata cannot be edited in place. Affected users can pin
   the previous MCP release until the patch is available.

This changes only the MCP companion package's dependency range and CI.
It does not alter Core, runtime, the nine tool contracts, or transport support.
