# pyobfus: the Python obfuscator

<p align="center"><img src="https://raw.githubusercontent.com/zhurong2020/pyobfus/main/docs/assets/logo.jpeg" alt="pyobfus Logo" width="180"></p>

<p align="center"><strong>Obfuscate Python before you ship it—and still debug what you shipped.</strong></p>

<p align="center"><a href="https://github.com/zhurong2020/pyobfus/blob/main/README.zh-CN.md">简体中文</a> · <a href="https://zhurong2020.github.io/pyobfus/">Product</a> · <a href="https://pyobfus.readthedocs.io/">Documentation</a> · <a href="https://pypi.org/project/pyobfus/">PyPI</a></p>

[![PyPI version](https://img.shields.io/pypi/v/pyobfus.svg)](https://pypi.org/project/pyobfus/)
[![PyPI downloads](https://img.shields.io/pypi/dm/pyobfus.svg)](https://pypi.org/project/pyobfus/)
[![Documentation Status](https://readthedocs.org/projects/pyobfus/badge/?version=latest)](https://pyobfus.readthedocs.io/en/latest/)
[![License](https://img.shields.io/badge/License-Dual%20(Apache%202.0%20%2B%20Proprietary)-blue.svg)](https://github.com/zhurong2020/pyobfus/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.9--3.14-blue.svg)](https://www.python.org/downloads/)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/12788/badge)](https://www.bestpractices.dev/projects/12788)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20846053.svg)](https://doi.org/10.5281/zenodo.20846053)

pyobfus is a local-first, AST-based Python obfuscator for Python 3.9–3.14. It
handles complete projects, keeps generated output portable, and can reverse-map
protected production tracebacks for developers and AI coding agents. Community
is Apache-2.0, has no file or line limits, and requires no trial.

## Why pyobfus

| Advantage | What it means in practice |
|---|---|
| **Complete Community edition** | Obfuscate real projects without a file/line cap or trial clock. Optional limits are your CI safety rails, not an upgrade gate. |
| **Diagnosable protection** | Keep the private mapping and restore identifiers in production tracebacks without giving customers the original source. |
| **Evidence, not a black box** | Scan, preview, verify syntax, retain provenance and compare reproducible build reports. |
| **Portable and local-first** | Source stays local; Community emits ordinary cross-platform Python without a native build matrix. |
| **Explicit security claims** | Tested, verified-once and advisory-only claims are separated; deterrents are not presented as irreversible security. |

## Quick start

```bash
pip install pyobfus

# Check compatibility, preview, then build
pyobfus --check src/
pyobfus src/ -o dist/ --dry-run --json
pyobfus src/ -o dist/ --save-mapping mapping.json --verify-syntax
# --verify-syntax only compiles the output; run your own tests against dist/

# Restore names when a production traceback arrives
pyobfus --unmap --trace error.log --mapping mapping.json
```

For framework presets, configuration discovery, packaging and verification,
start at the [task-oriented documentation](https://pyobfus.readthedocs.io/).

## Minimal example

Input:

```python
def greet(name):
    message = f"Hello, {name}!"
    return message

print(greet("world"))
```

Run `pyobfus input.py -o output.py`. Representative Community output:

```python
def I0(I1):
    I2 = f"Hello, {I1}!"
    return I2

print(I0("world"))
```

Both print `Hello, world!`. Generated identifiers can differ with input and
configuration; verify the exact output with your own tests. Keep a mapping when
you need to restore names from a shipped traceback.

## Features at a glance

Community includes project-wide name mangling and import rewriting, string and
numeric transforms, framework-aware presets, config-aware pre-flight scanning,
SARIF, structured dry-run, reverse traceback mapping, syntax verification,
provenance, reproducible output and verifiable build reports.

Professional adds four kinds of commercial value:

- **Protection strength:** AES encryption, control-flow flattening, dead-code
  injection, anti-debugging, Selective Opacity and sealing.
- **Protected assets:** import strings, embedded data, Runtime String Vault and
  protected tracebacks.
- **Distribution control:** device, expiry, run-count, platform and
  application-supplied-key policies.
- **Accountability:** forensic watermarking and buyer-specific builds.

The durable classification rule is documented in the
[Community / Pro boundary policy](https://github.com/zhurong2020/pyobfus/blob/main/docs/EDITION_BOUNDARY_POLICY.md).

## 🔌 Companion MCP server: `pyobfus-mcp`

Install the MCP server with no API key and no source upload:

```bash
uvx pyobfus-mcp
# or: pip install pyobfus-mcp
```

It exposes structured tools for scanning, configuration, protection,
verification, preset explanation, tier recommendations and traceback mapping.
See the [MCP package guide](https://github.com/zhurong2020/pyobfus/tree/main/pyobfus_mcp)
and its registration in the
[official MCP Registry](https://registry.modelcontextprotocol.io/).

### Agent and editor integrations

- `pyobfus-review` and `pyobfus-protect` skills separate read-only review from
  build-producing work. See [skills](https://github.com/zhurong2020/pyobfus/tree/main/skills).
- The [VS Code extension](https://marketplace.visualstudio.com/items?itemName=zhurong2020.pyobfus)
  provides inline risk diagnostics and traceback reversal; it is also on
  [Open VSX](https://open-vsx.org/extension/zhurong2020/pyobfus).
- [`zhurong2020/pyobfus-action@v1`](https://github.com/marketplace/actions/pyobfus-scan-and-build)
  runs scans or verified builds in GitHub Actions with SARIF support.
- The stable JSON CLI includes reason codes and an `ai_hint` next action.
- Agent-readable project facts are published in
  [`llms.txt`](https://github.com/zhurong2020/pyobfus/blob/main/llms.txt), while
  contributor instructions live in
  [`AGENTS.md`](https://github.com/zhurong2020/pyobfus/blob/main/AGENTS.md).

All Agent guidance is public and human-auditable. pyobfus does not serve hidden
instructions or different facts based on User-Agent.

## Configuration

Generate a starting configuration or use a named preset:

```bash
pyobfus --init src/
pyobfus src/ -o dist/ --preset django
pyobfus --list-presets
```

Community presets include `safe`, `balanced`, `aggressive`, `fastapi`, `django`,
`flask`, `pydantic`, `click`, `sqlalchemy` and `ml`. See the
[documentation home](https://pyobfus.readthedocs.io/) and
[`pyobfus --help`](https://github.com/zhurong2020/pyobfus/blob/main/pyobfus/cli.py)
for current options. Optional `max_files` and `max_total_loc` values are
user-selected safety limits at every tier.

## How do I debug an obfuscated crash with an AI assistant?

Build with `--save-mapping mapping.json`, keep that file private, then run:

```bash
pyobfus --unmap --trace error.log --mapping mapping.json
```

The restored identifiers can be read by you or an AI assistant without giving
the customer your mapping or original source. `--trace-marker` can also stamp
generated files with the exact recovery command.

## Purchase Professional Edition

Professional Edition is **$45 USD, one time**—not a subscription. A five-day
trial requires no registration or card:

```bash
pyobfus-trial start
```

The trial is an honor-system convenience control, not a security boundary.
Visit the [product and purchase page](https://zhurong2020.github.io/pyobfus/#purchase-professional-edition)
for current payment methods, refund terms and purchase steps. After purchase,
use the [license activation guide](https://pyobfus.readthedocs.io/en/latest/LICENSE_ACTIVATION_GUIDE/).

Runtime-backed Pro artifacts depend on the separately redistributable,
pure-Python `pyobfus-runtime` package. Target machines do not need the complete
proprietary builder or a licence key.

## Security and limitations

Obfuscation raises the cost of inspection; it does not make client-side Python
irreversible. Runtime-decrypted material can be observed by a determined
attacker. Keep credentials and authorization decisions behind environment,
secret-manager or server boundaries.

- [Threat model](https://pyobfus.readthedocs.io/en/latest/THREAT_MODEL/)
- [Support matrix](https://pyobfus.readthedocs.io/en/latest/SUPPORT_MATRIX/)
- [Release provenance](https://github.com/zhurong2020/pyobfus/blob/main/docs/RELEASE_PROVENANCE_VERIFICATION.md)
- [Security policy](https://github.com/zhurong2020/pyobfus/blob/main/SECURITY.md)

## Comparison and deployment guides

- [Comparison overview](https://pyobfus.readthedocs.io/en/latest/COMPARISON/)
- [vs PyArmor](https://pyobfus.readthedocs.io/en/latest/compare/pyarmor/)
- [vs Nuitka](https://pyobfus.readthedocs.io/en/latest/compare/nuitka/)
- [PyInstaller cookbook](https://pyobfus.readthedocs.io/en/latest/PYINSTALLER_COOKBOOK/)
- [Compiled-packaging cookbook](https://github.com/zhurong2020/pyobfus/blob/main/docs/COMPILED_PACKAGING_COOKBOOK.md)
- [Integration testing](https://pyobfus.readthedocs.io/en/latest/INTEGRATION_TESTING/)

## Architecture and development

The product line separates the Apache-2.0 Core, proprietary Pro builder,
redistributable runtime, MCP package, editor extension and GitHub Action. See:

- [Project structure](https://pyobfus.readthedocs.io/en/latest/PROJECT_STRUCTURE/)
- [Contributing guide](https://github.com/zhurong2020/pyobfus/blob/main/CONTRIBUTING.md)
- [Developer instructions](https://github.com/zhurong2020/pyobfus/blob/main/AGENTS.md)
- [Changelog](https://github.com/zhurong2020/pyobfus/blob/main/CHANGELOG.md)

## Community and citation

Use [GitHub Issues](https://github.com/zhurong2020/pyobfus/issues) for bugs and
[Discussions](https://github.com/zhurong2020/pyobfus/discussions) for questions
and ideas. Citation metadata is in
[`CITATION.cff`](https://github.com/zhurong2020/pyobfus/blob/main/CITATION.cff),
with archival DOI [10.5281/zenodo.20846053](https://doi.org/10.5281/zenodo.20846053).

Core is Apache-2.0; Professional implementation is proprietary. See
[`LICENSE-NOTICE.md`](https://github.com/zhurong2020/pyobfus/blob/main/LICENSE-NOTICE.md).
