# pyobfus for VS Code

Inline obfuscation-risk diagnostics and reverse-mapped stack traces for
[pyobfus](https://github.com/zhurong2020/pyobfus), the open-source
AST-based Python code obfuscator.

## Why trust this extension

This category has a documented trust problem: in April 2025, a malicious
extension named "Python Obfuscator for VSCode" was part of a 10-extension
malware campaign that reached 300,000+ installs before removal (it deployed
the XMRig cryptominer via a PowerShell loader). This extension is not that,
and doesn't have to ask you to take that on faith:

- **Fully open source**: [github.com/zhurong2020/pyobfus](https://github.com/zhurong2020/pyobfus), Apache-2.0.
- **[OpenSSF Best Practices](https://www.bestpractices.dev/) verified** — the underlying pyobfus project holds the passing badge.
- **PEP 740 attested PyPI releases** — every `pyobfus` release is published via OIDC Trusted Publishing with cryptographic build attestations, independently verifiable via PyPI's integrity API.
- **A build-provenance manifest** (`--provenance-manifest`) and a **tool-description integrity manifest** (`pyobfus-mcp-verify`, for the companion MCP server) — both self-consistency-checkable, not just claimed.
- **No telemetry, no network calls** beyond the explicit, user-initiated "Unlock Pro" link. This extension only ever shells out to your own locally-installed `pyobfus`.

## Features

### Inline risk diagnostics

Runs `pyobfus --check` on every save and surfaces findings (dynamic
`eval`/`exec`, reflection, unsafe deserialization, and more) as native VS
Code diagnostics — squiggly underlines + Problems panel, no extra
extension required. If you already use
[Error Lens](https://marketplace.visualstudio.com/items?itemName=usernamehw.errorlens),
pyobfus's findings get its enhanced inline treatment automatically.

### Reverse stack traces

pyobfus's signature feature: obfuscated code still produces AI-debuggable
tracebacks. Select (or copy) a mangled stack trace, run **pyobfus: Reverse
Stack Trace**, pick the `mapping.json` from your build, and get the
original identifiers back in a new tab — without ever exposing the mapping
to whoever sent you the trace.

## Requirements

- Python 3.9+ with `pyobfus` installed (`pip install pyobfus`) in the
  interpreter VS Code is using for your workspace (the
  [ms-python.python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
  extension is used to detect this automatically).

## Settings

| Setting | Default | Description |
|---|---|---|
| `pyobfus.pythonPath` | `""` (auto-detect) | Explicit interpreter path, if you don't want auto-detection via ms-python.python. |
| `pyobfus.checkOnSave` | `true` | Run the risk check on every `.py` save. |

## Commands

| Command | Description |
|---|---|
| `pyobfus: Check Current File for Obfuscation Risks` | Manual check, current file. |
| `pyobfus: Check Workspace for Obfuscation Risks` | Manual check, whole workspace. |
| `pyobfus: Reverse Stack Trace` | Reverse a mangled traceback via a mapping.json. |

## Links

- [pyobfus on GitHub](https://github.com/zhurong2020/pyobfus)
- [pyobfus on PyPI](https://pypi.org/project/pyobfus/)
- [Documentation](https://pyobfus.readthedocs.io)
- [Companion MCP server](https://pypi.org/project/pyobfus-mcp/) for Claude Code / Cursor / other AI coding agents

## License

Apache-2.0.
