# Cross-file function-local names: review evidence

Status: review rework on `feat/crossfile-local-names`, awaiting Claude re-review.
Rebased onto main `33837b6` (includes the released 0.5.32 / #58 fixes).
No version change, release, tag, or merge.

## Problem and edition decision

Commercial source-distribution users build directories to retain working imports.
The published 0.5.31 build rewrites module names but leaves each method's `result`
and other function locals readable. This is a Community local transformation:
reliable obfuscation and reverse debugging, rather than runtime/distribution
control or an organizational service. It follows `EDITION_BOUNDARY_POLICY.md`;
no Pro or MCP release changes are included.

## Design

`core/function_locals.py` uses Python's symbol table with explicit AST scope
traversal. Defaults/decorators use the enclosing scope; functions, lambdas,
classes and comprehensions retain their lexical binding rules. PEP 709 inlined
comprehensions receive a synthetic scope, so iteration targets cannot shadow
outer names accidentally. Walrus bindings resolve to their enclosing function.
Nonlocal reads, writes and declarations share the outer binding's replacement;
explicit globals share the existing module mapping and declaration.

Phase 1 reserves source identifiers and configured exclusions before module
allocation, then allocates locals in sorted file order, deterministic function
traversal and sorted binding order using the same build-wide allocator. Workers
receive frozen plans keyed by full source span, node type and attribute,
including explicit aliases for preserved
function-local imports and protected lexical references
that the existing import/module passes must leave alone. Workers allocate no
local names. Reusing an orchestrator resets its allocation state.

Local reverse mappings are kept separately from importable exports. Mapping v1's
`modules` retains module-level `{original: obfuscated}` entries. The optional
`locals` section uses `{module: {obfuscated: original}}`, and `global` still
contains local reverse entries for existing unmap consumers. Loading old v1
files without `locals` is supported, and merge preserves local reverse entries.
CLI total-name statistics include locals, while mapping `original_names` retains
its module-level meaning. `local_names_obfuscated`, `local_functions_skipped`
and `local_files_skipped` are aggregated per file. A lexical planning ValueError
skips local renaming only in that file, discards partial allocations, and emits
a library/CLI warning; other files continue.

## Configuration and conservative preservation

`crossfile_local_names: true` is the dataclass/YAML/schema default; CLI supports
`--crossfile-local-names` and `--no-crossfile-local-names`, with explicit CLI
values taking precedence over YAML. All presets, including safe and framework
presets, inherit true. Function locals are implementation details; parameters,
method names, attributes and class-body bindings remain unchanged. The FastAPI
fixture confirms this choice for one pinned application, not all frameworks.

Dunder names, exclusions, `super` and `__class__` stay intact. Lambdas and
comprehensions retain their own bindings while references to captured function
locals follow the outer mapping. String literals and f-string text stay intact.

References/calls to `eval`, `exec`, `locals`, and zero-argument calls to `vars`
or `dir` cause conservative skips. Enclosing scopes are skipped too because
child reflection can observe captured names. Unaliased dotted imports skip the
containing scope: adding an alias would change the bound object. Files with
generic type parameters skip local renaming until their annotation scopes are
fully supported. Names needed by string/future annotations and private class
name mangling are preserved. Normal annotation expressions, including Python
3.14 annotation scopes, are covered by behavioral tests.

## Example: calculator.py

Published 0.5.31 / switch disabled:

```python
def add(self, a, b):
    result = a + b
    self._record_operation('add', a, b, result)
    return round(result, self.precision)
```

New default:

```python
def add(self, a, b):
    I5 = a + b
    self._record_operation('add', a, b, I5)
    return round(I5, self.precision)
```

Parameters and the method name remain unchanged; the next method's `result`
receives its own unique name (`I6`).

## Validation after review rework on WSL / Python 3.12.3

All roots ran separately with normal HOME (no home-state workaround).

| Command | Result |
|---|---|
| `scripts/check.sh` | all checks passed: Black, Ruff, mypy, metadata, agent twins, README links, strict MkDocs |
| `venv/bin/pytest tests/` | 1437 passed, 1 skipped, 7 warnings; core coverage 91% |
| `venv/bin/pytest pyobfus_mcp/tests/` | 99 passed |
| `venv/bin/pytest integration_tests/` | 12 passed, 1 skipped (optional framework stack absent) |
| `venv/bin/pytest pyobfus_runtime/tests/` | 24 passed |
| `venv/bin/python scripts/dogfood/run.py all --out /tmp/dogfood` | A/B/D passed; A findings remain observational; D byte-identical under varied environment |
| Separate venv: `pip install -e ./pyobfus_runtime -e ".[dev]" -r integration_tests/frameworks/requirements.txt`, then `pytest integration_tests/test_framework_fastapi.py --no-cov` | 3/3 passed; 7 HTTP scenarios equal; private mapping and traceback checks passed |
| `venv/bin/python scripts/generate_vscode_schema.py --check` | schema current |
| VS Code lint, typecheck, pretest and Extension Host tests | 53 passed |
| Local scope, decorators/bases and mapping tests (`--no-cov`) | 53 passed on Python 3.10, 3.13 and 3.14; Python 3.12 covered by full core suite |

The 3.10 checks used a separately installed editable environment; supplemental
3.13/3.14 checks used their interpreters with the local venv's pure Python test
dependencies on PYTHONPATH. Python 3.9/3.11 and other OS coverage is left to the
existing PR CI matrix. Match fixtures explicitly skip on 3.9.

Independent public-package comparison: installed PyPI `pyobfus==0.5.32` in an
isolated target and ran it outside the checkout. All four generated multifile
Python files were byte-identical to this branch with the switch disabled.
The enabled multifile build's stdout was byte-identical to the original.
Mapping save/load and CLI `--save-mapping` / `--unmap` behavior are tested,
including no unmatched-name warnings for known local identifiers.

`all` intentionally runs A/B/D; Lane C is opt-in/release-time and was not run.
No artifact was released. Full raw local logs are retained in the ignored
`docs/internal/geo-2026-10/crossfile-local-names-evidence/` directory.

## Review findings addressed

- Nested MatchAs captures sharing a start coordinate now use full-span/type edit
  keys. Execution tests cover list/mapping captures, parenthesized captures and
  three nested captures, including process-pool workers.
- Mapping v1 retains `modules` semantics and adds `locals`; old-file load,
  forward-only load, save/load, merge, marker identity and CLI/MCP unmap are tested.
- A failed local plan leaves the remaining project build running, reports a
  warning and skip counts, and clears stale warnings on a reused orchestrator.
- The landing page and both `llms.txt` copies describe the published behavior.
- Support matrix and changelog document undetected frame-based reflection.
- Global-declaration handling belongs to the Added entry for this new feature.
- MkDocs excludes this maintainer evidence file from the product documentation.

The separately reported decorator/base/metaclass/lambda NameError was fixed in
#58 and released in 0.5.32. This branch now includes that fix and its regression
test; it is no longer an outstanding issue in the rebased implementation.

## Remaining limits for review

Generic type parameter files currently get less local renaming. Explicit
reflection detection does not cover arbitrary aliases, externally supplied
inspection helpers, `inspect.currentframe().f_locals`, `sys._getframe().f_locals`
or all dynamically constructed annotation strings. The disabled-output comparison covers the maintained multifile example,
not an exhaustive old-release corpus. Framework evidence covers the pinned
FastAPI fixture only. These limitations must not become claims of general
runtime correctness or stronger protection.
