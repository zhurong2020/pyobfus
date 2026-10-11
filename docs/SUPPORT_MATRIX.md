# Support matrix

What is actually verified, by what, as of 2026-10-10 (`pyobfus` 0.6.1 /
`pyobfus-mcp` 0.3.12 / `pyobfus-runtime` 0.1.0 / VS Code extension 0.4.3 /
`pyobfus-action` 1.0.1).

Four labels, used strictly:

| Label | Meaning |
|---|---|
| **tested** | An automated check runs it on every push. The cell names that check. |
| **tested weekly** | An automated check runs it on a schedule and when its own files change, not on every push. The cell names the workflow and a green run. |
| **verified once** | A human reproduced it on a stated date. It is not re-run automatically, so it can rot. |
| **advisory-only** | Documented recipe or design intent, no automated or recorded verification. Treat as a starting point, not a guarantee. |

The rule this table is written under: **a cell that cannot point at a specific
CI job, test file or dated record is advisory-only**, regardless of how
confident anyone feels about it.

## Python versions and operating systems

| Surface | Linux | macOS | Windows | Evidence |
|---|---|---|---|---|
| Core obfuscator, 3.9–3.14 | tested | tested | tested | `ci.yml` job `test`, 3 OS × 6 versions |
| `pyobfus-runtime`, 3.9–3.14 | tested | tested | tested | PyPI `0.1.0` clean install passed; local boundary suite 2/2; CI run [`35931303008`](https://github.com/zhurong2020/pyobfus/actions/runs/35931303008) and release run [`35931605485`](https://github.com/zhurong2020/pyobfus/actions/runs/35931605485) built, inspected, and published the standalone wheel |
| End-to-end CLI (obfuscate, execute output) | tested (3.11) | advisory-only | tested (3.11) | `ci.yml` job `integration` runs `integration_tests/` on Ubuntu and Windows; single-file and cross-file outputs are executed and compared with the originals |
| `pyobfus-mcp` server | tested (3.11, 3.13) | advisory-only | advisory-only | `ci.yml` jobs `mcp-tests` (3.11), `mcp-sdk-latest` and `mcp-sdk-2x` (3.13) |
| VS Code extension | tested (Node 22, Python 3.12) | advisory-only | advisory-only | `vscode-extension-ci.yml`, headless xvfb |
| `pyobfus-action` composite wrapper | tested | tested | tested | External `zhurong2020/pyobfus-action` CI runs the local action against real clean/risky fixtures on all three hosted-runner OS families; Action release 1.0.1 |
| Free-threaded 3.14 (`--disable-gil`) | verified once, 2026-08-20 | advisory-only | advisory-only | Manual run of the full core suite plus an end-to-end smoke on a downloaded free-threaded build; not in CI. See [`PYTHON314_FREETHREADING.md`](PYTHON314_FREETHREADING.md) |

Reading this honestly: the **transformation** is broadly tested, and basic
generated-code execution is now enforced on Linux and Windows. macOS output
execution remains advisory-only, as do heavyweight framework and packaging
combinations; those platform-specific failures can still reach users first.

## What gets renamed

| Build | Renamed | Not renamed | Evidence |
|---|---|---|---|
| Single file (or `--no-cross-file`) | Module-level names, method names, local variables; parameters only with explicit `--no-preserve-param-names` (unverified keyword/signature compatibility) | Parameters by default (all presets); names of functions/classes defined inside functions and class-body annotated field names (since 0.6.0); instance attributes (`self.precision`). Each file is renamed on its own, so imports between modules of one project break in this mode | `tests/`, single-file end-to-end in `integration_tests/` |
| Directory, default cross-file mode | Module-level classes, functions and variables, consistently in every file, plus the import statements that reference them; function locals (since 0.6.0) | Methods, attributes, parameters; locals in reflection-sensitive functions | `integration_tests/test_cli_end_to_end.py` (multifile); `tests/test_crossfile_decorators_bases.py` covers decorators, base classes, metaclasses and lambdas (fixed in 0.5.32); new local scope tests in `tests/test_crossfile_function_locals.py`; historical 0.5.30 scope observed on 2026-10-07, see the [selling guide](guides/protect-python-before-selling.md#what-you-get-measured) |

Single-file parameter preservation is the default for every preset. Explicit
YAML `preserve_param_names: false` or `--no-preserve-param-names` retains legacy
renaming with a warning; keyword calls and signature compatibility remain
unverified. Restore true with YAML or `--preserve-param-names`. Rebuilding can
change mapping numbers: old mappings cannot decode new artifacts. `--check`
reports a medium advisory for bare same-file function names called with keywords
or `**` forwarding when renaming is enabled. This is a syntactic candidate
check, not callable resolution; absence of a finding does not establish safety.
Existing exit-code rules are unchanged. Default (cross-file) directory builds preserve
parameters even with explicit false; legacy `--no-cross-file` directory builds
rename them when false is set.

Directory builds rewrite the imported symbol in `from M import X as A` using
M's export mapping, while preserving the explicit local alias A (including
`X as X`) and its references. Explicit aliases remain preserved in functions,
classes and conditional imports, with `crossfile_local_names` on or off;
`__all__` and downstream re-exports retain the alias spelling. Third-party
imports keep their original symbol and alias names. Unaliased imports retain
the existing cross-file naming rules. Execution evidence:
`integration_tests/test_crossfile_import_alias.py`.

**Limitation H:** `import pkg.core as engine` binds the module alias correctly,
but `engine.scale()` still uses the original attribute spelling. If `scale`
was renamed in the target module, execution raises `AttributeError`.
Module-object attribute rewriting remains unsupported; preserve those names
with `exclude_names`. The same test file locks this current limitation.

Single-file builds preserve the spelling of a function or class whose lexical
parent is a function (including async functions and methods), even inside
control-flow suites. A class body starts its own scope: its methods and nested
classes remain eligible for renaming. Because the single-file map is keyed by
spelling rather than scope, a protected spelling is preserved throughout that
file, including same-named module definitions, parameters and attributes.
Other module definitions, methods and unannotated class attributes keep their
existing renaming policy. This preserves nested definitions' `__name__`, not
the full `__qualname__` when an enclosing module function or class is renamed.

Class-body `AnnAssign` Name targets are also preserved throughout the file.
This framework-independent rule protects annotated dataclass, NamedTuple,
TypedDict, pydantic and attrs fields, including fields declared by same-file
parents, `InitVar` and `ClassVar`. Module/method-local annotations and
Attribute/Subscript annotation targets keep their existing policy. Generated
identifiers skip preserved field spellings to avoid collisions.

Field preservation does not preserve renamed class identities or enclosing
`__qualname__` prefixes in repr; use `exclude_names` for those identities when
needed. Unannotated fields (such as legacy attrs `x = attr.ib()`), functional
schema declarations and dynamically generated/external field declarations
are not detected: preserve required names explicitly with `exclude_names`.
Unannotated Enum assignments keep their existing policy; Enum behavior is not
validated by this field fix. Methods and instance attributes have no new
preservation rule, except when their spelling matches a preserved field.
Behavioral field evidence: `tests/test_singlefile_class_fields.py`.
Evidence: `tests/test_singlefile_nested_definition_names.py`.

Since 0.6.0, `crossfile_local_names` defaults to `true`, including `safe`
and framework presets. It preserves parameters, class-body bindings, lambda and
comprehension bindings, names of functions and classes defined inside functions
(their `__name__`/`__qualname__` stay observable, e.g. Flask app-factory endpoints
and Click commands), dunder names and `exclude_names`, while updating captured
function locals. Direct `locals()`, `eval`, `exec`, zero-argument `vars()` or
`dir()` cause conservative function/ancestor skips, counted as
`local_functions_skipped`. Unaliased dotted imports skip their containing scope;
files with generic type parameters currently skip local renaming. Local names
used in string/future annotations and class names needed for private name
mangling are preserved. Disable with
`--no-crossfile-local-names` or YAML `obfuscation.crossfile_local_names: false`
for the 0.5.32 naming behavior. Lexical planning failures skip
local renaming for that file with a warning and `local_files_skipped` /
`local_functions_skipped` counts. Frame-based reflection such as
`inspect.currentframe().f_locals.get("secret_total")` or
`sys._getframe().f_locals` is not detected: reading by the original name can fail
after renaming. Disable local renaming for that code. Always run application tests.

Directory class bodies preserve references to names already bound in their
namespace, in execution order; earlier references and method/lambda bodies
still use module globals. Comprehensions evaluate only their outermost iterable
in the class namespace. Nested classes start a fresh namespace; an explicit
`del` removes a binding. An annotation without a value does not bind a name.
**Limitation:** bindings inside `if`, `try`, `for` and `while` are conservatively
treated as already bound, including within the suite and afterwards, even if
that path never executes. There is no control-flow analysis of conditional
class bindings; a reference that falls back to a renamed module global on an
untaken path can therefore fail. This policy applies with local renaming both
on and off. Behavioral evidence: `tests/test_crossfile_classbody_shadow.py`.

## Pre-flight secret screening

Community `--check` reports `hardcoded_secret`: medium for high-signal
credential shapes, info for sensitive names with a non-placeholder literal.
It checks assignments, annotations with literal values, defaults, keywords
and dictionary values; ignores docstrings, annotation strings, environment
lookups, dynamic expressions, placeholders, URLs and common field names.
No entropy detection or value output; exit codes remain unchanged. This is a
coarse screen; use gitleaks or detect-secrets for full scanning. Evidence:
`tests/test_preflight_secrets.py` (including text/JSON/SARIF/MCP privacy) and
`tests/test_sarif_preflight.py`. See [rule details](SARIF_CODE_SCANNING.md#hardcoded-secret-screening-community).

## Framework presets

Every preset is tested for **what it excludes**. Only `fastapi` is also
tested by obfuscating a real application and running it; the others are not.

| Preset | Preset contents | Real app runs after obfuscation | Evidence |
|---|---|---|---|
| `fastapi` | tested | tested weekly (not every push): `framework-lane.yml` on Ubuntu and Windows, Python 3.12; first green run [`37608069469`](https://github.com/zhurong2020/pyobfus/actions/runs/37608069469) on 2026-10-07 | `tests/test_framework_presets.py` for the preset contents. `integration_tests/test_framework_fastapi.py`: a three-module FastAPI 0.142.2 + Pydantic 2.13.5 app built as a directory with `--preset fastapi`; 7 HTTP scenarios (including 422 validation errors) answer identically to the original, the mapping stays out of the build, and a traceback from the build unmaps. One small app, pinned versions |
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
| PyInstaller | tested (CI, Linux CPython 3.12) | `integration_tests/test_packaging.py`: PyInstaller 6.22.3 `--onefile`, Linux CPython 3.12, stdlib-only pricing CLI; three tiers match the original and a bundled traceback reverses through CLI JSON. Since 2026-10-11 also a multi-module fixture (`integration_tests/packaging/multimodule/`: subpackage, relative imports, entry script) built as a directory: no renamed original name in any frozen module, output matches, and a three-module traceback reverses. `packaging-lane.yml` passed its [first hosted run](https://github.com/zhurong2020/pyobfus/actions/runs/37690761303) on 2026-10-08; it runs weekly, on main pushes and on PRs that change the obfuscator (`pyobfus/**`), the fixtures or the workflow. Other platforms and third-party projects remain advisory-only; `--check` still emits a `compatibility_advisory` |
| Nuitka / Cython compiled packaging | tested (CI, Linux CPython 3.12) | `integration_tests/test_packaging.py`: Cython 3.3.0 / Nuitka 4.2.2 `--module`, Linux CPython 3.12, single module. Both native modules execute without their source, match original behavior, omit the fixture's original function/class names, and reverse a compiled traceback through CLI JSON. `packaging-lane.yml` passed its [first hosted run](https://github.com/zhurong2020/pyobfus/actions/runs/37690761303) on 2026-10-08; it runs weekly, on main pushes and on PRs that change the obfuscator (`pyobfus/**`), the fixtures or the workflow. Historical public-package measurements remain in [`COMPILED_PACKAGING_COOKBOOK.md`](COMPILED_PACKAGING_COOKBOOK.md). Since 2026-10-11 also Nuitka `--mode=standalone` of the multi-module fixture (patchelf 0.19.1.0): output matches, `main.bin` contains none of the renamed names, and a three-module traceback reverses. Nuitka onefile, whole-package Cython, macOS and Windows remain advisory-only |
| Import hook — stdlib `importlib` loader | tested | `integration_tests/test_examples.py` — obfuscated module loads through the custom hook; original identifiers never reach the loaded source |
| Import hook — SOURCEdefender `.pye` encrypted files | advisory-only | [`IMPORT_HOOK_COOKBOOK.md`](IMPORT_HOOK_COOKBOOK.md); the stdlib path above is what CI covers |
| Model serving | advisory-only | [`MODEL_SERVING_COOKBOOK.md`](MODEL_SERVING_COOKBOOK.md) |
| Reverse stack-trace mapping workflow | tested | `tests/test_unmap_cli.py`, plus `integration_tests/test_examples.py` — the `examples/ai_debugging/` round trip (obfuscated crash → `--unmap` restores originals) runs on every push |
| Pro artifact on a target without `pyobfus_pro` | tested | Standalone runtime wheel installed in clean local and CI environments; `pyobfus_pro` was not importable, the runtime API executed, and wheel inspection found no Pro, transformer, licence-client, or CLI files. CI evidence: run [`35931303008`](https://github.com/zhurong2020/pyobfus/actions/runs/35931303008), `runtime-wheel` job. |
| Action `check` mode → SARIF/JSON/step outputs | tested | External Action CI runs clean and risky fixtures, both finding gates, and a nonexistent-path tool error; the public repo also documents the contract in [`SARIF_CODE_SCANNING.md`](SARIF_CODE_SCANNING.md). |
| Action `build` mode → generated output | tested for wrapper behavior; deployment remains caller-owned | External Action CI exercises build mode and syntax verification. The Action does not vendor dependencies into the output: runtime-backed Pro artifacts still require the compatible `pyobfus-runtime` package in the target environment. |

First-batch examples executed by the `integration` job (Ubuntu and Windows),
each obfuscated, run, and compared against the original behavior:
`simple.py` and `multifile/` via `test_cli_end_to_end.py`; `string_encoding.py`,
`keyword_arguments.py` (parameters preserved by default), `ai_debugging/`, and
`import_hook/` via `test_examples.py`. The remaining examples
(`pyinstaller/`, `compiled_packaging/`) use pinned optional toolchains in the
separate `packaging-lane.yml` workflow, not the normal integration job. Pro
examples require a license and are not part of these Community packaging checks.

## Dependency and SDK ranges

| Dependency | Range | Status | Evidence |
|---|---|---|---|
| `mcp` SDK 1.x | `>=1.27,<2.0` (shipped) | tested | `ci.yml` job `mcp-sdk-latest`, resolves to newest 1.x |
| `mcp` SDK 2.x | not shipped; cap holds it back | tested anyway | `ci.yml` job `mcp-sdk-2x` installs over the cap and runs the whole MCP suite. See [`MCP_SDK_2X_SPIKE.md`](MCP_SDK_2X_SPIKE.md) |
| `pyobfus` floor for the MCP server | `>=0.5.18` | tested | MCP suite installs the local Core checkout |
| `pyobfus-runtime` for the builder/artifacts | `>=0.1,<1` | tested | Declared by Core metadata; runtime boundary suite and clean-wheel install verify the current 0.x contract |
| `pyobfus-action` → `pyobfus` | latest by default; exact `pyobfus-version` supported | tested | External Action CI covers default install and version pinning. Action and Core versions are independent; pin for reproducible CI. |

## How to change a cell

Move a cell up by adding the check, not by gaining confidence. A cell becomes
**tested** when a named CI job runs it on every push; it becomes **verified
once** when someone records the run and the date in a document that this table
links to. Downgrade a cell the moment its evidence stops running.
