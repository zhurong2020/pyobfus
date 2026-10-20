# Python 3.15 validation

Scope: the next Core release, runtime metadata and MCP metadata; CPython
3.15.0 on Linux x86_64, tested on 2026-10-20. Core 0.7.5 remains the released
baseline. This work does not publish a release or change edition boundaries.
Compatibility and local verification remain Community capabilities.

## Defects and audit

`tests/test_python315.py` executes original and generated files in separate
processes, with the generated directory as cwd and an isolated home. Four
initial native regressions failed against unmodified `origin/main` (`3283e0d`):
lazy `from` side effects moved before `START`, and dictionary unpacking failed
with `AttributeError: 'NoneType' object has no attribute '_fields'`, at both
one and four workers. The published 0.7.5 probe reproduces the same defects.

- **PY315-1:** `ImportRewriter` shallow-copies the original node and replaces
  only its alias list, retaining `is_lazy` and other original fields.
- **PY315-2:** the first failure was `ImportedAccessVisitor.visit_ListComp`
  calling `visit(None)` during enum injection analysis. All six custom
  comprehension visitors now guard optional expressions: import resolution,
  class bindings, function locals, module attributes, scoped imports and
  local-name rewriting. Ordinary generic visitors already skip absent values.
- **Lexical scopes:** native 3.15 uses `<lambda>` and `<genexpr>` where earlier
  symbol tables use `lambda` and `genexpr`. Both lexical planners accept these
  spellings only for anonymous AST scopes. Existing tests cover same-line
  lambdas, signatures, generators, closures and imported aliases.

The import-constructor audit covered Core and Pro, including `build_fusion`,
seal, opacity, vault, scrub, string AES, string encoding and import
obfuscation. Only `ImportRewriter` reconstructs a source import; the other
constructors inject new helpers. Existing nodes mutated in place retain their
fields. Seal/opacity/vault helper coalescing skips lazy imports. Pro importlib
rewriting leaves explicit lazy imports intact; if `__lazy_modules__` is
referenced, it conservatively leaves all imports in that module intact because
the control list may be dynamic.

Import/export analyzers record lexical bindings without executing imports;
a lazy binding still identifies its declared module/symbol on first use.
They do not promise eager initialization. Package attribute proofs reject
packages containing lazy imports or `__lazy_modules__`; lazy dotted imports
cannot prove eager child initialization for unrelated reads. Direct lazy
aliases resolve when used. Unproved accesses retain the existing warning and
preservation guidance; this is a conservative limitation, not a timing repair.
Incremental module-attribute analysis invalidates the previous cache signature.

An automated full comparison of `dir(builtins)`, all AST `_fields`, and all
available `_field_types` between native 3.14 and 3.15 found:

| Surface | Difference |
|---|---|
| Builtins | `ImportCycleError`, `__lazy_import__`, `frozendict`, `sentinel` added; none removed |
| `Import`, `ImportFrom` | optional `is_lazy` added |
| `DictComp` | `value` becomes optional; field names unchanged |

The new builtins are reserved on all builders. `__lazy_modules__` is already
protected by the dunder rule. Source/report/mapping paths use explicit UTF-8 or coding-cookie-aware reads;
non-ASCII input and output are exercised on 3.15. The native unparser retains
new syntax, so lazy imports and unpacking comprehensions require Python 3.15
at runtime. This work does not lower new language syntax to older Python.
Ordinary source built on 3.15 was also parsed and executed on 3.10, including
f-strings, starred tuple subscripts, Unicode and cross-file imported symbols.

## Verification record

The implementation PR records the exact head, CI runs, separated test-root
results, full standard-library diff inventory and clean-install results.
Local raw evidence is retained under the ignored
`docs/internal/codex-2026-10/py315-evidence/` directory, including
`main-regressions.log`, `main-traceback.txt`, `ast-delta.json`,
`ast-source-audit.txt`, `version-enumeration-audit.txt`, `tests-*.log`,
`stdlib-*.json`, `portable315-to310.json`, `adversarial-*`, and clean-wheel logs.

The Core CI matrix retains 3.9–3.14 and adds 3.15 on Linux, Windows and macOS.
CLI integration and MCP checks also include 3.15; standalone runtime wheels
are installed and tested on 3.12 and 3.15. Stable 3.15 is requested directly;
`allow-prereleases` is unnecessary. Black 26.10.1 recognizes `py315`; its
existing dependency floor is unchanged. Mypy and Ruff retain the Python 3.9
minimum target. Other workflows have fixed interpreters rather than additional
support matrices; their unrelated packaging/framework claims are unchanged.

Runtime classifier changes alone may pass the release-version guard; all
other metadata (including dependencies) and runtime source still require a
version bump. `tests/test_runtime_version_guard.py` verifies that classifier
changes cannot waive simultaneous dependency or code changes.

## Limits

L3 artifacts contain interpreter-specific marshal/bytecode and require the
same CPython minor version for building and execution. Synthetic source
transforms and L3/seal/vault artifacts execute in subprocesses on 3.15 with
isolated license state. The existing `requires_python_min` policy is a minimum
version gate, not a bytecode cross-minor portability check.

The standard-library corpus is a stress probe, not a promise that arbitrary
stdlib internals can be safely renamed. Unproved module attributes, dynamic
exports, interpreter-owned helpers and C-extension name contracts retain the
existing [support-matrix limits](SUPPORT_MATRIX.md). Every failed smoke is
listed in the PR rather than counted as successful execution.

Python 3.9 and 3.11 are unavailable locally; hosted CI covers them. Windows
and macOS depend on hosted CI rather than local testing. Free-threaded 3.15,
compiled/frozen 3.15 packages and exhaustive third-party frameworks are not
validated by this change. Independent review, merge and release remain pending.

## Standard-library and adversarial probes

The nine inputs are `json`, `email`, `logging`, `asyncio`, `unittest`, `xml`,
`importlib`, `http`, and `calendar.py`. On both 3.12 and 3.14 builders the source
is the 3.12 standard library. Main and branch complete every build, and every
one/four-worker pair is byte-identical. Eight inputs are also byte-identical
between main and branch. Only `unittest` differs, on both builders, in these
12 files: `__init__.py`, `_log.py`, `async_case.py`, `case.py`, `loader.py`,
`main.py`, `mock.py`, `result.py`, `runner.py`, `signals.py`, `suite.py`,
`util.py`. Reserving `sentinel` retains that global's spelling in `mock.py`
and shifts later global allocations and synchronized references; these are
expected rename-table changes, not a new syntax requirement. Rebuilding main
with only `sentinel` preserved reproduces the branch bytes exactly on both
builders (`sentinel-diff-proof.json`).

The same nine inputs from the native 3.15 standard library all build. Original
imports pass 9/9; generated imports pass 7/9. Both main and branch fail for
`json` (unrewritten `scanner.make_scanner`) and `unittest` (unrewritten
`util.three_way_cmp` / `case.TestCase`). These are inherited product defects
within the existing module-attribute proof limitations, not new 3.15 parser
failures. No new smoke regression was observed. Smoke processes run from the
artifact parent, avoiding stdlib sibling files shadowing unrelated top-level
imports. Empty-package imports such as `xml` are intentionally only basic
import smoke, not full stdlib API coverage.

The historical H proof corpus is re-exercised through its three maintained
regression modules on main and branch. The I review harness runs all 37 cases
from both JSON corpora, with local renaming on/off; no case working on main
regresses on the branch. Raw output and exact changed-file lists accompany the
local evidence.

VS Code lint, typecheck and pretest pass; VS Code 1.141.0 under WSLg runs all
53 extension tests with the native 3.15 interpreter. A local copy of the
unchanged Action driver exercises check/build JSON and step-output contracts
against the installed candidate wheel; its generated canary prints `25`.
This driver smoke does not replace the external Action repository's hosted
composite three-platform CI.

One existing scrub test used prose with discarded punctuation as invalid
base64. Python 3.15 decodes that input and correctly rejects the resulting
short encrypted blob. The fixture now uses a single sextet, an invalid base64
length on every supported interpreter; runtime decoding behavior is unchanged.
