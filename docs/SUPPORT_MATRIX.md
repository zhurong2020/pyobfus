# Support matrix

What is actually verified, by what, as of 2026-09-12 (`pyobfus` 0.5.25 /
`pyobfus-mcp` 0.3.12 / VS Code extension 0.4.3).

Three labels, used strictly:

| Label | Meaning |
|---|---|
| **tested** | An automated check runs it on every push. The cell names that check. |
| **verified once** | A human reproduced it on a stated date. It is not re-run automatically, so it can rot. |
| **advisory-only** | Documented recipe or design intent, no automated or recorded verification. Treat as a starting point, not a guarantee. |

The rule this table is written under: **a cell that cannot point at a specific
CI job, test file or dated record is advisory-only**, regardless of how
confident anyone feels about it.

## Python versions and operating systems

| Surface | Linux | macOS | Windows | Evidence |
|---|---|---|---|---|
| Core obfuscator, 3.9–3.14 | tested | tested | tested | `ci.yml` job `test`, 3 OS × 6 versions |
| End-to-end CLI (obfuscate, execute output) | tested (3.11) | advisory-only | advisory-only | `ci.yml` job `integration` runs `integration_tests/` on ubuntu + 3.11 only |
| `pyobfus-mcp` server | tested (3.11, 3.13) | advisory-only | advisory-only | `ci.yml` jobs `mcp-tests` (3.11), `mcp-sdk-latest` and `mcp-sdk-2x` (3.13) |
| VS Code extension | tested (Node 22, Python 3.12) | advisory-only | advisory-only | `vscode-extension-ci.yml`, headless xvfb |
| Free-threaded 3.14 (`--disable-gil`) | verified once, 2026-08-20 | advisory-only | advisory-only | Manual run of the full core suite plus an end-to-end smoke on a downloaded free-threaded build; not in CI. See [`PYTHON314_FREETHREADING.md`](PYTHON314_FREETHREADING.md) |

Reading this honestly: the **transformation** is broadly tested, while
**running the generated code** is only proven on Linux. Nothing here says
macOS or Windows execution is broken; it says nobody has automated the check,
so a platform-specific breakage would reach a user before it reached us.

## Framework presets

Every preset is tested for **what it excludes**. No preset is tested by
obfuscating a real application built on that framework and running it.

| Preset | Preset contents | Real app runs after obfuscation | Evidence |
|---|---|---|---|
| `fastapi` | tested | advisory-only | `tests/test_framework_presets.py` — HTTP verbs, router paths, docstring retention |
| `django` | tested | advisory-only | same file — ORM surface, migrations, entry points, signal receivers |
| `flask` | tested | advisory-only | same file — dispatch methods |
| `pydantic` | tested | advisory-only | same file — v1 and v2 API surface |
| `click` | tested | advisory-only | same file — decorator names |
| `sqlalchemy` | tested | advisory-only | same file — ORM dunders, session surface |
| `ml` | tested | advisory-only | same file — model-serving surface |

The distinction matters. A preset test proves the exclusion list contains the
names we intended. It does not prove a Django project survives obfuscation,
because no Django project is built and served in CI. Anyone who needs that
guarantee should run `--check` and then their own test suite against the
generated output; `--verify-syntax` compiles it, which is weaker than running.

## Delivery combinations

| Combination | Status | Evidence |
|---|---|---|
| PyInstaller | advisory-only | [`PYINSTALLER_COOKBOOK.md`](PYINSTALLER_COOKBOOK.md) + `examples/pyinstaller/`; `--check` emits a `compatibility_advisory` for it |
| Nuitka / Cython compiled packaging | advisory-only | [`COMPILED_PACKAGING_COOKBOOK.md`](COMPILED_PACKAGING_COOKBOOK.md) + `examples/compiled_packaging/` |
| Import hook / encrypted files (e.g. SOURCEdefender `.pye`) | advisory-only | [`IMPORT_HOOK_COOKBOOK.md`](IMPORT_HOOK_COOKBOOK.md) + `examples/import_hook/` |
| Model serving | advisory-only | [`MODEL_SERVING_COOKBOOK.md`](MODEL_SERVING_COOKBOOK.md) |
| Reverse stack-trace mapping workflow | tested | `tests/test_unmap_cli.py`, plus `examples/ai_debugging/` |

**No `examples/` directory is executed in CI.** They were reproduced by hand
when written and are correct as recipes, but nothing re-runs them, so a
breaking change elsewhere would not fail a build. That is the single largest
gap in this table and the obvious next thing to close.

## Dependency and SDK ranges

| Dependency | Range | Status | Evidence |
|---|---|---|---|
| `mcp` SDK 1.x | `>=1.27,<2.0` (shipped) | tested | `ci.yml` job `mcp-sdk-latest`, resolves to newest 1.x |
| `mcp` SDK 2.x | not shipped; cap holds it back | tested anyway | `ci.yml` job `mcp-sdk-2x` installs over the cap and runs the whole MCP suite. See [`MCP_SDK_2X_SPIKE.md`](MCP_SDK_2X_SPIKE.md) |
| `pyobfus` floor for the MCP server | `>=0.5.18` | tested | MCP suite installs the local Core checkout |

## How to change a cell

Move a cell up by adding the check, not by gaining confidence. A cell becomes
**tested** when a named CI job runs it on every push; it becomes **verified
once** when someone records the run and the date in a document that this table
links to. Downgrade a cell the moment its evidence stops running.
